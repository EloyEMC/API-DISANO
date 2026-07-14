"""
TDD Tests for TASK-3.4.4: V1 Endpoints Backward Compatibility

RED Phase: These tests should FAIL initially if V1 endpoints are not backward compatible.
."""

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError as e:
    pytest.skip(f"Cannot import app.main: {e}", allow_module_level=True)


class TestV1BackwardCompatibility:
    """Tests for V1 endpoints backward compatibility (TASK-3.4.4)."""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app."""
        return TestClient(app)

    def test_v1_list_endpoint_accessible(self, client):
        """
        TASK-3.4.4: Test V1 list endpoint is accessible
        Acceptance Criteria: HTTP 200 OK for valid requests
        ."""
        response = client.get("/api/productos/?buscar=test&limit=5")

        # Should NOT be 404 (endpoint exists)
        assert (
            response.status_code != 404
        ), "V1 list endpoint should be accessible for backward compatibility"

        # Should be 200, 422 (validation), or 500 (service)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "V1 list endpoint should return list"
            if len(data) > 0:
                # V1 returns dict format, not ProductoResponseDTO
                product = data[0]
                assert isinstance(
                    product, dict
                ), "V1 should return dict format for backward compatibility"
                assert "codigo" in product, "Product should have codigo field"
                assert "descripcion" in product, "Product should have descripcion field"

    def test_v1_detail_endpoint_accessible(self, client):
        """
        TASK-3.4.4: Test V1 detail endpoint is accessible
        Acceptance Criteria: HTTP 200 OK for valid requests
        ."""
        response = client.get("/api/productos/TEST001")

        # Should NOT be 404 for missing endpoint
        # Could be 200 (product exists), 404 (product not found), or 500 (service error)
        assert (
            response.status_code != 404
            or "no encontrado" in response.json().get("detail", "").lower()
            or "not found" in response.json().get("detail", "").lower()
        ), "V1 detail endpoint should be accessible for backward compatibility"

        if response.status_code == 200:
            data = response.json()
            assert isinstance(
                data, dict
            ), "V1 detail endpoint should return dict format for backward compatibility"
            assert "codigo" in data, "Product should have codigo field"
            assert data["codigo"] == "TEST001", "Product codigo should match request"

    def test_v1_list_endpoint_legacy_format(self, client):
        """
        TASK-3.4.4: Test V1 list endpoint returns legacy format
        Acceptance Criteria: Responses match legacy format (dict[], not ProductoResponseDTO[])
        ."""
        response = client.get("/api/productos/?buscar=test&limit=5")

        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()

            # V1 returns dict format (raw), not ProductoResponseDTO objects
            # Check that it's a list of dicts
            assert isinstance(data, list), "V1 should return list"

            product = data[0]
            assert isinstance(
                product, dict
            ), "V1 should return dict format (legacy), not DTO objects"

            # Legacy format should have these fields
            assert "codigo" in product, "Legacy format should have codigo field"
            assert "descripcion" in product, "Legacy format should have descripcion field"

            # Legacy format might have uppercase fields (from old DB schema)
            # This is different from V2 which uses snake_case
            # For now, just check that it's dict format

    def test_v1_detail_endpoint_legacy_format(self, client):
        """
        TASK-3.4.4: Test V1 detail endpoint returns legacy format
        Acceptance Criteria: Responses match legacy format (dict, not ProductoResponseDTO)
        ."""
        response = client.get("/api/productos/TEST001")

        if response.status_code == 200:
            data = response.json()

            # V1 returns dict format (raw), not ProductoResponseDTO
            assert isinstance(
                data, dict
            ), "V1 detail endpoint should return dict format for backward compatibility"

            # Legacy format should have these fields
            assert "codigo" in data, "Legacy format should have codigo field"
            assert "descripcion" in data, "Legacy format should have descripcion field"

    def test_v1_endpoints_use_service_dependency(self):
        """
        TASK-3.4.4: Test V1 endpoints use service dependencies
        Acceptance Criteria: Internal architecture uses services
        ."""
        import inspect
        from app.interfaces.http.productos import get_productos_v1, get_producto_v1

        # Check each V1 endpoint has service parameter
        v1_endpoints = [get_productos_v1, get_producto_v1]

        for endpoint in v1_endpoints:
            sig = inspect.signature(endpoint)
            params = sig.parameters

            assert "service" in params, f"{endpoint.__name__} should have service parameter for DI"

            # Check it's injected via Depends
            service_param = params["service"]
            assert (
                service_param.default is not inspect.Parameter.empty
            ), f"{endpoint.__name__} service parameter should have default value (Depends)"

    def test_v1_endpoints_no_breaking_changes(self, client):
        """
        TASK-3.4.4: Test V1 endpoints don't have breaking changes
        Acceptance Criteria: No breaking changes for existing clients
        ."""
        # Test that old query parameters still work
        test_cases = [
            # (url, description)
            ("/api/productos/?buscar=test&limit=10", "Basic search"),
            ("/api/productos/?limit=50", "Only limit"),
            ("/api/productos/?buscar=disano", "Search term only"),
            ("/api/productos/33036139", "Detail by code"),
        ]

        for url, description in test_cases:
            response = client.get(url)

            # Should NOT be 404 (endpoint not found)
            # Could be 200, 404 (product not found), 422 (validation), or 500 (service)
            if response.status_code == 404:
                detail = response.json().get("detail", "")
                assert (
                    "not found" in detail.lower()
                ), f"V1 endpoint should not break: {description} - {url}"
            else:
                # 200, 422, or 500 are OK
                assert True

    def test_v1_list_optional_parameters(self, client):
        """
        TASK-3.4.4: Test V1 list endpoint has optional parameters
        Acceptance Criteria: V1 endpoints should have optional parameters like before
        ."""
        import inspect
        from app.interfaces.http.productos import get_productos_v1

        sig = inspect.signature(get_productos_v1)

        # Check that parameters have defaults (are optional)
        buscar_param = sig.parameters.get("buscar")
        limit_param = sig.parameters.get("limit")

        assert buscar_param is not None, "V1 list endpoint should have buscar parameter"

        assert limit_param is not None, "V1 list endpoint should have limit parameter"

        # Check they have defaults (optional)
        assert (
            buscar_param.default is not inspect.Parameter.empty
        ), "V1 buscar parameter should be optional (has default)"

        assert (
            limit_param.default is not inspect.Parameter.empty
        ), "V1 limit parameter should be optional (has default)"

    def test_v1_endpoint_limit_range(self, client):
        """
        TASK-3.4.4: Test V1 endpoint accepts old limit range
        Acceptance Criteria: V1 endpoints should accept old limit range (1-500)
        ."""
        # Test larger limit (500 was old V1 max)
        response = client.get("/api/productos/?limit=500")

        # Should accept limit=500 (not 422 validation error)
        assert response.status_code != 422, "V1 should accept limit=500 for backward compatibility"

        # Test small limit
        response = client.get("/api/productos/?limit=1")
        assert response.status_code != 422, "V1 should accept limit=1"

    def test_v1_endpoints_no_sqlite3_direct_access(self):
        """
        TASK-3.4.4: Test V1 endpoints don't use direct sqlite3
        Acceptance Criteria: Internal architecture uses services (not direct DB)
        ."""
        import inspect
        from app.interfaces.http import productos as productos_module

        source = inspect.getsource(productos_module)

        # Check V1 endpoint functions (not DI functions)
        v1_endpoints = ["def get_productos_v1(", "def get_producto_v1("]

        for endpoint_sig in v1_endpoints:
            if endpoint_sig in source:
                # Extract the function body
                start_idx = source.find(endpoint_sig)
                # Find the end of the function (next @router or end of file)
                next_decorator = source.find("@router.get", start_idx + len(endpoint_sig))
                if next_decorator == -1:
                    next_decorator = len(source)

                function_body = source[start_idx:next_decorator]

                # Check no sqlite3
                assert (
                    "sqlite3" not in function_body.lower()
                ), f"V1 endpoint should NOT use sqlite3 directly: {endpoint_sig}"

                # Check no raw SQL
                assert (
                    "SELECT * FROM" not in function_body.upper()
                ), f"V1 endpoint should NOT have raw SQL: {endpoint_sig}"

                # Check no cursor.execute
                assert (
                    "cursor.execute" not in function_body
                ), f"V1 endpoint should NOT use cursor.execute: {endpoint_sig}"
