# app/api/dependencies.py
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union, Annotated
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from app.db.models import User, Patient, Clinician, UserRole
from app.db.database import get_session
from app.services.auth_service import AuthService
from app.utils.settings import settings
from app.utils.security import TokenData
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scheme_name="JWT"
)


def get_auth_role(user_role: UserRole = Header()) -> UserRole:
  return user_role

def admin_permissions(user_role: UserRole = Depends(get_auth_role)) :
    if user_role != UserRole.ADMIN: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session)
) -> Tuple[Union[User, Patient, Clinician], UserRole]:

    """
    Get the current authenticated user from the JWT token.
    
    Returns:
        Tuple of (user_object, user_role)
    
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        user_role_str: str = payload.get("user_role")
        
        if email is None or user_role_str is None:
            raise credentials_exception
            
        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            raise credentials_exception
            
        token_data = TokenData(email=email, user_role=user_role)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await session.exec(select(User).where(User.email == token_data.email))
    user = result.first()
    if user is None or not user.is_active:
        raise credentials_exception      
    return user, token_data.user_role

async def get_current_active_user(
    current_user: Annotated[Tuple[Union[User, Patient, Clinician], UserRole], Depends(get_current_user)]
) -> Tuple[Union[User, Patient, Clinician], UserRole]:
    """
    Verify that the current user is active.
    """
    user, role = current_user
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive"
        )
    return user, role

async def get_current_admin(
    current_user: Annotated[Tuple[User, UserRole], Depends(get_current_user)]
) -> User:
    """
    Verify that the current user is an admin.
    """
    user, role = current_user
    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

async def get_current_clinician(
    current_user: Annotated[Tuple[Clinician, UserRole], Depends(get_current_user)],
    session: AsyncSession = Depends(get_session),
) -> Clinician:
    """
    Verify that the current user is a clinician.
    """
    user, role = current_user
    if role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinician privileges required"
        )
    result = await session.exec(select(Clinician).where(Clinician.user_id == user.user_id))
    clinician = result.first()

    if not clinician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician not found",
        )

    return Clinician

async def get_current_patient(
    current_user: Annotated[Tuple[UserRole, UserRole], Depends(get_current_user)],
    session: AsyncSession = Depends(get_session),
) -> Patient:
    """
    Verify that the current user is a patient and return the Patient object.
    """
    user, role = current_user

    if role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient privileges required",
        )
    result = await session.exec(select(Patient).where(Patient.user_id == user.user_id))
    patient = result.first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return patient

async def get_current_user_safe(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Optional[Tuple[Union[User, Patient, Clinician], UserRole]]:
    """
    A safe version of get_current_user that returns None instead of raising exceptions.
    Useful for endpoints that can work with both authenticated and unauthenticated users.
    """
    if not token:
        return None
        
    try:
        return await get_current_user(token, session)
    except HTTPException:
        return None


