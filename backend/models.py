# models.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=False, index=True)  # no auto-increment
    file = Column(String, nullable=False)
    process = Column(String, nullable=False)
    user = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)
    riskLevel = Column(String, nullable=False)


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True, index=True)
    hostname = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    status = Column(String, nullable=False)
