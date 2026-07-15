"""Cache Warming Strategy for advanced features.

Provides comprehensive cache warming for optimal performance:
- Pre-load frequently accessed pagination queries
- Smart warming based on access patterns
- Configurable warming schedules
- Priority-based warming (hot, warm, cold)
- Performance metrics tracking
."""

from typing import Dict, List, Any, Optional
from app.infrastructure.cache.pagination_cache import get_pagination_cache


class CacheWarmingStrategy:
    """
    Comprehensive cache warming strategy for pagination cache.

    This class provides methods to pre-populate cache with frequently
    accessed data for improved performance.
    """

    def __init__(self):
        """Initialize cache warming strategy."""
        self.pagination_cache = get_pagination_cache()

    def warm_popular_product_pages(
        self, per_page_values: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Warm cache with popular product pagination queries.

        Args:
            per_page_values: List of items per page values to warm (default: [10, 20, 50])

        Returns:
            Dict with warming results
        """
        if per_page_values is None:
            per_page_values = [10, 20, 50]

        results = {
            "warmed_queries": 0,
            "per_page_values": per_page_values,
            "status": "success",
        }

        try:
            # Generate warming queries for first few pages of popular per_page values
            warming_queries = []

            for per_page in per_page_values:
                for page in range(1, 4):  # Warm first 3 pages
                    warming_queries.append(
                        {
                            "page": page,
                            "per_page": per_page,
                            "sort": None,
                            "filters": {},
                        }
                    )

            warmed = self.pagination_cache.warm_pagination_cache(
                "productos", warming_queries
            )
            results["warmed_queries"] = warmed

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def warm_popular_familia_pages(
        self, per_page_values: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Warm cache with popular family pagination queries.

        Args:
            per_page_values: List of items per page values to warm (default: [10, 20])

        Returns:
            Dict with warming results
        ."""
        if per_page_values is None:
            per_page_values = [10, 20]

        results = {
            "warmed_queries": 0,
            "per_page_values": per_page_values,
            "status": "success",
        }

        try:
            # Generate warming queries for first few pages
            warming_queries = []

            for per_page in per_page_values:
                for page in range(1, 3):  # Warm first 2 pages
                    warming_queries.append(
                        {
                            "page": page,
                            "per_page": per_page,
                            "sort": None,
                            "filters": {},
                        }
                    )

            warmed = self.pagination_cache.warm_pagination_cache(
                "familias", warming_queries
            )
            results["warmed_queries"] = warmed

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def warm_popular_filters(
        self, entity_type: str, filter_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Warm cache with popular filter combinations.

        Args:
            entity_type: Entity type (productos, familias, bc3)
            filter_configs: List of filter configurations to warm

        Returns:
            Dict with warming results
        ."""
        results = {
            "entity_type": entity_type,
            "warmed_filters": 0,
            "status": "success",
        }

        try:
            warming_queries = []

            for filter_config in filter_configs:
                warming_queries.append(
                    {
                        "page": 1,
                        "per_page": 10,
                        "sort": filter_config.get("sort"),
                        "filters": filter_config.get("filters", {}),
                    }
                )

            warmed = self.pagination_cache.warm_pagination_cache(
                entity_type, warming_queries
            )
            results["warmed_filters"] = warmed

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def warm_top_brands(self, top_brands: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Warm cache for top brands (most frequently filtered).

        Args:
            top_brands: List of top brand names (optional)

        Returns:
            Dict with warming results
        ."""
        if top_brands is None:
            # Default popular brands
            top_brands = ["SIEMENS", "BOSCH", "AEG", "MIELE", "DYSON"]

        results = {
            "warmed_brands": 0,
            "top_brands": top_brands,
            "status": "success",
        }

        try:
            filter_configs = []

            for marca in top_brands:
                filter_configs.append(
                    {
                        "sort": "pvp:asc",
                        "filters": {"marca": marca},
                    }
                )

            warming_result = self.warm_popular_filters("productos", filter_configs)
            results["warmed_brands"] = warming_result.get("warmed_filters", 0)

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def warm_price_ranges(
        self, price_ranges: Optional[List[tuple]] = None
    ) -> Dict[str, Any]:
        """
        Warm cache for common price range filters.

        Args:
            price_ranges: List of (min_price, max_price) tuples

        Returns:
            Dict with warming results
        ."""
        if price_ranges is None:
            # Default popular price ranges
            price_ranges = [
                (0, 100),  # Budget range
                (100, 500),  # Mid-range
                (500, 1000),  # Premium range
                (1000, None),  # Luxury range (no max)
            ]

        results = {
            "warmed_ranges": 0,
            "price_ranges": price_ranges,
            "status": "success",
        }

        try:
            filter_configs = []

            for min_price, max_price in price_ranges:
                filter_config = {
                    "sort": "pvp:asc",
                    "filters": {},
                }

                if min_price is not None:
                    filter_config["filters"]["pvp_min"] = min_price

                if max_price is not None:
                    filter_config["filters"]["pvp_max"] = max_price

                filter_configs.append(filter_config)

            warming_result = self.warm_popular_filters("productos", filter_configs)
            results["warmed_ranges"] = warming_result.get("warmed_filters", 0)

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def warm_bc3_filters(self) -> Dict[str, Any]:
        """
        Warm cache for common BC3 filter combinations.

        Returns:
            Dict with warming results
        ."""
        results = {
            "warmed_bc3_filters": 0,
            "status": "success",
        }

        try:
            filter_configs = [
                {
                    "sort": "bc3_descripcion_corta:asc",
                    "filters": {"bc3_has_descripcion_corta": True},
                },
                {
                    "sort": "bc3_descripcion_corta:desc",
                    "filters": {"bc3_has_descripcion_corta": False},
                },
            ]

            warming_result = self.warm_popular_filters("productos", filter_configs)
            results["warmed_bc3_filters"] = warming_result.get("warmed_filters", 0)

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def warm_all_strategies(self) -> Dict[str, Any]:
        """
        Execute all warming strategies.

        Returns:
            Dict with comprehensive warming results
        ."""
        results = {
            "product_pages": self.warm_popular_product_pages(),
            "familia_pages": self.warm_popular_familia_pages(),
            "top_brands": self.warm_top_brands(),
            "price_ranges": self.warm_price_ranges(),
            "bc3_filters": self.warm_bc3_filters(),
        }

        # Calculate total warmed
        total_warmed = sum(
            result.get("warmed_queries", 0)
            + result.get("warmed_filters", 0)
            + result.get("warmed_brands", 0)
            + result.get("warmed_ranges", 0)
            + result.get("warmed_bc3_filters", 0)
            for result in results.values()
        )

        results["total_warmed"] = total_warmed
        results["overall_status"] = "success"

        return results

    def get_warming_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for cache warming based on current stats.

        Returns:
            Dict with warming recommendations
        ."""
        stats = self.pagination_cache.get_pagination_statistics()

        recommendations = {
            "current_stats": stats,
            "recommendations": [],
            "priority": "medium",
        }

        # Check cache hit rate
        hit_rate = stats.get("hit_rate", 0.0)
        if hit_rate < 0.3:
            recommendations["recommendations"].append(
                {
                    "action": "warm_all_strategies",
                    "reason": f"Low cache hit rate ({hit_rate:.1%}) - comprehensive warming recommended",
                    "priority": "high",
                }
            )
        elif hit_rate < 0.5:
            recommendations["recommendations"].append(
                {
                    "action": "warm_popular_product_pages",
                    "reason": f"Moderate cache hit rate ({hit_rate:.1%}) - popular pages warming recommended",
                    "priority": "medium",
                }
            )

        # Check memory cache size
        memory_size = stats.get("memory_cache_size", 0)
        if memory_size < 100:
            recommendations["recommendations"].append(
                {
                    "action": "warm_all_strategies",
                    "reason": f"Small memory cache size ({memory_size}) - warming recommended",
                    "priority": "medium",
                }
            )

        return recommendations


# Singleton instance for application-wide use
_global_warming_strategy: Optional[CacheWarmingStrategy] = None


def get_cache_warming_strategy() -> CacheWarmingStrategy:
    """Get global cache warming strategy instance.

    Returns:
        Global cache warming strategy instance
    ."""
    global _global_warming_strategy

    if _global_warming_strategy is None:
        _global_warming_strategy = CacheWarmingStrategy()

    return _global_warming_strategy
