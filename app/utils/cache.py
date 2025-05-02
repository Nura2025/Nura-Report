"""
Caching utilities for cognitive API endpoints.
"""
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union
from uuid import UUID
from functools import wraps
import json
import hashlib
from datetime import datetime
import asyncio
from fastapi import Request, Response, Depends
from redis import asyncio as aioredis

# Type variable for generic function return type
T = TypeVar('T')

# Redis client instance
redis: Optional[aioredis.Redis] = None

async def init_redis_pool(redis_url: str = "redis://localhost:6379/0"):
    """
    Initialize Redis connection pool.
    
    Args:
        redis_url: Redis connection URL
    """
    global redis
    if redis is None:
        redis = await aioredis.from_url(redis_url, decode_responses=True)
    return redis

async def get_redis() -> aioredis.Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis client instance
    """
    if redis is None:
        await init_redis_pool()
    return redis

def serialize_value(value: Any) -> str:
    """
    Serialize a value to JSON string.
    
    Args:
        value: Value to serialize
        
    Returns:
        JSON string
    """
    def _serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    
    return json.dumps(value, default=_serialize_datetime)

def deserialize_value(value: str) -> Any:
    """
    Deserialize a JSON string to a value.
    
    Args:
        value: JSON string
        
    Returns:
        Deserialized value
    """
    return json.loads(value)

def build_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Build a cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Convert args and kwargs to strings
    args_str = ":".join(str(arg) for arg in args)
    kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # Combine prefix, args, and kwargs
    key_parts = [prefix]
    if args_str:
        key_parts.append(args_str)
    if kwargs_str:
        key_parts.append(kwargs_str)
    
    # Join parts with colons
    key = ":".join(key_parts)
    
    # If key is too long, hash it
    if len(key) > 100:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        key = f"{prefix}:hash:{key_hash}"
    
    return key

def user_profile_cache_key(func, *args, **kwargs) -> str:
    """
    Build a cache key for user profile data.
    
    Args:
        func: Function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Extract user_id from args or kwargs
    user_id = None
    if args and len(args) > 0:
        user_id = args[0]
    elif 'user_id' in kwargs:
        user_id = kwargs['user_id']
    
    if not user_id:
        return None
    
    return f"user:{user_id}:profile"

def timeseries_cache_key(func, *args, **kwargs) -> str:
    """
    Build a cache key for timeseries data.
    
    Args:
        func: Function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Extract parameters from args or kwargs
    user_id = None
    domain = None
    interval = kwargs.get('interval', '1 day')
    
    if args and len(args) > 0:
        user_id = args[0]
    elif 'user_id' in kwargs:
        user_id = kwargs['user_id']
    
    if len(args) > 1:
        domain = args[1]
    elif 'domain' in kwargs:
        domain = kwargs['domain']
    
    if not user_id or not domain:
        return None
    
    return f"user:{user_id}:timeseries:{domain}:{interval}"

def progress_cache_key(func, *args, **kwargs) -> str:
    """
    Build a cache key for progress data.
    
    Args:
        func: Function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Extract parameters from args or kwargs
    user_id = None
    domain = None
    period = kwargs.get('period', '90d')
    
    if args and len(args) > 0:
        user_id = args[0]
    elif 'user_id' in kwargs:
        user_id = kwargs['user_id']
    
    if len(args) > 1:
        domain = args[1]
    elif 'domain' in kwargs:
        domain = kwargs['domain']
    
    if not user_id or not domain:
        return None
    
    return f"user:{user_id}:progress:{domain}:{period}"

def component_cache_key(func, *args, **kwargs) -> str:
    """
    Build a cache key for component details data.
    
    Args:
        func: Function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Extract parameters from args or kwargs
    session_id = None
    domain = None
    
    if args and len(args) > 0:
        session_id = args[0]
    elif 'session_id' in kwargs:
        session_id = kwargs['session_id']
    
    if len(args) > 1:
        domain = args[1]
    elif 'domain' in kwargs:
        domain = kwargs['domain']
    
    if not session_id or not domain:
        return None
    
    return f"session:{session_id}:component:{domain}"

def session_cache_key(func, *args, **kwargs) -> str:
    """
    Build a cache key for session data.
    
    Args:
        func: Function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Extract parameters from args or kwargs
    user_id = None
    session_id = kwargs.get('session_id')
    
    if args and len(args) > 0:
        user_id = args[0]
    elif 'user_id' in kwargs:
        user_id = kwargs['user_id']
    
    if not user_id:
        return None
    
    if session_id:
        return f"user:{user_id}:session:{session_id}"
    else:
        return f"user:{user_id}:latest_session"

def session_history_cache_key(func, *args, **kwargs) -> str:
    """
    Build a cache key for session history data.
    
    Args:
        func: Function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key
    """
    # Extract parameters from args or kwargs
    user_id = None
    page = kwargs.get('page', 1)
    page_size = kwargs.get('page_size', 10)
    
    if args and len(args) > 0:
        user_id = args[0]
    elif 'user_id' in kwargs:
        user_id = kwargs['user_id']
    
    if not user_id:
        return None
    
    return f"user:{user_id}:sessions:page{page}:size{page_size}"

def cached(expire: int = 300, key_builder: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        expire: Cache expiration time in seconds
        key_builder: Function to build cache key
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get Redis client
            cache = await get_redis()
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(func, *args, **kwargs)
            else:
                cache_key = build_cache_key(func.__name__, *args, **kwargs)
            
            if not cache_key:
                # If no cache key could be built, just call the function
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value:
                return deserialize_value(cached_value)
            
            # Call the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache.set(cache_key, serialize_value(result), ex=expire)
            
            return result
        return wrapper
    return decorator

async def invalidate_cache_for_user(user_id: UUID):
    """
    Invalidate all cached data for a user.
    
    Args:
        user_id: User ID
    """
    cache = await get_redis()
    
    # Get all keys for the user
    pattern = f"user:{user_id}:*"
    keys = await cache.keys(pattern)
    
    if keys:
        # Delete all keys
        await cache.delete(*keys)
    
    return len(keys)

async def invalidate_cache_for_session(session_id: UUID):
    """
    Invalidate all cached data for a session.
    
    Args:
        session_id: Session ID
    """
    cache = await get_redis()
    
    # Get all keys for the session
    pattern = f"session:{session_id}:*"
    keys = await cache.keys(pattern)
    
    if keys:
        # Delete all keys
        await cache.delete(*keys)
    
    return len(keys)

async def warm_cache_for_user(user_id: UUID, repository):
    """
    Warm cache for frequently accessed user data.
    
    Args:
        user_id: User ID
        repository: Repository instance
    """
    # Get profile data
    profile = await repository.get_cognitive_profile(user_id)
    
    # Cache profile data
    if profile:
        cache = await get_redis()
        cache_key = f"user:{user_id}:profile"
        await cache.set(cache_key, serialize_value(profile), ex=300)
    
    return profile is not None
