from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from uuid import UUID
import logging

from app.calculation.attention import (
    compute_crop_attention_score,
    compute_sequence_attention_score,
    compute_overall_attention_score,
)
from app.db.models import AttentionAnalysis, GameResult


class AttentionAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_and_save_attention_analysis(self, session_id: UUID):
        try:
            # Fetch game results for the session
            result = await self.db.execute(
                select(GameResult)
                .where(GameResult.session_id == session_id)
                .options(
                    selectinload(GameResult.crop_metrics),
                    selectinload(GameResult.sequence_metrics),
                )
            )
            game_results = result.scalars().all()

            if not game_results:
                logging.warning(f"No game results found for session {session_id}")
                return None

            crop_score = 0
            sequence_score = 0

            # Calculate scores for each game type
            for game_result in game_results:
                if game_result.crop_metrics:
                    crop_metrics = game_result.crop_metrics
                    crop_score = compute_crop_attention_score(
                        crops_identified=crop_metrics.crops_identified,
                        omission_errors=crop_metrics.omission_errors,
                        distractions=crop_metrics.distractions,
                        total_crops=crop_metrics.total_crops_presented,
                        response_times=list(crop_metrics.response_times.values()),
                    )

                if game_result.sequence_metrics:
                    sequence_metrics = game_result.sequence_metrics
                    sequence_score = compute_sequence_attention_score(
                        sequence_length=sequence_metrics.sequence_length,
                        expected_max_sequence=sequence_metrics.total_sequence_elements,
                        commission_errors=sequence_metrics.commission_errors,
                        total_elements=sequence_metrics.total_sequence_elements,
                    )

            # Compute overall attention score
            overall_score = compute_overall_attention_score(crop_score, sequence_score)

            # Validate that we have a valid overall score
            if overall_score is None:
                logging.warning(f"No valid scores found for session {session_id}, skipping attention analysis")
                return None

            # Create and save the AttentionAnalysis object
            attention_analysis = AttentionAnalysis(
                session_id=session_id,  # Ensure session_id is set
                crop_score=crop_score,
                sequence_score=sequence_score,
                overall_score=overall_score,
                created_at=game_results[0].start_time if game_results else None,
            )

            self.db.add(attention_analysis)
            await self.db.commit()
            await self.db.refresh(attention_analysis)

            return attention_analysis

        except Exception as e:
            logging.error(f"Error in attention analysis for session {session_id}: {e}")
            print("Error in attention analysis:", e)
            raise e