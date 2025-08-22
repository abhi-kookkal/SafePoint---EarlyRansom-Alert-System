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
    ip: str

@app.post("/alerts")
def receive_alert(alert: AlertIn, db: Session = Depends(get_db)):
    print("[backend] received alert:", alert)
    
    db_alert = models.Alert(
        id=alert.id,   # store incoming alert id here
        file=alert.file,
        process=alert.process,
        user=alert.user,
        timestamp=alert.timestamp,
        status=alert.status,
        riskLevel=alert.riskLevel,
        ip=alert.ip
    )
    
    merged_alert = db.merge(db_alert)  # use merge so re-sending same alert doesn’t break
    db.commit()
    db.refresh(merged_alert)

    return {"status": "alert_received", "alert_id": merged_alert.id}


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
            "riskLevel": alert.riskLevel,
            "device_id": alert.ip
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
        "riskLevel": alert.riskLevel,
        "device_id": alert.ip
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
import requests
# In-memory actions DB (for demo)
actions_db = {}

@app.post("/fetch_alerts/{id}/kill_process")
def kill_process(id: int, db: Session = Depends(get_db)):   # 👈 id should be int
    # Fetch the alert by id
    alert = db.query(models.Alert).filter(models.Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Get IP and process from DB row
    endpoint_ip = alert.ip
    process_name = alert.process

    try:
        print(f"[backend] kill_process: {process_name} on {endpoint_ip}")
        # Call the agent API with process_name (not the id!)
        r = requests.post(f"http://{endpoint_ip}:9000/agent/kill_process/{id}")
        print("[backend] kill_process response:", r.json())
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to contact agent {endpoint_ip}: {e}")


@app.post("/fetch_alerts/{id}/isolate")
def isolate_device(id: int, db: Session = Depends(get_db)):
    # Fetch the alert by id
    alert = db.query(models.Alert).filter(models.Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Get the endpoint IP from DB
    agent_ip = alert.ip

    try:
        print(f"[backend] isolate_device: alert={id}, forwarding request to agent {agent_ip}")
        r = requests.post(
            f"http://{agent_ip}:9000/agent/isolate_device",
            timeout=5
        )
        response = r.json()
        return {"status": "ok", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to contact agent at {agent_ip}: {e}")


@app.get("/actions")
def poll_actions(endpoint_id: str):
    return actions_db.get(endpoint_id, [])