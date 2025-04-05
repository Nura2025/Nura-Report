from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict
from uuid import UUID

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    gender: Optional[str] = Field(None, max_length=20)
    adhd_subtype: Optional[str] = Field(None, max_length=30)
    diagnosis_date: Optional[date]
    medication_status: Optional[str] = Field(None, max_length=100)
    parent_contact: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=100)

class PatientCreate(PatientBase):
    password: str = Field(..., min_length=10)
    
    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain a lowercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain a digit")
        return value

class PatientResponse(PatientBase):
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    links: List[Dict[str, str]] = []
    
    @classmethod
    def add_hateoas_links(cls, patient_id: UUID):
        return [
            {"rel": "self", "href": f"/patients/{patient_id}"},
            {"rel": "sessions", "href": f"/patients/{patient_id}/sessions"},
            {"rel": "clinician", "href": f"/patients/{patient_id}/clinician"}
        ]