from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from uuid import UUID
import logging

from app.calculation.impulse import compute_impulse_control_score
from app.db.models import GameResult, ImpulseAnalysis
from app.utils.age_utils import get_age_group


class ImpulseAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_and_save_impulse_analysis(
        self, session_id: UUID, date_of_birth: Optional[datetime]
    ):
        try:
            # Calculate age group if date_of_birth is provided
            age_group = None
            if date_of_birth:
                today = datetime.utcnow().date()
                age = (
                    today.year
                    - date_of_birth.year
                    - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                )
                age_group = get_age_group(age)

            # Fetch game results for the session
            result = await self.db.execute(
                select(GameResult)
                .where(GameResult.session_id == session_id)
                .options(
                    selectinload(GameResult.sequence_metrics),
                    selectinload(GameResult.crop_metrics),
                    selectinload(GameResult.matching_metrics),
                )
            )
            game_results = result.scalars().all()

            if not game_results:
                logging.warning(f"No game results found for session {session_id}")
                return None

            # Initialize metrics
            sequence_metrics = None
            crop_metrics = None
            matching_metrics = None

            # Extract metrics from game results
            for game_result in game_results:
                if game_result.sequence_metrics:
                    sequence_metrics = game_result.sequence_metrics
                if game_result.crop_metrics:
                    crop_metrics = game_result.crop_metrics
                if game_result.matching_metrics:
                    matching_metrics = game_result.matching_metrics

            # Calculate impulse control score
            impulse_result = compute_impulse_control_score(
                # Sequence memory metrics
                commission_errors=sequence_metrics.commission_errors if sequence_metrics else 0,
                total_sequence_elements=sequence_metrics.total_sequence_elements if sequence_metrics else 0,
                retention_times=sequence_metrics.retention_times if sequence_metrics else [],
                
                # Crop recognition metrics
                distractions=crop_metrics.distractions if crop_metrics else 0,
                total_crops_presented=crop_metrics.total_crops_presented if crop_metrics else 0,
                crop_response_times=crop_metrics.response_times if crop_metrics else {},
                
                # Matching cards metrics
                incorrect_matches=matching_metrics.incorrect_matches if matching_metrics else 0,
                matches_attempted=matching_metrics.matches_attempted if matching_metrics else 0,
                time_per_match=matching_metrics.time_per_match if matching_metrics else [],
                
                # Age group
                age_group=age_group,
            )

            # Save the analysis if valid data is available
            if impulse_result["overall_impulse_control_score"] > 0:
                impulse_analysis = ImpulseAnalysis(
                    session_id=session_id,
                    overall_impulse_control_score=impulse_result["overall_impulse_control_score"],
                    inhibitory_control=impulse_result["inhibitory_control"],
                    response_control=impulse_result["response_control"],
                    decision_speed=impulse_result["decision_speed"],
                    error_adaptation=impulse_result["error_adaptation"],
                    created_at=game_results[0].start_time if game_results and game_results[0].start_time else datetime.utcnow(),
                )

                self.db.add(impulse_analysis)
                await self.db.commit()
                await self.db.refresh(impulse_analysis)

                return impulse_analysis
            else:
                logging.warning(
                    f"No valid impulse control metrics found for session {session_id}, skipping impulse analysis"
                )
                return None

        except Exception as e:
            logging.error(f"Error in impulse analysis for session {session_id}: {e}")
            raise