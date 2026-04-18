from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DB_URL = "sqlite:///./database/traffic_system.db"

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    owner_name = Column(String, default="Unknown")
    vehicle_type = Column(String)  # car, bike, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class VehicleOwner(Base):
    """Mock owner lookup table: maps plate → owner details."""
    __tablename__ = "vehicle_owners"
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    owner_name = Column(String)
    email = Column(String)
    phone = Column(String, default="N/A")
    address = Column(String, default="Smart City, India")

class Violation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    violation_type = Column(String)  # Red Light, Over Speed
    value = Column(Float)  # Speed value or signal status
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String, default="Main Junction - Signal 01")
    image_path = Column(String)
    fine_amount = Column(Integer)

    # --- E-Challan fields ---
    challan_number = Column(String, unique=True, index=True)   # CH-2026-0001
    payment_status = Column(String, default="Pending")          # Pending | Paid
    payment_date = Column(DateTime, nullable=True)
    challan_pdf_path = Column(String, nullable=True)

    # Legacy alias kept for backward compat
    @property
    def status(self):
        return self.payment_status

    vehicle = relationship("Vehicle")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="officer")  # admin, officer

class SystemSettings(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, default="Main Junction - Signal 01")
    camera_source = Column(String, default="videos/traffic_demo.mp4")
    input_mode = Column(String, default="VIDEO") # VIDEO or CAMERA
    speed_limit = Column(Float, default=50.0)
    distance_meters = Column(Float, default=5.0)
    presentation_mode = Column(Integer, default=1) # 1 for True, 0 for False
    helmet_detection = Column(Integer, default=1) # 1 for ON, 0 for OFF
    lane_detection = Column(Integer, default=1)   # 1 for ON, 0 for OFF
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine

SessionLocal = None
if not os.path.exists("./database"):
    os.makedirs("./database")

engine = init_db()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
