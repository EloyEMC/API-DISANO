"""
Redis cache integration tests following TDD methodology.

RED Phase: Write failing tests for Redis cache integration.
GREEN Phase: Implement cache decorators and integration.
REFACTOR Phase: Optimize cache performance while maintaining functionality.
."""

import time
from unittest.mock import Mock
from typing import Any


class TestRedisCacheIntegrationRed:
    """RED Phase: Failing integration tests for Redis cache."""

    def test_redis_connection_configured(self):
        ."""Test that Redis connection is properly configured."""
        from app.infrastructure.cache.cache_manager import CacheManager

        # Mock Redis client
        mock_redis = Mock()
        mock_redis.ping.return_value = True

        # Create cache manager with Redis
        cache_manager = CacheManager(redis_client=mock_redis)

        assert cache_manager.redis_client is not None
        assert cache_manager.redis_client.ping()

    def test_cache_manager_implements_redis_interface(self):
        ."""Test that cache manager implements Redis-compatible interface."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache_manager = CacheManager()

        # Test all Redis-compatible methods exist
        assert hasattr(cache_manager, "get")
        assert hasattr(cache_manager, "set")
        assert hasattr(cache_manager, "delete")
        assert hasattr(cache_manager, "invalidate")
        assert hasattr(cache_manager, "invalidate_pattern")
        assert hasattr(cache_manager, "invalidate_all")
        assert hasattr(cache_manager, "warm_cache")
        assert hasattr(cache_manager, "get_or_compute")

    def test_cache_fallback_when_redis_unavailable(self):
        """Test that cache falls back to in-memory when Redis unavailable."""
        from app.infrastructure.cache.cache_manager import CacheManager

        # Mock Redis that raises errors
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis unavailable")
        mock_redis.setex.side_effect = Exception("Redis unavailable")

        # Create cache manager with failing Redis
        cache_manager = CacheManager(redis_client=mock_redis)

        # Should still work with in-memory fallback
        cache_manager.set("test_key", {"data": "test"})
        result = cache_manager.get("test_key")

        assert result is not None
        assert result["data"] == "test"

    def test_cache_decorator_applies_to_service_methods(self):
        """Test that cache decorator can be applied to service methods."""
        from app.infrastructure.cache.cache_manager import cache_result

        # Create decorated method
        @cache_result("product:{codigo}", ttl=3600)
        def get_producto_cached(codigo: str) -> dict[str, Any]:
            return {"codigo": codigo, "nombre": "Test Product"}

        # Should execute and cache (using keyword arguments)
        result1 = get_producto_cached(codigo="TEST001")
        result2 = get_producto_cached(codigo="TEST001")

        assert result1 == result2


class TestCacheIntegrationWithServicesRed:
    """RED Phase: Failing integration tests for cache with services."""

    def test_producto_service_uses_cache(self):
        ."""Test that ProductoService can use cache for expensive operations."""
        from app.infrastructure.cache.cache_manager import CacheManager

        # Create cache manager
        cache_manager = CacheManager()

        # Cache should be available for service methods
        assert cache_manager.get_statistics()["total_operations"] == 0

        # Simulate service operation
        result = cache_manager.get_or_compute(
            "producto:TEST001", lambda: {"codigo": "TEST001", "nombre": "Test Product"}
        )

        assert result is not None
        assert result["codigo"] == "TEST001"

    def test_familia_service_uses_cache(self):
        """Test that FamiliaService can use cache for expensive operations."""
        from app.infrastructure.cache.cache_manager import CacheManager

        # Create cache manager
        cache_manager = CacheManager()

        # Cache should be available for service methods
        result = cache_manager.get_or_compute(
            "familia:FAM001", lambda: {"codigo": "FAM001", "nombre": "Test Familia"}
        )

        assert result is not None
        assert result["codigo"] == "FAM001"

    def test_cache_invalidation_on_data_changes(self):
        """Test that cache is invalidated when data changes."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache_manager = CacheManager()

        # Set cache
        cache_manager.set("producto:TEST001", {"codigo": "TEST001", "nombre": "Old Name"})

        # Invalidate on data change
        cache_manager.invalidate("producto:TEST001")

        # Should be None after invalidation
        result = cache_manager.get("producto:TEST001")

        assert result is None


class TestCachePerformanceRed:
    """RED Phase: Failing performance tests for cache."""

    def test_cache_hit_improves_performance(self):
        ."""Test that cache hit significantly improves performance."""
        import time
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        def expensive_operation():
            time.sleep(0.01)  # Simulate expensive operation
            return {"codigo": "TEST001", "nombre": "Test Product"}

        # First call (cache miss)
        start = time.time()
        result1 = cache.get_or_compute("key", expensive_operation)
        miss_time = time.time() - start

        # Second call (cache hit)
        start = time.time()
        result2 = cache.get_or_compute("key", expensive_operation)
        hit_time = time.time() - start

        # Cache hit should be faster
        assert hit_time < miss_time
        # Results should be identical
        assert result1 == result2
        # Performance improvement should be significant
        assert (miss_time / hit_time) > 2.0  # 2x faster

    def test_cache_hit_rate_measured(self):
        """Test that cache hit rate can be measured accurately."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Simulate cache operations
        for i in range(10):
            cache.get_or_compute(f"key_{i}", lambda i=i: {"value": i})

        # Re-access same keys (should hit cache)
        for i in range(10):
            cache.get_or_compute(f"key_{i}", lambda i=i: {"value": i})

        # Get statistics
        stats = cache.get_statistics()

        assert stats["hits"] == 10  # All re-accesses hit
        assert stats["misses"] == 10  # Initial accesses missed
        assert stats["hit_rate"] == 0.5  # 50% hit rate
        assert stats["total_operations"] == 20

    def test_cache_ttl_expires_old_data(self):
        """Test that cache TTL expires old data correctly."""
        import time
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Set cache with short TTL
        cache.set("test_key", {"data": "test"}, ttl=1)  # 1 second TTL

        # Should be available immediately
        result1 = cache.get("test_key")
        assert result1 is not None

        # Wait for TTL to expire
        time.sleep(1.5)

        # Should be expired
        result2 = cache.get("test_key")
        assert result2 is None


class TestCacheStatisticsRed:
    """RED Phase: Failing tests for cache statistics."""

    def test_cache_statistics_track_operations(self):
        ."""Test that cache statistics track all operations correctly."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Perform cache operations
        cache.set("key1", {"data": "test1"})
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit
        cache.invalidate("key1")
        cache.get("key1")  # Miss (after invalidation)

        # Get statistics
        stats = cache.get_statistics()

        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["total_operations"] == 4

    def test_cache_statistics_can_be_reset(self):
        """Test that cache statistics can be reset."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Perform operations
        cache.set("key1", {"data": "test1"})
        cache.get("key1")

        # Reset statistics
        cache.reset_statistics()

        # Get reset statistics
        stats = cache.get_statistics()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total_operations"] == 0


class TestCacheIntegrationWithHTTPRed:
    """RED Phase: Failing integration tests for cache with HTTP layer."""

    def test_http_responses_cached(self):
        ."""Test that HTTP responses can be cached."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Simulate HTTP response
        response_data = {"codigo": "TEST001", "nombre": "Test Product", "pvp": 99.99}

        # Cache response
        cache_key = "http_response:GET:api/productos/v2/TEST001"
        cache.set(cache_key, response_data, ttl=300)  # 5 minutes

        # Retrieve cached response
        cached_response = cache.get(cache_key)

        assert cached_response is not None
        assert cached_response["codigo"] == "TEST001"

    def test_search_results_cached(self):
        """Test that search results can be cached efficiently."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Simulate search results
        search_results = [
            {"codigo": "TEST001", "nombre": "Product 1"},
            {"codigo": "TEST002", "nombre": "Product 2"},
            {"codigo": "TEST003", "nombre": "Product 3"},
        ]

        # Cache search results
        search_key = cache.generate_key("search", "productos", term="test", limit=3)
        cache.set(search_key, search_results, ttl=300)  # 5 minutes

        # Retrieve cached search
        cached_results = cache.get(search_key)

        assert cached_results is not None
        assert len(cached_results) == 3


# Helper functions for testing
def mock_expensive_database_call(codigo: str) -> dict[str, Any]:
    """Mock expensive database call for testing."""
    time.sleep(0.01)  # Simulate database delay
    return {"codigo": codigo, "nombre": f"Product {codigo}", "pvp": 99.99}


def get_cache_hit_rate(cache_manager) -> float:
    """Helper to calculate cache hit rate."""
    stats = cache_manager.get_statistics()
    return stats["hit_rate"]
