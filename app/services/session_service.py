from datetime import timezone
from uuid import UUID
from fastapi import HTTPException
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import selectinload

from app.db.models import Patient, Session
from app.schemas.sessions_schema import GameResultResponse, SessionCreate, SessionCreateResponse, SessionResponse


from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session_data: SessionCreate) -> SessionCreateResponse:
        # Convert session_date to UTC naive datetime
        session_date = session_data.session_date
        if session_date.tzinfo is not None:
            session_date = session_date.astimezone(timezone.utc).replace(tzinfo=None)
        
        new_session = Session(
            session_date=session_date,
            session_duration=session_data.session_duration,
            notes=session_data.notes,
            user_id=session_data.user_id
        )
        
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return SessionCreateResponse.from_orm(new_session)

    async def get_sessions_by_patient_id(self, patient_id: UUID) -> list[SessionResponse]:
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == patient_id)
            .options(selectinload(Session.game_results))  # Eagerly load game_results
        )
        sessions = result.scalars().all()
        return [SessionResponse.from_orm(s) for s in sessions]

    async def get_sessions_for_clinician(self, clinician_id: UUID) -> list[SessionResponse]:
        # join between patient and clicican tables to get all patients for the doctor
        result = await self.db.execute(
            select(Session)
            .join(Patient)
            .where(Patient.clinician_id == clinician_id)
        )
        sessions = result.scalars().all()
        return [SessionResponse.from_orm(s) for s in sessions]

