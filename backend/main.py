from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

DB = {"endpoints": {}, "alerts": [], "actions": []}
# super simple in-memory for hackathon; swap to SQLite later if you want

class AlertIn(BaseModel):
    endpoint_id: str
    process_name: str
    risk_score: int
    reason: str

class AlertOut(AlertIn):
    id: int
    timestamp: str
    action_taken: Optional[str] = None

class ActionIn(BaseModel):
    endpoint_id: str
    command: str  # "kill" | "isolate" | "message"
    target_pid: Optional[int] = None

@app.post("/register")
def register_endpoint(endpoint_id: str, name: str):
    DB["endpoints"][endpoint_id] = {"name": name, "last_seen": datetime.utcnow().isoformat(), "status": "ok"}
    return {"ok": True}

@app.post("/alerts", response_model=AlertOut)
def post_alert(alert: AlertIn):
    if alert.endpoint_id not in DB["endpoints"]:
        raise HTTPException(400, "Unknown endpoint")
    row = {
        "id": len(DB["alerts"])+1,
        "timestamp": datetime.utcnow().isoformat(),
        **alert.dict(),
        "action_taken": None
    }
    DB["alerts"].append(row)
    # naive auto-response: if risk >= 80, schedule a kill command
    if alert.risk_score >= 80:
        DB["actions"].append({"id": len(DB["actions"])+1, "endpoint_id": alert.endpoint_id, "command": "kill", "status": "pending", "target_pid": None})
        row["action_taken"] = "queued_kill"
    return row

@app.get("/alerts")
def list_alerts():
    return DB["alerts"][::-1]

@app.get("/endpoints")
def list_endpoints():
    return DB["endpoints"]

@app.post("/actions")
def create_action(action: ActionIn):
    row = {"id": len(DB["actions"])+1, "endpoint_id": action.endpoint_id, "command": action.command, "status": "pending", "target_pid": action.target_pid}
    DB["actions"].append(row)
    return row

@app.get("/actions")
def get_actions(endpoint_id: str):
    # agent polls this
    pending = [a for a in DB["actions"] if a["endpoint_id"] == endpoint_id and a["status"] == "pending"]
    return pending

@app.post("/actions/{action_id}/done")
def mark_action_done(action_id: int):
    for a in DB["actions"]:
        if a["id"] == action_id:
            a["status"] = "done"
            return {"ok": True}
    raise HTTPException(404, "not found")
