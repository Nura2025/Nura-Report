from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from app.db.models import Patient
from app.schemas.sessions_schema import SessionCreate, SessionCreateResponse, SessionResponse
from app.db.database import get_session
from app.services.session_service import SessionService

from fastapi import APIRouter, Depends, status, Body
from sqlmodel import Session
from app.services.mini_games_services import MiniGameService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.post("/{metric_type}", status_code=status.HTTP_201_CREATED)
def create_metric(
    metric_type: str,
    data: dict = Body(...),
    db: Session = Depends(get_session)
):
    """
    Creates a metric entry based on the game type.
    Valid types: crop, sequence, matching.
    """
    service = MiniGameService(db)
    return service.create_metric(metric_type, data)
