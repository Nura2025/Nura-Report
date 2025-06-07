import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, SecretStr, field_validator
from datetime import date, datetime
from typing import Literal, Optional
from app.db.models import UserRole


def validate_password(value: str) -> str:
    errors = []
    if len(value) < 6:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[a-z]", value):
        errors.append("Password must include at least one lowercase letter.")
    if not re.search(r"[A-Z]", value):
        errors.append("Password must include at least one uppercase letter.")
    if not re.search(r"\d", value):
        errors.append("Password must include at least one number.")
    if not re.search(r"[@$!%*?&]", value):
        errors.append("Password must include at least one special character.")

    if errors:
        raise ValueError(" ".join(errors))
    return value

phone_regex = re.compile(r"^\+?\d{8,15}$")

class UserBasics(BaseModel):
    email: EmailStr
    username: str
    password: str
    
    # @field_validator("password")
    # def validate_password_field(cls, value):
    #     return validate_password(value)


class UserPublic(BaseModel):
    user_id: UUID
    email: EmailStr
    role: str | None = None
    is_active: bool |None = None
    created_at: datetime

    class Config:
        from_orm = True
        from_attributes = True  

class PatientCreateRequest(UserBasics):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date
    gender: str
    phone_number: Optional[str] = None

    @field_validator("gender")
    def validate_gender(cls, value):
        allowed = {"male", "female", "other"}
        if value.lower() not in allowed:
            raise ValueError(f"Gender must be one of {allowed}")
        return value.lower()

class ClinicianCreateRequest(UserBasics):
    first_name: str
    last_name: str
    specialty: Optional[str] = None
    phone_number: Optional[str] = None

    # @field_validator("phone_number")
    # def validate_phone(cls, v):
    #     if v and not phone_regex.match(v):
    #         raise ValueError("Phone number must be valid and contain only digits (optionally starting with '+')")
    #     return v



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PatientUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    adhd_subtype: Optional[str] = None
    diagnosis_date: Optional[date] = None
    medication_status: Optional[str] = None
    parent_contact: Optional[str] = None
    notes: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    clinician_id: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    def validate_password_field(cls, value):
        # Only validate if a password is provided
        if value:
            return validate_password(value)
        return None

    @field_validator("gender")
    def validate_gender(cls, value):
        if value:
            allowed = {"male", "female", "other"}
            if value.lower() not in allowed:
                raise ValueError(f"Gender must be one of {allowed}")
            return value.lower()
        return value

    @field_validator("phone_number")
    def validate_phone(cls, v):
        if v and not phone_regex.match(v):
            raise ValueError("Phone number must be valid and contain only digits")
        return v
    

class PatientResponse(BaseModel):
    user_id: UUID
    clinician_id: Optional[UUID] = None

    first_name: str
    last_name: str
    date_of_birth: date
    gender: Literal["male", "female", "other"]
    adhd_subtype: Optional[str] = None
    diagnosis_date: Optional[date] = None
    medication_status: Optional[str] = None
    parent_contact: Optional[str] = None
    notes: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_orm = True
        from_attributes = True

class ClinicianUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    specialty: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("password")
    def validate_password_field(cls, value):
        if value:
            return validate_password(value)
        return None

    @field_validator("phone_number")
    def validate_phone(cls, v):
        if v and not phone_regex.match(v):
            raise ValueError("Phone number must be valid and contain only digits (optionally starting with '+')")
        return v

class ClinicianResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    specialty: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: Optional[bool] = None

    class Config:
        from_orm = True
        from_attributes = True



