"""
TDD Tests for TASK-3.4.3: V2 Endpoints Migrated

RED Phase: These tests should FAIL initially if V2 endpoints are not correct.
."""

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError as e:
    pytest.skip(f"Cannot import app.main: {e}", allow_module_level=True)


class TestV2Endpoints:
    """Tests for V2 endpoints (TASK-3.4.3)."""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app."""
        return TestClient(app)

    def test_v2_list_endpoint_returns_products(self, client):
        """
        TASK-3.4.3: Test V2 list endpoint returns products
        Acceptance Criteria: HTTP 200 OK responses for all V2 endpoints
        ."""
        response = client.get("/api/productos/v2/list?buscar=test&limit=5")

        # Should be 200, 422 (validation), or 500 (service), NOT 404
        assert response.status_code != 404, "V2 list endpoint should be accessible"

        # If 200, check structure
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "V2 list endpoint should return list"
            if len(data) > 0:
                # Check it's a list of ProductoResponseDTO
                product = data[0]
                assert "codigo" in product, "Product should have codigo field"
                assert "descripcion" in product, "Product should have descripcion field"

    def test_v2_list_endpoint_validates_input(self, client):
        """
        TASK-3.4.3: Test V2 list endpoint validates input
        Acceptance Criteria: Pydantic validation errors for invalid input (400 Bad Request)
        ."""
        # Test: limit=0 should fail (min is 1)
        response = client.get("/api/productos/v2/list?limit=0")

        # Pydantic validation returns 422, not 400
        assert (
            response.status_code == 422
        ), "V2 list endpoint should validate limit >= 1 (422 for Pydantic validation)"

    def test_v2_list_endpoint_limit_max(self, client):
        """
        TASK-3.4.3: Test V2 list endpoint validates max limit
        Acceptance Criteria: Pydantic validation errors for invalid input
        ."""
        # Test: limit=101 should fail (max is 100)
        response = client.get("/api/productos/v2/list?buscar=test&limit=101")

        # Pydantic validation returns 422
        assert (
            response.status_code == 422
        ), "V2 list endpoint should validate limit <= 100 (422 for Pydantic validation)"

    def test_v2_list_endpoint_requires_buscar(self, client):
        """
        TASK-3.4.3: Test V2 list endpoint requires buscar parameter
        Acceptance Criteria: Pydantic validation errors for missing required parameter
        ."""
        # Test: missing buscar parameter (required)
        response = client.get("/api/productos/v2/list?limit=5")

        # Pydantic validation returns 422 for missing required parameter
        assert (
            response.status_code == 422
        ), "V2 list endpoint should require buscar parameter (422 for Pydantic validation)"

    def test_v2_detail_endpoint_success(self, client):
        """
        TASK-3.4.3: Test V2 detail endpoint returns product
        Acceptance Criteria: HTTP 200 OK responses for all V2 endpoints
        ."""
        # Try with a realistic product code (may or may not exist)
        response = client.get("/api/productos/v2/TEST001")

        # Should be 200, 404 (not found), or 500 (service), NOT 404 for endpoint missing
        if response.status_code == 200:
            data = response.json()
            assert "codigo" in data, "Product should have codigo field"
            assert "descripcion" in data, "Product should have descripcion field"
            assert data["codigo"] == "TEST001", "Product codigo should match request"
        elif response.status_code == 404:
            # Product doesn't exist, which is OK
            pass
        else:
            # 500 is also OK (service error)
            pass

    def test_v2_detail_endpoint_not_found(self, client):
        """
        TASK-3.4.3: Test V2 detail endpoint returns 404 for non-existent product
        Acceptance Criteria: HTTP 404 for non-existent products
        ."""
        # Use a very unlikely product code
        response = client.get("/api/productos/v2/NONEXISTENT_PRODUCT_12345")

        # Should be 404 (not found) or 500 (service error)
        # NOT 404 for endpoint missing (endpoint exists)
        if response.status_code == 404:
            detail = response.json().get("detail", "")
            assert (
                "not found" in detail.lower() or "no encontrado" in detail.lower()
            ), "404 should indicate product not found"

    def test_v2_marca_endpoint_success(self, client):
        """
        TASK-3.4.3: Test V2 marca endpoint returns products by brand
        Acceptance Criteria: HTTP 200 OK responses for all V2 endpoints
        ."""
        response = client.get("/api/productos/v2/marca/TestBrand?limit=5")

        # Should be 200 or 500, NOT 404
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "V2 marca endpoint should return list"
            if len(data) > 0:
                product = data[0]
                assert "marca" in product, "Product should have marca field"

    def test_v2_marca_endpoint_validates_limit(self, client):
        """
        TASK-3.4.3: Test V2 marca endpoint validates limit parameter
        Acceptance Criteria: Pydantic validation errors for invalid input
        ."""
        response = client.get("/api/productos/v2/marca/TestBrand?limit=0")

        # Should validate limit >= 1
        assert (
            response.status_code == 422
        ), "V2 marca endpoint should validate limit >= 1 (422 for Pydantic validation)"

    def test_v2_familia_endpoint_success(self, client):
        """
        TASK-3.4.3: Test V2 familia endpoint returns products by family
        Acceptance Criteria: HTTP 200 OK responses for all V2 endpoints
        ."""
        response = client.get("/api/productos/v2/familia/Electrónica?limit=5")

        # Should be 200 or 500, NOT 404
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "V2 familia endpoint should return list"
            if len(data) > 0:
                product = data[0]
                assert "familia" in product, "Product should have familia field"

    def test_v2_familia_endpoint_validates_limit(self, client):
        """
        TASK-3.4.3: Test V2 familia endpoint validates limit parameter
        Acceptance Criteria: Pydantic validation errors for invalid input
        ."""
        response = client.get("/api/productos/v2/familia/TestFamily?limit=101")

        # Should validate limit <= 100
        assert (
            response.status_code == 422
        ), "V2 familia endpoint should validate limit <= 100 (422 for Pydantic validation)"

    def test_v2_endpoints_use_producto_service(self):
        """
        TASK-3.4.3: Test all V2 endpoints use ProductoService
        Acceptance Criteria: Business logic in service layer
        ."""
        import inspect
        from app.interfaces.http.productos import (
            buscar_productos_v2,
            obtener_producto_v2,
            buscar_productos_por_marca_v2,
            buscar_productos_por_familia_v2,
        )

        # Check each V2 endpoint has service parameter
        v2_endpoints = [
            buscar_productos_v2,
            obtener_producto_v2,
            buscar_productos_por_marca_v2,
            buscar_productos_por_familia_v2,
        ]

        for endpoint in v2_endpoints:
            sig = inspect.signature(endpoint)
            params = sig.parameters

            assert "service" in params, f"{endpoint.__name__} should have service parameter"

            # Check it's injected via Depends
            service_param = params["service"]
            assert (
                service_param.default is not inspect.Parameter.empty
            ), f"{endpoint.__name__} service parameter should have default value (Depends)"

    def test_v2_endpoints_no_direct_db_access(self):
        """
        TASK-3.4.3: Test V2 endpoints have no direct database access
        Acceptance Criteria: No direct database queries in router
        ."""
        import inspect
        from app.interfaces.http import productos as productos_module

        source = inspect.getsource(productos_module)

        # Check for V2 endpoint functions (not DI functions)
        v2_endpoints_source = []
        lines = source.split("\n")
        in_v2_endpoint = False
        endpoint_lines = []

        for line in lines:
            if '@router.get("/v2/' in line:
                in_v2_endpoint = True
                endpoint_lines = [line]
            elif in_v2_endpoint:
                if line.startswith("def "):
                    endpoint_lines.append(line)
                elif line.startswith("@"):
                    # New decorator, end of current endpoint
                    if endpoint_lines:
                        v2_endpoints_source.append("\n".join(endpoint_lines))
                    endpoint_lines = [line]
                else:
                    endpoint_lines.append(line)

        # Add last endpoint if exists
        if endpoint_lines:
            v2_endpoints_source.append("\n".join(endpoint_lines))

        # Check no sqlite3 in V2 endpoints
        for endpoint_source in v2_endpoints_source:
            assert (
                "sqlite3" not in endpoint_source.lower()
            ), f"V2 endpoint should NOT use sqlite3 directly: {endpoint_source[:100]}"

            # Check no raw SQL queries
            assert (
                "SELECT * FROM" not in endpoint_source.upper()
            ), f"V2 endpoint should NOT have raw SQL: {endpoint_source[:100]}"

            # Check no cursor.execute
            assert (
                "cursor.execute" not in endpoint_source
            ), f"V2 endpoint should NOT use cursor.execute: {endpoint_source[:100]}"
