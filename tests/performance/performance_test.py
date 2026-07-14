"""Performance benchmarks for critical endpoints

Tests response time degradation is minimal (< 100ms P95)
."""

import time
import statistics
from typing import List, Tuple
from fastapi.testclient import TestClient
from app.main import app


class PerformanceBenchmark:
    """Performance benchmarking for API endpoints."""

    def __init__(self, client: TestClient):
        self.client = client

    def benchmark_endpoint(
        self, url: str, num_requests: int = 100
    ) -> Tuple[float, float, float, List[float]]:
        """
        Benchmark endpoint response times

        Returns:
            (mean_ms, p95_ms, p99_ms, all_times)
        ."""
        times = []

        for _ in range(num_requests):
            start = time.time()
            response = self.client.get(url)
            end = time.time()

            # Convert to milliseconds
            elapsed_ms = (end - start) * 1000
            times.append(elapsed_ms)

        # Calculate statistics
        mean_ms = statistics.mean(times)
        sorted_times = sorted(times)
        p95_ms = sorted_times[int(len(times) * 0.95)]
        p99_ms = sorted_times[int(len(times) * 0.99)]

        return mean_ms, p95_ms, p99_ms, times

    def print_results(self, endpoint: str, results: Tuple[float, float, float]):
        """Print benchmark results."""
        mean_ms, p95_ms, p99_ms = results
        print(f"\n📊 {endpoint}")
        print(f"  Mean: {mean_ms:.2f}ms")
        print(f"  P95:  {p95_ms:.2f}ms")
        print(f"  P99:  {p99_ms:.2f}ms")

        # Check against requirements
        if p95_ms < 100:
            print("  ✅ PASS: P95 < 100ms")
        else:
            print("  ❌ FAIL: P95 >= 100ms")


def main():
    """Run performance benchmarks for critical endpoints."""
    print("🚀 Starting Performance Benchmarks")
    print("=" * 50)

    client = TestClient(app)
    benchmark = PerformanceBenchmark(client)

    # Benchmark critical endpoints
    endpoints = [
        ("V2 List", "/api/productos/v2/list?buscar=test&limit=10"),
        ("V2 Detail", "/api/productos/v2/11253300"),
        ("V1 List", "/api/productos/?buscar=test&limit=5"),
    ]

    results = {}

    for name, url in endpoints:
        print(f"\n⏱️  Benchmarking: {name}")
        mean, p95, p99, times = benchmark.benchmark_endpoint(url, num_requests=50)
        results[name] = (mean, p95, p99)
        benchmark.print_results(name, results[name])

    # Summary
    print("\n" + "=" * 50)
    print("📋 PERFORMANCE SUMMARY")
    print("=" * 50)

    all_passed = True
    for name, (mean, p95, p99) in results.items():
        status = "✅ PASS" if p95 < 100 else "❌ FAIL"
        print(f"{name:15s} P95: {p95:6.2f}ms {status}")
        if p95 >= 100:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")

    return all_passed


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
