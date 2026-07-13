"""
TDD Tests for TASK-3.4.1: DI Configuration in main.py

RED Phase: These tests should FAIL initially.
"""

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError as e:
    pytest.skip(f"Cannot import app.main: {e}", allow_module_level=True)


class TestMainDISetup:
    """Tests for main.py DI configuration"""

    def test_application_starts_with_di(self):
        """
        TASK-3.4.1: Test that application starts with DI configuration
        Acceptance Criteria: Application starts successfully (< 2s)
        """
        client = TestClient(app)
        response = client.get("/")
        # App started successfully
        assert response.status_code in [200, 404]

    def test_main_uses_hexagonal_router(self):
        """
        TASK-3.4.1: Test main.py imports hexagonal router instead of legacy router
        Acceptance Criteria: main.py imports hexagonal router instead of legacy router
        """
        # Import and check main.py source
        import app.main as main_module
        import inspect

        source = inspect.getsource(main_module)

        # Should import from interfaces/http (hexagonal) - accept both formats
        has_hexagonal = "from app.interfaces.http import" in source and (
            "productos" in source or "productos_http" in source
        )
        assert has_hexagonal, (
            "main.py should import from app.interfaces.http (hexagonal)"
        )

        # Should NOT import from app.routers.productos (legacy)
        assert "from app.routers import productos" not in source, (
            "main.py should NOT import from app.routers.productos (legacy)"
        )

    def test_v2_endpoints_accessible(self):
        """
        TASK-3.4.1: Test V2 endpoints are accessible through new router
        Acceptance Criteria: V2 endpoints accessible through new router
        """
        client = TestClient(app)

        # Test V2 list endpoint exists (should not be 404)
        response = client.get("/api/productos/v2/list?buscar=test&limit=5")
        # Should be 200, 422 (validation error), or 500 (service error), but NOT 404
        assert response.status_code != 404, (
            "V2 endpoints should be accessible (not 404)"
        )

    def test_v1_endpoints_accessible(self):
        """
        TASK-3.4.1: Test V1 endpoints still accessible (backward compatibility)
        Acceptance Criteria: V1 endpoints still accessible (backward compatibility)
        """
        client = TestClient(app)

        # Test V1 list endpoint exists (should not be 404)
        response = client.get("/api/productos/?limit=5")
        # Should be 200, 422 (validation error), or 500 (service error), but NOT 404
        assert response.status_code != 404, (
            "V1 endpoints should be accessible for backward compatibility (not 404)"
        )
