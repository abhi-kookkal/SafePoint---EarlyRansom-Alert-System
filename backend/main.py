from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
import models
from fastapi.middleware.cors import CORSMiddleware

# create tables if not exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:4200",   # Angular dev server
    "http://127.0.0.1:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],    # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # allow all headers
)
# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# ENDPOINT REGISTRATION
# -----------------------


class DeviceRegistration(BaseModel):
    id: str
    hostname: str
    ip: str
    status: str

from sqlalchemy.orm import Session
from models import Device
from database import SessionLocal

@app.post("/register")
def register(device: DeviceRegistration, db: Session = Depends(get_db)):
    """Register or update an endpoint in the devices table"""
    db_device = db.query(Device).filter(Device.id == device.id).first()
    if db_device:
        db_device.hostname = device.hostname
        db_device.ip = device.ip
        db_device.status = device.status
    else:
        db_device = Device(
            id=device.id,
            hostname=device.hostname,
            ip=device.ip,
            status=device.status
        )
        db.add(db_device)
    db.commit()
    return {"status": "ok", "device": device}


# -----------------------
# ALERTS
# -----------------------
class AlertIn(BaseModel):
    id: int
    file: str
    process: str
    user: str
    timestamp: str
    status: str
    riskLevel: str

@app.post("/alerts")
def receive_alert(alert: AlertIn, db: Session = Depends(get_db)):
    db_alert = models.Alert(
        file=alert.file,
        process=alert.process,
        user=alert.user,
        timestamp=alert.timestamp,
        status=alert.status,
        riskLevel=alert.riskLevel
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return {"status": "alert_received", "alert_id": db_alert.id}

@app.get("/fetch_alerts")
def fetch_alerts(db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).order_by(models.Alert.id.desc()).all()
    return [
        {
            "id": str(alert.id),
            "file": alert.file,
            "process": alert.process,
            "user": alert.user,
            "timestamp": alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else str(alert.timestamp),
            "status": alert.status,
            "riskLevel": alert.riskLevel
        }
        for alert in alerts
    ]

@app.get("/fetch_alerts/{id}")
def fetch_alert_by_id(id: str, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.id == id).first()
    if not alert:
        return {"error": "Alert not found"}
    return {
        "id": str(alert.id),
        "file": alert.file,
        "process": alert.process,
        "user": alert.user,
        "timestamp": alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else str(alert.timestamp),
        "status": alert.status,
        "riskLevel": alert.riskLevel
    }


# -----------------------
# ENDPOINTS
# -----------------------
@app.get("/fetch_endpoints")
def fetch_endpoints(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    return [
        {
            "id": device.id,
            "hostname": device.hostname,
            "ip": device.ip,
            "status": device.status
        }
        for device in devices
    ]

# -----------------------
# ACTIONS
# -----------------------
from fastapi import HTTPException

# In-memory actions DB (for demo)
actions_db = {}

@app.post("/fetch_alerts/{id}/kill_process")
def kill_process(id: str, db: Session = Depends(get_db)):
    """
    Frontend calls this API when user clicks 'Kill Process' for a specific alert.
    We enqueue the kill action for the endpoint associated with the alert.
    """
    alert = db.query(models.Alert).filter(models.Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    endpoint_id = alert.user  # adjust if endpoint_id is stored elsewhere
    process_name = alert.process
    # Since we don't have pid in alert, use a dummy value or extend model if needed
    pid = -1
    if endpoint_id not in actions_db:
        actions_db[endpoint_id] = []
    action_id = len(actions_db[endpoint_id]) + 1
    action = {
        "id": action_id,
        "action": "kill_process",
        "pid": pid,
        "process_name": process_name
    }
    actions_db[endpoint_id].append(action)
    return {"status": "queued", "action": action}


@app.get("/actions")
def poll_actions(endpoint_id: str):
    return actions_db.get(endpoint_id, [])