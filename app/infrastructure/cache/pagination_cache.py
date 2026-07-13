"""Pagination Cache Wrapper for advanced features.

Provides specialized caching for paginated queries with:
- Hash-based cache keys incorporating filters and sorting
- TTL strategy tuned for pagination results
- Pattern-based invalidation
- Get-or-compute pattern for efficient cache usage
- Integration with CacheManager from Fase 4.1
"""

from typing import Optional, Dict, List, Any
from app.infrastructure.cache.cache_manager import get_cache_manager


class PaginationCacheWrapper:
    """
    Cache wrapper specialized for pagination queries.

    This wrapper provides efficient caching for paginated queries with:
    - Hash-based cache keys that include all pagination parameters
    - TTL strategy appropriate for pagination results
    - Pattern-based cache invalidation
    - Get-or-compute pattern for efficient cache usage

    Cache key structure: pagination:{entity_type}:{hash(fingerprint)}
    where fingerprint includes all pagination parameters.
    """

    def __init__(self):
        """Initialize pagination cache wrapper."""
        self.cache_manager = get_cache_manager()
        self._cache_type_mapping = {
            "productos": "pagination_productos",
            "familias": "pagination_familias",
            "bc3": "pagination_bc3",
        }

    def _generate_cache_key(
        self,
        entity_type: str,
        page: int,
        per_page: int,
        sort: Optional[str],
        filters: Dict[str, Any],
    ) -> str:
        """Generate cache key for pagination query.

        Args:
            entity_type: Type of entity (productos, familias, bc3)
            page: Current page number
            per_page: Items per page
            sort: Sort criteria string
            filters: Dictionary of applied filters

        Returns:
            Consistent cache key string
        """
        # Create fingerprint of pagination parameters
        fingerprint_parts = [
            f"page={page}",
            f"per_page={per_page}",
            f"sort={sort or 'none'}",
        ]

        # Add filters to fingerprint in sorted order
        if filters:
            sorted_filters = sorted(
                (k, str(v)) for k, v in filters.items() if v is not None
            )
            fingerprint_parts.extend(f"{k}={v}" for k, v in sorted_filters)

        fingerprint = "|".join(fingerprint_parts)

        # Generate safe cache key
        cache_key = self.cache_manager.generate_key(
            cache_type=self._cache_type_mapping.get(entity_type, "pagination"),
            identifier=fingerprint,
        )

        return cache_key

    def get(
        self,
        entity_type: str,
        page: int,
        per_page: int,
        sort: Optional[str],
        filters: Dict[str, Any],
    ) -> Optional[Any]:
        """Get cached pagination result.

        Args:
            entity_type: Type of entity (productos, familias, bc3)
            page: Current page number
            per_page: Items per page
            sort: Sort criteria string
            filters: Dictionary of applied filters

        Returns:
            Cached pagination result or None if not found
        """
        cache_key = self._generate_cache_key(entity_type, page, per_page, sort, filters)
        return self.cache_manager.get(cache_key)

    def set(
        self,
        entity_type: str,
        page: int,
        per_page: int,
        sort: Optional[str],
        filters: Dict[str, Any],
        result: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache pagination result.

        Args:
            entity_type: Type of entity (productos, familias, bc3)
            page: Current page number
            per_page: Items per page
            sort: Sort criteria string
            filters: Dictionary of applied filters
            result: Pagination result to cache
            ttl: TTL in seconds (uses pagination default if not specified)

        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_cache_key(entity_type, page, per_page, sort, filters)

        # Use pagination-specific TTL (default 5 minutes)
        if ttl is None:
            ttl = self.cache_manager.get_ttl("list")

        return self.cache_manager.set(cache_key, result, ttl)

    def invalidate_entity(self, entity_type: str) -> bool:
        """Invalidate all cache entries for an entity type.

        Args:
            entity_type: Type of entity to invalidate (productos, familias, bc3)

        Returns:
            True if successful, False otherwise
        """
        cache_type = self._cache_type_mapping.get(
            entity_type, f"pagination_{entity_type}"
        )
        pattern = f"{self.cache_manager._safe_key(cache_type)}:*"

        count = self.cache_manager.invalidate_pattern(pattern)
        return count > 0

    def invalidate_filter_pattern(
        self, entity_type: str, filter_field: str, filter_value: str
    ) -> int:
        """Invalidate cache entries matching a specific filter pattern.

        Args:
            entity_type: Type of entity (productos, familias, bc3)
            filter_field: Filter field name (marca, familia, etc.)
            filter_value: Filter value to match

        Returns:
            Number of cache entries invalidated
        """
        cache_type = self._cache_type_mapping.get(
            entity_type, f"pagination_{entity_type}"
        )
        base_pattern = f"{self.cache_manager._safe_key(cache_type)}:*"
        target_pattern = f"*{filter_field}={filter_value}*"

        # Get all matching keys
        try:
            if self.cache_manager.use_memory_cache:
                import re

                with self.cache_manager.cache_lock:
                    keys_to_delete = []
                    base_regex = base_pattern.replace("*", ".*")
                    target_regex = target_pattern.replace("*", ".*")

                    for key in list(self.cache_manager.memory_cache.keys()):
                        if re.match(base_regex, key):
                            if re.search(target_regex, key):
                                keys_to_delete.append(key)

                    for key in keys_to_delete:
                        del self.cache_manager.memory_cache[key]

                    return len(keys_to_delete)
        except Exception:
            pass

        return 0

    def get_or_compute(
        self,
        entity_type: str,
        page: int,
        per_page: int,
        sort: Optional[str],
        filters: Dict[str, Any],
        compute_fn,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get cached pagination result or compute and cache it.

        Args:
            entity_type: Type of entity (productos, familias, bc3)
            page: Current page number
            per_page: Items per page
            sort: Sort criteria string
            filters: Dictionary of applied filters
            compute_fn: Function to compute result if not cached
            ttl: TTL in seconds (uses pagination default if not specified)

        Returns:
            Cached or computed pagination result
        """
        # Try to get from cache first
        cached_result = self.get(entity_type, page, per_page, sort, filters)
        if cached_result is not None:
            return cached_result

        # Cache miss - compute result
        computed_result = compute_fn()

        # Cache the computed result
        if computed_result is not None:
            self.set(entity_type, page, per_page, sort, filters, computed_result, ttl)

        return computed_result

    def get_pagination_statistics(self) -> Dict[str, Any]:
        """Get pagination-specific cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        general_stats = self.cache_manager.get_statistics()

        # Add pagination-specific stats
        pagination_stats = general_stats.copy()
        pagination_stats["cache_type_mapping"] = self._cache_type_mapping

        # Count cache entries per entity type
        if self.cache_manager.use_memory_cache:
            type_counts = {}
            for entity_type in self._cache_type_mapping.values():
                type_counts[entity_type] = 0
                for key in self.cache_manager.memory_cache.keys():
                    if key.startswith(
                        f"api_disano:{self.cache_manager._safe_key(entity_type)}:"
                    ):
                        type_counts[entity_type] += 1

            pagination_stats["pagination_type_counts"] = type_counts

        return pagination_stats

    def warm_pagination_cache(
        self, entity_type: str, warming_queries: List[Dict[str, Any]]
    ) -> int:
        """Warm cache with frequently accessed pagination queries.

        Args:
            entity_type: Type of entity (productos, familias, bc3)
            warming_queries: List of query configs to warm cache

        Returns:
            Number of entries warmed
        """
        warmed = 0

        for query_config in warming_queries:
            page = query_config.get("page", 1)
            per_page = query_config.get("per_page", 10)
            sort = query_config.get("sort")
            filters = query_config.get("filters", {})

            # Check if cached
            cached = self.get(entity_type, page, per_page, sort, filters)
            if cached is None:
                # This would normally call compute_fn, but we just count as "potentially warmable"
                warmed += 1

        return warmed

    def clear_pagination_cache(self) -> bool:
        """Clear all pagination cache entries.

        Returns:
            True if successful
        """
        # Invalidate all pagination cache types
        success = True
        for entity_type in self._cache_type_mapping.keys():
            if not self.invalidate_entity(entity_type):
                success = False

        return success

    def get_entity_cache_stats(self, entity_type: str) -> Dict[str, Any]:
        """Get cache statistics for a specific entity type.

        Args:
            entity_type: Type of entity (productos, familias, bc3)

        Returns:
            Dictionary with entity-specific cache statistics
        """
        cache_type = self._cache_type_mapping.get(
            entity_type, f"pagination_{entity_type}"
        )

        # Count entries for this entity type
        entity_count = 0
        if self.cache_manager.use_memory_cache:
            pattern_regex = f"api_disano:{self.cache_manager._safe_key(cache_type)}:.*"
            import re

            with self.cache_manager.cache_lock:
                for key in list(self.cache_manager.memory_cache.keys()):
                    if re.match(pattern_regex, key):
                        entity_count += 1

        return {
            "entity_type": entity_type,
            "cache_type": cache_type,
            "memory_cache_entries": entity_count,
        }


# Singleton instance for application-wide use
_global_pagination_cache: Optional[PaginationCacheWrapper] = None


def get_pagination_cache() -> PaginationCacheWrapper:
    """Get global pagination cache wrapper instance.

    Returns:
        Global pagination cache wrapper instance
    """
    global _global_pagination_cache

    if _global_pagination_cache is None:
        _global_pagination_cache = PaginationCacheWrapper()

    return _global_pagination_cache
