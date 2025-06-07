# Session_schema.py
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, validator
from typing import Optional, List, Dict, Union
from uuid import UUID

from app.schemas.game_result_schema import GameResultCreate, GameResultMatchingCreate, GameResultResponse, GameResultSequenceCreate

class SessionBase(BaseModel):
    session_date: datetime
    session_duration: Optional[int] = None
    notes: Optional[str] = None
    game_results: List[GameResultCreate] = Field(..., description="List of game results")

class SessionCreate(SessionBase):
    user_id: Optional[UUID] = None
    
class SessionCreateResponse(BaseModel):
    session_id: UUID | None = None
    session_date: datetime
    created_at: Optional[datetime] = None

    class Config:
        from_orm = True
        from_attributes = True


class SessionResponse(SessionBase):
    session_id: UUID
    created_at: datetime
    game_results: List[GameResultResponse] = []

    class Config:
        from_orm = True
        from_attributes = True  


  
    