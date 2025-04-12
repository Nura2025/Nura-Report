from uuid import UUID
from fastapi import HTTPException
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from sqlmodel import Session
from fastapi import HTTPException, status
from app.db.models import CropRecognitionMetrics ,SequenceMemoryMetrics,MatchingCardsMetrics
from app.schemas.mini_games_schema import CropRecognitionMetricCreate, SequenceMemoryMetricCreate, MatchingCardsMetricCreate



class MiniGameService:
    def __init__(self, db: Session):
        self.db = db

    def create_metric(self, metric_type: str, data: dict):
        if metric_type == "crop":
            metric = CropRecognitionMetrics(**data)
        elif metric_type == "sequence":
            metric = SequenceMemoryMetrics(**data)
        elif metric_type == "matching":
            metric = MatchingCardsMetrics(**data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported metric type: {metric_type}"
            )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric
