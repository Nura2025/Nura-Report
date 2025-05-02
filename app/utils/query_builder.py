"""
SQL query builder utilities for cognitive data access.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from uuid import UUID

class QueryBuilder:
    """Base class for building SQL queries."""
    
    @staticmethod
    def build_domain_scores_query(session_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Build a query to get domain scores for a session or user.
        
        Args:
            session_id: Optional session ID to get scores for
            user_id: Optional user ID to get scores for
            
        Returns:
            Tuple of (query string, query parameters)
        """
        if session_id:
            query = """
            SELECT 
                COALESCE(ma.overall_memory_score, 0) AS memory_score,
                COALESCE(aa.overall_score, 0) AS attention_score,
                COALESCE(ia.overall_impulse_control_score, 0) AS impulse_score,
                COALESCE(ea.executive_function_score, 0) AS executive_score
            FROM 
                sessions s
            LEFT JOIN LATERAL (
                SELECT overall_memory_score
                FROM memory_analysis
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 1
            ) ma ON true
            LEFT JOIN LATERAL (
                SELECT overall_score
                FROM attention_analysis
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 1
            ) aa ON true
            LEFT JOIN LATERAL (
                SELECT overall_impulse_control_score
                FROM impulse_analysis
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 1
            ) ia ON true
            LEFT JOIN LATERAL (
                SELECT executive_function_score
                FROM executive_function_analysis
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 1
            ) ea ON true
            WHERE 
                s.session_id = :session_id
            """
            params = {"session_id": str(session_id)}
        elif user_id:
            query = """
            SELECT 
                COALESCE(AVG(ma.overall_memory_score), 0) AS avg_memory_score,
                COALESCE(AVG(aa.overall_score), 0) AS avg_attention_score,
                COALESCE(AVG(ia.overall_impulse_control_score), 0) AS avg_impulse_score,
                COALESCE(AVG(ea.executive_function_score), 0) AS avg_executive_score,
                COUNT(DISTINCT s.session_id) AS total_sessions,
                MIN(s.session_date) AS first_session_date,
                MAX(s.session_date) AS last_session_date
            FROM 
                sessions s
            LEFT JOIN memory_analysis ma ON s.session_id = ma.session_id
            LEFT JOIN attention_analysis aa ON s.session_id = aa.session_id
            LEFT JOIN impulse_analysis ia ON s.session_id = ia.session_id
            LEFT JOIN executive_function_analysis ea ON s.session_id = ea.session_id
            WHERE 
                s.user_id = :user_id
            """
            params = {"user_id": str(user_id)}
        else:
            raise ValueError("Either session_id or user_id must be provided")
        
        return query, params
    
    @staticmethod
    def build_trend_query(user_id: UUID) -> Tuple[str, Dict[str, Any]]:
        """
        Build a query to get trend data for a user.
        
        Args:
            user_id: User ID to get trend data for
            
        Returns:
            Tuple of (query string, query parameters)
        """
        query = """
        SELECT 
            s.session_date AS session_date,
            COALESCE(ma.overall_memory_score, 0) AS memory_score,
            COALESCE(aa.overall_score, 0) AS attention_score,
            COALESCE(ia.overall_impulse_control_score, 0) AS impulse_score,
            COALESCE(ea.executive_function_score, 0) AS executive_score
        FROM 
            sessions s
        LEFT JOIN LATERAL (
            SELECT overall_memory_score
            FROM memory_analysis
            WHERE session_id = s.session_id
            ORDER BY created_at DESC
            LIMIT 1
        ) ma ON true
        LEFT JOIN LATERAL (
            SELECT overall_score
            FROM attention_analysis
            WHERE session_id = s.session_id
            ORDER BY created_at DESC
            LIMIT 1
        ) aa ON true
        LEFT JOIN LATERAL (
            SELECT overall_impulse_control_score
            FROM impulse_analysis
            WHERE session_id = s.session_id
            ORDER BY created_at DESC
            LIMIT 1
        ) ia ON true
        LEFT JOIN LATERAL (
            SELECT executive_function_score
            FROM executive_function_analysis
            WHERE session_id = s.session_id
            ORDER BY created_at DESC
            LIMIT 1
        ) ea ON true
        WHERE 
            s.user_id = :user_id
        ORDER BY 
            s.session_date ASC
        """
        params = {"user_id": str(user_id)}
        
        return query, params
    
    @staticmethod
    def build_timeseries_query(
        user_id: UUID,
        domain_info: Dict[str, str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1 day"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build a query to get time series data for a domain.
        
        Args:
            user_id: User ID to get data for
            domain_info: Domain information (table, column, agg_view)
            start_date: Start date for time series
            end_date: End date for time series
            interval: Time bucket interval
            
        Returns:
            Tuple of (query string, query parameters)
        """
        table = domain_info["table"]
        column = domain_info["column"]
        agg_view = domain_info.get("agg_view")
        
        # Try to use continuous aggregate view if available and interval matches
        if agg_view and interval == "1 day":
            query = f"""
                SELECT 
                    bucket AS time_bucket,
                    avg_score
                FROM 
                    {agg_view}
                WHERE 
                    session_id IN (SELECT session_id FROM sessions WHERE user_id = :user_id)
                    AND bucket BETWEEN :start_date AND :end_date
                ORDER BY 
                    bucket ASC
            """
        else:
            # Fall back to regular time bucket query
            query = f"""
                SELECT 
                    time_bucket('{interval}', created_at) AS time_bucket,
                    AVG({column}) AS avg_score
                FROM 
                    {table}
                WHERE 
                    session_id IN (SELECT session_id FROM sessions WHERE user_id = :user_id)
                    AND created_at BETWEEN :start_date AND :end_date
                GROUP BY 
                    time_bucket
                ORDER BY 
                    time_bucket ASC
            """
        
        params = {
            "user_id": str(user_id),
            "start_date": start_date,
            "end_date": end_date,
        }
        
        return query, params
    
    @staticmethod
    def build_progress_query(
        user_id: UUID,
        domain_info: Dict[str, str],
        interval: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build a query to get progress comparison data for a domain.
        
        Args:
            user_id: User ID to get progress for
            domain_info: Domain information (table, column)
            interval: Time interval for comparison
            
        Returns:
            Tuple of (query string, query parameters)
        """
        table = domain_info["table"]
        column = domain_info["column"]
        
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
        
        params = {"user_id": str(user_id)}
        
        return query, params
