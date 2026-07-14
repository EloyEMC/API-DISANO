"""
Cache Manager Implementation for API-DISANO.

This module provides a Redis-compatible cache manager with in-memory fallback,
following hexagonal architecture principles. The cache manager supports:

- Consistent cache key generation
- TTL strategy per data type
- Cache invalidation (key, pattern, all)
- Cache warming for frequently accessed data
- Performance tracking and statistics
- Fallback mechanism when cache unavailable

TDD Approach: GREEN Phase - Implementation to pass failing tests.
."""

import time
import json
from typing import Any, Optional, Callable, Dict
from functools import wraps
from threading import Lock


class CacheManager:
    """
    Cache manager with Redis-compatible interface and in-memory fallback.

    Provides consistent cache key generation, TTL strategy, invalidation,
    warming, and performance tracking. Falls back to in-memory cache when
    Redis is unavailable.
    ."""

    # TTL Strategy: Time to live in seconds per data type
    TTL_STRATEGY = {
        "product": 3600,  # 1 hour for products
        "familia": 7200,  # 2 hours for families
        "list": 600,  # 10 minutes for lists
        "search": 300,  # 5 minutes for searches
        "stats": 60,  # 1 minute for statistics
        "default": 1800,  # 30 minutes default
    }

    def __init__(self, redis_client=None, use_memory_cache: bool = True):
        """
        Initialize cache manager.

        Args:
            redis_client: Optional Redis client (falls back to in-memory)
            use_memory_cache: Whether to use in-memory cache as fallback
        ."""
        self.redis_client = redis_client
        self.use_memory_cache = use_memory_cache
        self.memory_cache: Dict[str, tuple] = {}  # {key: (value, expiry)}
        self.cache_lock = Lock()

        # Statistics tracking
        self.stats = {"hits": 0, "misses": 0, "errors": 0, "total_operations": 0}

    def generate_key(self, cache_type: str, identifier: str, **kwargs) -> str:
        """
        Generate consistent cache key with type, identifier, and optional params.

        Args:
            cache_type: Type of cached data (product, familia, list, etc.)
            identifier: Unique identifier (codigo, ID, etc.)
            **kwargs: Additional parameters for cache key

        Returns:
            Consistent cache key string
        ."""
        # Base key with type and identifier
        key_parts = [cache_type, identifier]

        # Add any additional parameters
        if kwargs:
            # Sort kwargs for consistency
            sorted_params = sorted(kwargs.items())
            for param_name, param_value in sorted_params:
                key_parts.append(f"{param_name}={param_value}")

        # Create consistent key string
        key_string = ":".join(str(part) for part in key_parts)

        # Hash special characters for safety
        safe_key = self._safe_key(key_string)

        return f"api_disano:{safe_key}"

    def _safe_key(self, key_string: str) -> str:
        """
        Create safe cache key from potentially unsafe strings.

        Args:
            key_string: Raw key string that may contain special characters

        Returns:
            Safe cache key string
        ."""
        # Replace special characters with underscores
        safe = key_string.replace("/", "_").replace(" ", "_").replace("-", "_")
        return safe

    def get_ttl(self, cache_type: str) -> int:
        """
        Get TTL for specific cache type.

        Args:
            cache_type: Type of cached data

        Returns:
            TTL in seconds
        ."""
        return self.TTL_STRATEGY.get(cache_type, self.TTL_STRATEGY["default"])

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (tries Redis first, falls back to memory).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        ."""
        self.stats["total_operations"] += 1

        try:
            # Try Redis first if available
            if self.redis_client:
                try:
                    value = self.redis_client.get(key)
                    if value is not None:
                        self.stats["hits"] += 1
                        return json.loads(value)
                except Exception:
                    self.stats["errors"] += 1
                    # Fall through to memory cache

            # Fallback to memory cache
            if self.use_memory_cache:
                with self.cache_lock:
                    if key in self.memory_cache:
                        value, expiry = self.memory_cache[key]
                        # Check if expired
                        if expiry > time.time():
                            self.stats["hits"] += 1
                            return value
                        else:
                            # Remove expired entry
                            del self.memory_cache[key]

            self.stats["misses"] += 1
            return None

        except Exception:
            self.stats["errors"] += 1
            self.stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL (tries Redis first, falls back to memory).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds (uses default if not specified)

        Returns:
            True if successful, False otherwise
        ."""
        try:
            # Try Redis first if available
            if self.redis_client:
                try:
                    self.redis_client.setex(key, ttl or self.get_ttl("default"), json.dumps(value))
                    return True
                except Exception:
                    # Fall through to memory cache
                    pass

            # Fallback to memory cache
            if self.use_memory_cache:
                with self.cache_lock:
                    expiry = time.time() + (ttl or self.get_ttl("default"))
                    self.memory_cache[key] = (value, expiry)
                    return True

            return False

        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        Delete specific key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        try:
            deleted = False

            # Try Redis first if available
            if self.redis_client:
                try:
                    result = self.redis_client.delete(key)
                    deleted = result > 0
                except Exception:
                    pass

            # Also delete from memory cache
            if self.use_memory_cache:
                with self.cache_lock:
                    if key in self.memory_cache:
                        del self.memory_cache[key]
                        deleted = True

            return deleted

        except Exception:
            return False

    def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache key (alias for delete).

        Args:
            key: Cache key to invalidate

        Returns:
            True if invalidated, False if key didn't exist
        """
        return self.delete(key)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching pattern.

        Args:
            pattern: Glob pattern (e.g., "product:*")

        Returns:
            Number of keys invalidated
        """
        count = 0

        try:
            # Try Redis first if available
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        count = self.redis_client.delete(*keys)
                except Exception:
                    pass

            # Also invalidate from memory cache
            if self.use_memory_cache:
                with self.cache_lock:
                    keys_to_delete = []
                    pattern_regex = pattern.replace("*", ".*")

                    for key in list(self.memory_cache.keys()):
                        import re

                        if re.match(pattern_regex, key):
                            keys_to_delete.append(key)

                    for key in keys_to_delete:
                        del self.memory_cache[key]
                        count += 1

            return count

        except Exception:
            return count

    def invalidate_all(self) -> bool:
        """
        Invalidate all cache entries.

        Returns:
            True if successful
        """
        try:
            # Try Redis first if available
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception:
                    pass

            # Clear memory cache
            if self.use_memory_cache:
                with self.cache_lock:
                    self.memory_cache.clear()

            return True

        except Exception:
            return False

    def warm_cache(self, warming_data: Dict[str, Any]) -> int:
        """
        Warm cache with frequently accessed data.

        Args:
            warming_data: Dictionary of {cache_key: value} to prepopulate

        Returns:
            Number of entries warmed
        """
        warmed = 0

        try:
            for key, value in warming_data.items():
                if self.set(key, value):
                    warmed += 1

            return warmed

        except Exception:
            return warmed

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: Optional[int] = None,
        fallback_on_error: bool = True,
    ) -> Optional[Any]:
        """
        Get value from cache or compute and cache it.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl: Optional TTL for computed value
            fallback_on_error: Whether to return computed value on cache error

        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value

        # Cache miss - compute value
        try:
            computed_value = compute_fn()
            if computed_value is not None:
                # Cache the computed value
                self.set(key, computed_value, ttl)
            return computed_value

        except Exception:
            if fallback_on_error:
                # Return None or computed value despite cache error
                return None
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        ."""
        total_ops = self.stats["total_operations"]
        hit_rate = self.stats["hits"] / total_ops if total_ops > 0 else 0.0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "total_operations": total_ops,
            "hit_rate": hit_rate,
            "memory_cache_size": len(self.memory_cache),
        }

    def reset_statistics(self) -> None:
        """Reset cache statistics counters."""
        self.stats = {"hits": 0, "misses": 0, "errors": 0, "total_operations": 0}


def cache_result(cache_key_pattern: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results.

    Args:
        cache_key_pattern: Cache key pattern with {param} placeholders
        ttl: Optional TTL for cached results

    Returns:
        Decorated function with caching

    Example:
        @cache_result("product:{codigo}", ttl=3600)
        def get_producto(codigo: str):
            # Database query here
            return product_data
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache manager
            cache_manager = CacheManager()

            # Generate cache key
            cache_key = cache_key_pattern.format(**kwargs)

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Compute result
            result = func(*args, **kwargs)

            # Cache result
            if result is not None:
                cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Singleton instance for application-wide cache
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get global cache manager instance.

    Returns:
        Global cache manager instance
    """
    global _global_cache_manager

    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()

    return _global_cache_manager
