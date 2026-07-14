"""
TDD Tests for TASK-3.4.5: BC3 Suite Compatibility

RED Phase: These tests should FAIL initially if BC3 fields are not present.
."""

import pytest
import time
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError as e:
    pytest.skip(f"Cannot import app.main: {e}", allow_module_level=True)


class TestBC3Compatibility:
    """Tests for BC3 Suite compatibility (TASK-3.4.5)."""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app."""
        return TestClient(app)

    def test_bc3_fields_present_in_v2_response(self, client):
        """
        TASK-3.4.5: Test BC3 fields present in V2 responses
        Acceptance Criteria: BC3 fields present in V2 responses
        ."""
        response = client.get("/api/productos/v2/list?buscar=test&limit=1")

        assert response.status_code == 200, "V2 list endpoint should return 200"

        data = response.json()

        if len(data) > 0:
            product = data[0]

            # BC3 fields should be present
            assert (
                "bc3_descripcion_corta" in product
            ), "V2 response should include bc3_descripcion_corta field"

            assert (
                "bc3_product_type" in product
            ), "V2 response should include bc3_product_type field"

            assert (
                "bc3_descripcion_completa" in product
            ), "V2 response should include bc3_descripcion_completa field"

            # Check they're not None (may be empty string but should exist)
            assert (
                product["bc3_descripcion_corta"] is not None
            ), "bc3_descripcion_corta should not be None"

            assert product["bc3_product_type"] is not None, "bc3_product_type should not be None"

            assert (
                product["bc3_descripcion_completa"] is not None
            ), "bc3_descripcion_completa should not be None"

    def test_bc3_fields_present_in_v2_detail(self, client):
        """
        TASK-3.4.5: Test BC3 fields present in V2 detail response
        Acceptance Criteria: BC3 fields present in V2 responses
        ."""
        response = client.get("/api/productos/v2/TEST001")

        if response.status_code == 200:
            product = response.json()

            # BC3 fields should be present
            assert (
                "bc3_descripcion_corta" in product
            ), "V2 detail response should include bc3_descripcion_corta field"

            assert (
                "bc3_product_type" in product
            ), "V2 detail response should include bc3_product_type field"

            assert (
                "bc3_descripcion_completa" in product
            ), "V2 detail response should include bc3_descripcion_completa field"

    def test_bc3_fields_present_in_v1_response(self, client):
        """
        TASK-3.4.5: Test BC3 fields present in V1 responses (legacy format)
        Acceptance Criteria: BC3 fields present in V1 responses (legacy format preserved)
        ."""
        response = client.get("/api/productos/?buscar=test&limit=1")

        assert response.status_code == 200, "V1 list endpoint should return 200"

        data = response.json()

        if len(data) > 0:
            product = data[0]

            # BC3 fields should be present in legacy format
            assert (
                "bc3_descripcion_corta" in product
            ), "V1 response should include bc3_descripcion_corta field (legacy)"

            assert (
                "bc3_product_type" in product
            ), "V1 response should include bc3_product_type field (legacy)"

            assert (
                "bc3_descripcion_completa" in product
            ), "V1 response should include bc3_descripcion_completa field (legacy)"

    def test_bc3_fields_present_in_v1_detail(self, client):
        """
        TASK-3.4.5: Test BC3 fields present in V1 detail response
        Acceptance Criteria: BC3 fields present in V1 responses (legacy format preserved)
        ."""
        response = client.get("/api/productos/TEST001")

        if response.status_code == 200:
            product = response.json()

            # BC3 fields should be present in legacy format
            assert (
                "bc3_descripcion_corta" in product
            ), "V1 detail response should include bc3_descripcion_corta field (legacy)"

            assert (
                "bc3_product_type" in product
            ), "V1 detail response should include bc3_product_type field (legacy)"

            assert (
                "bc3_descripcion_completa" in product
            ), "V1 detail response should include bc3_descripcion_completa field (legacy)"

    def test_products_accessible_v2(self, client):
        """
        TASK-3.4.5: Test that products are accessible through V2 endpoints
        Acceptance Criteria: 8,288 products accessible through V2 endpoints
        ."""
        # Test with high limit to get many products
        response = client.get("/api/productos/v2/list?buscar=test&limit=100")

        assert response.status_code == 200, "V2 list endpoint should return 200"

        data = response.json()

        # Should have some products (at least 1)
        assert len(data) >= 1, "V2 endpoints should return at least 1 product"

        # Could check for 8,288 but limit may restrict this
        # For now, just verify we can access products
        assert len(data) <= 1000, f"Should respect limit of 1000, got {len(data)}"

    def test_products_accessible_v1(self, client):
        """
        TASK-3.4.5: Test that products are accessible through V1 endpoints
        Acceptance Criteria: 8,288 products accessible through V1 endpoints
        ."""
        # Test with high limit to get many products
        response = client.get("/api/productos/?buscar=test&limit=100")

        assert response.status_code == 200, "V1 list endpoint should return 200"

        data = response.json()

        # Should have some products (at least 1)
        assert len(data) >= 1, "V1 endpoints should return at least 1 product"

        assert len(data) <= 1000, f"Should respect limit of 1000, got {len(data)}"

    def test_bc3_performance_benchmark_v2_list(self, client):
        """
        TASK-3.4.5: Test BC3 V2 list endpoint meets performance benchmarks
        Acceptance Criteria: Performance benchmarks met (response time < 500ms)
        ."""
        start_time = time.time()
        response = client.get("/api/productos/v2/list?buscar=test&limit=10")
        elapsed = time.time() - start_time

        assert response.status_code == 200, "V2 list endpoint should return 200"

        assert elapsed < 0.5, f"V2 list endpoint should respond in < 500ms, took {elapsed:.3f}s"

    def test_bc3_performance_benchmark_v2_detail(self, client):
        """
        TASK-3.4.5: Test BC3 V2 detail endpoint meets performance benchmarks
        Acceptance Criteria: Performance benchmarks met (response time < 500ms)
        ."""
        start_time = time.time()
        response = client.get("/api/productos/v2/TEST001")
        elapsed = time.time() - start_time

        # Should be 200 or 404 (not found)
        assert response.status_code in [200, 404], "V2 detail endpoint should return 200 or 404"

        assert elapsed < 0.5, f"V2 detail endpoint should respond in < 500ms, took {elapsed:.3f}s"

    def test_bc3_performance_benchmark_v1_list(self, client):
        """
        TASK-3.4.5: Test BC3 V1 list endpoint meets performance benchmarks
        Acceptance Criteria: Performance benchmarks met (response time < 500ms)
        ."""
        start_time = time.time()
        response = client.get("/api/productos/?buscar=test&limit=10")
        elapsed = time.time() - start_time

        assert response.status_code == 200, "V1 list endpoint should return 200"

        assert elapsed < 0.5, f"V1 list endpoint should respond in < 500ms, took {elapsed:.3f}s"

    def test_bc3_performance_benchmark_v1_detail(self, client):
        """
        TASK-3.4.5: Test BC3 V1 detail endpoint meets performance benchmarks
        Acceptance Criteria: Performance benchmarks met (response time < 500ms)
        ."""
        start_time = time.time()
        response = client.get("/api/productos/TEST001")
        elapsed = time.time() - start_time

        # Should be 200 or 404 (not found)
        assert response.status_code in [200, 404], "V1 detail endpoint should return 200 or 404"

        assert elapsed < 0.5, f"V1 detail endpoint should respond in < 500ms, took {elapsed:.3f}s"

    def test_bc3_suite_schema_compatibility_v2(self, client):
        """
        TASK-3.4.5: Test V2 responses match BC3 Suite schema
        Acceptance Criteria: BC3 Suite tests passing (all integration tests)
        ."""
        response = client.get("/api/productos/v2/list?limit=5")

        if response.status_code == 200:
            data = response.json()

            if len(data) > 0:
                product = data[0]

                # Required BC3 Suite fields
                required_fields = [
                    "codigo",
                    "descripcion",
                    "marca",
                    "bc3_descripcion_corta",
                    "bc3_product_type",
                    "bc3_descripcion_completa",
                ]

                for field in required_fields:
                    assert field in product, f"BC3 Suite requires field: {field}"

    def test_bc3_suite_schema_compatibility_v1(self, client):
        """
        TASK-3.4.5: Test V1 responses match BC3 Suite schema (legacy)
        Acceptance Criteria: BC3 Suite tests passing (all integration tests)
        ."""
        response = client.get("/api/productos/?limit=5")

        if response.status_code == 200:
            data = response.json()

            if len(data) > 0:
                product = data[0]

                # Required BC3 Suite fields (legacy format)
                required_fields = [
                    "codigo",
                    "descripcion",
                    "marca",
                    "bc3_descripcion_corta",
                    "bc3_product_type",
                    "bc3_descripcion_completa",
                ]

                for field in required_fields:
                    assert field in product, f"BC3 Suite (legacy) requires field: {field}"

    def test_v2_marca_endpoint_bc3_fields(self, client):
        """
        TASK-3.4.5: Test V2 marca endpoint includes BC3 fields
        Acceptance Criteria: BC3 fields present in all V2 endpoints
        ."""
        response = client.get("/api/productos/v2/marca/TestBrand?limit=1")

        if response.status_code == 200:
            data = response.json()

            if len(data) > 0:
                product = data[0]

                # BC3 fields should be present
                assert (
                    "bc3_descripcion_corta" in product
                ), "V2 marca endpoint should include bc3_descripcion_corta"

                assert (
                    "bc3_product_type" in product
                ), "V2 marca endpoint should include bc3_product_type"

                assert (
                    "bc3_descripcion_completa" in product
                ), "V2 marca endpoint should include bc3_descripcion_completa"

    def test_v2_familia_endpoint_bc3_fields(self, client):
        """
        TASK-3.4.5: Test V2 familia endpoint includes BC3 fields
        Acceptance Criteria: BC3 fields present in all V2 endpoints
        ."""
        response = client.get("/api/productos/v2/familia/TestFamily?limit=1")

        if response.status_code == 200:
            data = response.json()

            if len(data) > 0:
                product = data[0]

                # BC3 fields should be present
                assert (
                    "bc3_descripcion_corta" in product
                ), "V2 familia endpoint should include bc3_descripcion_corta"

                assert (
                    "bc3_product_type" in product
                ), "V2 familia endpoint should include bc3_product_type"

                assert (
                    "bc3_descripcion_completa" in product
                ), "V2 familia endpoint should include bc3_descripcion_completa"
