# GameResultService.py
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException ,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from uuid import UUID
from app.db.models import GameResult, Session
from app.schemas.game_result_schema import GameResultBase, GameResultCreate, GameResultMatchingCreate, GameResultResponse, GameResultSequenceCreate
from app.utils.logger import logger

from app.services.mini_games_services import MiniGameService

class GameResultService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_game_result(self, game_result_data: GameResultCreate , session_id : UUID) -> GameResultResponse:
        # Convert start_time and end_time to timezone-naive
        start_time = game_result_data.start_time
        if start_time.tzinfo is not None:
            start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)

        end_time = game_result_data.end_time
        if end_time and end_time.tzinfo is not None:
            end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)

        new_game_result = GameResult(
            session_id=session_id,
            game_type=game_result_data.game_type,
            start_time=start_time,
            end_time=end_time,
            difficulty_level=game_result_data.difficulty_level,
        )

        self.db.add(new_game_result)
        await self.db.commit()
        await self.db.refresh(new_game_result)

        # Eagerly load relationships
        result = await self.db.execute(
            select(GameResult)
            .where(GameResult.result_id == new_game_result.result_id)
            .options(
                selectinload(GameResult.go_no_go_metrics),
                selectinload(GameResult.sequence_metrics),
                selectinload(GameResult.matching_metrics),
            )
        )
        new_game_result = result.scalar_one()

        return GameResultResponse.from_orm(new_game_result)
    async def get_game_results_by_user_id(self, user_id: UUID) -> List[GameResultResponse]:
        result = await self.db.execute(
            select(GameResult)
            .join(Session)
            .where(Session.user_id == user_id)
            .options(
                selectinload(GameResult.go_no_go_metrics),
                selectinload(GameResult.sequence_metrics),
                selectinload(GameResult.matching_metrics),
            )
        )
        game_results = result.scalars().all()

        return [GameResultResponse.from_orm(game_result) for game_result in game_results]

