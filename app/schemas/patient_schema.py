from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str] = None
    adhd_subtype: Optional[str] = None
    diagnosis_date: Optional[date] = None
    medication_status: Optional[str] = None
    parent_contact: Optional[str] = None
    clinician_id: Optional[int] = None
    notes: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    patient_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
