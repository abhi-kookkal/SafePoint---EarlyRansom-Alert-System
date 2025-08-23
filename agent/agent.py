import os
import time
import threading
import requests
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from pathlib import Path
from collections import deque, defaultdict
from math import log2
import socket
from typing import Optional
from fastapi import FastAPI
import uvicorn
import subprocess, platform
import re
import asyncio
import websockets
import json

# =========================
# Config
# =========================
BACKEND = "http://172.19.103.44:8000"
BACKEND_WS = "ws://172.19.103.44:8000/ws/device"   #  WebSocket endpoint

ENDPOINT_NAME = socket.gethostname()
WATCH_DIR = Path.home() / "Documents" / "Canaries"
WATCH_DIR.mkdir(parents=True, exist_ok=True)

CANARY_COUNT = 3
WRITE_RATE_WINDOW_SEC = 5
WRITE_RATE_THRESHOLD = 20
ENTROPY_THRESHOLD = 7.5
SUSPICIOUS_SCORE_THRESHOLD = 80
POLL_ACTIONS_INTERVAL = 3
# Interval (in seconds) between WebSocket status pushes
default_push_status_interval = 5
PUSH_STATUS_INTERVAL = globals().get('PUSH_STATUS_INTERVAL', default_push_status_interval)

# =========================
# Helpers
# =========================
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"
ENDPOINT_ID = get_local_ip()

def file_entropy(path: Path) -> float:
    try:
        data = path.read_bytes()[:8192]
        if not data:
            return 0.0
        from collections import Counter
        counts = Counter(data)
        total = len(data)
        return -sum((c / total) * log2(c / total) for c in counts.values())
    except Exception:
        return 0.0

def find_writer_process(path: Path):
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = p.info["name"] or ""
            cmd = " ".join(p.info.get("cmdline") or [])
            if "simulate_ransom" in cmd:
                return (name, p.info["pid"])
        except Exception:
            pass
    return ("unknown", None)

# =========================
# Backend wrapper
# =========================
class Backend:
    def __init__(self, base: str):
        self.base = base

    def register(self, endpoint_id: int, endpoint_name: str, ip: str):
        try:
            payload = {"id": endpoint_id, "hostname": endpoint_name, "ip": ip, "status": "online"}
            resp = requests.post(f"{self.base}/register", json=payload, timeout=5)
            print("[backend] registered endpoint:", resp.json())
        except Exception as e:
            print("[backend] register failed:", e)

    def send_alert(self, endpoint_id: str, ip: str, process_name: str, pid: Optional[int],
                   risk_score: int, reason: str, file_path: str, entropy: float, write_rate: int,
                   device_risk_score: int, request_terminate: bool = True):
        payload = {
            "id": pid,
            "file": file_path,
            "process": process_name,
            "user": os.environ.get("USER", "unknown"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Active",
            "riskLevel": "high",
            "ip": ip,
            "risk_score": risk_score,
            "device_risk_score": device_risk_score
        }
        print("[backend] alert sent:", payload)
        try:
            r = requests.post(f"{self.base}/alerts", json=payload, timeout=5)
            r.raise_for_status()
            print("[backend] alert sent:", reason)
        except Exception as e:
            print("[backend] alert error:", e)

    def poll_actions(self, endpoint_id: str):
        try:
            r = requests.get(f"{self.base}/actions", params={"endpoint_id": endpoint_id}, timeout=5)
            return r.json()
        except Exception:
            return []

    def mark_action_done(self, action_id: int):
        try:
            requests.post(f"{self.base}/actions/{action_id}/done", timeout=5)
        except Exception:
            pass

# =========================
# Detector
# =========================
class RansomwareDetector(FileSystemEventHandler):
    def __init__(self, backend: Backend, endpoint_id: str, local_ip: str, agent):
        super().__init__()
        self.backend = backend
        self.endpoint_id = endpoint_id
        self.local_ip = local_ip
        self.events_window = deque(maxlen=200)
        self.watch_dir = WATCH_DIR
        self.canaries = self._ensure_canaries()
        self.agent = agent

    def _ensure_canaries(self):
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        cans = [self.watch_dir / f"canary_{i}.txt" for i in range(CANARY_COUNT)]
        for c in cans:
            if not c.exists():
                c.write_text("harmless canary file\n")
        return cans

    def _is_canary(self, path: Path) -> bool:
        return str(path).startswith(str(self.watch_dir)) or any(path == c for c in self.canaries)

    def _write_rate(self) -> int:
        now = time.time()
        recent = [t for t in self.events_window if now - t < WRITE_RATE_WINDOW_SEC]
        return len(recent)

    def _risk_score(self, ent: float, rate: int, is_canary: bool) -> int:
        score = 0
        if rate > WRITE_RATE_THRESHOLD:
            score += 40
        if is_canary:
            score += 70
        if ent > ENTROPY_THRESHOLD:
            score += 30
        return min(score, 100)

    # watchdog hooks
    def on_modified(self, event): self._handle(event)
    def on_created(self, event): self._handle(event)
    def on_moved(self, event): self._handle(event)
    def on_deleted(self, event): self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        path = Path(getattr(event, "src_path", ""))
        if not path.is_file():
            return
        self.events_window.append(time.time())
        is_canary = self._is_canary(path)
        ent = file_entropy(path) if path.exists() else 0.0
        rate = self._write_rate()
        score = self._risk_score(ent, rate, is_canary)
        if score >= SUSPICIOUS_SCORE_THRESHOLD:
            proc_name, pid = find_writer_process(path)
            reason = self._build_reason(path, ent, rate, is_canary)
            self.backend.send_alert(
                endpoint_id=self.endpoint_id,
                ip=self.local_ip,
                process_name=proc_name,
                pid=pid,
                risk_score=score,
                reason=reason,
                file_path=str(path),
                entropy=ent,
                write_rate=rate,
                device_risk_score=self.agent.device_risk_score,
                request_terminate=True,
            )

    @staticmethod
    def _build_reason(path: Path, ent: float, rate: int, is_canary: bool) -> str:
        parts = []
        if is_canary:
            parts.append("canary/decoy touched")
        if rate > WRITE_RATE_THRESHOLD:
            parts.append(f"high write rate ({rate} events/{WRITE_RATE_WINDOW_SEC:.0f}s)")
        if ent > ENTROPY_THRESHOLD:
            parts.append(f"high entropy (~{ent:.2f})")
        return "; ".join(parts) or "suspicious pattern"

# =========================
# Agent
# =========================
class Agent:
    def __init__(self):
        self.backend = Backend(BACKEND)
        self.local_ip = get_local_ip()
        self.backend.register(
            endpoint_id=ENDPOINT_ID,
            endpoint_name=socket.gethostname(),
            ip=self.local_ip
        )
        self.detector = RansomwareDetector(self.backend, ENDPOINT_ID, self.local_ip, self)
        self.observer = Observer()
        self.process_file_history = defaultdict(lambda: deque(maxlen=50))
        self.process_scores = defaultdict(int)
        self.device_risk_score = 0

    # -------------------------
    # Preemptive process monitoring
    # -------------------------
    def monitor_processes_loop(self):
        while True:
            try:
                for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "open_files"]):
                    pid = p.info["pid"]
                    score = 0
                    if p.info["cpu_percent"] > 50:
                        score += 10
                    if p.info["memory_percent"] > 50:
                        score += 10
                    if p.info["open_files"]:
                        score += min(len(p.info["open_files"]), 20)
                    for f in p.info.get("open_files") or []:
                        path = f.path
                        self.process_file_history[pid].append(path)
                        if str(WATCH_DIR) in path:
                            score += 50
                    self.process_scores[pid] = min(score, 100)
                if self.process_scores:
                    self.device_risk_score = max(self.process_scores.values())
                else:
                    self.device_risk_score = 0
            except Exception as e:
                print("[agent] process monitoring error:", e)
            time.sleep(2)

        
    # -------------------------
    # New: WebSocket status push
    # -------------------------
    async def push_status_loop(self):
        while True:
            try:
                print(f"[agent] Attempting to connect to backend WebSocket at {BACKEND_WS}...")
                async with websockets.connect(BACKEND_WS) as ws:
                    print("[agent] Connected to backend WebSocket!")
                    while True:
                        status = self.get_device_status()
                        status.update({
                            "endpoint_id": ENDPOINT_ID,
                            "hostname": ENDPOINT_NAME,
                            "ip": self.local_ip
                        })
                        msg = json.dumps(status)
                        try:
                            await ws.send(msg)
                            # print(f"[agent] WS status sent: {msg}")
                        except Exception as send_err:
                            # print(f"[agent] Error sending WS message: {send_err}")
                            break  # Force reconnect
                        await asyncio.sleep(PUSH_STATUS_INTERVAL)
            except Exception as e:
                # print("[agent] push_status WS error:", e)
                # print("[agent] Troubleshooting tips: Is the backend running and accessible at the specified WS URL? Is the port correct? Any firewall issues? Retrying in 5s...")
                await asyncio.sleep(2)  # retry

    def start_push_status(self):
        def runner():
            asyncio.run(self.push_status_loop())
        threading.Thread(target=runner, daemon=True).start()

    # -------------------------
    # Existing methods
    # -------------------------
    def start(self):
        self.backend.register(ENDPOINT_ID, ENDPOINT_NAME, self.local_ip)
        self.observer.schedule(self.detector, str(WATCH_DIR), recursive=True)
        self.observer.start()
        print(f"[agent] watching: {WATCH_DIR}")
        print(f"[agent] endpoint_id={ENDPOINT_ID}  name={ENDPOINT_NAME}  ip={self.local_ip}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[agent] stopping…")
        finally:
            self.observer.stop()
            self.observer.join()

    def kill_process(self, pid: int) -> bool:
        if not pid or not isinstance(pid, int) or pid <= 0:
            return False
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            print(f"[agent] killed process (pid {pid}, name={proc.name()})")
            return True
        except Exception as e:
            print(f"[agent] failed to kill process {pid}: {e}")
        return False

    def kill_process_by_name(self, process_name: str) -> bool:
        success = False
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == process_name:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                    print(f"[agent] killed process {process_name} (pid {proc.info['pid']})")
                    success = True
                except Exception as e:
                    print(f"[agent] failed to kill {process_name} (pid {proc.info['pid']}): {e}")
        return success

    def poll_actions_loop(self):
        while True:
            try:
                actions = self.backend.poll_actions(ENDPOINT_ID)
                print("[agent] polled actions:", actions)
                for a in actions:
                    print("[agent] action item:", a, type(a))
                    if isinstance(a, dict) and a.get("action") == "kill_process":
                        pid = a.get("pid")
                        process_name = a.get("process_name")
                        success = False
                        if pid:
                            success = self.kill_process(pid)
                        elif process_name:
                            success = self.kill_process_by_name(process_name)
                        if success:
                            print(f"[agent] action completed: {a}")
                        else:
                            print(f"[agent] action failed: {a}")
                        self.backend.mark_action_done(a.get("id"))
            except Exception as e:
                print("[agent] action polling error:", e)
            time.sleep(POLL_ACTIONS_INTERVAL)


    def get_device_status(self):
        processes = [
            {"pid": pid, "name": psutil.Process(pid).name(), "risk_score": score}
            for pid, score in self.process_scores.items()
            if psutil.pid_exists(pid)
        ]
        return {
        "device_risk_score": self.device_risk_score,
        "monitored_processes": processes,
        "ip": self.local_ip
    }

# =========================
# Isolation
# =========================
def get_active_interface():
    result = subprocess.run("ip link show", shell=True, capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        match = re.match(r'^\d+: ([^:]+): <([^>]+)>', line)
        if match:
            name, flags = match.groups()
            if "UP" in flags and not name.startswith(("lo", "docker", "br-")):
                interfaces.append(name)
    return interfaces[0] if interfaces else None

def isolate_device():
    os_type = platform.system()
    interface = get_active_interface()
    if not interface:
        return {"status": "failed", "reason": "no interface"}
    try:
        if os_type == "Linux":
            subprocess.run(f"sudo iptables -A OUTPUT -o {interface} -d {BACKEND.replace('http://', '')} -j ACCEPT", shell=True)
            subprocess.run(f"sudo iptables -A OUTPUT -o {interface} -j DROP", shell=True)
        elif os_type == "Windows":
            backend_host = BACKEND.replace("http://", "")
            subprocess.run(f'netsh advfirewall firewall add rule name="EDR Backend Allow" dir=out action=allow remoteip={backend_host}', shell=True)
            subprocess.run(f'netsh advfirewall firewall add rule name="EDR Block All" dir=out action=block', shell=True)
        print(f"Device isolated (except backend): {interface}")
        return {"status": "success", "interface": interface}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# =========================
# FastAPI
# =========================
agent_app = FastAPI()
agent = Agent()

@agent_app.post("/agent/kill_process/{pid}")
def kill_process_api(pid: int):
    success = agent.kill_process(pid)
    return {"status": "success" if success else "failed"}

@agent_app.post("/agent/isolate_device")
def isolate_device_api():
    return isolate_device()

@agent_app.get("/agent/device_status")
def device_status():
    return agent.get_device_status()

# =========================
# Main
# =========================
if __name__ == "__main__":
    threading.Thread(target=agent.poll_actions_loop, daemon=True).start()
    threading.Thread(target=agent.monitor_processes_loop, daemon=True).start()
    threading.Thread(target=agent.start, daemon=True).start()
    agent.start_push_status()
    uvicorn.run(agent_app, host="0.0.0.0", port=9000)
