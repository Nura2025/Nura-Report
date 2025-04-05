# app/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
import jwt
from sqlmodel.ext.asyncio.session import AsyncSession 
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status

from app.db.database import get_session
from app.utils.security import (
    get_password_hash,
    verify_password,
)
from app.utils.settings import settings
from app.db.models import Patient, Clinician
from app.schemas.patient_schema import PatientCreate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

ALGORITHM = settings.algorithm

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_by_email(self, email: str, model: type) -> Optional[Union[Patient, Clinician]]:
        statement = select(model).where(model.email == email)
        result = await self.session.execute(statement)  
        return result.scalars().first()

    async def register_patient(self, patient_data: PatientCreate) -> dict:
        existing_user = await self._get_user_by_email(patient_data.email, Patient)  
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(patient_data.password)
        patient = Patient(
            **patient_data.dict(exclude={"password"}),
            password=hashed_password
        )
        
        self.session.add(patient)
        await self.session.commit()  
        await self.session.refresh(patient)  
        return {"message": "Patient created successfully"}
    # def register_clinician(self, clinician_data: ClinicianCreate) -> dict:
    #     if self._get_user_by_email(clinician_data.email, Clinician):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Email already registered"
    #         )

    #     hashed_password = get_password_hash(clinician_data.password)
    #     clinician = Clinician(
    #         **clinician_data.dict(exclude={"password"}),
    #         password=hashed_password
    #     )
        
    #     self.session.add(clinician)
    #     self.session.commit()
    #     self.session.refresh(clinician)
    #     return {"message": "Clinician created successfully"}

    async def  authenticate_user(self, email: str, password: str) -> Union[Patient, Clinician, None]:
        user = await self._get_user_by_email(email, Patient)
        user_type = "patient"
        
        if not user:
            user = await self._get_user_by_email(email, Clinician)
            user_type = "clinician"
            if not user:
                return None, None

        if not verify_password(password, user.password):
            return None, None

        return user, user_type

    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session)
    ) -> Union[Patient, Clinician]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            user_type: str = payload.get("user_type")
            if not email or not user_type:
                raise credentials_exception
            # Check token expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp is None:
                raise credentials_exception
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except JWTError:
            raise credentials_exception
        
        # Fetch user based on user_type and email
        if user_type == "patient":
            result = await session.execute(select(Patient).where(Patient.email == email))
            user = result.scalars().first()
        elif user_type == "clinician":
            result = await session.execute(select(Clinician).where(Clinician.email == email))
            user = result.scalars().first()
        else:
            raise credentials_exception
        
        if user is None:
            raise credentials_exception
        # if not user.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Inactive user",
        #         headers={"WWW-Authenticate": "Bearer"},
        #     )
        return user

    def require_role(role: str):
        def role_checker(current_user: Union[Patient, Clinician] = Depends(get_current_user)):
            if (isinstance(current_user, Patient) and role != "patient") or \
            (isinstance(current_user, Clinician) and role != "clinician"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return role_checker
    



