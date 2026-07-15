"""Cache configuration optimization for production deployment.

Provides optimized cache settings for different deployment scenarios:
- Development: Fast cache for rapid iteration
- Testing: Minimal cache overhead
- Production: Optimized for performance and scalability
- Performance monitoring and auto-tuning capabilities
."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class DeploymentEnvironment(Enum):
    """Deployment environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class CacheConfiguration:
    """
    Optimized cache configuration for pagination.

    Provides tunable parameters for different deployment scenarios
    and workloads.
    """

    # TTL settings (in seconds)
    product_ttl: int = 3600  # 1 hour for products
    familia_ttl: int = 7200  # 2 hours for families
    list_ttl: int = 600  # 10 minutes for lists
    search_ttl: int = 300  # 5 minutes for searches
    stats_ttl: int = 60  # 1 minute for statistics
    default_ttl: int = 1800  # 30 minutes default

    # Cache sizing
    max_memory_entries: int = 10000  # Maximum entries in memory cache
    max_redis_entries: Optional[int] = None  # Redis limit (None = unlimited)

    # Performance tuning
    cache_hit_rate_target: float = 0.5  # Target 50% hit rate
    warm_cache_on_startup: bool = True  # Pre-populate cache on startup
    auto_warm_threshold: float = 0.3  # Auto-warm if hit rate falls below this

    # Monitoring
    enable_statistics: bool = True  # Track cache statistics
    statistics_interval: int = 60  # Log statistics every N seconds

    # Advanced tuning
    enable_cache_compression: bool = False  # Compress large cache entries
    compression_threshold: int = 1024  # Compress entries larger than 1KB

    def get_ttl_for_type(self, cache_type: str) -> int:
        """
        Get TTL for specific cache type.

        Args:
            cache_type: Type of cached data (product, familia, list, etc.)

        Returns:
            TTL in seconds
        ."""
        ttl_mapping = {
            "product": self.product_ttl,
            "familia": self.familia_ttl,
            "list": self.list_ttl,
            "search": self.search_ttl,
            "stats": self.stats_ttl,
        }

        return ttl_mapping.get(cache_type, self.default_ttl)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "ttl_settings": {
                "product": self.product_ttl,
                "familia": self.familia_ttl,
                "list": self.list_ttl,
                "search": self.search_ttl,
                "stats": self.stats_ttl,
                "default": self.default_ttl,
            },
            "cache_sizing": {
                "max_memory_entries": self.max_memory_entries,
                "max_redis_entries": self.max_redis_entries,
            },
            "performance_tuning": {
                "cache_hit_rate_target": self.cache_hit_rate_target,
                "warm_cache_on_startup": self.warm_cache_on_startup,
                "auto_warm_threshold": self.auto_warm_threshold,
            },
            "monitoring": {
                "enable_statistics": self.enable_statistics,
                "statistics_interval": self.statistics_interval,
            },
            "advanced_tuning": {
                "enable_cache_compression": self.enable_cache_compression,
                "compression_threshold": self.compression_threshold,
            },
        }


class CacheConfigurationManager:
    """
    Manager for cache configuration optimization.

    Provides environment-specific configurations and auto-tuning capabilities.
    """

    @staticmethod
    def get_development_config() -> CacheConfiguration:
        """
        Get optimized configuration for development.

        Development prioritizes fast iteration over cache hit rate.
        """
        return CacheConfiguration(
            product_ttl=300,  # 5 minutes
            familia_ttl=600,  # 10 minutes
            list_ttl=120,  # 2 minutes
            search_ttl=60,  # 1 minute
            stats_ttl=30,  # 30 seconds
            default_ttl=300,  # 5 minutes
            max_memory_entries=1000,
            max_redis_entries=None,
            cache_hit_rate_target=0.3,
            warm_cache_on_startup=False,
            auto_warm_threshold=0.2,
            enable_statistics=True,
            statistics_interval=30,
            enable_cache_compression=False,
            compression_threshold=1024,
        )

    @staticmethod
    def get_testing_config() -> CacheConfiguration:
        """
        Get optimized configuration for testing.

        Testing prioritizes minimal cache overhead and consistent results.
        """
        return CacheConfiguration(
            product_ttl=60,  # 1 minute
            familia_ttl=120,  # 2 minutes
            list_ttl=30,  # 30 seconds
            search_ttl=15,  # 15 seconds
            stats_ttl=10,  # 10 seconds
            default_ttl=60,  # 1 minute
            max_memory_entries=100,
            max_redis_entries=None,
            cache_hit_rate_target=0.2,
            warm_cache_on_startup=False,
            auto_warm_threshold=0.1,
            enable_statistics=False,
            statistics_interval=60,
            enable_cache_compression=False,
            compression_threshold=1024,
        )

    @staticmethod
    def get_staging_config() -> CacheConfiguration:
        """
        Get optimized configuration for staging.

        Staging balances performance and data freshness.
        """
        return CacheConfiguration(
            product_ttl=1800,  # 30 minutes
            familia_ttl=3600,  # 1 hour
            list_ttl=300,  # 5 minutes
            search_ttl=150,  # 2.5 minutes
            stats_ttl=30,  # 30 seconds
            default_ttl=900,  # 15 minutes
            max_memory_entries=5000,
            max_redis_entries=None,
            cache_hit_rate_target=0.4,
            warm_cache_on_startup=True,
            auto_warm_threshold=0.25,
            enable_statistics=True,
            statistics_interval=60,
            enable_cache_compression=False,
            compression_threshold=2048,
        )

    @staticmethod
    def get_production_config() -> CacheConfiguration:
        """
        Get optimized configuration for production.

        Production prioritizes high performance and scalability.
        """
        return CacheConfiguration(
            product_ttl=7200,  # 2 hours
            familia_ttl=14400,  # 4 hours
            list_ttl=900,  # 15 minutes
            search_ttl=300,  # 5 minutes
            stats_ttl=60,  # 1 minute
            default_ttl=3600,  # 1 hour
            max_memory_entries=20000,
            max_redis_entries=None,
            cache_hit_rate_target=0.6,
            warm_cache_on_startup=True,
            auto_warm_threshold=0.4,
            enable_statistics=True,
            statistics_interval=120,
            enable_cache_compression=True,
            compression_threshold=1024,
        )

    @staticmethod
    def get_config(environment: DeploymentEnvironment) -> CacheConfiguration:
        """
        Get configuration for specific environment.

        Args:
            environment: Deployment environment

        Returns:
            Optimized cache configuration
        """
        config_map = {
            DeploymentEnvironment.DEVELOPMENT: CacheConfigurationManager.get_development_config(),
            DeploymentEnvironment.TESTING: CacheConfigurationManager.get_testing_config(),
            DeploymentEnvironment.STAGING: CacheConfigurationManager.get_staging_config(),
            DeploymentEnvironment.PRODUCTION: CacheConfigurationManager.get_production_config(),
        }

        return config_map.get(
            environment, CacheConfigurationManager.get_development_config()
        )

    @staticmethod
    def auto_tune_configuration(
        current_config: CacheConfiguration, current_stats: Dict[str, Any]
    ) -> CacheConfiguration:
        """
        Automatically tune configuration based on current performance statistics.

        Args:
            current_config: Current cache configuration
            current_stats: Current cache statistics

        Returns:
            Optimized cache configuration
        ."""
        hit_rate = current_stats.get("hit_rate", 0.0)
        memory_size = current_stats.get("memory_cache_size", 0)

        # Create a copy of current config
        optimized_config = CacheConfiguration(**current_config.__dict__)

        # Adjust TTL based on hit rate
        if hit_rate < optimized_config.cache_hit_rate_target:
            # Increase TTL to improve hit rate
            optimized_config.product_ttl = int(
                min(optimized_config.product_ttl * 1.5, 14400)
            )  # Max 4 hours
            optimized_config.familia_ttl = int(
                min(optimized_config.familia_ttl * 1.5, 28800)
            )  # Max 8 hours
        elif hit_rate > optimized_config.cache_hit_rate_target + 0.2:
            # Decrease TTL to improve data freshness
            optimized_config.product_ttl = int(
                max(optimized_config.product_ttl * 0.8, 300)
            )  # Min 5 minutes
            optimized_config.familia_ttl = int(
                max(optimized_config.familia_ttl * 0.8, 600)
            )  # Min 10 minutes

        # Adjust cache size based on memory usage
        if memory_size > optimized_config.max_memory_entries * 0.9:
            # Reduce max entries to prevent memory issues
            optimized_config.max_memory_entries = max(
                int(optimized_config.max_memory_entries * 0.8), 100
            )
        elif memory_size < optimized_config.max_memory_entries * 0.5 and hit_rate < 0.3:
            # Increase max entries if not utilizing cache effectively
            optimized_config.max_memory_entries = min(
                int(optimized_config.max_memory_entries * 1.2), 50000
            )

        return optimized_config

    @staticmethod
    def get_performance_recommendations(
        current_config: CacheConfiguration, current_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get performance optimization recommendations.

        Args:
            current_config: Current cache configuration
            current_stats: Current cache statistics

        Returns:
            List of optimization recommendations
        ."""
        recommendations = []

        hit_rate = current_stats.get("hit_rate", 0.0)
        total_operations = current_stats.get("total_operations", 0)
        hits = current_stats.get("hits", 0)
        misses = current_stats.get("misses", 0)

        # Hit rate analysis
        if hit_rate < current_config.cache_hit_rate_target:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "hit_rate",
                    "message": f"Cache hit rate ({hit_rate:.1%}) below target ({current_config.cache_hit_rate_target:.1%})",
                    "recommendations": [
                        "Increase TTL values",
                        "Enable cache warming on startup",
                        "Review cache key strategy",
                    ],
                }
            )

        # Memory usage analysis
        memory_size = current_stats.get("memory_cache_size", 0)
        if memory_size > current_config.max_memory_entries * 0.9:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "memory",
                    "message": f"Memory cache usage ({memory_size}) near limit ({current_config.max_memory_entries})",
                    "recommendations": [
                        "Reduce TTL values",
                        "Implement cache eviction policy",
                        "Enable cache compression",
                    ],
                }
            )

        # Error rate analysis
        errors = current_stats.get("errors", 0)
        if total_operations > 100 and errors / total_operations > 0.05:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "reliability",
                    "message": f"High cache error rate ({errors}/{total_operations})",
                    "recommendations": [
                        "Check Redis connectivity",
                        "Review error logs",
                        "Implement fallback mechanisms",
                    ],
                }
            )

        return recommendations


def get_optimized_cache_config(
    environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION,
) -> CacheConfiguration:
    """
    Get optimized cache configuration for deployment environment.

    Args:
        environment: Deployment environment (defaults to production)

    Returns:
        Optimized cache configuration
    """
    return CacheConfigurationManager.get_config(environment)


def apply_cache_configuration(
    cache_config: CacheConfiguration,
    cache_manager,
) -> bool:
    """
    Apply cache configuration to cache manager.

    Args:
        cache_config: Configuration to apply
        cache_manager: Cache manager instance to configure

    Returns:
        True if successful
    ."""
    try:
        # Update TTL strategy
        cache_manager.TTL_STRATEGY = {
            "product": cache_config.product_ttl,
            "familia": cache_config.familia_ttl,
            "list": cache_config.list_ttl,
            "search": cache_config.search_ttl,
            "stats": cache_config.stats_ttl,
            "default": cache_config.default_ttl,
        }

        # Apply memory cache limits
        if len(cache_manager.memory_cache) > cache_config.max_memory_entries:
            # Clear excess entries
            keys_to_remove = list(cache_manager.memory_cache.keys())[
                : len(cache_manager.memory_cache) - cache_config.max_memory_entries
            ]
            for key in keys_to_remove:
                del cache_manager.memory_cache[key]

        return True

    except Exception:
        return False
