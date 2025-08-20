import os, time, json, psutil, requests, threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from pathlib import Path
from collections import deque
from math import log2

BACKEND = "http://127.0.0.1:8000"
ENDPOINT_ID = os.environ.get("ENDPOINT_ID", "laptop-001")
ENDPOINT_NAME = os.environ.get("ENDPOINT_NAME", "Alice-Laptop")
WATCH_DIR = Path.home() / "Documents" / "Canaries"
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# create canaries
CANARIES = [WATCH_DIR / f"canary_{i}.txt" for i in range(3)]
for c in CANARIES:
    if not c.exists():
        c.write_text("harmless canary file\n")

file_events = deque(maxlen=200)  # timestamps of recent writes

def entropy_of_file(path: Path) -> float:
    try:
        data = path.read_bytes()[:8192]  # small sample
        if not data: return 0.0
        from collections import Counter
        counts = Counter(data)
        total = len(data)
        return -sum((c/total) * log2(c/total) for c in counts.values())
    except Exception:
        return 0.0

def risk_score_for_event(path: Path, is_canary: bool) -> int:
    score = 0
    now = time.time()
    # write-rate: how many events in last 5s?
    recent = [t for t in file_events if now - t < 5]
    rate = len(recent)
    if rate > 20: score += 40   # many writes quickly
    if is_canary: score += 70   # canary touched
    ent = entropy_of_file(path)
    if ent > 7.5: score += 30   # high entropy ~ encrypted-like
    return min(score, 100)

def send_alert(process_name: str, score: int, reason: str):
    try:
        payload = {"endpoint_id": ENDPOINT_ID, "process_name": process_name, "risk_score": score, "reason": reason}
        r = requests.post(f"{BACKEND}/alerts", json=payload, timeout=5)
        r.raise_for_status()
    except Exception as e:
        print("alert error:", e)

def kill_suspicious_processes():
    # simple demo: kill any python process touching canaries folder (lab simulator)
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = p.info["name"] or ""
            cmd = " ".join(p.info.get("cmdline") or [])
            if "python" in name.lower() and "simulate_ransom" in cmd:
                p.terminate()
        except Exception:
            pass

class Handler(FileSystemEventHandler):
    def on_modified(self, event): self.handle(event)
    def on_created(self, event): self.handle(event)
    def on_moved(self, event): self.handle(event)
    def on_deleted(self, event): self.handle(event)

    def handle(self, event):
        if event.is_directory: return
        path = Path(event.src_path)
        file_events.append(time.time())
        is_canary = any(path == c for c in CANARIES) or str(path).startswith(str(WATCH_DIR))
        score = risk_score_for_event(path, is_canary)
        if score >= 80:
            send_alert(process_name="unknown", score=score, reason=f"suspicious write: {path.name}")
            kill_suspicious_processes()

def poll_actions():
    while True:
        try:
            r = requests.get(f"{BACKEND}/actions", params={"endpoint_id": ENDPOINT_ID}, timeout=5)
            for action in r.json():
                if action["command"] == "kill" and action.get("target_pid"):
                    try:
                        psutil.Process(action["target_pid"]).terminate()
                    except Exception:
                        pass
                # mark done
                requests.post(f"{BACKEND}/actions/{action['id']}/done", timeout=5)
        except Exception:
            pass
        time.sleep(2)

def main():
    try:
        requests.post(f"{BACKEND}/register", params={"endpoint_id": ENDPOINT_ID, "name": ENDPOINT_NAME}, timeout=5)
    except Exception as e:
        print("register failed:", e)

    t = threading.Thread(target=poll_actions, daemon=True)
    t.start()

    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=True)
    observer.start()
    print("Agent watching:", WATCH_DIR)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
