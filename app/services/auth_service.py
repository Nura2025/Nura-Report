# app/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
import jwt
from typing import Tuple
from sqlmodel.ext.asyncio.session import AsyncSession 
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status

from app.db.database import get_session
from app.schemas.auth_schema import ClinicianCreateRequest, PatientCreateRequest, UserPublic
from app.utils.security import (
    get_password_hash,
    verify_password,
)
from app.utils.settings import settings
from app.db.models import Patient, Clinician, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

ALGORITHM = settings.algorithm

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

Patient_role = "patient"
Clinician_role = "doctor"
class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def check_email_exists(self, email: str) -> bool:
        result = await self.session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        return existing_user is not None
    
    async def check_username_exists(self, username: str) -> bool:
        result = await self.session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        return existing_user is not None


    @staticmethod
    def parse_user_role(role) -> UserRole:
        if isinstance(role, UserRole):
            return role
        elif isinstance(role, str):
            return UserRole(role.lower())
        raise ValueError("Invalid user role")
   
    async def register_user(
            self,
            profile_data: Union[PatientCreateRequest, ClinicianCreateRequest],
            role: str  
        ) -> UserPublic:
            if await self.check_email_exists(profile_data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
            if await self.check_username_exists(profile_data.username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="username already exists"
                )
            
           

            # Create user with hashed password
            user = User(
                email=profile_data.email,
                username=profile_data.username,
                hashed_password=get_password_hash(profile_data.password),
                role = role,
                is_active=True
            )
            print("userrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",user.__dict__)

            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            print("the role is ", role)
            print ("the patient role is ", Patient_role)
            # Create role-specific profile
            if role == Patient_role:
                print("indside patient role")
                patient_data = profile_data.dict(exclude={"password"})
                patient = Patient(user_id=user.user_id, **patient_data)
                self.session.add(patient)
            elif role == Clinician_role:
                clinician_data = profile_data.dict(exclude={"password"})
                clinician = Clinician(user_id=user.user_id, **clinician_data)
                self.session.add(clinician)

            await self.session.commit()
            return UserPublic.from_orm(user)


    async def authenticate_user(self, email: str, password: str) -> Tuple[Union[User, Patient, Clinician, None], Optional[str]]:
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not verify_password(password, user.hashed_password):
            return None, None

        # if user.role == Patient_role:
        #     result = await self.session.execute(select(Patient).where(Patient.user_id == user.user_id))
        #     patient = result.scalars().first()
        #     return patient, user.role
        # elif user.role == Clinician_role:
        #     result = await self.session.execute(select(Clinician).where(Clinician.user_id == user.user_id))
        #     clinician = result.scalars().first()
        #     return clinician, user.role
        return user , user.role




