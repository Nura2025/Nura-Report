from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict
from uuid import UUID

class SessionBase(BaseModel):
    session_date: datetime
    session_duration: Optional[int] = None
    notes: Optional[str] = None
    user_id: UUID

class SessionCreate(SessionBase):
    pass

class SessionCreateResponse(SessionBase):
    session_id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_orm = True
        from_attributes = True  


class SessionResponse(SessionBase):
    session_id: UUID
    created_at: datetime
    game_results: List["GameResultResponse"] = []

    class Config:
        from_orm = True
        from_attributes = True  

class GameResultResponse(BaseModel):
    result_id: UUID
    game_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    difficulty_level: Optional[int] = None
    created_at: datetime