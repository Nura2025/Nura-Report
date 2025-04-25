# cognitive_api.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Tuple, text, select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlmodel import func
from app.api.dependinces import get_current_user
from app.db.database import get_session
from app.services.cognitive_assessment_service import CognitiveAssessmentService
from app.db.models import (
    MemoryAnalysis, ImpulseAnalysis, ExecutiveFunctionAnalysis, 
    AttentionAnalysis, NormativeData, Session, Patient, User, UserRole
)
from app.utils.age_utils import get_age_group

router = APIRouter(prefix="/api/cognitive", tags=["cognitive"])

@router.get("/profile/{user_id}")
async def get_cognitive_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user),
):
    """
    Get comprehensive cognitive profile for a user, including trend graph data.
    """
    patient_result = await db.execute(
        select(Patient).where(Patient.user_id == user_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    avg_memory_score = await db.execute(
        select(func.avg(MemoryAnalysis.overall_memory_score))
        .join(Session, MemoryAnalysis.session_id == Session.session_id)
        .where(Session.user_id == user_id)
    )
    avg_memory_score = avg_memory_score.scalar_one_or_none() or 0.0

    avg_attention_score = await db.execute(
        select(func.avg(AttentionAnalysis.overall_score))
        .join(Session, AttentionAnalysis.session_id == Session.session_id)
        .where(Session.user_id == user_id)
    )
    avg_attention_score = avg_attention_score.scalar_one_or_none() or 0.0

    avg_impulse_score = await db.execute(
        select(func.avg(ImpulseAnalysis.overall_impulse_control_score))
        .join(Session, ImpulseAnalysis.session_id == Session.session_id)
        .where(Session.user_id == user_id)
    )
    avg_impulse_score = avg_impulse_score.scalar_one_or_none() or 0.0

    avg_executive_score = await db.execute(
        select(func.avg(ExecutiveFunctionAnalysis.executive_function_score))
        .join(Session, ExecutiveFunctionAnalysis.session_id == Session.session_id)
        .where(Session.user_id == user_id)
    )
    avg_executive_score = avg_executive_score.scalar_one_or_none() or 0.0

    trend_query = text("""
        SELECT 
            s.session_date AS session_date,
            COALESCE(ma.overall_memory_score, 0) AS memory_score,
            COALESCE(aa.overall_score, 0) AS attention_score,
            COALESCE(ia.overall_impulse_control_score, 0) AS impulse_score,
            COALESCE(ea.executive_function_score, 0) AS executive_score
        FROM sessions s
        LEFT JOIN memory_analysis ma ON s.session_id = ma.session_id
        LEFT JOIN attention_analysis aa ON s.session_id = aa.session_id
        LEFT JOIN impulse_analysis ia ON s.session_id = ia.session_id
        LEFT JOIN executive_function_analysis ea ON s.session_id = ea.session_id
        WHERE s.user_id = :user_id
        ORDER BY s.session_date ASC
    """)
    trend_result = await db.execute(trend_query, {"user_id": str(user_id)})
    trend_data = trend_result.fetchall()

    trend_graph = [
        {
            "session_date": row.session_date,
            "overall_score": round(
                (row.memory_score + row.attention_score + row.impulse_score + row.executive_score) / 4, 2
            ),
        }
        for row in trend_data
    ]

    today = datetime.utcnow().date()
    age = (
        today.year
        - patient.date_of_birth.year
        - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
    )
    age_group = get_age_group(age)

    session_stats = await db.execute(
        select(
            func.count(Session.session_id).label("total_sessions"),
            func.min(Session.session_date).label("first_session_date"),
            func.max(Session.session_date).label("last_session_date")
        ).where(Session.user_id == user_id)
    )
    stats = session_stats.first()
    profile = {
        "user_id": user_id,
        "user_name": f"{patient.first_name} {patient.last_name}",
        "age": age,
        "age_group": age_group,
        "gender": patient.gender,
        "total_sessions": stats.total_sessions if stats else 0,
        "first_session_date": stats.first_session_date if stats else None,
        "last_session_date": stats.last_session_date if stats else None,
        "adhd_subtype": patient.adhd_subtype,
        "avg_domain_scores": {
            "memory": avg_memory_score,
            "attention": avg_attention_score,
            "impulse_control": avg_impulse_score,
            "executive_function": avg_executive_score,
        },
        "trend_graph": trend_graph,
    }

    return profile

@router.get("/timeseries/{user_id}")
async def get_cognitive_timeseries(
    user_id: UUID,
    domain: str = Query(..., description="Cognitive domain: attention, memory, impulse_control, executive_function"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    interval: str = Query("1 day", description="Time bucket interval (e.g., '1 day', '1 week')"),
    db: AsyncSession = Depends(get_session)
):
    """Get time series data for cognitive domain scores."""
    if not start_date:
        start_date = datetime.now() - timedelta(days=90)
    if not end_date:
        end_date = datetime.now()
    
    domain_map = {
        "attention": {"table": "attention_analysis", "column": "overall_score"},
        "memory": {"table": "memory_analysis", "column": "overall_memory_score"},
        "impulse_control": {"table": "impulse_analysis", "column": "overall_impulse_control_score"},
        "executive_function": {"table": "executive_function_analysis", "column": "executive_function_score"}
    }
    
    if domain not in domain_map:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    
    table = domain_map[domain]["table"]
    column = domain_map[domain]["column"]

    # امنع SQL Injection عبر التحقق من صيغة الـ interval
    allowed_intervals = {"1 day", "1 week", "1 month", "1 hour"}
    if interval not in allowed_intervals:
        raise HTTPException(status_code=400, detail=f"Invalid interval: {interval}")

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

    result = await db.execute(
        text(query),
        {
            "user_id": str(user_id),
            "start_date": start_date,
            "end_date": end_date,
        }
    )

    data = result.fetchall()
    return [{"date": row.time_bucket, "score": float(row.avg_score)} for row in data]

@router.get("/progress/{user_id}")
async def get_cognitive_progress(
    user_id: UUID,
    domain: str = Query(..., description="Cognitive domain: attention, memory, impulse_control, executive_function"),
    period: str = Query("90d", description="Period for comparison: 30d, 60d, 90d"),
    db: AsyncSession = Depends(get_session)
):
    """Get progress comparison data for a cognitive domain."""
    # Map domain to table and column
    domain_map = {
        "attention": {"table": "attention_analysis", "column": "overall_score"},
        "memory": {"table": "memory_analysis", "column": "overall_memory_score"},
        "impulse_control": {"table": "impulse_analysis", "column": "overall_impulse_control_score"},
        "executive_function": {"table": "executive_function_analysis", "column": "executive_function_score"}
    }
    
    if domain not in domain_map:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    
    table = domain_map[domain]["table"]
    column = domain_map[domain]["column"]
    
    # Map period string to interval
    period_map = {
        "30d": "30 days",
        "60d": "60 days",
        "90d": "90 days"
    }
    interval = period_map.get(period, "90 days")
    
    query = f"""
        WITH first_measurement AS (
            SELECT 
                {column} AS score,
                created_at
            FROM 
                {table}
            WHERE 
                session_id IN (SELECT session_id FROM sessions WHERE user_id = :user_id)
                AND created_at >= NOW() - INTERVAL :interval
            ORDER BY 
                created_at ASC
            LIMIT 1
        ),
        latest_measurement AS (
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
        )
        SELECT 
            f.score AS initial_score,
            l.score AS current_score,
            f.created_at AS initial_date,
            l.created_at AS current_date,
            (l.score - f.score) AS absolute_change,
            CASE 
                WHEN f.score = 0 THEN 0
                ELSE ((l.score - f.score) / f.score) * 100 
            END AS percentage_change
        FROM 
            first_measurement f,
            latest_measurement l
    """
    
    result = await db.execute(
        text(query),
        {
            "user_id": str(user_id),
            "interval": interval
        }
    )
    
    data = result.fetchone()
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No {domain} progress data found for user")
    
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

@router.get("/component-details/{session_id}")
async def get_component_details(
    session_id: UUID,
    domain: str = Query(..., description="Cognitive domain: memory, impulse_control"),
    db: AsyncSession = Depends(get_session)
):
    """Get detailed component scores for a cognitive domain."""
    if domain == "memory":
        result = await db.execute(
            select(MemoryAnalysis)
            .where(MemoryAnalysis.session_id == session_id)
            .order_by(MemoryAnalysis.created_at.desc())
            .limit(1)
        )
        memory = result.scalar_one_or_none()
        
        if not memory:
            raise HTTPException(status_code=404, detail="No memory analysis found for session")
        
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
        result = await db.execute(
            select(ImpulseAnalysis)
            .where(ImpulseAnalysis.session_id == session_id)
            .order_by(ImpulseAnalysis.created_at.desc())
            .limit(1)
        )
        impulse = result.scalar_one_or_none()
        
        if not impulse:
            raise HTTPException(status_code=404, detail="No impulse control analysis found for session")
        
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
    
    else:
        raise HTTPException(status_code=400, detail="Domain must be 'memory' or 'impulse_control'")

@router.get("/normative-comparison/{user_id}")
async def get_normative_comparison(
    user_id: UUID,
    domain: str = Query(..., description="Cognitive domain: attention, memory, impulse_control, executive_function"),
    db: AsyncSession = Depends(get_session)
):
    """Get normative comparison data for a user's cognitive domain."""
    # Map domain to table and column
    domain_map = {
        "attention": {"table": "attention_analysis", "column": "overall_score"},
        "memory": {"table": "memory_analysis", "column": "overall_memory_score"},
        "impulse_control": {"table": "impulse_analysis", "column": "overall_impulse_control_score"},
        "executive_function": {"table": "executive_function_analysis", "column": "executive_function_score"}
    }
    
    if domain not in domain_map:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    
    table = domain_map[domain]["table"]
    column = domain_map[domain]["column"]
    
    # Get patient info for age group
    patient_result = await db.execute(
        select(Patient)
        .where(Patient.user_id == user_id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Calculate age and age group
    today = datetime.utcnow().date()
    age = (
        today.year
        - patient.date_of_birth.year
        - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
    )
    
    age_group = get_age_group(age)
    # Get latest score
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
    
    result = await db.execute(text(query), {"user_id": str(user_id)})
    user_data = result.fetchone()
    
    if not user_data:
        raise HTTPException(status_code=404, detail=f"No {domain} data found for user")
    
    user_score = float(user_data.score)
    
    # Get normative data
    norm_result = await db.execute(
        select(NormativeData)
        .where(
            NormativeData.domain == domain,
            NormativeData.age_group == age_group,
            NormativeData.clinical_group == None
        )
    )
    norm_data = norm_result.scalar_one_or_none()
    
    if not norm_data:
        raise HTTPException(status_code=404, detail=f"No normative data found for {domain} in age group {age_group}")
    
    # Calculate z-score and percentile
    z_score = (user_score - norm_data.mean_score) / norm_data.standard_deviation
    
    # Calculate percentile using error function
    import math
    percentile = 100 * (0.5 * (1 + math.erf(z_score / math.sqrt(2))))
    
    # Get ADHD comparison if available
    adhd_comparison = None
    if patient.adhd_subtype:
        adhd_result = await db.execute(
            select(NormativeData)
            .where(
                NormativeData.domain == domain,
                NormativeData.age_group == age_group,
                NormativeData.clinical_group == "ADHD"
            )
        )
        adhd_data = adhd_result.scalar_one_or_none()
        
        if adhd_data:
            adhd_z_score = (user_score - adhd_data.mean_score) / adhd_data.standard_deviation
            adhd_percentile = 100 * (0.5 * (1 + math.erf(adhd_z_score / math.sqrt(2))))
            
            adhd_comparison = {
                "z_score": round(adhd_z_score, 2),
                "percentile": round(adhd_percentile, 1),
                "reference": adhd_data.reference
            }
    
    return {
        "user_id": user_id,
        "domain": domain,
        "age_group": age_group,
        "raw_score": user_score,
        "normative_comparison": {
            "mean": norm_data.mean_score,
            "standard_deviation": norm_data.standard_deviation,
            "z_score": round(z_score, 2),
            "percentile": round(percentile, 1),
            "reference": norm_data.reference,
            "sample_size": norm_data.sample_size
        },
        "adhd_comparison": adhd_comparison
    }
