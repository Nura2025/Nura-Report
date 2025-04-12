# schemas/game_results_schema.py

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class GameResultCreate(BaseModel):
    game_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    difficulty_level: Optional[int] = None
    session_id: UUID

class GameResultCreateResponse(GameResultCreate):
    result_id: UUID
    created_at: datetime
