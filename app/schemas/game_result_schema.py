# game_result_schema.py
from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from uuid import UUID

from app.db.enums import GameType
from app.schemas.mini_games_schema import GoNoGoMetricCreate, MatchingCardsMetricCreate, MatchingCardsMetricsResponse, SequenceMemoryMetricCreate, SequenceMemoryMetricsResponse

class GameResultBase(BaseModel):
    session_id: UUID | None = None
    start_time: datetime
    end_time: datetime | None = None
    difficulty_level: int

class GameResultGoNoGoCreate(GameResultBase):
    game_type: Literal["go_no_go"] = "go_no_go"
    go_no_go_metrics: GoNoGoMetricCreate

class GameResultSequenceCreate(GameResultBase):
    game_type: Literal["sequence_memory"] = "sequence_memory"
    sequence_metrics: SequenceMemoryMetricCreate

class GameResultMatchingCreate(GameResultBase):
    game_type: Literal["matching_cards"] = "matching_cards"
    matching_metrics: MatchingCardsMetricCreate
  
class GameResultResponse(BaseModel):
    result_id: UUID
    created_at: datetime
    game_type: GameType
    go_no_go_metrics: GoNoGoMetricCreate | None = None
    sequence_metrics: SequenceMemoryMetricCreate | None = None
    matching_metrics: MatchingCardsMetricCreate | None = None

    class Config:
        from_attributes = True
        orm_mode = True

    
GameResultCreate = Annotated[
    Union[
        GameResultGoNoGoCreate,
        GameResultSequenceCreate,
        GameResultMatchingCreate,
    ],
    Field(discriminator="game_type") ]

