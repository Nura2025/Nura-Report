# mini_games_services.py
from typing import Union, Dict, Type, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from sqlmodel import select

from app.db.models import CropRecognitionMetrics, GameResult, MatchingCardsMetrics, SequenceMemoryMetrics
from app.schemas.mini_games_schema import CropRecognitionMetricCreate, CropRecognitionMetricsResponse, MatchingCardsMetricCreate, MatchingCardsMetricsResponse, SequenceMemoryMetricCreate, SequenceMemoryMetricsResponse

class MiniGameService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Define mappings once during initialization for better performance
        self.metric_model_map = {
            "crop_recognition": (CropRecognitionMetricCreate, CropRecognitionMetrics),
            "sequence_memory": (SequenceMemoryMetricCreate, SequenceMemoryMetrics),
            "matching_cards": (MatchingCardsMetricCreate, MatchingCardsMetrics),
        }

    async def create_metric(self, metric_type: str, data: Union[CropRecognitionMetricCreate, SequenceMemoryMetricCreate, MatchingCardsMetricCreate, dict]) -> Union[CropRecognitionMetricsResponse, SequenceMemoryMetricsResponse, MatchingCardsMetricsResponse]:
        metric_model_create, metric_model_response = self.metric_model_map.get(metric_type, (None, None))
        if not metric_model_create:
            raise HTTPException(status_code=400, detail="Unsupported metric type")

        # Ensure data is a dictionary
        if isinstance(data, dict):
            metric_data = data
        else:
            metric_data = data.dict()

        # Create the metric instance
        metric = metric_model_response(**metric_data)

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric

        
    async def get_metrics_by_type(self, metric_type: str, result_id: UUID):
            print(f"inside the get query")

            if metric_type == "crop":
                query = select(CropRecognitionMetrics).where(CropRecognitionMetrics.result_id == result_id)
            elif metric_type == "sequence":
                query = select(SequenceMemoryMetrics).where(SequenceMemoryMetrics.result_id == result_id)
            elif metric_type == "matching":
                query = select(MatchingCardsMetrics).where(MatchingCardsMetrics.result_id == result_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported metric type: {metric_type}"
                )
            print(f" before Executing query: {query}")

            result = await self.db.execute(query)
            return result.scalars().all()

