from typing import List
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_session
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

@router.post(
    "/crop/{result_id}",
    response_model=CropRecognitionMetricsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create crop recognition metrics for a specific game result",
)
async def create_crop_metric(
    result_id: UUID,
    crop_data: CropRecognitionMetricCreate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    service = MiniGameService(session)
    return await service.create_metric("crop", crop_data.dict())

@router.post(
    "/sequence/{result_id}",
    response_model=SequenceMemoryMetricsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sequence memory metrics for a specific game result",
)
async def create_sequence_metric(
    result_id: UUID,
    sequence_data: SequenceMemoryMetricCreate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    service = MiniGameService(session)
    return await service.create_metric("sequence", sequence_data.dict())


@router.post(
    "/matching/{result_id}",
    response_model=MatchingCardsMetricsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create matching cards metrics for a specific game result",
)
async def create_matching_metric(
    result_id: UUID,
    matching_data: MatchingCardsMetricCreate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    service = MiniGameService(session)
    return await service.create_metric("matching", matching_data.dict())

@router.get(
    "/sequence/{result_id}",
    response_model=List[SequenceMemoryMetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve sequence memory metrics for a specific game result",
)
async def get_sequence_metrics(
    result_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    service = MiniGameService(session)
    return await service.get_metrics_by_type("sequence", result_id)
