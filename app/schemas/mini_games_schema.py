# mini_games_schema.py
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict
from uuid import UUID

from pydantic import BaseModel, Field, root_validator
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime


class BaseMetric(BaseModel):
    result_id: UUID

# Crop
class CropRecognitionMetricCreate(BaseModel):
    crops_identified: int
    omission_errors: int
    response_times: Dict[str, float]
    distractions: int
    total_crops_presented: int

# Sequence
class SequenceMemoryMetricCreate(BaseModel):
    sequence_length: int
    commission_errors: int
    num_of_trials: int
    retention_times: List[int]
    total_sequence_elements: int

# Matching
class MatchingCardsMetricCreate(BaseModel):
    matches_attempted: int
    correct_matches: int
    incorrect_matches: int
    time_per_match: List[int]



class CropRecognitionMetricsResponse(BaseModel):
    metric_id: UUID
    crops_identified: int
    omission_errors: int
    response_times: Dict[str, float]
    distractions: int
    total_crops_presented: int
    created_at: datetime
    score: Optional[float]

    class Config:
        from_attributes = True
        orm_mode = True


class SequenceMemoryMetricsResponse(BaseModel):
    metric_id: UUID
    sequence_length: int
    commission_errors: int
    num_of_trials: int
    retention_times: List[int]
    total_sequence_elements: int
    created_at: datetime
    score: Optional[float]

    class Config:
        from_attributes = True
        orm_mode = True


class MatchingCardsMetricsResponse(BaseModel):
    metric_id: UUID
    matches_attempted: int
    correct_matches: int
    incorrect_matches: int
    time_per_match: List[int]
    created_at: datetime
    score: Optional[float]

    class Config:
        from_attributes = True  
        orm_mode = True
