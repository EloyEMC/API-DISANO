"""Integration tests for cache functionality.

Tests pagination cache wrapper, invalidation strategy, and warming strategy
following TDD principles (RED -> GREEN -> REFACTOR).
."""

from unittest.mock import Mock

from app.infrastructure.cache.pagination_cache import (
    PaginationCacheWrapper,
    get_pagination_cache,
)
from app.infrastructure.cache.cache_invalidation_strategy import (
    CacheInvalidationStrategy,
    get_cache_invalidation_strategy,
)
from app.infrastructure.cache.cache_warming_strategy import (
    CacheWarmingStrategy,
    get_cache_warming_strategy,
)
from app.infrastructure.cache.cache_manager import CacheManager, get_cache_manager


class TestPaginationCacheWrapper:
    """Test pagination cache wrapper functionality."""

    def test_pagination_cache_wrapper_initialization(self):
        """Test that pagination cache wrapper initializes correctly."""
        cache_wrapper = PaginationCacheWrapper()

        assert cache_wrapper.cache_manager is not None
        assert "productos" in cache_wrapper._cache_type_mapping
        assert "familias" in cache_wrapper._cache_type_mapping
        assert "bc3" in cache_wrapper._cache_type_mapping

    def test_get_pagination_cache_singleton(self):
        """Test that get_pagination_cache returns singleton instance."""
        cache1 = get_pagination_cache()
        cache2 = get_pagination_cache()

        assert cache1 is cache2
        assert isinstance(cache1, PaginationCacheWrapper)

    def test_generate_cache_key_consistency(self):
        """Test that cache keys are generated consistently."""
        cache_wrapper = PaginationCacheWrapper()

        # Same parameters should produce same key
        key1 = cache_wrapper._generate_cache_key(
            "productos", 1, 10, "codigo:asc", {"marca": "SIEMENS"}
        )
        key2 = cache_wrapper._generate_cache_key(
            "productos", 1, 10, "codigo:asc", {"marca": "SIEMENS"}
        )

        assert key1 == key2

    def test_generate_cache_key_different_parameters(self):
        """Test that different parameters produce different keys."""
        cache_wrapper = PaginationCacheWrapper()

        # Different page should produce different key
        key1 = cache_wrapper._generate_cache_key("productos", 1, 10, None, {})
        key2 = cache_wrapper._generate_cache_key("productos", 2, 10, None, {})

        assert key1 != key2

    def test_cache_get_set_productos(self):
        """Test caching and retrieving product pagination results."""
        cache_wrapper = PaginationCacheWrapper()

        # Set a result
        test_result = {
            "entities": [{"codigo": "P1", "descripcion": "Test Product"}],
            "total": 1,
        }

        success = cache_wrapper.set("productos", 1, 10, None, {}, test_result)
        assert success is True

        # Get the result back
        cached = cache_wrapper.get("productos", 1, 10, None, {})
        assert cached is not None
        assert cached["entities"][0]["codigo"] == "P1"
        assert cached["total"] == 1

    def test_cache_get_set_familias(self):
        """Test caching and retrieving family pagination results."""
        cache_wrapper = PaginationCacheWrapper()

        # Set a result
        test_result = {
            "entities": [{"nombre": "Test Family", "total_productos": 10}],
            "total": 1,
        }

        success = cache_wrapper.set("familias", 1, 10, None, {}, test_result)
        assert success is True

        # Get the result back
        cached = cache_wrapper.get("familias", 1, 10, None, {})
        assert cached is not None
        assert cached["entities"][0]["nombre"] == "Test Family"
        assert cached["total"] == 1

    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        cache_wrapper = PaginationCacheWrapper()

        # Try to get non-existent entry
        cached = cache_wrapper.get("productos", 999, 999, None, {})
        assert cached is None

    def test_cache_with_filters(self):
        """Test caching with different filter combinations."""
        cache_wrapper = PaginationCacheWrapper()

        # Set results with different filters
        result1 = {"entities": [{"codigo": "P1"}], "total": 1}
        result2 = {"entities": [{"codigo": "P2"}], "total": 1}

        cache_wrapper.set("productos", 1, 10, None, {"marca": "SIEMENS"}, result1)
        cache_wrapper.set("productos", 1, 10, None, {"marca": "BOSCH"}, result2)

        # Retrieve with specific filters
        cached1 = cache_wrapper.get("productos", 1, 10, None, {"marca": "SIEMENS"})
        cached2 = cache_wrapper.get("productos", 1, 10, None, {"marca": "BOSCH"})

        assert cached1["entities"][0]["codigo"] == "P1"
        assert cached2["entities"][0]["codigo"] == "P2"

    def test_cache_with_sorting(self):
        """Test caching with different sort criteria."""
        cache_wrapper = PaginationCacheWrapper()

        # Set results with different sorting
        result_asc = {"entities": [{"codigo": "P1"}], "total": 1}
        result_desc = {"entities": [{"codigo": "P2"}], "total": 1}

        cache_wrapper.set("productos", 1, 10, "pvp:asc", {}, result_asc)
        cache_wrapper.set("productos", 1, 10, "pvp:desc", {}, result_desc)

        # Retrieve with specific sorting
        cached_asc = cache_wrapper.get("productos", 1, 10, "pvp:asc", {})
        cached_desc = cache_wrapper.get("productos", 1, 10, "pvp:desc", {})

        assert cached_asc["entities"][0]["codigo"] == "P1"
        assert cached_desc["entities"][0]["codigo"] == "P2"

    def test_get_or_compute_cache_hit(self):
        """Test get_or_compute with cache hit."""
        cache_wrapper = PaginationCacheWrapper()

        # Set cached result
        test_result = {"entities": [], "total": 0}
        cache_wrapper.set("productos", 1, 10, None, {}, test_result)

        # get_or_compute should return cached result without calling compute_fn
        compute_fn = Mock(return_value={"entities": [], "total": 1})
        result = cache_wrapper.get_or_compute("productos", 1, 10, None, {}, compute_fn)

        assert result["total"] == 0  # Should return cached result
        compute_fn.assert_not_called()

    def test_get_or_compute_cache_miss(self):
        """Test get_or_compute with cache miss."""
        cache_wrapper = PaginationCacheWrapper()

        # No cached result
        test_result = {"entities": [], "total": 1}
        compute_fn = Mock(return_value=test_result)

        result = cache_wrapper.get_or_compute("productos", 1, 10, None, {}, compute_fn)

        assert result["total"] == 1  # Should return computed result
        compute_fn.assert_called_once()

        # Verify it was cached
        cached = cache_wrapper.get("productos", 1, 10, None, {})
        assert cached["total"] == 1

    def test_invalidate_entity(self):
        """Test invalidating all cache entries for an entity type."""
        cache_wrapper = PaginationCacheWrapper()

        # Set multiple entries for productos
        cache_wrapper.set("productos", 1, 10, None, {}, {"entities": [], "total": 1})
        cache_wrapper.set("productos", 2, 10, None, {}, {"entities": [], "total": 1})

        # Invalidate productos
        cache_wrapper.invalidate_entity("productos")

        # Verify cache is cleared
        cached1 = cache_wrapper.get("productos", 1, 10, None, {})
        cached2 = cache_wrapper.get("productos", 2, 10, None, {})

        assert cached1 is None
        assert cached2 is None

    def test_get_pagination_statistics(self):
        """Test getting pagination cache statistics."""
        cache_wrapper = PaginationCacheWrapper()

        # Set some cache entries
        cache_wrapper.set("productos", 1, 10, None, {}, {"entities": [], "total": 1})

        # Get statistics
        stats = cache_wrapper.get_pagination_statistics()

        assert "hits" in stats
        assert "misses" in stats
        assert "total_operations" in stats
        assert "hit_rate" in stats
        assert "cache_type_mapping" in stats


class TestCacheInvalidationStrategy:
    """Test cache invalidation strategy functionality."""

    def test_invalidation_strategy_initialization(self):
        """Test that invalidation strategy initializes correctly."""
        strategy = CacheInvalidationStrategy()

        assert strategy.pagination_cache is not None
        assert strategy.cache_manager is not None

    def test_get_cache_invalidation_strategy_singleton(self):
        """Test that get_cache_invalidation_strategy returns singleton instance."""
        strategy1 = get_cache_invalidation_strategy()
        strategy2 = get_cache_invalidation_strategy()

        assert strategy1 is strategy2
        assert isinstance(strategy1, CacheInvalidationStrategy)

    def test_invalidate_on_product_change(self):
        """Test cache invalidation on product change."""
        strategy = CacheInvalidationStrategy()

        # Set up cache with product data
        test_result = {"entities": [{"codigo": "P1"}], "total": 1}
        strategy.pagination_cache.set("productos", 1, 10, None, {}, test_result)

        # Invalidate on product change
        result = strategy.invalidate_on_product_change("P1", marca="SIEMENS")

        assert result["status"] == "success"
        assert result["product_code"] == "P1"

    def test_invalidate_on_familia_change(self):
        """Test cache invalidation on family change."""
        strategy = CacheInvalidationStrategy()

        # Set up cache with family data
        test_result = {"entities": [{"nombre": "Test Family"}], "total": 1}
        strategy.pagination_cache.set("familias", 1, 10, None, {}, test_result)

        # Invalidate on family change
        result = strategy.invalidate_on_familia_change("Test Family")

        assert result["status"] == "success"
        assert result["familia_name"] == "Test Family"

    def test_smart_invalidate_product_change(self):
        """Test smart invalidation for product change event."""
        strategy = CacheInvalidationStrategy()

        result = strategy.smart_invalidate(
            "product_change", product_code="P1", marca="SIEMENS", familia="Kitchen"
        )

        assert result["status"] == "success"
        assert result["product_code"] == "P1"

    def test_smart_invalidate_familia_change(self):
        """Test smart invalidation for family change event."""
        strategy = CacheInvalidationStrategy()

        result = strategy.smart_invalidate("familia_change", familia_name="Kitchen")

        assert result["status"] == "success"
        assert result["familia_name"] == "Kitchen"

    def test_smart_invalidate_unknown_event_type(self):
        """Test smart invalidation with unknown event type."""
        strategy = CacheInvalidationStrategy()

        result = strategy.smart_invalidate("unknown_event")

        assert result["status"] == "error"
        assert "Unknown event type" in result["message"]

    def test_batch_invalidate(self):
        """Test batch invalidation of multiple events."""
        strategy = CacheInvalidationStrategy()

        events = [
            {"event_type": "product_change", "product_code": "P1"},
            {"event_type": "familia_change", "familia_name": "Test Family"},
        ]

        results = strategy.batch_invalidate(events)

        assert len(results) == 2
        assert all(result["status"] == "success" for result in results)

    def test_get_invalidation_stats(self):
        """Test getting invalidation statistics."""
        strategy = CacheInvalidationStrategy()

        stats = strategy.get_invalidation_stats()

        assert "pagination_stats" in stats
        assert "general_stats" in stats


class TestCacheWarmingStrategy:
    """Test cache warming strategy functionality."""

    def test_warming_strategy_initialization(self):
        """Test that warming strategy initializes correctly."""
        warming_strategy = CacheWarmingStrategy()

        assert warming_strategy.pagination_cache is not None

    def test_get_cache_warming_strategy_singleton(self):
        """Test that get_cache_warming_strategy returns singleton instance."""
        strategy1 = get_cache_warming_strategy()
        strategy2 = get_cache_warming_strategy()

        assert strategy1 is strategy2
        assert isinstance(strategy1, CacheWarmingStrategy)

    def test_warm_popular_product_pages(self):
        """Test warming popular product pages."""
        warming_strategy = CacheWarmingStrategy()

        result = warming_strategy.warm_popular_product_pages()

        assert result["status"] == "success"
        assert "per_page_values" in result
        assert result["warmed_queries"] >= 0

    def test_warm_popular_familia_pages(self):
        """Test warming popular family pages."""
        warming_strategy = CacheWarmingStrategy()

        result = warming_strategy.warm_popular_familia_pages()

        assert result["status"] == "success"
        assert "per_page_values" in result

    def test_warm_popular_filters(self):
        """Test warming popular filter combinations."""
        warming_strategy = CacheWarmingStrategy()

        filter_configs = [
            {"sort": "pvp:asc", "filters": {"marca": "SIEMENS"}},
            {"sort": "pvp:desc", "filters": {"marca": "BOSCH"}},
        ]

        result = warming_strategy.warm_popular_filters("productos", filter_configs)

        assert result["status"] == "success"
        assert result["entity_type"] == "productos"

    def test_warm_top_brands(self):
        """Test warming top brands cache."""
        warming_strategy = CacheWarmingStrategy()

        result = warming_strategy.warm_top_brands()

        assert result["status"] == "success"
        assert "top_brands" in result
        assert len(result["top_brands"]) > 0

    def test_warm_price_ranges(self):
        """Test warming price ranges cache."""
        warming_strategy = CacheWarmingStrategy()

        result = warming_strategy.warm_price_ranges()

        assert result["status"] == "success"
        assert "price_ranges" in result

    def test_warm_bc3_filters(self):
        """Test warming BC3 filters cache."""
        warming_strategy = CacheWarmingStrategy()

        result = warming_strategy.warm_bc3_filters()

        assert result["status"] == "success"
        assert result["warmed_bc3_filters"] >= 0

    def test_warm_all_strategies(self):
        """Test warming all cache strategies."""
        warming_strategy = CacheWarmingStrategy()

        result = warming_strategy.warm_all_strategies()

        assert "product_pages" in result
        assert "familia_pages" in result
        assert "top_brands" in result
        assert "price_ranges" in result
        assert "bc3_filters" in result
        assert "total_warmed" in result
        assert "overall_status" in result

    def test_get_warming_recommendations(self):
        """Test getting warming recommendations."""
        warming_strategy = CacheWarmingStrategy()

        recommendations = warming_strategy.get_warming_recommendations()

        assert "current_stats" in recommendations
        assert "recommendations" in recommendations
        assert "priority" in recommendations


class TestCacheManagerIntegration:
    """Test CacheManager integration with pagination cache."""

    def test_cache_manager_basic_operations(self):
        """Test basic cache manager operations."""
        cache_manager = CacheManager()

        # Test set and get
        test_key = "test_key"
        test_value = {"data": "test_value"}

        cache_manager.set(test_key, test_value)
        retrieved = cache_manager.get(test_key)

        assert retrieved is not None
        assert retrieved["data"] == "test_value"

    def test_cache_manager_statistics(self):
        """Test cache manager statistics tracking."""
        cache_manager = CacheManager()

        # Set some values
        cache_manager.set("key1", {"value": 1})
        cache_manager.set("key2", {"value": 2})

        # Get some values (cache hits)
        cache_manager.get("key1")
        cache_manager.get("key2")

        # Try to get non-existent value (cache miss)
        cache_manager.get("non_existent")

        stats = cache_manager.get_statistics()

        assert stats["hits"] >= 2
        assert stats["misses"] >= 1
        assert stats["total_operations"] >= 3

    def test_cache_manager_delete(self):
        """Test cache manager delete operation."""
        cache_manager = CacheManager()

        test_key = "test_delete_key"
        test_value = {"data": "to_delete"}

        cache_manager.set(test_key, test_value)
        assert cache_manager.get(test_key) is not None

        cache_manager.delete(test_key)
        assert cache_manager.get(test_key) is None

    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns singleton instance."""
        cache1 = get_cache_manager()
        cache2 = get_cache_manager()

        assert cache1 is cache2
        assert isinstance(cache1, CacheManager)
