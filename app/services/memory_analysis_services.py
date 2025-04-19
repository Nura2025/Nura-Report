from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from uuid import UUID
import logging

from app.calculation.memory import compute_memory_score
from app.db.models import (
    GameResult,
    MemoryAnalysis,
    SequenceMemoryMetrics,
    MatchingCardsMetrics,
)
from app.utils.age_utils import get_age_group


class MemoryAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def calculate_and_save_memory_analysis(
        self, session_id: UUID, date_of_birth: Optional[datetime]
    ):
        try:
            age_group = None
            if date_of_birth:
                today = datetime.utcnow().date()
                age = (
                    today.year
                    - date_of_birth.year
                    - (
                        (today.month, today.day)
                        < (date_of_birth.month, date_of_birth.day)
                    )
                )
                age_group = get_age_group(age)
            # Fetch game results for the session
            result = await self.db.execute(
                select(GameResult)
                .where(GameResult.session_id == session_id)
                .options(
                    selectinload(GameResult.sequence_metrics),
                    selectinload(GameResult.matching_metrics),
                )
            )
            
            game_results = result.scalars().all()
            print(f"Game resultsssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss: {game_results}")

            if not game_results:
                logging.warning(f"No game results found for session {session_id}")
                return None
            

            print(f"Game results: {game_results}")



            # Initialize metrics
            sequence_metrics = None
            matching_metrics = None

            # Extract metrics from game results
            for game_result in game_results:
                print(f"Game type: {game_result.game_type}")
                print(f"Sequence metrics: {game_result.sequence_metrics}")
                print(f"Matching metrics: {game_result.matching_metrics}")
                if game_result.sequence_metrics:
                    sequence_metrics = game_result.sequence_metrics
                if game_result.matching_metrics:
                    matching_metrics = game_result.matching_metrics

            # Calculate memory score
            memory_result = compute_memory_score(
                sequence_length=(
                    sequence_metrics.sequence_length if sequence_metrics else 0
                ),
                commission_errors=(
                    sequence_metrics.commission_errors if sequence_metrics else 0
                ),
                num_of_trials=sequence_metrics.num_of_trials if sequence_metrics else 0,
                retention_times=(
                    sequence_metrics.retention_times if sequence_metrics else []
                ),
                total_sequence_elements=(
                    sequence_metrics.total_sequence_elements if sequence_metrics else 0
                ),
                correct_matches=(
                    matching_metrics.correct_matches if matching_metrics else 0
                ),
                incorrect_matches=(
                    matching_metrics.incorrect_matches if matching_metrics else 0
                ),
                matches_attempted=(
                    matching_metrics.matches_attempted if matching_metrics else 0
                ),
                time_per_match=(
                    matching_metrics.time_per_match if matching_metrics else []
                ),
                age_group=age_group,
            )

            # Save the analysis if valid data is available
            if memory_result["overall_memory_score"] > 0:
                memory_analysis = MemoryAnalysis(
                    session_id=session_id,
                    overall_memory_score=memory_result["overall_memory_score"],
                    working_memory_score=memory_result["components"].get(
                        "working_memory", 0
                    ),
                    visual_memory_score=memory_result["components"].get(
                        "visual_memory", 0
                    ),
                    created_at=game_results[0].start_time if game_results and game_results[0].start_time else datetime.utcnow()
,
                )

                self.db.add(memory_analysis)
                await self.db.commit()
                await self.db.refresh(memory_analysis)

                return memory_analysis
            else:
                logging.warning(
                    f"No valid memory metrics found for session {session_id}, skipping memory analysis"
                )
                return None

        except Exception as e:
            logging.error(f"Error in memory analysis for session {session_id}: {e}")
            raise
