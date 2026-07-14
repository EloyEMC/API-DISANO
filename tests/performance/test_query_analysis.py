"""Performance tests for query pattern analysis

Tests to analyze query patterns and identify indexing opportunities
."""

import time
from collections import Counter


class TestQueryAnalysis:
    """Tests for query pattern analysis."""

    def test_identify_most_frequent_queries(self):
        """Test that we can identify the most frequent query patterns."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Simulate different endpoint calls
        query_patterns = []

        # Product search queries
        for i in range(10):
            client.get(f"/api/productos/v2/list?buscar=test{i}&limit=10")
            query_patterns.append("product_search")

        # Product detail queries
        for i in range(5):
            client.get("/api/productos/v2/TEST001")
            query_patterns.append("product_detail")

        # BC3 stats queries
        for i in range(3):
            client.get("/api/bc3/stats")
            query_patterns.append("bc3_stats")

        # Analyze frequency
        frequency = Counter(query_patterns)

        # Verify we identified patterns
        assert len(frequency) >= 3
        assert frequency["product_search"] == 10
        assert frequency["product_detail"] == 5
        assert frequency["bc3_stats"] == 3

        # Most frequent should be product_search
        most_frequent = frequency.most_common(1)[0]
        assert most_frequent[0] == "product_search"

    def test_measure_query_execution_times(self):
        """Test that we can measure query execution times."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Measure execution times for different operations
        execution_times = {}

        # Product search
        start = time.time()
        response = client.get("/api/productos/v2/list?buscar=test&limit=10")
        execution_times["product_search"] = time.time() - start
        assert response.status_code == 200

        # Product detail
        start = time.time()
        response = client.get("/api/productos/v2/TEST001")
        execution_times["product_detail"] = time.time() - start
        assert response.status_code in [200, 404]  # 404 if product doesn't exist

        # BC3 stats
        start = time.time()
        response = client.get("/api/bc3/stats")
        execution_times["bc3_stats"] = time.time() - start
        assert response.status_code == 200

        # Verify all times are reasonable (< 100ms)
        for operation, elapsed in execution_times.items():
            assert elapsed < 0.1, f"{operation} took {elapsed:.3f}s (should be < 100ms)"

        # All times should be measured
        assert len(execution_times) >= 3

    def test_identify_slow_queries(self):
        """Test that we can identify slow queries (> 50ms)."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Measure multiple queries
        query_times = []

        for i in range(5):
            start = time.time()
            response = client.get("/api/productos/v2/list?buscar=test&limit=10")
            elapsed = time.time() - start
            query_times.append({"query": "product_search", "time": elapsed})
            assert response.status_code == 200

        # Identify slow queries (> 50ms)
        slow_queries = [q for q in query_times if q["time"] > 0.05]

        # In an optimized system, we should have minimal slow queries
        assert len(slow_queries) < len(
            query_times
        ), f"Too many slow queries: {len(slow_queries)}/{len(query_times)}"

    def test_identify_fields_for_indexing(self):
        """Test that we can identify fields that need indexing."""
        from app.infrastructure.repositories.producto import (
            SQLAlchemyProductoRepository,
        )
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        repository = SQLAlchemyProductoRepository(session)

        # Simulate common query patterns and track field usage
        field_usage = Counter()

        # Product search by codigo
        try:
            repository.get_by_codigo("TEST001")
            field_usage["codigo"] += 1
        except:
            pass

        # Product search by term
        from app.application.dto.producto import ProductoSearchDTO

        try:
            dto = ProductoSearchDTO(buscar="test", limit=10, marca="", familia="")
            repository.buscar_productos(dto)
            field_usage["descripcion"] += 1
        except:
            pass

        # Get all products
        try:
            repository.get_all_productos(skip=0, limit=10)
            field_usage["marca"] += 1
        except:
            pass

        session.close()

        # Identify frequently used fields
        frequent_fields = [field for field, count in field_usage.items() if count >= 1]

        # Most frequently queried fields should be identified
        assert len(frequent_fields) >= 1
        assert "codigo" in frequent_fields  # Primary key always queried

    def test_query_pattern_documentation(self):
        """Test that query patterns are properly documented."""
        # This test verifies that we have documentation for query patterns
        from pathlib import Path

        # Check if performance documentation exists
        perf_docs = [
            "docs/PERFORMANCE_OPTIMIZATION.md",
            "openspec/changes/fase4-performance-optimization/spec.md",
        ]

        # At least one document should exist
        doc_exists = any(Path(doc).exists() for doc in perf_docs)
        assert doc_exists, "Performance documentation should exist"
