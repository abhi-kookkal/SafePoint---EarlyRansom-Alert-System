# SafePoint — Early Ransomware Alert System

SafePoint is a deception-based early ransomware detection and response system that leverages canary files to proactively identify and mitigate ransomware attacks on endpoints. The system is designed for real-time monitoring, alerting, and automated response, providing a robust defense for enterprise or research environments.

---

## Key Features
- Early Ransomware Detection: Uses canary/decoy files to detect suspicious file operations and high-entropy writes typical of ransomware.
- Automated Response: Supports actions like process kill and device isolation upon detection.
- Live Dashboard: Angular-based frontend for real-time visibility into alerts, endpoints, and device risk scores.
- Backend APIs: FastAPI backend for alert ingestion, device management, and action orchestration.
- Agent: Python agent for endpoint monitoring and communication with backend.
- Simulation: Includes a script to simulate ransomware behavior for testing and demo purposes.

---

## Architecture Overview

```
[Endpoint Agent] <---WS/HTTP---> [FastAPI Backend] <---REST/WS---> [Angular Dashboard]
```
- `Agent`: Monitors filesystem, detects suspicious events using canary files, and communicates with backend.
- `Backend`: Collects alerts, manages device registry, exposes REST/WebSocket APIs, and coordinates actions.
- `Frontend`: Provides dashboards for alerts, device status, and response actions.

---

## Repository Structure
- `agent/` — Python agent for endpoint monitoring
- `backend/` — FastAPI backend with database models, APIs, and device/alert management
- `frontend/` — Angular dashboard for monitoring and response
- `simulate_ransom.py` — Script to simulate ransomware activity on canary files

---

## Getting Started

### 1. Agent (Python)
- Install dependencies: `pip install -r requirements.txt`
- Run agent: `python agent/agent.py`

### 2. Backend (FastAPI)
- Install dependencies: `pip install -r requirements.txt`
- Run backend: `uvicorn backend.main:app --reload`

### 3. Frontend (Angular)
- Navigate to `frontend/`
- Install dependencies: `npm install`
- Run dev server: `ng serve`
- Access dashboard at [http://localhost:4200](http://localhost:4200)

### 4. Simulate Ransomware
- Run `python simulate_ransom.py` to test detection and alert flow

---

## How It Works
- Canary Files: Agent places decoy files in monitored directories. Unauthorized or high-entropy writes to these files trigger alerts.
- Alerting: Alerts contain file/process/user info, risk level, and device risk score.
- Response: Admins can kill malicious processes or isolate devices directly from the dashboard.
- Live Status: Device and alert status are updated in real time using WebSockets.

---

## Technologies Used
- Python (Agent, Backend)
- FastAPI, SQLAlchemy
- Angular, Angular Material (Frontend)
- WebSockets, REST APIs

---
