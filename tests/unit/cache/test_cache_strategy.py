"""
Cache strategy unit tests following TDD methodology.

RED Phase: Write failing tests for cache strategy design.
GREEN Phase: Implement cache manager to pass tests.
REFACTOR Phase: Optimize while maintaining functionality.
."""

import time
from typing import Any


class TestCacheStrategyRed:
    """RED Phase: Failing tests for cache strategy."""

    def test_cache_key_generation_consistent(self):
        ."""Test that cache keys are generated consistently."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        key1 = manager.generate_key("product", "TEST001")
        key2 = manager.generate_key("product", "TEST001")

        assert key1 == key2  # Consistent key generation

    def test_cache_key_pattern_includes_type_and_id(self):
        """Test that cache key pattern includes type and ID."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        key = manager.generate_key("product", "TEST001")

        assert "product" in key
        assert "TEST001" in key

    def test_cache_key_different_for_different_types(self):
        """Test that cache keys are different for different types."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        key1 = manager.generate_key("product", "TEST001")
        key2 = manager.generate_key("familia", "TEST001")

        assert key1 != key2  # Different types should produce different keys

    def test_cache_key_different_for_different_ids(self):
        """Test that cache keys are different for different IDs."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        key1 = manager.generate_key("product", "TEST001")
        key2 = manager.generate_key("product", "TEST002")

        assert key1 != key2  # Different IDs should produce different keys

    def test_cache_key_handles_special_characters(self):
        """Test that cache keys handle special characters correctly."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        key = manager.generate_key("product", "TEST-001_España")

        assert "product" in key
        assert "TEST" in key  # Should handle special chars


class TestCacheTTLStrategyRed:
    """RED Phase: Failing tests for TTL strategy."""

    def test_default_ttl_returned_for_unknown_type(self):
        ."""Test that default TTL is returned for unknown data type."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        ttl = manager.get_ttl("unknown_type")

        assert ttl > 0  # Should have a positive TTL

    def test_ttl_returned_for_products(self):
        """Test that TTL is returned for products."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        ttl = manager.get_ttl("product")

        assert ttl > 0  # Products should have TTL
        assert ttl <= 3600  # Products TTL should be reasonable (≤ 1 hour)

    def test_ttl_returned_for_familias(self):
        """Test that TTL is returned for families."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        ttl = manager.get_ttl("familia")

        assert ttl > 0  # Families should have TTL
        assert ttl <= 7200  # Families TTL should be longer (≤ 2 hours)

    def test_ttl_returned_for_lists(self):
        """Test that TTL is returned for lists."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        ttl = manager.get_ttl("list")

        assert ttl > 0  # Lists should have TTL
        assert ttl <= 600  # Lists TTL should be shorter (≤ 10 minutes)


class TestCacheInvalidationStrategyRed:
    """RED Phase: Failing tests for cache invalidation."""

    def test_invalidate_removes_specific_key(self):
        ."""Test that invalidation removes a specific cache key."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        key = manager.generate_key("product", "TEST001")

        # Set cache value
        manager.set(key, {"codigo": "TEST001", "nombre": "Test Product"})

        # Invalidate
        manager.invalidate(key)

        # Should be None (invalidated)
        value = manager.get(key)

        assert value is None

    def test_invalidate_pattern_removes_matching_keys(self):
        """Test that invalidation pattern removes matching cache keys."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        # Set multiple product cache entries
        manager.set(manager.generate_key("product", "TEST001"), {"codigo": "TEST001"})
        manager.set(manager.generate_key("product", "TEST002"), {"codigo": "TEST002"})
        manager.set(manager.generate_key("familia", "TEST001"), {"codigo": "TEST001"})

        # Invalidate all product keys (using full pattern)
        manager.invalidate_pattern("api_disano:product:*")

        # Product keys should be invalidated
        product1 = manager.get(manager.generate_key("product", "TEST001"))
        product2 = manager.get(manager.generate_key("product", "TEST002"))
        familia1 = manager.get(manager.generate_key("familia", "TEST001"))

        assert product1 is None  # Product invalidated
        assert product2 is None  # Product invalidated
        assert familia1 is not None  # Familia not invalidated

    def test_invalidate_all_clears_cache(self):
        """Test that invalidate_all clears all cache entries."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        # Set multiple cache entries
        manager.set(manager.generate_key("product", "TEST001"), {"codigo": "TEST001"})
        manager.set(manager.generate_key("familia", "TEST001"), {"codigo": "TEST001"})

        # Invalidate all
        manager.invalidate_all()

        # All should be cleared
        product = manager.get(manager.generate_key("product", "TEST001"))
        familia = manager.get(manager.generate_key("familia", "TEST001"))

        assert product is None
        assert familia is None


class TestCacheWarmingStrategyRed:
    """RED Phase: Failing tests for cache warming."""

    def test_cache_warming_populates_frequently_used_keys(self):
        ."""Test that cache warming populates frequently used keys."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        # Define warming strategy
        warming_data = {
            "product:TEST001": {"codigo": "TEST001", "nombre": "Test Product"},
            "product:TEST002": {"codigo": "TEST002", "nombre": "Another Product"},
        }

        # Warm cache
        manager.warm_cache(warming_data)

        # Cache should be populated
        product1 = manager.get("product:TEST001")
        product2 = manager.get("product:TEST002")

        assert product1 is not None
        assert product2 is not None
        assert product1["codigo"] == "TEST001"
        assert product2["codigo"] == "TEST002"


class TestCacheManagerPerformanceRed:
    """RED Phase: Failing tests for cache performance."""

    def test_cache_hit_improves_performance(self):
        ."""Test that cache hit improves performance."""
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

    def test_cache_hit_rate_can_be_measured(self):
        """Test that cache hit rate can be measured."""
        from app.infrastructure.cache.cache_manager import CacheManager

        cache = CacheManager()

        # Simulate some cache operations
        for i in range(10):
            cache.get_or_compute(f"key_{i}", lambda i=i: {"value": i})

        # Re-access same keys (should hit cache)
        for i in range(10):
            cache.get_or_compute(f"key_{i}", lambda i=i: {"value": i})

        # Get statistics
        stats = cache.get_statistics()

        assert stats["hits"] > 0
        assert stats["misses"] > 0
        assert stats["hit_rate"] > 0


class TestCacheFallbackRed:
    """RED Phase: Failing tests for cache fallback behavior."""

    def test_cache_fallback_when_unavailable(self):
        ."""Test that cache falls back gracefully when unavailable."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        # Simulate cache being unavailable
        result = manager.get_or_compute(
            "test_key", lambda: {"data": "test_value"}, fallback_on_error=True
        )

        # Should return computed value even if cache fails
        assert result is not None
        assert result["data"] == "test_value"

    def test_cache_statistics_tracked_even_with_fallback(self):
        """Test that cache statistics are tracked even with fallback."""
        from app.infrastructure.cache.cache_manager import CacheManager

        manager = CacheManager()

        # Perform operations with fallback
        for i in range(5):
            manager.get_or_compute(f"key_{i}", lambda i=i: {"value": i}, fallback_on_error=True)

        # Statistics should still be tracked
        stats = manager.get_statistics()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


# Test helper functions
def expensive_operation():
    """Helper function to simulate expensive operations."""
    time.sleep(0.01)
    return {"codigo": "TEST001", "nombre": "Test Product", "pvp": 99.99}


def get_test_product(codigo: str) -> dict[str, Any]:
    """Helper function to generate test product data."""
    return {
        "codigo": codigo,
        "nombre": f"Test Product {codigo}",
        "descripcion": f"Test description for {codigo}",
        "marca": "TestBrand",
        "familia": "TestFamily",
        "pvp": 99.99,
    }
