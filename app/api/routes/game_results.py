from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.db.database import get_session
from app.schemas.game_result_schema import GameResultCreate, GameResultCreateResponse
from app.services.game_result_services import GameResultService

router = APIRouter(prefix="/game-results", tags=["Game Results"])

@router.post(
    "",
    response_model=GameResultCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new game result",
    description="Endpoint to save game result data after gameplay for a specific session."
)
def create_game_result(
    game_result: GameResultCreate,
    db: Session = Depends(get_session)
):
    service = GameResultService(db)
    return service.create_game_result(game_result)
