"""
Tests Unitarios - Main Module Execution (TDD + AAA + Settings import)
===========================================================

Tests que importan Settings y ejecutan código real de app/main.py.
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.
."""

import pytest
from pathlib import Path


class TestMainModuleWithSettings:
    """Tests que importan Settings con main.py (TDD)."""

    def test_main_module_import_with_settings(self):
        """
        AAA: Arrange (import), Act (import), Assert (validation)
        """
        # Arrange & Act - Importar main con Settings
        try:
            from app.main import app

            # Assert - Verificar que app es FastAPI instance
            assert hasattr(app, "router")
            assert hasattr(app, "add_middleware")
        except ImportError as e:
            pytest.fail(f"Error importando app.main con Settings: {e}")

    def test_main_module_has_fastapi_app(self):
        """GREEN: Verificar que main.py crea FastAPI app."""
        # Arrange & Act
        from app.main import app

        # Assert
        from fastapi import FastAPI

        assert isinstance(app, FastAPI)

    def test_main_module_has_router_attribute(self):
        """GREEN: Verificar que app tiene router."""
        # Arrange & Act
        import app.main as main

        # Assert
        assert hasattr(main, "router")

    def test_main_module_has_root_endpoint(self):
        """GREEN: Verificar que main.py tiene root endpoint."""
        # Arrange & Act
        from app.main import app

        # Assert - Verificar routes disponibles
        routes = [route.path for route in app.routes]
        assert "/" in routes, f"Debe tener route root, tiene: {routes}"

    def test_main_module_has_health_endpoint(self):
        """GREEN: Verificar que main.py tiene health endpoint."""
        # Arrange & Act
        from app.main import app

        # Assert - Verificar routes disponibles
        routes = [route.path for route in app.routes]
        assert "/health" in routes or "/health_check" in routes, (
            f"Debe tener health endpoint, tiene: {routes}"
        )


class TestMainModuleCORSConfiguration:
    """Tests que verifican configuración CORS en main.py (TDD)."""

    def test_main_module_imports_cors(self):
        """GREEN: Verificar que main.py importa CORS middleware."""
        # Arrange
        from pathlib import Path

        content = Path("app/main.py").read_text()

        # Assert
        assert "CORSMiddleware" in content

    def test_main_module_has_cors_config(self):
        """GREEN: Verificar que main.py configura CORS."""
        # Arrange
        content = Path("app/main.py").read_text()

        # Assert - Verificar configuración CORS
        assert "add_middleware" in content
        assert "CORSMiddleware" in content


if __name__ == "__main__":
    pytest.main([__file__])
