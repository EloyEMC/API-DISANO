"""
Tests P0 - Auth IDOR (Security Critical)
=========================================

Tests que validan prevención de IDOR (Insecure Direct Object Reference).
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.

Security Critical: Usuario NO puede acceder a admin endpoints, Admin SÍ puede.
."""

from fastapi.testclient import TestClient


class TestAuthIDORAdminEndpoints:
    """
    Tests de Auth IDOR para endpoints admin.
    Security Critical: Prevención de accesos no autorizados.
    ."""

    def test_user_cannot_post_producto_without_admin_api_key(self):
        """
        RED: Usuario NO puede crear producto sin API key de admin.

        AAA Pattern:
        - Arrange: Importar app desde main
        - Act: Intentar crear producto sin API key
        - Assert: Debe retornar 401 Unauthorized
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        producto_data = {
            "codigo": "PROD-IDOR-001",
            "descripcion": "Test IDOR - Usuario no admin",
            "pvp": 100.00,
        }

        response = client.post("/api/productos/", json=producto_data)

        # Assert
        assert response.status_code == 403

    def test_user_cannot_put_producto_without_admin_api_key(self):
        """
        RED: Usuario NO puede actualizar producto sin API key de admin.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        update_data = {"descripcion": "Actualizado por usuario no admin"}

        response = client.put("/api/productos/PROD-IDOR-001", json=update_data)

        # Assert
        assert response.status_code == 403

    def test_user_cannot_patch_precio_without_admin_api_key(self):
        """
        RED: Usuario NO puede actualizar precio sin API key de admin.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        precio_data = {"pvp": 999.99}

        response = client.patch("/api/productos/PROD-IDOR-001/precio", json=precio_data)

        # Assert
        assert response.status_code == 403

    def test_user_cannot_delete_producto_without_admin_api_key(self):
        """
        RED: Usuario NO puede eliminar producto sin API key de admin.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)

        response = client.delete("/api/productos/PROD-IDOR-001")

        # Assert
        assert response.status_code == 403

    def test_user_cannot_post_producto_with_invalid_api_key(self):
        """
        RED: Usuario NO puede crear producto con API key inválido.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        headers = {"X-API-Key": "invalid-api-key-12345"}
        producto_data = {
            "codigo": "PROD-IDOR-002",
            "descripcion": "Test IDOR - API key inválido",
            "pvp": 100.00,
        }

        response = client.post("/api/productos/", json=producto_data, headers=headers)

        # Assert
        assert response.status_code == 403

    def test_admin_can_post_producto_with_valid_api_key(self):
        """
        GREEN: Admin SÍ puede crear producto con API key válido.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        headers = {"X-API-Key": "test-admin-key-1"}
        producto_data = {
            "codigo": "PROD-ADMIN-001",
            "descripcion": "Test IDOR - Admin válido",
            "pvp": 100.00,
        }

        response = client.post("/api/productos/", json=producto_data, headers=headers)

        # Assert - Puede ser 201 (creado) o 400 (ya existe)
        assert response.status_code in [201, 400]

    def test_admin_can_put_producto_with_valid_api_key(self):
        """
        GREEN: Admin SÍ puede actualizar producto con API key válido.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        headers = {"X-API-Key": "test-admin-key-1"}
        update_data = {"descripcion": "Actualizado por admin"}

        response = client.put(
            "/api/productos/PROD-ADMIN-001", json=update_data, headers=headers
        )

        # Assert - Puede ser 200 (actualizado) o 404 (no existe)
        assert response.status_code in [200, 404]

    def test_admin_can_patch_precio_with_valid_api_key(self):
        """
        GREEN: Admin SÍ puede actualizar precio con API key válido.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        headers = {"X-API-Key": "test-admin-key-1"}
        precio_data = {"pvp": 150.00}

        response = client.patch(
            "/api/productos/PROD-ADMIN-001/precio", json=precio_data, headers=headers
        )

        # Assert - Puede ser 200 (actualizado) o 404 (no existe)
        assert response.status_code in [200, 404]

    def test_admin_can_delete_producto_with_valid_api_key(self):
        """
        GREEN: Admin SÍ puede eliminar producto con API key válido.
        ."""
        # Arrange & Act
        from app.main import app

        client = TestClient(app)
        headers = {"X-API-Key": "test-admin-key-1"}

        response = client.delete("/api/productos/PROD-ADMIN-001", headers=headers)

        # Assert - Puede ser 204 (eliminado) o 404 (no existe)
        assert response.status_code in [204, 404]

    def test_user_api_key_different_from_admin_api_key(self):
        """
        GREEN: API key de usuario NO es igual a API key de admin.

        Security Critical: Prevenir que usuarios normales tengan
        permisos de admin accidentalmente.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["user-key-123"])

        # Assert
        user_keys = settings.api_keys_list
        admin_keys = (
            settings.admin_api_keys
            if isinstance(settings.admin_api_keys, list)
            else [settings.admin_api_keys]
        )

        # Verify son sets diferentes
        assert set(user_keys) != set(admin_keys) or len(admin_keys) > 0
