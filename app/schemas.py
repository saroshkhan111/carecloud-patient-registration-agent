import re
from datetime import datetime, date
from typing import Optional, List, Any, Generic, TypeVar
from enum import Enum
from pydantic import BaseModel, Field, field_validator, EmailStr

T = TypeVar("T")

class SexEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE = "Decline to Answer"

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU"
}

def validate_us_phone(v: Optional[str]) -> Optional[str]:
    if not v:
        return v
    digits = re.sub(r"\D", "", v)
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Must be a valid 10-digit U.S. phone number (e.g. 555-123-4567)")
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

def validate_date_not_future(v: Optional[str]) -> Optional[str]:
    if not v:
        return v
    cleaned = v.strip()
    parsed_date = None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            parsed_date = datetime.strptime(cleaned, fmt).date()
            break
        except ValueError:
            continue

    if not parsed_date:
        raise ValueError("Invalid date format. Expected MM/DD/YYYY or YYYY-MM-DD.")
    if parsed_date > date.today():
        raise ValueError("Date of birth cannot be in the future.")
    return parsed_date.strftime("%m/%d/%Y")

class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., description="Date of birth in MM/DD/YYYY format")
    sex: str = Field(..., description="Male, Female, Other, or Decline to Answer")
    phone_number: str = Field(..., description="10-digit U.S. phone number")
    email: Optional[str] = None
    address_line_1: str = Field(..., min_length=1, max_length=150)
    address_line_2: Optional[str] = Field(None, max_length=150)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2, description="2-letter U.S. state code")
    zip_code: str = Field(..., description="5-digit or ZIP+4 format")
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    def validate_name(cls, v):
        if not re.match(r"^[A-Za-z\s'\-]+$", v):
            raise ValueError("Name can only contain alphabetic characters, spaces, hyphens, and apostrophes.")
        return v.strip().title()

    @field_validator("date_of_birth")
    def check_dob(cls, v):
        return validate_date_not_future(v)

    @field_validator("sex")
    def validate_sex(cls, v):
        formatted = v.strip().title()
        valid_options = {"Male": "Male", "Female": "Female", "Other": "Other", "Decline To Answer": "Decline to Answer", "Decline": "Decline to Answer"}
        if formatted not in valid_options:
            raise ValueError(f"Sex must be one of: {list(valid_options.values())}")
        return valid_options[formatted]

    @field_validator("phone_number")
    def check_phone(cls, v):
        return validate_us_phone(v)

    @field_validator("emergency_contact_phone")
    def check_emergency_phone(cls, v):
        return validate_us_phone(v)

    @field_validator("state")
    def validate_state(cls, v):
        code = v.strip().upper()
        if code not in US_STATES:
            raise ValueError(f"'{code}' is not a valid 2-letter U.S. state abbreviation.")
        return code

    @field_validator("zip_code")
    def validate_zip(cls, v):
        clean = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", clean):
            raise ValueError("ZIP code must be a 5-digit number or ZIP+4 (e.g. 12345 or 12345-6789).")
        return clean

    @field_validator("email")
    def validate_email_format(cls, v):
        if not v or v.lower() == "skip" or v.lower() == "none":
            return None
        clean = v.strip()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", clean):
            raise ValueError("Invalid email format.")
        return clean

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    def validate_name(cls, v):
        if v is not None and not re.match(r"^[A-Za-z\s'\-]+$", v):
            raise ValueError("Name can only contain alphabetic characters, spaces, hyphens, and apostrophes.")
        return v.strip().title() if v else v

    @field_validator("date_of_birth")
    def check_dob(cls, v):
        return validate_date_not_future(v) if v else v

    @field_validator("sex")
    def validate_sex(cls, v):
        if not v:
            return v
        formatted = v.strip().title()
        valid_options = {"Male": "Male", "Female": "Female", "Other": "Other", "Decline To Answer": "Decline to Answer"}
        if formatted not in valid_options:
            raise ValueError(f"Sex must be one of: {list(valid_options.values())}")
        return valid_options[formatted]

    @field_validator("phone_number", "emergency_contact_phone")
    def check_phone(cls, v):
        return validate_us_phone(v) if v else v

    @field_validator("state")
    def validate_state(cls, v):
        if not v:
            return v
        code = v.strip().upper()
        if code not in US_STATES:
            raise ValueError(f"'{code}' is not a valid 2-letter U.S. state abbreviation.")
        return code

    @field_validator("zip_code")
    def validate_zip(cls, v):
        if not v:
            return v
        clean = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", clean):
            raise ValueError("ZIP code must be a 5-digit number or ZIP+4 format.")
        return clean

class PatientResponse(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    sex: str
    phone_number: str
    email: Optional[str] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Standard response envelope: { "data": {...}, "error": null }
class ApiResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[str] = None

class AgentInfo(BaseModel):
    agent_id: str
    phone_number: Optional[str] = None
    status: str
    environment: str

class SignedUrlResponse(BaseModel):
    signed_url: str
    agent_id: str

class CallEndRequest(BaseModel):
    conversation_id: Optional[str] = None
    duration_seconds: Optional[int] = 0
    transcript: Optional[str] = None
    summary: Optional[str] = None
    patient_id: Optional[str] = None
