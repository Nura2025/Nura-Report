from typing import List ,Tuple
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependinces import get_current_user
from app.db.database import get_session
from app.db.models import User, UserRole
from app.services.mini_games_services import MiniGameService
from app.schemas.mini_games_schema import (
    CropRecognitionMetricsResponse,
    SequenceMemoryMetricsResponse,
    MatchingCardsMetricsResponse,
    CropRecognitionMetricCreate,
    SequenceMemoryMetricCreate,
    MatchingCardsMetricCreate,
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get(
    "/sequence/{result_id}",
    response_model=List[SequenceMemoryMetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve sequence memory metrics for a specific game result",
)
async def get_sequence_metrics(
    result_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user),
):
    service = MiniGameService(session)

    # Fetch the session associated with the result_id
    game_result = await service.get_game_result_by_id(result_id)
    if not game_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game result not found.",
        )

    session_data = await service.get_session_by_id(game_result.session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    user, role = current_user
    if role == UserRole.PATIENT:
        if session_data.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data.",
            )
    elif role == UserRole.DOCTOR:
        # Ensure the session belongs to a patient associated with the clinician
        if session_data.clinician_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data.",
            )

    # Fetch and return the metrics
    return await service.get_metrics_by_type("sequence", result_id)


@router.get(
    "/crop/{result_id}",
    response_model=List[CropRecognitionMetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve crop recognition metrics for a specific game result",
)
async def get_crop_metrics(
    result_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user),
):
    service = MiniGameService(session)

    # Fetch the session associated with the result_id
    game_result = await service.get_game_result_by_id(result_id)
    if not game_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game result not found.",
        )

    session_data = await service.get_session_by_id(game_result.session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    user, role = current_user
    if role == UserRole.PATIENT:
        if session_data.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data.",
            )
    elif role == UserRole.DOCTOR:
        # Ensure the session belongs to a patient associated with the clinician
        if session_data.clinician_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data.",
            )

    # Fetch and return the metrics
    return await service.get_metrics_by_type("crop", result_id)


@router.get(
    "/matching/{result_id}",
    response_model=List[MatchingCardsMetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve matching cards metrics for a specific game result",
)
async def get_matching_cards_metrics(
    result_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user),
):
    service = MiniGameService(session)

    # Fetch the session associated with the result_id
    game_result = await service.get_game_result_by_id(result_id)
    if not game_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game result not found.",
        )

    session_data = await service.get_session_by_id(game_result.session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    user, role = current_user
    if role == UserRole.PATIENT:
        if session_data.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data.",
            )
    elif role == UserRole.DOCTOR:
        # Ensure the session belongs to a patient associated with the clinician
        if session_data.clinician_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data.",
            )

    # Fetch and return the metrics
    return await service.get_metrics_by_type("matching", result_id)