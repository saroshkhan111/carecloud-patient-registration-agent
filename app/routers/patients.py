from datetime import datetime
from typing import Optional, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models import Patient
from app.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    ApiResponse,
    validate_us_phone,
    validate_date_not_future
)

router = APIRouter(prefix="/patients", tags=["Patients REST API"])

def seed_demo_patients(db: Session):
    """Optionally seeds 2 initial patient records as specified in assessment."""
    if db.query(Patient).count() == 0:
        demo1 = Patient(
            patient_id=str(uuid.uuid4()),
            first_name="Jane",
            last_name="Doe",
            date_of_birth="05/14/1988",
            sex="Female",
            phone_number="555-123-4567",
            email="jane.doe@example.com",
            address_line_1="123 Maple Street",
            address_line_2="Apt 4B",
            city="Austin",
            state="TX",
            zip_code="78701",
            insurance_provider="Blue Cross Blue Shield",
            insurance_member_id="BCBS-987654",
            preferred_language="English",
            emergency_contact_name="John Doe",
            emergency_contact_phone="555-987-6543",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        demo2 = Patient(
            patient_id=str(uuid.uuid4()),
            first_name="Robert",
            last_name="Smith",
            date_of_birth="11/22/1975",
            sex="Male",
            phone_number="555-234-5678",
            email="robert.smith@example.com",
            address_line_1="456 Oak Avenue",
            city="Denver",
            state="CO",
            zip_code="80202",
            preferred_language="English",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add_all([demo1, demo2])
        db.commit()

@router.get("", response_model=ApiResponse[List[PatientResponse]])
def list_patients(
    last_name: Optional[str] = Query(None, description="Filter by patient last name"),
    date_of_birth: Optional[str] = Query(None, description="Filter by date of birth"),
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    db: Session = Depends(get_db)
):
    """
    List all registered patients.
    Supports optional query filters: ?last_name=, ?date_of_birth=, ?phone_number=
    Excludes soft-deleted patients.
    """
    seed_demo_patients(db)
    query = db.query(Patient).filter(Patient.deleted_at.is_(None))

    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name.strip()}%"))
    if date_of_birth:
        clean_dob = date_of_birth.strip()
        query = query.filter(Patient.date_of_birth == clean_dob)
    if phone_number:
        clean_phone = phone_number.strip()
        try:
            norm = validate_us_phone(clean_phone)
            query = query.filter(Patient.phone_number == norm)
        except ValueError:
            query = query.filter(Patient.phone_number.ilike(f"%{clean_phone}%"))

    patients = query.order_by(Patient.created_at.desc()).all()
    return ApiResponse(data=[PatientResponse.model_validate(p) for p in patients], error=None)

@router.get("/{patient_id}", response_model=ApiResponse[PatientResponse])
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve a single active patient record by UUID."""
    patient = db.query(Patient).filter(
        and_(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )

    return ApiResponse(data=PatientResponse.model_validate(patient), error=None)

@router.post("", response_model=ApiResponse[PatientResponse], status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    """
    Create a new patient record.
    Returns HTTP 201 with generated patient_id UUID.
    """
    patient = Patient(
        patient_id=str(uuid.uuid4()),
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

    return ApiResponse(data=PatientResponse.model_validate(patient), error=None)

@router.put("/{patient_id}", response_model=ApiResponse[PatientResponse])
def update_patient(patient_id: str, payload: PatientUpdate, db: Session = Depends(get_db)):
    """
    Update an existing patient record.
    Partial updates are allowed.
    """
    patient = db.query(Patient).filter(
        and_(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(patient, field, value)

    patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(patient)

    return ApiResponse(data=PatientResponse.model_validate(patient), error=None)

@router.delete("/{patient_id}", response_model=ApiResponse[dict])
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """
    Soft-delete a patient record by setting deleted_at timestamp.
    Does not hard-delete data.
    """
    patient = db.query(Patient).filter(
        and_(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )

    patient.deleted_at = datetime.utcnow()
    db.commit()

    return ApiResponse(
        data={"message": "Patient successfully deleted", "patient_id": patient_id},
        error=None
    )
