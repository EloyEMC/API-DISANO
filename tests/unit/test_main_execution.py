"""
Tests Unitarios - Main Module Execution (TDD + AAA + Settings import)
===========================================================

Tests que importan Settings y ejecutan código real de app/main.py.
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.
."""

import pytest
from pathlib import Path


def _route_paths(routes, prefix=""):
    """Return paths from routes, including FastAPI router include prefixes."""
    paths = []
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.append(f"{prefix}{path}")

        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            include_context = getattr(route, "include_context", None)
            nested_prefix = prefix + getattr(include_context, "prefix", "")
            paths.extend(_route_paths(original_router.routes, nested_prefix))
            continue

        nested_routes = getattr(route, "routes", None)
        if nested_routes is not None:
            paths.extend(_route_paths(nested_routes, prefix))
    return paths


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

    def test_main_module_composes_http_interfaces(self):
        """Verify main composes the current HTTP interface routers."""
        from app.interfaces.http import bc3, familias, productos
        import app.main as main

        assert main.productos_http is productos
        assert main.familias_http is familias
        assert main.bc3_http is bc3

        route_paths = set(_route_paths(main.app.routes))
        assert any(path.startswith("/api/productos") for path in route_paths)
        assert any(path.startswith("/api/familias") for path in route_paths)
        assert any(path.startswith("/api/bc3") for path in route_paths)

    def test_main_module_has_root_endpoint(self):
        """GREEN: Verificar que main.py tiene root endpoint."""
        # Arrange & Act
        from app.main import app

        # Assert - Verificar routes disponibles
        routes = _route_paths(app.routes)
        assert "/" in routes, f"Debe tener route root, tiene: {routes}"

    def test_main_module_has_health_endpoint(self):
        """GREEN: Verificar que main.py tiene health endpoint."""
        # Arrange & Act
        from app.main import app

        # Assert - Verificar routes disponibles
        routes = _route_paths(app.routes)
        assert (
            "/health" in routes or "/health_check" in routes
        ), f"Debe tener health endpoint, tiene: {routes}"


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
