from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import HTTPException , status
from sqlmodel import Session, select
from app import schemas
from app.db import models
from app.schemas.auth_schema import PatientResponse
from app.utils.security import get_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class UserService:
    def __init__(self, session: Session):
        self.session = session 

    def get_patient_by_id(self, id: UUID) -> PatientResponse:
        user = self.session.exec(select(models.Patient).where(models.Patient.user_id == id)).first()
        if user  is None :
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return PatientResponse.from_orm(user)
    
