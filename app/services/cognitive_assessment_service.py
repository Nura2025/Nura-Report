# cognitive_assessment_service.py

import statistics
from typing import Dict, List, Optional, Union, Tuple
import math
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import json
from datetime import datetime
from sqlalchemy.orm import selectinload
from app.calculation.attention import compute_crop_attention_score, compute_overall_attention_score, compute_sequence_attention_score, get_attention_normative_comparison
from app.calculation.impulse import compute_impulse_control_score
from app.calculation.memory import compute_memory_score
from app.db.models import AttentionAnalysis
from app.db.models import (
    GameResult, CropRecognitionMetrics, SequenceMemoryMetrics, MatchingCardsMetrics,
    MemoryAnalysis, ImpulseAnalysis, ExecutiveFunctionAnalysis, NormativeData
)
from app.utils.age_utils import get_age_group

class CognitiveAssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_and_save_cognitive_assessment(self, session_id: UUID, date_of_birth: Optional[datetime]):
        """Calculate and save comprehensive cognitive assessment for a session."""
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
            # Fetch game results with metrics
            result = await self.db.execute(
                select(GameResult)
                .where(GameResult.session_id == session_id)
                .options(
                    selectinload(GameResult.crop_metrics),
                    selectinload(GameResult.sequence_metrics),
                    selectinload(GameResult.matching_metrics)
                )
            )
            game_results = result.scalars().all()
            
            # Extract metrics
            sequence_metrics = {}
            crop_metrics = {}
            matching_metrics = {}
            
            for game_result in game_results:
                if game_result.sequence_metrics:
                    sequence_metrics = {
                        "sequence_length": game_result.sequence_metrics.sequence_length,
                        "commission_errors": game_result.sequence_metrics.commission_errors,
                        "num_of_trials": game_result.sequence_metrics.num_of_trials,
                        "retention_times": game_result.sequence_metrics.retention_times,
                        "total_sequence_elements": game_result.sequence_metrics.total_sequence_elements
                    }
                
                if game_result.crop_metrics:
                    crop_metrics = {
                        "crops_identified": game_result.crop_metrics.crops_identified,
                        "omission_errors": game_result.crop_metrics.omission_errors,
                        "distractions": game_result.crop_metrics.distractions,
                        "total_crops_presented": game_result.crop_metrics.total_crops_presented,
                        "response_times": game_result.crop_metrics.response_times
                    }
                
                if game_result.matching_metrics:
                    matching_metrics = {
                        "matches_attempted": game_result.matching_metrics.matches_attempted,
                        "correct_matches": game_result.matching_metrics.correct_matches,
                        "incorrect_matches": game_result.matching_metrics.incorrect_matches,
                        "time_per_match": game_result.matching_metrics.time_per_match
                    }
            
            # Calculate memory score
            memory_result = compute_memory_score(
                # Sequence metrics
                sequence_length=sequence_metrics.get("sequence_length", 0),
                commission_errors=sequence_metrics.get("commission_errors", 0),
                num_of_trials=sequence_metrics.get("num_of_trials", 0),
                retention_times=sequence_metrics.get("retention_times", []),
                total_sequence_elements=sequence_metrics.get("total_sequence_elements", 0),
                
                # Matching card metrics
                correct_matches=matching_metrics.get("correct_matches", 0),
                incorrect_matches=matching_metrics.get("incorrect_matches", 0),
                matches_attempted=matching_metrics.get("matches_attempted", 0),
                time_per_match=matching_metrics.get("time_per_match", []),
                
                age_group=age_group
            )

              # Calculate attention scores
            crop_score = compute_crop_attention_score(
                crops_identified=crop_metrics.get("crops_identified", 0),
                omission_errors=crop_metrics.get("omission_errors", 0),
                distractions=crop_metrics.get("distractions", 0),
                total_crops_presented=crop_metrics.get("total_crops_presented", 0),
                response_times=crop_metrics.get("response_times", {}),
                age_group=age_group
            ) if crop_metrics else 0

            sequence_score = compute_sequence_attention_score(
                sequence_length=sequence_metrics.get("sequence_length", 0),
                expected_max_sequence=sequence_metrics.get("total_sequence_elements", 0),
                commission_errors=sequence_metrics.get("commission_errors", 0),
                total_sequence_elements=sequence_metrics.get("total_sequence_elements", 0),
                retention_times=sequence_metrics.get("retention_times", []),
                age_group=age_group
            ) if sequence_metrics else 0

            overall_attention_score = compute_overall_attention_score(crop_score, sequence_score)
            
            # Calculate impulse control score
            impulse_result = compute_impulse_control_score(
                # Sequence metrics
                commission_errors=sequence_metrics.get("commission_errors", 0),
                total_sequence_elements=sequence_metrics.get("total_sequence_elements", 0),
                retention_times=sequence_metrics.get("retention_times", []),
                distractions=crop_metrics.get("distractions", 0),
                total_crops_presented=crop_metrics.get("total_crops_presented", 0),
                crop_response_times=crop_metrics.get("response_times", {}),                
                incorrect_matches=matching_metrics.get("incorrect_matches", 0),
                matches_attempted=matching_metrics.get("matches_attempted", 0),
                time_per_match=matching_metrics.get("time_per_match", []),
                
                age_group=age_group
            )
            
            # Calculate executive function score
            executive_result = self.compute_executive_function_score(
                memory_score=memory_result["overall_memory_score"],
                impulse_score=impulse_result["overall_impulse_control_score"],
                attention_score=overall_attention_score
            )

            attention_comparison = await self.compare_to_normative_data(
                overall_attention_score,
                "attention",
                 age_group = age_group
            )
            
            memory_comparison = await self.compare_to_normative_data(
                memory_result["overall_memory_score"], 
                "memory", 
                age_group
            )
            
            impulse_comparison = await self.compare_to_normative_data(
                impulse_result["overall_impulse_control_score"], 
                "impulse_control", 
                age_group
            )
            
            executive_comparison = await self.compare_to_normative_data(
                executive_result["executive_function_score"], 
                "executive_function", 
                age_group
            )

            attention_analysis = AttentionAnalysis(
                session_id=session_id,
                crop_score=crop_score,
                sequence_score=sequence_score,
                overall_score=overall_attention_score,
                percentile=attention_comparison["percentile"],
                classification=attention_comparison["classification"]
            )
            
            memory_analysis = MemoryAnalysis(
                session_id=session_id,
                overall_memory_score=memory_result["overall_memory_score"],
                working_memory_score=memory_result["components"].get("working_memory", 0),
                visual_memory_score=memory_result["components"].get("visual_memory", 0),
                data_completeness=memory_result["data_completeness"],
                tasks_used=memory_result["tasks_used"],
                percentile=memory_comparison["percentile"],
                classification=memory_comparison["classification"],
                working_memory_components=memory_result["components"].get("working_memory_components", {}),
                visual_memory_components=memory_result["components"].get("visual_memory_components", {})
            )
            
            impulse_analysis = ImpulseAnalysis(
                session_id=session_id,
                overall_impulse_control_score=impulse_result["overall_impulse_control_score"],
                inhibitory_control=impulse_result["inhibitory_control"],
                response_control=impulse_result["response_control"],
                decision_speed=impulse_result["decision_speed"],
                error_adaptation=impulse_result["error_adaptation"],
                data_completeness=impulse_result["data_completeness"],
                games_used=impulse_result["games_used"],
                percentile=impulse_comparison["percentile"],
                classification=impulse_comparison["classification"]
            )
            
            executive_analysis = ExecutiveFunctionAnalysis(
                session_id=session_id,
                executive_function_score=executive_result["executive_function_score"],
                memory_contribution=executive_result["memory_contribution"],
                impulse_contribution=executive_result["impulse_contribution"],
                attention_contribution=executive_result["attention_contribution"],
                percentile=executive_comparison["percentile"],
                classification=executive_comparison["classification"],
                profile_pattern=executive_result["profile_pattern"],
            )
            
            self.db.add(attention_analysis)
            self.db.add(memory_analysis)
            self.db.add(impulse_analysis)
            self.db.add(executive_analysis)
            
            await self.db.commit()
            
            return {
                "memory_analysis": memory_analysis,
                "impulse_analysis": impulse_analysis,
                "executive_analysis": executive_analysis
            }
            
        except Exception as e:
            await self.db.rollback()
            raise e
      
    #  resourses :Diamond, A. (2013). Executive functions. Annual Review of Psychology, 64(1), 135–168. https://doi.org/10.1146/annurev-psych-113011-143750
    def compute_executive_function_score(self, memory_score=None, impulse_score=None, attention_score=None):
        """
        Calculate executive function score from memory, impulse control, and attention (if provided).
        Based on scientific literature: Diamond (2013), NIH Toolbox, BRIEF-2.
        Applies dynamic weighting based on available components.
        """

        # Initialize contributions and total score
        executive_score = 0
        total_weight = 0

        # Determine available scores and apply appropriate weights
        weights = {}
        if memory_score is not None and impulse_score is not None and attention_score is not None:
            weights = {'memory': 0.4, 'impulse': 0.35, 'attention': 0.25}
        elif memory_score is not None and impulse_score is not None:
            weights = {'memory': 0.55, 'impulse': 0.45}
        elif memory_score is not None and attention_score is not None:
            weights = {'memory': 0.6, 'attention': 0.4}
        elif impulse_score is not None and attention_score is not None:
            weights = {'impulse': 0.55, 'attention': 0.45}
        elif memory_score is not None:
            weights = {'memory': 1.0}
        elif impulse_score is not None:
            weights = {'impulse': 1.0}
        elif attention_score is not None:
            weights = {'attention': 1.0}
        else:
            raise ValueError("At least one score must be provided to compute executive function.")

        # Compute weighted score
        memory_contribution = impulse_contribution = attention_contribution = None
        if 'memory' in weights:
            memory_contribution = weights['memory'] * memory_score
            executive_score += memory_contribution
            total_weight += weights['memory']
        if 'impulse' in weights:
            impulse_contribution = weights['impulse'] * impulse_score
            executive_score += impulse_contribution
            total_weight += weights['impulse']
        if 'attention' in weights:
            attention_contribution = weights['attention'] * attention_score
            executive_score += attention_contribution
            total_weight += weights['attention']

        # Normalize score if total weight ≠ 1 (just to be extra robust)
        if total_weight > 0:
            executive_score /= total_weight

        # Determine profile pattern (only if memory & impulse are available)
        if memory_score is not None and impulse_score is not None:
            if memory_score >= 75 and impulse_score < 65:
                profile_pattern = "Memory strength with impulse control challenges"
            elif impulse_score >= 75 and memory_score < 65:
                profile_pattern = "Impulse control strength with memory challenges"
            elif memory_score >= 75 and impulse_score >= 75:
                profile_pattern = "Strong executive function profile"
            elif memory_score < 65 and impulse_score < 65:
                profile_pattern = "Executive function challenges"
            else:
                profile_pattern = "Mixed executive function profile"
        else:
            profile_pattern = "Insufficient data for full profile pattern"

        return {
            "executive_function_score": round(executive_score, 1),
            "memory_contribution": round(memory_contribution, 1) if memory_contribution is not None else None,
            "impulse_contribution": round(impulse_contribution, 1) if impulse_contribution is not None else None,
            "attention_contribution": round(attention_contribution, 1) if attention_contribution is not None else None,
            "profile_pattern": profile_pattern
        }

    
    async def compare_to_normative_data(self, score, domain, age_group):
        """Compare score to normative data."""
        # Query normative data
        result = await self.db.execute(
            select(NormativeData)
            .where(
                NormativeData.domain == domain,
                NormativeData.age_group == age_group
            )
        )
        norm_data = result.scalar_one_or_none()
        
        # Use default values if no normative data found
        if not norm_data:
            if domain == "memory":
                mean = 75
                std = 12
            elif domain == "impulse_control":
                mean = 70
                std = 15
            elif domain == "executive_function":
                mean = 73
                std = 13
            else:  # attention
                mean = 70
                std = 15
        else:
            mean = norm_data.mean_score
            std = norm_data.standard_deviation
        
        # Calculate z-score
        z_score = (score - mean) / std if std > 0 else 0
        
        # Calculate percentile
        percentile = 100 * (0.5 * (1 + math.erf(z_score / math.sqrt(2))))
        
        # Determine classification
        if percentile >= 98:
            classification = "Very Superior"
        elif percentile >= 91:
            classification = "Superior"
        elif percentile >= 75:
            classification = "High Average"
        elif percentile >= 25:
            classification = "Average"
        elif percentile >= 9:
            classification = "Low Average"
        elif percentile >= 2:
            classification = "Borderline"
        else:
            classification = "Extremely Low"
        
        return {
            "z_score": round(z_score, 2),
            "percentile": round(percentile, 1),
            "classification": classification
        }
