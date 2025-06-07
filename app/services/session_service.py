from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import selectinload

from app.db.models import GameResult, Patient, Session
from app.schemas.sessions_schema import GameResultResponse, SessionCreate, SessionCreateResponse, SessionResponse


from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.game_result_services import GameResultService
from app.services.mini_games_services import MiniGameService

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.game_result_service = GameResultService(db)
        self.mini_game_service = MiniGameService(db)
    async def create_session(self, session_data: SessionCreate, user_id: UUID) -> SessionCreateResponse:
        session_date = session_data.session_date
        if session_date.tzinfo:
            session_date = session_date.astimezone(timezone.utc).replace(tzinfo=None)

        new_session = Session(
            session_date=session_date,
            session_duration=session_data.session_duration,
            notes=session_data.notes,
            user_id=user_id,
        )

        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)

        for result in session_data.game_results:
            result_obj = await self.game_result_service.create_game_result(
                game_result_data=result,
                session_id=new_session.session_id,
            )

            match result.game_type:
                case "go_no_go":
                    metrics = result.go_no_go_metrics
                case "sequence_memory":
                    metrics = result.sequence_metrics
                case "matching_cards":
                    metrics = result.matching_metrics
                case _:
                    raise HTTPException(status_code=400, detail="Invalid game_type")

            if not metrics:
                raise HTTPException(status_code=400, detail="Missing metrics for the game result")

            metric_data = metrics.dict() if hasattr(metrics, "dict") else metrics
            metric_data["result_id"] = result_obj.result_id

            await self.mini_game_service.create_metric(result.game_type, metric_data)

        result = await self.db.execute(
            select(Session)
            .where(Session.session_id == new_session.session_id)
            .options(
                selectinload(Session.game_results).selectinload(GameResult.go_no_go_metrics),
                selectinload(Session.game_results).selectinload(GameResult.sequence_metrics),
                selectinload(Session.game_results).selectinload(GameResult.matching_metrics),
            )
        )
        new_session = result.scalar_one()
        new_session.created_at = new_session.created_at or datetime.utcnow()
        return SessionCreateResponse(
                session_id=new_session.session_id,
                session_date=new_session.session_date,
                created_at=new_session.created_at,
            )
    
    async def get_sessions_by_patient_id(self, patient_id: UUID, limit: int, offset: int) -> list[SessionResponse]:
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == patient_id)
            .options(
                selectinload(Session.game_results).selectinload(GameResult.go_no_go_metrics),
                selectinload(Session.game_results).selectinload(GameResult.sequence_metrics),
                selectinload(Session.game_results).selectinload(GameResult.matching_metrics),
            )
            .limit(limit)
            .offset(offset)
        )
        sessions = result.scalars().all()

        session_responses = []
        for session in sessions:
            session_dict = session.dict()
            session_dict["game_results"] = [
                GameResultResponse.from_orm(game_result) for game_result in session.game_results
            ]
            session_responses.append(SessionResponse(**session_dict))

        return session_responses

    async def get_sessions_by_patient_id(self, patient_id: UUID , limit :int , offset:int) -> list[SessionResponse]:
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == patient_id)
            .options(
                selectinload(Session.game_results).selectinload(GameResult.go_no_go_metrics),
                selectinload(Session.game_results).selectinload(GameResult.sequence_metrics),
                selectinload(Session.game_results).selectinload(GameResult.matching_metrics),
            ).limit(limit).offset(offset)
        )
        sessions = result.scalars().all()

        # Convert game_results to GameResultResponse
        session_responses = []
        for session in sessions:
            session_dict = session.dict()
            session_dict["game_results"] = [
                GameResultResponse.from_orm(game_result) for game_result in session.game_results
            ]
            session_responses.append(SessionResponse(**session_dict))

        return session_responses
    async def get_sessions_by_patient_id(self, patient_id: UUID , limit :int , offset:int) -> list[SessionResponse]:
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == patient_id)
            .options(
                selectinload(Session.game_results).selectinload(GameResult.go_no_go_metrics),
                selectinload(Session.game_results).selectinload(GameResult.sequence_metrics),
                selectinload(Session.game_results).selectinload(GameResult.matching_metrics),
            ).limit(limit).offset(offset)
        )
        sessions = result.scalars().all()

        # Convert game_results to GameResultResponse
        session_responses = []
        for session in sessions:
            session_dict = session.dict()
            session_dict["game_results"] = [
                GameResultResponse.from_orm(game_result) for game_result in session.game_results
            ]
            session_responses.append(SessionResponse(**session_dict))

        return session_responses