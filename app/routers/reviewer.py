import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import CallSession, Patient

security = HTTPBasic()
router = APIRouter(prefix="/api/reviewer", tags=["Reviewer Dashboard"])

def authenticate_reviewer(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, settings.reviewer_username)
    is_pass_ok = secrets.compare_digest(credentials.password, settings.reviewer_password)
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect reviewer username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.get("/dashboard")
def get_dashboard_summary(
    reviewer: str = Depends(authenticate_reviewer),
    db: Session = Depends(get_db)
):
    """Returns overview of all call sessions and registered patients."""
    total_calls = db.query(CallSession).count()
    total_patients = db.query(Patient).filter(Patient.deleted_at.is_(None)).count()
    recent_calls = db.query(CallSession).order_by(CallSession.created_at.desc()).limit(10).all()
    recent_patients = db.query(Patient).filter(Patient.deleted_at.is_(None)).order_by(Patient.created_at.desc()).limit(10).all()

    return {
        "reviewer": reviewer,
        "total_calls": total_calls,
        "total_patients": total_patients,
        "recent_calls": recent_calls,
        "recent_patients": recent_patients
    }
