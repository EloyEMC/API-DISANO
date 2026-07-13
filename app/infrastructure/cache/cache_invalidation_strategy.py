"""Cache Invalidation Strategy for advanced features.

Provides comprehensive cache invalidation logic for different scenarios:
- Entity-based invalidation (products, families, BC3 data)
- Filter-based invalidation (by marca, familia, price ranges)
- Pattern-based invalidation for complex scenarios
- Event-driven invalidation hooks
- Transaction-safe cache operations
"""

from typing import Dict, List, Any, Optional, Callable
from app.infrastructure.cache.pagination_cache import get_pagination_cache
from app.infrastructure.cache.cache_manager import get_cache_manager


class CacheInvalidationStrategy:
    """
    Comprehensive cache invalidation strategy for pagination cache.

    This class provides methods to invalidate cache entries based on
    different scenarios:
    - Entity-specific invalidation (products, families, BC3)
    - Filter-based invalidation (marca, familia, price ranges)
    - Pattern-based invalidation for complex scenarios
    - Event-driven invalidation hooks
    """

    def __init__(self):
        """Initialize cache invalidation strategy."""
        self.pagination_cache = get_pagination_cache()
        self.cache_manager = get_cache_manager()

    def invalidate_on_product_change(
        self,
        product_code: str,
        marca: Optional[str] = None,
        familia: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Invalidate cache entries when a product changes (create, update, delete).

        Args:
            product_code: The product code that changed
            marca: Product's brand (marca)
            familia: Product's family (familia)

        Returns:
            Dict with invalidation results
        """
        results = {
            "product_code": product_code,
            "invalidated_products_count": 0,
            "invalidated_marca_count": 0,
            "invalidated_familia_count": 0,
            "status": "success",
        }

        try:
            # Invalidate all product pagination cache
            products_invalidated = self.pagination_cache.invalidate_entity("productos")
            results["invalidated_products_count"] = products_invalidated

            # Invalidate marca-specific cache if brand provided
            if marca:
                marca_invalidated = self.pagination_cache.invalidate_filter_pattern(
                    "productos", "marca", marca
                )
                results["invalidated_marca_count"] = marca_invalidated

            # Invalidate familia-specific cache if family provided
            if familia:
                familia_invalidated = self.pagination_cache.invalidate_filter_pattern(
                    "productos", "familia", familia
                )
                results["invalidated_familia_count"] = familia_invalidated

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def invalidate_on_familia_change(self, familia_name: str) -> Dict[str, Any]:
        """
        Invalidate cache entries when a family changes or is created/deleted.

        Args:
            familia_name: The family name that changed

        Returns:
            Dict with invalidation results
        """
        results = {
            "familia_name": familia_name,
            "invalidated_familias_count": 0,
            "invalidated_products_count": 0,
            "status": "success",
        }

        try:
            # Invalidate all family pagination cache
            familias_invalidated = self.pagination_cache.invalidate_entity("familias")
            results["invalidated_familias_count"] = familias_invalidated

            # Invalidate product cache filtered by this family
            products_invalidated = self.pagination_cache.invalidate_filter_pattern(
                "productos", "familia", familia_name
            )
            results["invalidated_products_count"] = products_invalidated

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def invalidate_on_bc3_data_change(self) -> Dict[str, Any]:
        """
        Invalidate all BC3-related cache when BC3 data changes.

        Returns:
            Dict with invalidation results
        """
        results = {
            "invalidated_bc3_count": 0,
            "status": "success",
        }

        try:
            # Invalidate BC3 pagination cache
            bc3_invalidated = self.pagination_cache.invalidate_entity("bc3")
            results["invalidated_bc3_count"] = bc3_invalidated

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def invalidate_on_price_range_change(
        self, marca: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invalidate cache when prices change significantly.

        Args:
            marca: Optional brand to limit invalidation scope

        Returns:
            Dict with invalidation results
        """
        results = {
            "marca": marca,
            "invalidated_count": 0,
            "status": "success",
        }

        try:
            # Price filters affect most product queries, so invalidate all
            if marca:
                # Scope to specific brand
                marca_invalidated = self.pagination_cache.invalidate_filter_pattern(
                    "productos", "marca", marca
                )
                results["invalidated_count"] = marca_invalidated
            else:
                # Invalidate all product cache
                all_invalidated = self.pagination_cache.invalidate_entity("productos")
                results["invalidated_count"] = all_invalidated

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def invalidate_all_pagination_cache(self) -> Dict[str, Any]:
        """
        Invalidate all pagination cache entries.

        Returns:
            Dict with invalidation results
        """
        results = {
            "invalidated_entities": 0,
            "status": "success",
        }

        try:
            success = self.pagination_cache.clear_pagination_cache()
            results["invalidated_entities"] = 1 if success else 0

        except Exception as e:
            results["status"] = f"error: {str(e)}"

        return results

    def get_invalidation_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics to help determine invalidation needs.

        Returns:
            Dict with cache statistics
        """
        return {
            "pagination_stats": self.pagination_cache.get_pagination_statistics(),
            "general_stats": self.cache_manager.get_statistics(),
        }

    def smart_invalidate(self, event_type: str, **event_data) -> Dict[str, Any]:
        """
        Smart cache invalidation based on event type and data.

        Automatically determines the appropriate invalidation strategy
        based on the event type and provides detailed results.

        Args:
            event_type: Type of event (product_change, familia_change, bc3_change, price_change)
            **event_data: Event-specific data (product_code, marca, familia, etc.)

        Returns:
            Dict with invalidation results
        """
        invalidation_map = {
            "product_change": self.invalidate_on_product_change,
            "familia_change": self.invalidate_on_familia_change,
            "bc3_change": self.invalidate_on_bc3_data_change,
            "price_change": self.invalidate_on_price_range_change,
            "all": self.invalidate_all_pagination_cache,
        }

        invalidation_fn = invalidation_map.get(event_type)
        if invalidation_fn:
            return invalidation_fn(**event_data)
        else:
            return {
                "event_type": event_type,
                "status": "error",
                "message": f"Unknown event type: {event_type}",
            }

    def batch_invalidate(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch process multiple invalidation events.

        Args:
            events: List of invalidation events with 'event_type' and data

        Returns:
            List of invalidation results
        """
        results = []

        for event in events:
            event_type = event.get("event_type")
            event_data = {k: v for k, v in event.items() if k != "event_type"}
            result = self.smart_invalidate(event_type, **event_data)
            results.append(result)

        return results

    def transactional_invalidate(
        self, invalidation_fn: Callable, rollback_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Perform transactional cache invalidation with rollback support.

        Args:
            invalidation_fn: Function that performs the invalidation
            rollback_fn: Optional function to rollback invalidation if needed

        Returns:
            Dict with transaction results
        """
        result = {
            "status": "success",
            "message": "Invalidation completed",
        }

        try:
            # Perform invalidation
            invalidation_result = invalidation_fn()
            result["invalidation_result"] = invalidation_result

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Invalidation failed: {str(e)}"

            # Attempt rollback if provided
            if rollback_fn:
                try:
                    rollback_result = rollback_fn()
                    result["rollback_result"] = rollback_result
                except Exception as rollback_error:
                    result["rollback_error"] = str(rollback_error)

        return result


# Singleton instance for application-wide use
_global_invalidation_strategy: Optional[CacheInvalidationStrategy] = None


def get_cache_invalidation_strategy() -> CacheInvalidationStrategy:
    """Get global cache invalidation strategy instance.

    Returns:
        Global cache invalidation strategy instance
    """
    global _global_invalidation_strategy

    if _global_invalidation_strategy is None:
        _global_invalidation_strategy = CacheInvalidationStrategy()

    return _global_invalidation_strategy
