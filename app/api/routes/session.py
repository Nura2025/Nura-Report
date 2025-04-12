from typing import List, Tuple
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Depends, HTTPException, status
from sqlmodel import select
from app.db.models import Patient, Session, User, UserRole
from app.schemas.sessions_schema import SessionCreate, SessionCreateResponse, SessionResponse
from app.db.database import get_session
from app.services import RoleChecker
from app.services.session_service import SessionService
from app.api.dependinces import get_current_patient, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.utils.authchecker import AuthChecker



router = APIRouter(tags=["session"])

# Endpoint to create a new game session
# This endpoint is called by the Unity game client after gameplay.
@router.post(
    "/sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new game session",
    description="Endpoint for Unity game client to record a new gameplay session. Only accessible by patients."
)
async def create_session(
    session_data: SessionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: Patient = Depends(get_current_patient)
):
    if session_data.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create sessions for your own account"
        )

    service = SessionService(session)
    return await service.create_session(session_data)


@router.get(
    "/sessions/{user_id}",
    response_model=List[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve sessions for a specific user",
    description="Endpoint to retrieve all sessions for a specific user by their user ID."
)
async def get_sessions_for_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user)  # Unpack the tuple
):
    user, role = current_user  # Unpack the tuple into user and role

    # Check if the current user is the patient or their clinician
    if role == UserRole.PATIENT and user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access these sessions"
        )

    if role == UserRole.DOCTOR:
        # Verify if the clinician is associated with the patient
        result = await session.execute(
            select(Patient).where(Patient.user_id == user_id, Patient.clinician_id == user.user_id)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access these sessions"
            )

    service = SessionService(session)
    return await service.get_sessions_by_patient_id(user_id)



@router.get(
    "/sessions/{user_id}/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific session for a specific patient",
    description="Endpoint to retrieve a specific session for a specific patient by their user ID and session ID."
)
async def get_specific_session_for_patient(
    user_id: UUID,
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user)
):
    user, role = current_user  # Unpack the tuple into user and role

    # Check if the current user is the patient or their clinician
    if role == UserRole.PATIENT and user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session"
        )

    if role == UserRole.DOCTOR:
        # Verify if the clinician is associated with the patient
        result = await session.execute(
            select(Patient).where(Patient.user_id == user_id, Patient.clinician_id == user.user_id)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this session"
            )

    # Retrieve the specific session
    result = await session.execute(
        select(Session)
        .where(Session.session_id == session_id, Session.user_id == user_id)
        .options(selectinload(Session.game_results))  # Eagerly load game_results
    )
    specific_session = result.scalar_one_or_none()

    if not specific_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return SessionResponse.from_orm(specific_session)