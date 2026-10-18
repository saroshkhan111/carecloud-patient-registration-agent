from datetime import datetime
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config import settings
from app.database import get_db
from app.models import Patient
from app.schemas import PatientCreate, validate_us_phone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tools", tags=["ElevenLabs Webhook Tools"])

def verify_tool_token(
    x_tool_token: Optional[str] = Header(None, alias="X-Tool-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Verifies that the incoming webhook request contains the matching ELEVENLABS_TOOL_TOKEN.
    Accepts 'X-Tool-Token: <token>' or 'Authorization: Bearer <token>'.
    """
    configured_token = settings.elevenlabs_tool_token.strip()
    if not configured_token:
        return True

    incoming_token = None
    if x_tool_token:
        incoming_token = x_tool_token.strip()
    elif authorization:
        parts = authorization.strip().split()
        incoming_token = parts[-1] if parts else ""

    if incoming_token != configured_token:
        logger.warning("Unauthorized tool invocation attempt with invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid tool authentication token."
        )
    return True

@router.post("/register_patient")
@router.post("/register-patient")
def register_patient_tool(
    payload: PatientCreate,
    authenticated: bool = Depends(verify_tool_token),
    db: Session = Depends(get_db)
):
    """
    Called by ElevenLabs Voice Agent when caller confirms their information.
    Saves the new patient demographic record into carecloud.db.
    """
    try:
        patient = Patient(
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
            sex=payload.sex,
            phone_number=payload.phone_number,
            email=payload.email,
            address_line_1=payload.address_line_1,
            address_line_2=payload.address_line_2,
            city=payload.city,
            state=payload.state,
            zip_code=payload.zip_code,
            insurance_provider=payload.insurance_provider,
            insurance_member_id=payload.insurance_member_id,
            preferred_language=payload.preferred_language or "English",
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        logger.info(f"Registered patient: {patient.first_name} {patient.last_name} (ID: {patient.patient_id})")
        return {
            "status": "success",
            "patient_id": patient.patient_id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "message": f"You're all set, {patient.first_name}. Your registration has been successfully saved."
        }
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to register patient: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Database write failed: {str(exc)}"
        )

@router.post("/lookup_patient_by_phone")
@router.post("/lookup-patient-by-phone")
def lookup_patient_by_phone(
    payload: Dict[str, Any],
    authenticated: bool = Depends(verify_tool_token),
    db: Session = Depends(get_db)
):
    """
    Bonus Feature: Duplicate Detection.
    Recognizes returning callers by phone number and offers to update existing record.
    """
    raw_phone = payload.get("phone_number") or payload.get("phone")
    if not raw_phone:
        return {"found": False, "message": "No phone number provided."}

    try:
        norm_phone = validate_us_phone(raw_phone)
    except ValueError:
        norm_phone = raw_phone.strip()

    patient = db.query(Patient).filter(
        and_(Patient.phone_number == norm_phone, Patient.deleted_at.is_(None))
    ).order_by(Patient.created_at.desc()).first()

    if patient:
        return {
            "found": True,
            "patient_id": patient.patient_id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "message": f"It looks like we already have a record for {patient.first_name} {patient.last_name}. Would you like to update your information instead?"
        }

    return {
        "found": False,
        "message": "No existing record found for this phone number."
    }
