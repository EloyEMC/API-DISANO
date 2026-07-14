"""
Tests de correcciones Fase 1 - Bugs críticos
=============================================

Tests para verificar que los bugs críticos han sido corregidos.
."""

import pytest
from pathlib import Path
from fastapi import status


class TestRateLimitBugFixed:
    """Tests para verificar que el bug RATE_LIMIT ha sido corregido."""

    def test_rate_limit_variable_correctly_named(self):
        """Verificar que se usa 'rate_limit' no 'RATE_LIMIT'."""
        # Leer el archivo middleware.py
        middleware_path = Path(__file__).parent.parent.parent / "app" / "middleware.py"
        content = middleware_path.read_text()

        # Verificar que se usa 'rate_limit' (variable correcta)
        assert "rate_limit" in content

        # Verificar que no existe la variable incorrecta en contextos de headers
        assert '"X-RateLimit-Limit": str(RATE_LIMIT)' not in content

    def test_rate_limit_in_response_headers(self, client, mock_db_connection):
        """Verificar que rate_limit se usa en headers."""
        # Configurar mock para devolver producto
        mock_cursor = mock_db_connection.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = [0]

        # Test de rate limit headers
        response = client.get("/health")

        # No debería haber error de NameError: name 'RATE_LIMIT' is not defined
        assert response.status_code == status.HTTP_200_OK


class TestLegacyImportsMigrated:
    """Tests para verificar que los imports legacy han sido migrados."""

    def test_no_legacy_imports_in_routers(self):
        """Verificar que no hay imports legacy de app.security."""
        productos_path = (
            Path(__file__).parent.parent.parent / "app" / "routers" / "productos.py"
        )
        content = productos_path.read_text()

        # NO debería existir: from app.security import verify_admin_api_key
        assert "from app.security import verify_admin_api_key" not in content

        # DEBERÍA existir: from app.security.api_key import verify_admin_api_key
        assert "from app.security.api_key import verify_admin_api_key" in content

    def test_verify_admin_api_key_import_works(self):
        """Verificar que el import nuevo funciona correctamente."""
        try:
            from app.security.api_key import verify_admin_api_key

            assert callable(verify_admin_api_key)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestSecurityHeadersAdded:
    """Tests para verificar que los security headers han sido añadidos."""

    def test_content_security_policy_header_exists(self):
        """Verificar que CSP header existe."""
        middleware_path = Path(__file__).parent.parent.parent / "app" / "middleware.py"
        content = middleware_path.read_text()

        # Verificar que CSP header existe
        assert "Content-Security-Policy" in content

    def test_security_headers_present(self, client):
        """Verificar que los security headers están presentes en respuestas."""
        response = client.get("/health")

        # Verificar headers de seguridad
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers

        # Verificar valores
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"


class TestRequiredEnvVarsValidation:
    """Tests para verificar que las variables obligatorias se validan."""

    def test_secret_key_required_in_production(self):
        """Verificar que SECRET_KEY es obligatorio en producción."""
        from app.config import Settings

        # Test con SECRET_KEY vacío
        settings = Settings(environment="production", secret_key="")

        with pytest.raises(ValueError) as exc_info:
            settings.validate_required()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_api_keys_required_in_production(self):
        """Verificar que API_KEYS es obligatorio en producción."""
        from app.config import Settings

        # Test con API_KEYS vacíos
        settings = Settings(
            environment="production", secret_key="test-secret-32-chars!", api_keys=[]
        )

        with pytest.raises(ValueError) as exc_info:
            settings.validate_required()

        assert "API_KEYS" in str(exc_info.value)

    def test_no_validation_in_development(self):
        """Verificar que no hay validación en desarrollo."""
        from app.config import Settings

        # Test en desarrollo con valores vacíos
        settings = Settings(environment="development", secret_key="", api_keys=[])

        # No debería lanzar error
        settings.validate_required()  # Should not raise
