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
class CropRecognitionMetricCreate(BaseMetric):
    crops_identified: int
    omission_errors: int
    response_times: Dict[str, float]
    distractions: int
    total_crops_presented: int

# Sequence
class SequenceMemoryMetricCreate(BaseMetric):
    sequence_length: int
    commission_errors: int
    num_of_trials: int
    retention_times: List[int]
    total_sequence_elements: int

# Matching
class MatchingCardsMetricCreate(BaseMetric):
    matches_attempted: int
    correct_matches: int
    incorrect_matches: int
    time_per_match: List[int]

