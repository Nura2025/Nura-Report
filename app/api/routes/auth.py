# app/routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from jose import JWTError
from sqlmodel import Session
from app.db.database import get_session
from app.schemas.patient_schema import PatientCreate
from app.services.auth_service import ACCESS_TOKEN_EXPIRE_MINUTES, AuthService
from app.utils import settings
from app.utils.security import Token, create_access_token

router = APIRouter(tags=["Authentication"])

def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(session)


# for children unity signup only 
@router.post("/signup/patient", status_code=status.HTTP_201_CREATED)
async def patient_signup(
    patient_data: PatientCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.register_patient(patient_data) 

# @router.post("/signup/clinician", status_code=status.HTTP_201_CREATED)
# async def clinician_signup(
#     clinician_data: ClinicianCreate,
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     return auth_service.register_clinician(clinician_data)


# for login to unity and dashboard for doctor and childrens 
@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    user, user_type = await auth_service.authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": user_type},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")