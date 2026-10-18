import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(String(20), nullable=False)  # MM/DD/YYYY
    sex = Column(String(30), nullable=False)            # Male, Female, Other, Decline to Answer
    phone_number = Column(String(20), nullable=False, index=True) # Normalized 10-digit or E.164
    email = Column(String(120), nullable=True)
    address_line_1 = Column(String(150), nullable=False)
    address_line_2 = Column(String(150), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)           # 2-letter U.S. state code
    zip_code = Column(String(10), nullable=False)        # 5-digit or ZIP+4
    insurance_provider = Column(String(100), nullable=True)
    insurance_member_id = Column(String(100), nullable=True)
    preferred_language = Column(String(50), default="English")
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)        # Soft-delete timestamp

class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(128), unique=True, index=True, nullable=True)
    caller_identifier = Column(String(128), nullable=True)
    patient_id = Column(String(36), nullable=True)
    status = Column(String(50), default="completed")
    duration_seconds = Column(Integer, default=0)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
