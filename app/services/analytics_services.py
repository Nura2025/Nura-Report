"""
Repository for cognitive assessment data access with optimized implementation.
"""
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import Depends
from app.db.database import get_session
from app.db.models import (
    MemoryAnalysis, ImpulseAnalysis, ExecutiveFunctionAnalysis, 
    AttentionAnalysis, NormativeData, Session, Patient, GameResult
)
from app.utils.age_utils import get_age_group
from app.utils.query_builder import QueryBuilder
from app.utils.domain_validation import get_domain_info, DOMAIN_MAP
from app.utils.cache import cached, user_profile_cache_key, timeseries_cache_key, progress_cache_key

class CognitiveRepository:
    """Repository for accessing cognitive assessment data."""
    
    def __init__(self, db: AsyncSession = Depends(get_session)):
        """
        Initialize repository with database session.
        
        Args:
            db: AsyncSession - Database session
        """
        self.db = db
    
    @cached(expire=300, key_builder=user_profile_cache_key)
    async def get_cognitive_profile(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive cognitive profile with optimized queries.
        
        Args:
            user_id: UUID - User ID to get profile for
            
        Returns:
            Dict containing cognitive profile data
        """
        # Get patient info in a single query
        patient_result = await self.db.execute(
            select(
                Patient.first_name,
                Patient.last_name,
                Patient.date_of_birth,
                Patient.gender,
                Patient.adhd_subtype
            ).where(Patient.user_id == user_id)
        )
        patient_data = patient_result.first()
        if not patient_data:
            return None
        
        # Get all domain scores using the query builder
        scores_query, scores_params = QueryBuilder.build_domain_scores_query(user_id=user_id)
        scores_result = await self.db.execute(text(scores_query), scores_params)
        scores_data = scores_result.first()
        
        # Get trend data using the query builder
        trend_query, trend_params = QueryBuilder.build_trend_query(user_id=user_id)
        trend_result = await self.db.execute(text(trend_query), trend_params)
        trend_data = trend_result.fetchall()
        
        # Calculate age and age group
        today = datetime.utcnow().date()
        age = (
            today.year
            - patient_data.date_of_birth.year
            - ((today.month, today.day) < (patient_data.date_of_birth.month, patient_data.date_of_birth.day))
        )
        age_group = get_age_group(age)
        
        # Construct the profile response
        profile = {
            "user_id": user_id,
            "user_name": f"{patient_data.first_name} {patient_data.last_name}",
            "age": age,
            "age_group": age_group,
            "gender": patient_data.gender,
            "total_sessions": scores_data.total_sessions if scores_data else 0,
            "first_session_date": scores_data.first_session_date if scores_data else None,
            "last_session_date": scores_data.last_session_date if scores_data else None,
            "adhd_subtype": patient_data.adhd_subtype,
            "avg_domain_scores": {
                "memory": float(scores_data.avg_memory_score) if scores_data else 0.0,
                "attention": float(scores_data.avg_attention_score) if scores_data else 0.0,
                "impulse_control": float(scores_data.avg_impulse_score) if scores_data else 0.0,
                "executive_function": float(scores_data.avg_executive_score) if scores_data else 0.0,
            },
            "trend_graph": [
                {
                    "session_date": row.session_date,
                    "attention_score": float(row.attention_score),
                    "memory_score": float(row.memory_score),
                    "impulse_score": float(row.impulse_score),
                    "executive_score": float(row.executive_score),
                }
                for row in trend_data
            ],
        }
        
        return profile
    
    @cached(expire=600, key_builder=timeseries_cache_key)
    async def get_cognitive_timeseries(
        self, 
        user_id: UUID,
        domain: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1 day"
    ) -> List[Dict[str, Any]]:
        """
        Get time series data using continuous aggregates when possible.
        
        Args:
            user_id: UUID - User ID to get data for
            domain: str - Cognitive domain
            start_date: datetime - Start date for time series
            end_date: datetime - End date for time series
            interval: str - Time bucket interval
            
        Returns:
            List of time series data points
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=90)
        if not end_date:
            end_date = datetime.now()
        
        # Get domain info using the domain validation utility
        domain_info = get_domain_info(domain)
        
        # Build query using the query builder
        query, params = QueryBuilder.build_timeseries_query(
            user_id=user_id,
            domain_info=domain_info,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )

        result = await self.db.execute(text(query), params)
        data = result.fetchall()
        
        return [{"date": row.time_bucket, "score": float(row.avg_score)} for row in data]
    
    @cached(expire=600, key_builder=progress_cache_key)
    async def get_cognitive_progress(
        self,
        user_id: UUID,
        domain: str,
        period: str = "90d"
    ) -> Dict[str, Any]:
        """
        Get progress comparison data for a cognitive domain.
        
        Args:
            user_id: UUID - User ID to get progress for
            domain: str - Cognitive domain
            period: str - Period for comparison (30d, 60d, 90d)
            
        Returns:
            Dict containing progress comparison data
        """
        # Get domain info using the domain validation utility
        domain_info = get_domain_info(domain)
        
        # Map period to interval
        period_map = {
            "30d": "30 days",
            "60d": "60 days",
            "90d": "90 days"
        }
        interval = period_map.get(period, "90 days")
        
        # Build query using the query builder
        query, params = QueryBuilder.build_progress_query(
            user_id=user_id,
            domain_info=domain_info,
            interval=interval
        )
        
        result = await self.db.execute(text(query), params)
        data = result.fetchone()
        
        if not data:
            return None
        
        return {
            "user_id": user_id,
            "domain": domain,
            "period": period,
            "initial_score": float(data.initial_score),
            "current_score": float(data.current_score),
            "initial_date": data.initial_date,
            "current_date": data.current_date,
            "absolute_change": float(data.absolute_change),
            "percentage_change": float(data.percentage_change)
        }
    
    @cached(expire=600)
    async def get_component_details(
        self,
        session_id: UUID,
        domain: str
    ) -> Dict[str, Any]:
        """
        Get detailed component scores for a cognitive domain.
        
        Args:
            session_id: UUID - Session ID to get details for
            domain: str - Cognitive domain
            
        Returns:
            Dict containing component details
        """
        if domain == "memory":
            result = await self.db.execute(
                select(MemoryAnalysis)
                .where(MemoryAnalysis.session_id == session_id)
                .order_by(MemoryAnalysis.created_at.desc())
                .limit(1)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            return {
                "session_id": session_id,
                "domain": domain,
                "overall_score": float(memory.overall_memory_score),
                "percentile": float(memory.percentile),
                "classification": memory.classification,
                "components": {
                    "working_memory": {
                        "score": float(memory.working_memory_score),
                        "components": memory.working_memory_components
                    },
                    "visual_memory": {
                        "score": float(memory.visual_memory_score),
                        "components": memory.visual_memory_components
                    }
                },
                "data_completeness": float(memory.data_completeness),
                "tasks_used": memory.tasks_used
            }
        
        elif domain == "impulse_control":
            result = await self.db.execute(
                select(ImpulseAnalysis)
                .where(ImpulseAnalysis.session_id == session_id)
                .order_by(ImpulseAnalysis.created_at.desc())
                .limit(1)
            )
            impulse = result.scalar_one_or_none()
            
            if not impulse:
                return None
            
            return {
                "session_id": session_id,
                "domain": domain,
                "overall_score": float(impulse.overall_impulse_control_score),
                "classification": impulse.classification,
                "components": {
                    "inhibitory_control": float(impulse.inhibitory_control),
                    "response_control": float(impulse.response_control),
                    "decision_speed": float(impulse.decision_speed),
                    "error_adaptation": float(impulse.error_adaptation)
                },
                "data_completeness": float(impulse.data_completeness) if hasattr(impulse, 'data_completeness') else 1.0,
                "games_used": impulse.games_used if hasattr(impulse, 'games_used') else []
            }
        
        return None
    
    @cached(expire=3600)
    async def get_normative_comparison(
        self,
        user_id: UUID,
        domain: str
    ) -> Dict[str, Any]:
        """
        Get normative comparison data for a user's cognitive domain.
        
        Args:
            user_id: UUID - User ID to get comparison for
            domain: str - Cognitive domain
            
        Returns:
            Dict containing normative comparison data
        """
        # Get domain info using the domain validation utility
        domain_info = get_domain_info(domain)
        table = domain_info["table"]
        column = domain_info["column"]
        
        # Get patient info for age group
        patient_result = await self.db.execute(
            select(Patient)
            .where(Patient.user_id == user_id)
        )
        patient = patient_result.scalar_one_or_none()
        
        if not patient:
            return None
        
        # Calculate age and age group
        today = datetime.utcnow().date()
        age = (
            today.year
            - patient.date_of_birth.year
            - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
        )
        
        age_group = get_age_group(age)
        
        # Get latest score with optimized query
        query = f"""
            SELECT 
                {column} AS score,
                created_at
            FROM 
                {table}
            WHERE 
                session_id IN (SELECT session_id FROM sessions WHERE user_id = :user_id)
            ORDER BY 
                created_at DESC
            LIMIT 1
        """
        
        result = await self.db.execute(text(query), {"user_id": str(user_id)})
        user_data = result.fetchone()
        
        if not user_data:
            return None
        
        user_score = float(user_data.score)
        
        # Get normative data
        norm_result = await self.db.execute(
            select(NormativeData)
            .where(
                NormativeData.domain == domain,
                NormativeData.age_group == age_group,
                NormativeData.clinical_group == None
            )
        )
        norm_data = norm_result.scalar_one_or_none()
        
        if not norm_data:
            return None
        
        # Calculate z-score and percentile
        import math
        z_score = (user_score - norm_data.mean_score) / norm_data.standard_deviation
        percentile = 100 * (0.5 * (1 + math.erf(z_score / math.sqrt(2))))
        
        # Get ADHD comparison data if available
        adhd_result = await self.db.execute(
            select(NormativeData)
            .where(
                NormativeData.domain == domain,
                NormativeData.age_group == age_group,
                NormativeData.clinical_group == "ADHD"
            )
        )
        adhd_data = adhd_result.scalar_one_or_none()
        
        adhd_comparison = None
        if adhd_data:
            adhd_z_score = (user_score - adhd_data.mean_score) / adhd_data.standard_deviation
            adhd_percentile = 100 * (0.5 * (1 + math.erf(adhd_z_score / math.sqrt(2))))
            adhd_comparison = {
                "mean_score": float(adhd_data.mean_score),
                "standard_deviation": float(adhd_data.standard_deviation),
                "z_score": float(adhd_z_score),
                "percentile": float(adhd_percentile)
            }
        
        return {
            "user_id": user_id,
            "domain": domain,
            "user_score": user_score,
            "age_group": age_group,
            "normative_comparison": {
                "mean_score": float(norm_data.mean_score),
                "standard_deviation": float(norm_data.standard_deviation),
                "z_score": float(z_score),
                "percentile": float(percentile),
                "sample_size": norm_data.sample_size,
                "reliability": float(norm_data.reliability)
            },
            "adhd_comparison": adhd_comparison
        }
    
    @cached(expire=300)
    async def get_session_details(
        self,
        user_id: UUID,
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get detailed session information including game results.
        
        Args:
            user_id: UUID - User ID to get session details for
            session_id: UUID - Optional specific session ID
            
        Returns:
            Dict containing session details
        """
        # If session_id is provided, get that specific session
        # Otherwise, get the most recent session
        if session_id:
            session_query = select(Session).where(
                Session.session_id == session_id,
                Session.user_id == user_id
            )
        else:
            session_query = select(Session).where(
                Session.user_id == user_id
            ).order_by(Session.session_date.desc()).limit(1)
        
        session_result = await self.db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Get game results for the session
        game_results_query = select(GameResult).where(
            GameResult.session_id == session.session_id
        )
        game_results_result = await self.db.execute(game_results_query)
        game_results = game_results_result.scalars().all()
        
        # Get cognitive domain scores for the session using the query builder
        scores_query, scores_params = QueryBuilder.build_domain_scores_query(session_id=session.session_id)
        scores_result = await self.db.execute(text(scores_query), scores_params)
        scores_data = scores_result.first()
        
        # Calculate overall performance score (average of all domain scores)
        domain_scores = {
            "memory": float(scores_data.memory_score) if scores_data else 0.0,
            "attention": float(scores_data.attention_score) if scores_data else 0.0,
            "impulse_control": float(scores_data.impulse_score) if scores_data else 0.0,
            "executive_function": float(scores_data.executive_score) if scores_data else 0.0,
        }
        
        non_zero_scores = [score for score in domain_scores.values() if score > 0]
        overall_score = sum(non_zero_scores) / len(non_zero_scores) if non_zero_scores else 0
        
        # Format game results
        formatted_game_results = []
        for game in game_results:
            game_data = {
                "result_id": game.result_id,
                "game_type": game.game_type.value,
                "start_time": game.start_time,
                "end_time": game.end_time,
                "difficulty_level": game.difficulty_level,
            }
            formatted_game_results.append(game_data)
        
        return {
            "session_id": session.session_id,
            "session_date": session.session_date,
            "session_duration": session.session_duration,
            "notes": session.notes,
            "overall_performance": overall_score,
            "domain_scores": domain_scores,
            "game_results": formatted_game_results
        }
    
    @cached(expire=300)
    async def get_session_history(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get session history for a user with pagination.
        
        Args:
            user_id: UUID - User ID to get session history for
            limit: int - Maximum number of sessions to return
            offset: int - Offset for pagination
            
        Returns:
            Tuple of (list of session data, total count)
        """
        # Get total count for pagination
        count_query = select(func.count(Session.session_id)).where(
            Session.user_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Get sessions with pagination
        sessions_query = select(Session).where(
            Session.user_id == user_id
        ).order_by(Session.session_date.desc()).offset(offset).limit(limit)
        
        sessions_result = await self.db.execute(sessions_query)
        sessions = sessions_result.scalars().all()
        
        # Get domain scores for each session
        session_data = []
        for session in sessions:
            # Get cognitive domain scores for the session using the query builder
            scores_query, scores_params = QueryBuilder.build_domain_scores_query(session_id=session.session_id)
            scores_result = await self.db.execute(text(scores_query), scores_params)
            scores_data = scores_result.first()
            
            # Calculate overall performance score (average of all domain scores)
            domain_scores = {
                "memory": float(scores_data.memory_score) if scores_data else 0.0,
                "attention": float(scores_data.attention_score) if scores_data else 0.0,
                "impulse_control": float(scores_data.impulse_score) if scores_data else 0.0,
                "executive_function": float(scores_data.executive_score) if scores_data else 0.0,
            }
            
            non_zero_scores = [score for score in domain_scores.values() if score > 0]
            overall_score = sum(non_zero_scores) / len(non_zero_scores) if non_zero_scores else 0
            
            # Get game count for the session
            game_count_query = select(func.count(GameResult.result_id)).where(
                GameResult.session_id == session.session_id
            )
            game_count_result = await self.db.execute(game_count_query)
            game_count = game_count_result.scalar_one()
            
            session_data.append({
                "session_id": session.session_id,
                "session_date": session.session_date,
                "session_duration": session.session_duration,
                "overall_score": overall_score,
                "domain_scores": domain_scores,
                "game_count": game_count,
                "status": "Completed" if session.session_duration else "Interrupted"
            })
        
        return session_data, total_count
        
    @cached(expire=300)
    async def get_cognitive_skills_comparison(
        self,
        user_id: UUID,
        comparison_period: str = "all"
    ) -> Dict[str, Any]:
        """
        Get comparative data for each cognitive skill showing scores before and after interventions.
        
        Args:
            user_id: UUID - User ID to get comparison for
            comparison_period: str - Period for comparison (all, 30d, 60d, 90d, 6m, 1y)
            
        Returns:
            Dict containing comparison data for all cognitive domains
        """
        # Map period to interval
        period_map = {
            "30d": "30 days",
            "60d": "60 days",
            "90d": "90 days",
            "6m": "180 days",
            "1y": "365 days",
            "all": None
        }
        interval = period_map.get(comparison_period)
        
        # Get data for each domain
        domains = ["memory", "attention", "impulse_control", "executive_function"]
        domain_data = {}
        overall_improvement = 0
        valid_domains = 0
        
        for domain in domains:
            # Get domain info
            domain_info = get_domain_info(domain)
            table = domain_info["table"]
            column = domain_info["column"]
            
            # Build query parameters
            query_params = {"user_id": str(user_id)}
            
            # Build query based on comparison period
            if interval:
                query = f"""
                WITH measurements AS (
                    SELECT 
                        {column} AS score,
                        created_at,
                        ROW_NUMBER() OVER (ORDER BY created_at ASC) AS rn_asc,
                        ROW_NUMBER() OVER (ORDER BY created_at DESC) AS rn_desc
                    FROM 
                        {table}
                    WHERE 
                        session_id IN (SELECT session_id FROM sessions WHERE user_id = :user_id)
                        AND created_at >= NOW() - INTERVAL '{interval}'
                )
                """
            else:
                query = f"""
                WITH measurements AS (
                    SELECT 
                        {column} AS score,
                        created_at,
                        ROW_NUMBER() OVER (ORDER BY created_at ASC) AS rn_asc,
                        ROW_NUMBER() OVER (ORDER BY created_at DESC) AS rn_desc
                    FROM 
                        {table}
                    WHERE 
                        session_id IN (SELECT session_id FROM sessions WHERE user_id = :user_id)
                )
                """
            
            # Complete the query
            query += """
            SELECT 
                first.score AS initial_score,
                last.score AS current_score,
                first.created_at AS initial_date,
                last.created_at AS current_date,
                (last.score - first.score) AS absolute_change,
                CASE 
                    WHEN first.score = 0 THEN 0
                    ELSE ((last.score - first.score) / first.score) * 100 
                END AS percentage_change
            FROM 
                (SELECT score, created_at FROM measurements WHERE rn_asc = 1) first,
                (SELECT score, created_at FROM measurements WHERE rn_desc = 1) last
            """
            
            # Execute query
            result = await self.db.execute(text(query), query_params)
            data = result.fetchone()
            
            if data and data.initial_score is not None and data.current_score is not None:
                domain_data[domain] = {
                    "initial_score": float(data.initial_score),
                    "current_score": float(data.current_score),
                    "initial_date": data.initial_date,
                    "current_date": data.current_date,
                    "absolute_change": float(data.absolute_change),
                    "percentage_change": float(data.percentage_change)
                }
                
                # Add to overall improvement calculation
                if data.initial_score > 0:
                    overall_improvement += float(data.percentage_change)
                    valid_domains += 1
        
        # Calculate average improvement
        avg_improvement = overall_improvement / valid_domains if valid_domains > 0 else 0
        
        # Get trend data for visualization
        trend_query, trend_params = QueryBuilder.build_trend_query(user_id=user_id)
        trend_result = await self.db.execute(text(trend_query), trend_params)
        trend_data = trend_result.fetchall()
        
        trend_graph = [
            {
                "session_date": row.session_date,
                "attention_score": float(row.attention_score),
                "memory_score": float(row.memory_score),
                "impulse_score": float(row.impulse_score),
                "executive_score": float(row.executive_score),
            }
            for row in trend_data
        ]
        
        return {
            "user_id": user_id,
            "comparison_period": comparison_period,
            "domain_comparisons": domain_data,
            "overall_improvement": avg_improvement,
            "trend_graph": trend_graph
        }
