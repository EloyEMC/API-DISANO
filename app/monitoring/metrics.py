"""Performance metrics collection and analysis module."""

import statistics
from typing import Any
from collections import defaultdict
from datetime import datetime


class MetricsCollector:
    ."""
    Performance metrics collector for monitoring application performance.

    Collects, analyzes, and exports performance metrics including response times,
    query execution times, cache performance, and database operations.
    """

    def __init__(self) -> None:
        ."""Initialize the metrics collector."""
        self._metrics: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._cache_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"hits": 0, "misses": 0})

    def record(self, metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """
        Record a metric with optional tags.

        Args:
            metric_name: Name of the metric (e.g., "response_time", "query_time")
            value: Numeric value of the metric
            tags: Optional dictionary of tags for categorization
        """
        metric_entry = {
            "value": value,
            "timestamp": datetime.now().timestamp(),
            "tags": tags or {},
        }

        self._metrics[metric_name].append(metric_entry)

        # Track cache statistics separately
        if metric_name in ["cache_hit", "cache_miss"]:
            cache_name = tags.get("cache", "default") if tags else "default"
            if cache_name not in self._cache_stats:
                self._cache_stats[cache_name] = {"hits": 0, "misses": 0}
            if metric_name == "cache_hit":
                self._cache_stats[cache_name]["hits"] += 1
            else:  # cache_miss
                self._cache_stats[cache_name]["misses"] += 1

    def get_metrics(self, metric_name: str) -> list[dict[str, Any]]:
        """
        Get all recorded metrics for a specific metric name.

        Args:
            metric_name: Name of the metric to retrieve

        Returns:
            List of metric entries
        ."""
        return self._metrics.get(metric_name, [])

    def get_aggregated_metrics(
        self, metric_name: str, tags: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get metrics aggregated by tags.

        Args:
            metric_name: Name of the metric to retrieve
            tags: Optional tag filters

        Returns:
            List of metric entries matching the tags
        ."""
        all_metrics = self.get_metrics(metric_name)

        if not tags:
            return all_metrics

        # Filter by tags
        filtered_metrics = []
        for metric in all_metrics:
            metric_tags = metric.get("tags", {})
            if all(metric_tags.get(k) == v for k, v in tags.items()):
                filtered_metrics.append(metric)

        return filtered_metrics

    def export_metrics(self) -> dict[str, Any]:
        """
        Export all metrics in standard format.

        Returns:
            Dictionary with all metrics organized by name
        ."""
        exported = {"timestamp": datetime.now().isoformat(), "metrics": {}}

        for metric_name, metrics_list in self._metrics.items():
            if metrics_list:
                exported["metrics"][metric_name] = [
                    {
                        "value": m["value"],
                        "timestamp": m["timestamp"],
                        "tags": m.get("tags", {}),
                    }
                    for m in metrics_list
                ]

        return exported

    def get_statistics(
        self, metric_name: str, percentiles: list[int] | None = None
    ) -> dict[str, float]:
        """
        Calculate statistics for a specific metric.

        Args:
            metric_name: Name of the metric to analyze
            percentiles: Optional list of percentiles to calculate (e.g., [50, 95, 99])

        Returns:
            Dictionary with calculated statistics
        ."""
        metrics_list = self.get_metrics(metric_name)

        if not metrics_list:
            return {}

        values = [m["value"] for m in metrics_list]

        stats: dict[str, float] = {
            "count": float(len(values)),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": float(min(values)) if values else 0.0,
            "max": float(max(values)) if values else 0.0,
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

        # Calculate percentiles if requested
        if percentiles:
            sorted_values = sorted(values)
            for percentile in percentiles:
                key = f"p{percentile}"
                try:
                    index = int((percentile / 100) * len(sorted_values))
                except (ValueError, ZeroDivisionError):
                    index = 0
                index = min(index, len(sorted_values) - 1)
                stats[key] = float(sorted_values[index])

        return stats

    def get_cache_statistics(self, cache_name: str = "default") -> dict[str, Any]:
        """
        Get cache performance statistics for a specific cache.

        Args:
            cache_name: Name of the cache to analyze

        Returns:
            Dictionary with cache statistics
        ."""
        cache_data = self._cache_stats.get(cache_name, {"hits": 0, "misses": 0})

        total_operations = cache_data["hits"] + cache_data["misses"]
        hit_rate = cache_data["hits"] / total_operations if total_operations > 0 else 0.0

        return {
            "total_hits": cache_data["hits"],
            "total_misses": cache_data["misses"],
            "total_operations": total_operations,
            "hit_rate": hit_rate,
            "cache_name": cache_name,
        }

    def get_trend(self, metric_name: str, window_size: int = 5) -> dict[str, Any]:
        """
        Analyze performance trend for a specific metric.

        Args:
            metric_name: Name of the metric to analyze
            window_size: Number of recent data points to analyze

        Returns:
            Dictionary with trend analysis
        ."""
        metrics_list = self.get_metrics(metric_name)

        if len(metrics_list) < 2:
            return {"direction": "insufficient_data", "change": 0.0, "trend": []}

        # Get recent metrics
        recent_metrics = metrics_list[-window_size:]
        values = [m["value"] for m in recent_metrics]

        # Calculate trend
        if len(values) >= 3:
            first_avg = statistics.mean(values[: len(values) // 2])
            second_avg = statistics.mean(values[len(values) // 2 :])
            change = second_avg - first_avg

            # Determine direction
            if abs(change) < values[0] * 0.05:  # Less than 5% change
                direction = "stable"
            elif change > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
        else:
            change = values[-1] - values[0] if len(values) > 1 else 0.0
            direction = (
                "insufficient_data"
                if abs(change) < 0.001
                else ("increasing" if change > 0 else "decreasing")
            )

        return {
            "direction": direction,
            "change": change,
            "trend": values,
            "window_size": len(values),
        }

    def get_all_metrics(self) -> dict[str, list[dict[str, Any]]]:
        """
        Get all collected metrics organized by name.

        Returns:
            Dictionary with all metrics
        ."""
        return dict(self._metrics)

    def reset(self) -> None:
        """Reset all collected metrics."""
        self._metrics.clear()
        self._cache_stats.clear()
