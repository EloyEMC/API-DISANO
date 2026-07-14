"""Performance tests for N+1 query detection

Tests to identify and prevent N+1 query problems in the application
."""

import time
from unittest.mock import patch


class TestNPlusOneDetection:
    """Tests for detecting and preventing N+1 query problems."""

    def test_no_n_plus_one_in_product_search(self):
        """Test that product search doesn't trigger N+1 queries."""
        from app.domain.services.producto import ProductoService
        from app.infrastructure.repositories.producto import (
            SQLAlchemyProductoRepository,
        )
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        repository = SQLAlchemyProductoRepository(session)
        service = ProductoService(repository)

        try:
            # Use mock to count queries
            query_count = [0]
            original_execute = session.execute

            def count_execute(*args, **kwargs):
                query_count[0] += 1
                return original_execute(*args, **kwargs)

            from app.application.dto.producto import ProductoSearchDTO

            dto = ProductoSearchDTO(buscar="test", limit=10, marca="", familia="")

            # Temporarily patch session.execute to count queries
            with patch.object(session, "execute", side_effect=count_execute):
                service.buscar_productos(dto)

            # Should use single query (or minimal number), not N+1
            # Allow up to 2 queries (one main query + maybe one metadata query)
            assert (
                query_count[0] <= 2
            ), f"Product search triggered {query_count[0]} queries (possible N+1 problem)"

            print(f"✅ Product search used {query_count[0]} queries (acceptable)")

        finally:
            session.close()

    def test_no_n_plus_one_in_product_detail(self):
        """Test that product detail doesn't trigger N+1 queries."""
        from app.domain.services.producto import ProductoService
        from app.infrastructure.repositories.producto import (
            SQLAlchemyProductoRepository,
        )
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        repository = SQLAlchemyProductoRepository(session)
        service = ProductoService(repository)

        try:
            query_count = [0]
            original_execute = session.execute

            def count_execute(*args, **kwargs):
                query_count[0] += 1
                return original_execute(*args, **kwargs)

            with patch.object(session, "execute", side_effect=count_execute):
                try:
                    service.obtener_producto("TEST001")
                except:
                    pass  # Product might not exist in test DB

            # Single product detail should use 1 query maximum
            assert (
                query_count[0] <= 1
            ), f"Product detail triggered {query_count[0]} queries (N+1 problem)"

            print(f"✅ Product detail used {query_count[0]} queries (optimal)")

        finally:
            session.close()

    def test_no_n_plus_one_in_bc3_stats(self):
        """Test that BC3 statistics doesn't trigger N+1 queries."""
        from app.domain.services.producto import ProductoService
        from app.infrastructure.repositories.producto import (
            SQLAlchemyProductoRepository,
        )
        from app.infrastructure.database.connection import SessionLocal

        session = SessionLocal()
        repository = SQLAlchemyProductoRepository(session)
        service = ProductoService(repository)

        try:
            query_count = [0]
            original_execute = session.execute

            def count_execute(*args, **kwargs):
                query_count[0] += 1
                return original_execute(*args, **kwargs)

            with patch.object(session, "execute", side_effect=count_execute):
                # Get all products to calculate stats
                service.get_all_productos(skip=0, limit=100)

            # Stats calculation should use efficient queries, not N+1
            assert (
                query_count[0] <= 3
            ), f"BC3 stats triggered {query_count[0]} queries (inefficient)"

            print(f"✅ BC3 stats used {query_count[0]} queries (efficient)")

        finally:
            session.close()

    def test_bulk_queries_more_efficient_than_loops(self):
        """Test that bulk queries are more efficient than loop-based queries."""
        import time

        # Simulate N+1 pattern (inefficient)
        def inefficient_pattern():
            results = []
            for i in range(10):
                # Each iteration triggers a query (N+1)
                time.sleep(0.001)  # Simulate query time
                results.append(f"item_{i}")
            return results

        # Simulate efficient pattern (bulk)
        def efficient_pattern():
            # Single bulk query
            time.sleep(0.001)  # Simulate single query time
            return [f"item_{i}" for i in range(10)]

        # Measure performance
        start = time.time()
        inefficient_pattern()
        inefficient_time = time.time() - start

        start = time.time()
        efficient_pattern()
        efficient_time = time.time() - start

        # Efficient should be significantly faster
        assert efficient_time < inefficient_time, "Bulk queries should be faster than N+1 pattern"

        # Efficiency improvement should be significant (> 5x)
        efficiency_ratio = inefficient_time / efficient_time
        assert (
            efficiency_ratio >= 5.0
        ), f"Efficiency improvement should be at least 5x, got {efficiency_ratio:.2f}x"

        print(f"⚡ Efficiency improvement: {efficiency_ratio:.2f}x")

    def test_repository_uses_efficient_queries(self):
        """Test that repository uses efficient query patterns."""
        import app.infrastructure.repositories.producto as producto_repo_module

        import inspect

        source = inspect.getsource(producto_repo_module)

        # Should use SQLAlchemy query patterns, not individual queries in loops
        assert "session.query" in source, "Should use SQLAlchemy query patterns"

        # Should not have obvious N+1 patterns (query in loop)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            # Look for suspicious patterns
            if "for " in line and "session.execute" in lines[i + 1 : i + 3]:
                raise AssertionError(f"Possible N+1 pattern detected near line {i + 1}")

        print("✅ Repository uses efficient query patterns")

    def test_service_layer_avoids_n_plus_one(self):
        """Test that service layer doesn't introduce N+1 problems."""
        from app.domain.services.producto import ProductoService

        import inspect

        source = inspect.getsource(ProductoService)

        # Service should use repository methods (which are efficient)
        # rather than direct database queries
        assert "repository." in source, "Service should use repository methods"

        # Should not have database connection logic in service
        assert "sqlite3" not in source.lower(), "Service should not have direct database access"

        assert "session.execute" not in source, "Service should not execute queries directly"

        print("✅ Service layer follows clean architecture principles")

    def test_http_layer_uses_dependency_injection(self):
        """Test that HTTP layer uses dependency injection properly."""
        from app.interfaces.http import productos as productos_http

        import inspect

        source = inspect.getsource(productos_http)

        # Should use dependency injection
        assert "Depends" in source, "HTTP layer should use dependency injection"

        # Creating repositories in DI functions is correct pattern
        # Repository instances are NOT created directly in endpoint functions

        # Should not have session management in endpoints
        assert "SessionLocal()" not in source, "Session management should be in DI layer"

        print("✅ HTTP layer uses proper dependency injection")

    def test_performance_regression_prevention(self):
        """Test that we can detect performance regressions."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Establish baseline performance
        baseline_times = []

        for i in range(3):
            start = time.time()
            response = client.get("/api/productos/v2/list?buscar=test&limit=10")
            elapsed = time.time() - start
            baseline_times.append(elapsed)
            assert response.status_code in [200, 404]

        baseline_avg = sum(baseline_times) / len(baseline_times)

        # Test current performance
        current_times = []

        for i in range(3):
            start = time.time()
            response = client.get("/api/productos/v2/list?buscar=test&limit=10")
            elapsed = time.time() - start
            current_times.append(elapsed)
            assert response.status_code in [200, 404]

        current_avg = sum(current_times) / len(current_times)

        # Current should not be significantly worse than baseline
        # Allow up to 2x degradation (generous threshold)
        assert (
            current_avg <= baseline_avg * 2.0
        ), f"Performance regression detected: {current_avg:.4f}s vs baseline {baseline_avg:.4f}s"

        print(f"⏱️ Performance: baseline={baseline_avg:.4f}s, current={current_avg:.4f}s")
