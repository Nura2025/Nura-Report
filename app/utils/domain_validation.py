"""
Domain validation utilities for cognitive API endpoints.
"""
from fastapi import HTTPException
from typing import Set, Dict, Any, Optional
from uuid import UUID

# Valid cognitive domains for different endpoint types
VALID_DOMAINS = {
    "general": {"attention", "memory", "impulse_control", "executive_function"},
    "component_details": {"memory", "impulse_control"}
}

# Valid time periods for different endpoint types
VALID_PERIODS = {
    "progress": {"30d", "60d", "90d"},
    "comparison": {"all", "30d", "60d", "90d", "6m", "1y"}
}

# Valid time intervals for timeseries data
VALID_INTERVALS = {"1 day", "1 week", "1 month", "1 hour"}

# Domain to table and column mapping
DOMAIN_MAP = {
    "attention": {
        "table": "attention_analysis", 
        "column": "overall_score", 
        "agg_view": "daily_attention_scores"
    },
    "memory": {
        "table": "memory_analysis", 
        "column": "overall_memory_score", 
        "agg_view": "daily_memory_scores"
    },
    "impulse_control": {
        "table": "impulse_analysis", 
        "column": "overall_impulse_control_score", 
        "agg_view": "daily_impulse_scores"
    },
    "executive_function": {
        "table": "executive_function_analysis", 
        "column": "executive_function_score", 
        "agg_view": "daily_executive_scores"
    }
}

def validate_domain(domain: str, domain_type: str = "general") -> str:
    """
    Validate a cognitive domain.
    
    Args:
        domain: Cognitive domain to validate
        domain_type: Type of domain validation to perform
        
    Returns:
        The validated domain
        
    Raises:
        HTTPException: If domain is invalid
    """
    valid_domains = VALID_DOMAINS.get(domain_type, VALID_DOMAINS["general"])
    
    if domain not in valid_domains:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid domain: {domain}. Must be one of {valid_domains}"
        )
    
    return domain

def validate_period(period: str, period_type: str = "progress") -> str:
    """
    Validate a time period.
    
    Args:
        period: Time period to validate
        period_type: Type of period validation to perform
        
    Returns:
        The validated period
        
    Raises:
        HTTPException: If period is invalid
    """
    valid_periods = VALID_PERIODS.get(period_type, VALID_PERIODS["progress"])
    
    if period not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid period: {period}. Must be one of {valid_periods}"
        )
    
    return period

def validate_interval(interval: str) -> str:
    """
    Validate a time interval.
    
    Args:
        interval: Time interval to validate
        
    Returns:
        The validated interval
        
    Raises:
        HTTPException: If interval is invalid
    """
    if interval not in VALID_INTERVALS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid interval: {interval}. Must be one of {VALID_INTERVALS}"
        )
    
    return interval

def get_domain_info(domain: str) -> Dict[str, str]:
    """
    Get database information for a cognitive domain.
    
    Args:
        domain: Cognitive domain
        
    Returns:
        Dictionary with table, column, and aggregate view information
        
    Raises:
        HTTPException: If domain is invalid
    """
    # Validate domain first
    validate_domain(domain)
    
    return DOMAIN_MAP[domain]

def format_pagination_response(data: Any, page: int, page_size: int, total_items: Optional[int] = None) -> Dict[str, Any]:
    """
    Format a paginated response.
    
    Args:
        data: Data to include in the response
        page: Current page number
        page_size: Items per page
        total_items: Total number of items (if known)
        
    Returns:
        Dictionary with data and pagination metadata
    """
    # If total_items is not provided, calculate it from data length
    if total_items is None and hasattr(data, "__len__"):
        total_items = len(data)
    
    # Calculate total pages
    total_pages = (total_items + page_size - 1) // page_size if total_items is not None else None
    
    # Apply pagination if data is a list
    if isinstance(data, list):
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_data = data[start_idx:end_idx]
    else:
        paginated_data = data
    
    return {
        "data": paginated_data,
        "pagination": {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size
        }
    }
