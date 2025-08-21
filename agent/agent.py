import os
import time
import threading
import requests
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from pathlib import Path
from collections import deque
from math import log2
import socket
from typing import Optional

# =========================
# Config
# =========================
BACKEND = "http://127.0.0.1:8000"
ENDPOINT_ID = os.environ.get("ENDPOINT_ID", "laptop-001")
ENDPOINT_NAME = socket.gethostname()
WATCH_DIR = Path.home() / "Documents" / "Canaries"
WATCH_DIR.mkdir(parents=True, exist_ok=True)

CANARY_COUNT = 3
WRITE_RATE_WINDOW_SEC = 5
WRITE_RATE_THRESHOLD = 20
ENTROPY_THRESHOLD = 7.5
SUSPICIOUS_SCORE_THRESHOLD = 80
POLL_ACTIONS_INTERVAL = 3


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
    # For hackathon demo: just return python if simulate_ransom is running
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
        """Send registration data to backend"""
        try:
            payload = {
                "id": endpoint_id,
                "hostname": endpoint_name,
                "ip": ip,
                "status": "online"
            }
            resp = requests.post(f"{self.base}/register", json=payload, timeout=5)
            print("[backend] registered endpoint:", resp.json())
        except Exception as e:
            print("[backend] register failed:", e)

    def send_alert(
        self,
        endpoint_id: str,
        ip: str,
        process_name: str,
        pid: Optional[int],
        risk_score: int,
        reason: str,
        file_path: str,
        entropy: float,
        write_rate: int,
        request_terminate: bool = True,
    ):
        # Compose alert payload as per new API requirements
        payload = {
            "id": pid,  # You may want to increment or generate this dynamically
            "file": file_path,
            "process": process_name,
            "user": os.environ.get("USER", "unknown"),
            "timestamp": "2025-08-21 22:14:19",  # Use provided local time
            "status": "Active",
            "riskLevel": "high"
        }
        # If you want to keep the old payload for other uses, consider renaming or duplicating it.
        try:
            # import pdb;pdb.set_trace()

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
    def __init__(self, backend: Backend, endpoint_id: str, local_ip: str):
        super().__init__()
        self.backend = backend
        self.endpoint_id = endpoint_id
        self.local_ip = local_ip

        self.events_window = deque(maxlen=200)
        self.watch_dir = WATCH_DIR
        self.canaries = self._ensure_canaries()

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

        # Always use src_path for file events
        path = Path(getattr(event, "src_path", ""))
        print(f"[DEBUG] Event: {event}, src_path: {getattr(event, 'src_path', None)}, dest_path: {getattr(event, 'dest_path', None)}, path: {path}")
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
        # Register this agent with the backend on startup
        self.backend.register(
            endpoint_id=ENDPOINT_ID,
            endpoint_name=socket.gethostname(),
            ip=self.local_ip
        )
        self.detector = RansomwareDetector(self.backend, ENDPOINT_ID, self.local_ip)
        self.observer = Observer()

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

    def poll_actions_loop(self):
        while True:
            try:
                actions = self.backend.poll_actions(ENDPOINT_ID)
                for a in actions:
                    if a.get("action") == "kill_process":
                        pid = a.get("pid")
                        try:
                            proc = psutil.Process(pid)
                            proc.terminate()
                            proc.wait(timeout=3)
                            print(f"[agent] killed process {a.get('process_name')} (pid {pid})")
                        except Exception as e:
                            print(f"[agent] failed to kill process {pid}: {e}")
                    # mark action done
                    self.backend.mark_action_done(a.get("id"))
            except Exception as e:
                print("[agent] action polling error:", e)
            time.sleep(POLL_ACTIONS_INTERVAL)



# =========================
# Main
# =========================
if __name__ == "__main__":
    agent = Agent()
    threading.Thread(target=agent.poll_actions_loop, daemon=True).start()
    agent.start()
