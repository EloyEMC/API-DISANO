"""
Tests P0 - Auth IDOR (Security Critical)
=========================================

Tests que validan prevención de IDOR (Insecure Direct Object Reference).
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.

Security Critical: Usuario NO puede acceder a admin endpoints, Admin SÍ puede.
."""

from contextlib import contextmanager
from importlib import import_module
from typing import Any, Iterator, cast
from unittest.mock import Mock

from fastapi.testclient import TestClient


def _client() -> TestClient:
    """Build a client without pulling application internals into test typing."""
    app_module = import_module("app.main")
    return TestClient(cast(Any, app_module.app))


@contextmanager
def _client_with_producto_service(service: Mock) -> Iterator[TestClient]:
    """Build a client with persistence isolated from authentication checks."""
    app_module = import_module("app.main")
    productos_module = import_module("app.interfaces.http.productos")
    app = cast(Any, app_module.app)
    dependency = productos_module.get_producto_service
    app.dependency_overrides[dependency] = lambda: service
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(dependency, None)


class TestAuthIDORAdminEndpoints:
    """
    Tests de Auth IDOR para endpoints admin.
    Security Critical: Prevención de accesos no autorizados.
    """

    def test_user_cannot_post_producto_without_admin_api_key(self) -> None:
        """
        RED: Usuario NO puede crear producto sin API key de admin.

        AAA Pattern:
        - Arrange: Importar app desde main
        - Act: Intentar crear producto sin API key
        - Assert: Debe retornar 403 Forbidden
        ."""
        # Arrange & Act
        client = _client()
        producto_data = {
            "codigo": "PROD-IDOR-001",
            "descripcion": "Test IDOR - Usuario no admin",
            "pvp": 100.00,
        }

        response = client.post("/api/admin/productos", json=producto_data)

        # Assert
        assert response.status_code == 403

    def test_user_cannot_delete_producto_without_admin_api_key(self) -> None:
        """
        RED: Usuario NO puede eliminar producto sin API key de admin.
        ."""
        # Arrange & Act
        client = _client()

        response = client.delete("/api/admin/productos/PROD-IDOR-001")

        # Assert
        assert response.status_code == 403

    def test_user_cannot_post_producto_with_invalid_api_key(self) -> None:
        """
        RED: Usuario NO puede crear producto con API key inválido.
        ."""
        # Arrange & Act
        client = _client()
        headers = {"X-Admin-API-Key": "invalid-api-key-placeholder"}
        producto_data = {
            "codigo": "PROD-IDOR-002",
            "descripcion": "Test IDOR - API key inválido",
            "pvp": 100.00,
        }

        response = client.post("/api/admin/productos", json=producto_data, headers=headers)

        # Assert
        assert response.status_code == 403

    def test_admin_can_post_producto_with_valid_api_key(self) -> None:
        """
        GREEN: Admin SÍ puede crear producto con API key válido.
        ."""
        # Arrange & Act
        headers = {"X-Admin-API-Key": "admin"}
        producto_data = {
            "codigo": "PROD-ADMIN-001",
            "descripcion": "Test IDOR - Admin válido",
            "pvp": 100.00,
        }
        service = Mock()
        service.crear_producto.return_value.model_dump.return_value = producto_data

        with _client_with_producto_service(service) as client:
            response = client.post("/api/admin/productos", json=producto_data, headers=headers)

        # Assert
        assert response.status_code == 201
        service.crear_producto.assert_called_once()

    def test_admin_can_delete_producto_with_valid_api_key(self) -> None:
        """
        GREEN: Admin SÍ puede eliminar producto con API key válido.
        ."""
        # Arrange & Act
        headers = {"X-Admin-API-Key": "admin"}
        service = Mock()
        service.eliminar_producto.return_value = True

        with _client_with_producto_service(service) as client:
            response = client.delete("/api/admin/productos/PROD-ADMIN-001", headers=headers)

        # Assert
        assert response.status_code == 200
        service.eliminar_producto.assert_called_once_with("PROD-ADMIN-001")

    def test_user_api_key_different_from_admin_api_key(self) -> None:
        """
        GREEN: API key de usuario NO es igual a API key de admin.

        Security Critical: Prevenir que usuarios normales tengan
        permisos de admin accidentalmente.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(
            secret_key="test-secret-key",
            api_keys=["test-user-api-key-placeholder"],
            admin_api_keys=["admin"],
        )

        # Assert
        user_keys = settings.api_keys_list
        admin_keys = (
            settings.admin_api_keys
            if isinstance(settings.admin_api_keys, list)
            else [settings.admin_api_keys]
        )

        assert admin_keys == ["admin"]
        assert set(user_keys).isdisjoint(admin_keys)
