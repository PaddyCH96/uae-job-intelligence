"""Redis-based caching manager for API responses and database queries."""

from __future__ import annotations

import json
import hashlib
import time
from typing import Any, Callable, Optional, TypeVar, Generic, Tuple
from datetime import timedelta
from functools import wraps

import redis
from redis.exceptions import ConnectionError, TimeoutError as RedisTimeoutError

from src.utils.logger import logger

T = TypeVar('T')

# Cache TTLs (in seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour
CACHE_TTL_AGGRESSIVE = 7200  # 2 hours


class CacheManager(Generic[T]):
    """Manages caching with Redis backend, with graceful fallback."""

    def __init__(self, redis_url: str = "redis://localhost:6379/1", namespace: str = "uae_jobs"):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL
            namespace: Key namespace prefix
        """
        self.namespace = namespace
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self.is_healthy = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Redis client with health check."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            self.client.ping()
            self.is_healthy = True
            logger.info("cache_manager_initialized", namespace=self.namespace)
        except (ConnectionError, RedisTimeoutError, Exception) as e:
            logger.warning(f"cache_manager_unavailable: {str(e)}")
            self.client = None
            self.is_healthy = False

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        # Create deterministic hash from args/kwargs
        key_parts = [prefix] + [str(arg) for arg in args]
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True, default=str))
        
        key_hash = hashlib.md5("|".join(key_parts).encode()).hexdigest()
        return f"{self.namespace}:{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.is_healthy or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug("cache_hit", key=key)
                return json.loads(value)
            logger.debug("cache_miss", key=key)
            return None
        except Exception as e:
            logger.warning(f"cache_get_error: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: int = CACHE_TTL_MEDIUM) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.is_healthy or not self.client:
            return False

        try:
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            logger.debug("cache_set", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"cache_set_error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.is_healthy or not self.client:
            return False

        try:
            self.client.delete(key)
            logger.debug("cache_delete", key=key)
            return True
        except Exception as e:
            logger.warning(f"cache_delete_error: {str(e)}")
            return False

    def clear_prefix(self, prefix: str) -> int:
        """
        Clear all keys matching prefix.

        Args:
            prefix: Key prefix pattern

        Returns:
            Number of keys deleted
        """
        if not self.is_healthy or not self.client:
            return 0

        try:
            pattern = f"{self.namespace}:{prefix}:*"
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info("cache_prefix_cleared", prefix=prefix, count=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"cache_clear_prefix_error: {str(e)}")
            return 0

    def invalidate_sliding_window(self, key: str, window_size: int = 60) -> Tuple[int, int]:
        """
        Implement sliding window counter for rate limiting.

        Args:
            key: Counter key
            window_size: Window size in seconds

        Returns:
            Tuple of (current_count, ttl_remaining)
        """
        if not self.is_healthy or not self.client:
            return (0, 0)

        try:
            pipe = self.client.pipeline()
            now = int(time.time())
            min_time = now - window_size

            # Remove old entries
            pipe.zremrangebyscore(key, 0, min_time)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Get count
            pipe.zcount(key, min_time, now)
            # Set expiry
            pipe.expire(key, window_size)

            results = pipe.execute()
            count = results[2]
            ttl = self.client.ttl(key)

            return (count, ttl)
        except Exception as e:
            logger.warning(f"sliding_window_error: {str(e)}")
            return (0, 0)

    def get_health(self) -> dict:
        """Get cache health status."""
        if not self.client:
            return {
                "status": "unavailable",
                "connected": False,
                "namespace": self.namespace
            }

        try:
            info = self.client.info("server")
            return {
                "status": "healthy" if self.is_healthy else "degraded",
                "connected": True,
                "namespace": self.namespace,
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "namespace": self.namespace
            }


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance


def cached(prefix: str, ttl: int = CACHE_TTL_MEDIUM):
    """
    Decorator for caching function results.

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds

    Example:
        @cached("user_profile", ttl=CACHE_TTL_LONG)
        def get_user_profile(user_id: str) -> dict:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache_manager()
            key = cache._make_key(prefix, *args, **kwargs)

            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"cache_hit_for_{func.__name__}", key=key)
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(key, result, ttl=ttl)
            return result

        return wrapper
    return decorator


def invalidate_cache(prefix: str):
    """
    Decorator to invalidate cache after function execution.

    Args:
        prefix: Cache key prefix to invalidate

    Example:
        @invalidate_cache("user_profile")
        def update_user_profile(user_id: str, data: dict):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = func(*args, **kwargs)
            cache = get_cache_manager()
            cache.clear_prefix(prefix)
            logger.info(f"cache_invalidated_after_{func.__name__}", prefix=prefix)
            return result

        return wrapper
    return decorator
