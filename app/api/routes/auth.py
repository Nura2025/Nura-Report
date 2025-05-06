from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Tuple
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependinces import get_current_user
from app.db.models import User, UserRole
from app.schemas.auth_schema import UserPublic, PatientCreateRequest, ClinicianCreateRequest, LoginRequest
from app.services.auth_service import AuthService
from app.utils.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_auth_role
)
from app.db.database import get_session

router = APIRouter(tags=["Authentication"])

@router.post("/login")
async def login(
    form_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    auth_service = AuthService(session)
    try:
        user, user_role = await auth_service.authenticate_user(form_data.email, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_role": user.role, "user_id": str(user.user_id)},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer" }

    except HTTPException as e:
        raise e

@router.post("/register/patient", response_model=UserPublic)
async def register_patient(
    patient_data: PatientCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    auth_service = AuthService(session)
    try:
        user = await auth_service.register_user(patient_data, "patient")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/register/clinician", response_model=UserPublic)
async def register_clinician(
    user_data: ClinicianCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    auth_service = AuthService(session)
    try:
        user = await auth_service.register_user(user_data, "doctor")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

