# services/game_result_service.py

from fastapi import HTTPException, status
from sqlmodel import Session
from uuid import UUID
from app.db.models import GameResult
from app.schemas.game_result_schema import GameResultCreate, GameResultCreateResponse

class GameResultService:
    def __init__(self, db: Session):
        self.db = db

    def create_game_result(self, data: GameResultCreate) -> GameResultCreateResponse:
        game_result = GameResult.from_orm(data)
        self.db.add(game_result)
        self.db.commit()
        self.db.refresh(game_result)

        return GameResultCreateResponse(
            result_id=game_result.result_id,
            created_at=game_result.created_at,
            **data.dict()
        )
