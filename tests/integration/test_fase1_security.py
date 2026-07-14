"""
Tests de Seguridad Integración - Fase 1
======================================

Tests de seguridad para verificar que las mejoras de Fase 1 funcionan correctamente.
."""

import pytest


class TestAdminEndpointsRequireAdminKey:
    """Tests para verificar que los endpoints admin requieren admin key."""

    def test_create_producto_requires_admin_key(self, client, mock_db_connection):
        """Verificar que POST /api/admin/productos requiere admin key."""
        # Configurar mock
        mock_cursor = mock_db_connection.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = [0]  # Código no existe

        response = client.post(
            "/api/admin/productos",
            json={"codigo": "12345678", "descripcion": "Test producto", "pvp": 19.99},
            headers={"X-API-Key": "regular-api-key"},  # Regular key, not admin
        )

        # Debería dar 403 Forbidden (requires admin key)
        assert response.status_code == 403

    def test_create_producto_with_admin_key(
        self, client, mock_db_connection, admin_headers
    ):
        """Verificar que POST /api/admin/productos funciona con admin key."""
        # Configurar mock
        mock_cursor = mock_db_connection.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = [0]  # Código no existe

        response = client.post(
            "/api/admin/productos",
            json={"codigo": "12345678", "descripcion": "Test producto", "pvp": 19.99},
            headers=admin_headers,
        )

        # No debería ser 403 (admin key es válida)
        # Puede ser 201 (creado) o error de base de datos, pero no 403
        assert response.status_code != 403

    def test_delete_producto_requires_admin_key(self, client, mock_db_connection):
        """Verificar que DELETE /api/admin/productos/{codigo} requiere admin key."""
        # Configurar mock
        mock_cursor = mock_db_connection.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = [1]  # Producto existe

        response = client.delete(
            "/api/admin/productos/12345678",
            headers={"X-API-Key": "regular-api-key"},  # Regular key, not admin
        )

        # Debería dar 403 Forbidden
        assert response.status_code == 403


class TestSecurityHeadersInProduction:
    """Tests para verificar que los security headers están presentes."""

    def test_security_headers_in_production(self, client):
        """Verificar que todos los security headers están presentes."""
        response = client.get("/health")

        # Headers obligatorios según BC3-Suite
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

        # Verificar valores correctos
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "1; mode=block" in response.headers["X-XSS-Protection"]
        assert "default-src" in response.headers["Content-Security-Policy"]


class TestRateLimitingNotBroken:
    """Tests para verificar que rate limiting no tiene el bug NAMEERROR."""

    def test_health_check_no_rate_limit_error(self, client):
        """Verificar que health check no lanza NameError."""
        response = client.get("/health")

        # Debería funcionar sin NameError: name 'RATE_LIMIT' is not defined
        assert response.status_code == 200

    def test_multiple_requests_work(self, client):
        """Verificar que múltiples requests no rompen el servidor."""
        # Varios requests consecutivos
        responses = [client.get("/health") for _ in range(5)]

        # Todos deberían funcionar sin NameError
        for response in responses:
            assert response.status_code == 200


class TestConfigValidationInProduction:
    """Tests para verificar que la configuración se valida correctamente."""

    def test_production_requires_secret_key(self):
        """Verificar que en producción se requiere SECRET_KEY."""
        from app.config import Settings

        with pytest.raises(ValueError) as exc_info:
            Settings(environment="production", secret_key="").validate_required()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_production_requires_api_keys(self):
        """Verificar que en producción se requieren API_KEYS."""
        from app.config import Settings

        with pytest.raises(ValueError) as exc_info:
            Settings(
                environment="production",
                secret_key="test-secret-32-chars!",
                api_keys=[],
            ).validate_required()

        assert "API_KEYS" in str(exc_info.value)

    def test_development_allows_empty_vars(self):
        """Verificar que en desarrollo se permiten variables vacías."""
        from app.config import Settings

        # No debería lanzar error en desarrollo
        settings = Settings(environment="development", secret_key="", api_keys=[])
        settings.validate_required()  # Should not raise


class TestNoLegacySecurityImports:
    """Tests para verificar que no hay imports legacy."""

    def test_no_legacy_verify_admin_import(self):
        """Verificar que no hay import legacy de verify_admin_api_key."""
        from app.routers import productos

        # Verificar que el módulo no tiene el import legacy
        import inspect

        source = inspect.getsource(productos)

        assert "from app.security import verify_admin_api_key" not in source

    def test_new_verify_admin_import_exists(self):
        """Verificar que existe el import nuevo."""
        from app.routers import productos

        # Verificar que el módulo tiene el import nuevo
        import inspect

        source = inspect.getsource(productos)

        assert "from app.security.api_key import verify_admin_api_key" in source


class TestOTPSecurityIntegration:
    """Tests de integración para seguridad OTP."""

    def test_otp_service_exists(self):
        """Verificar que el servicio OTP está disponible."""
        from app.security.otp_service import otp_service

        assert otp_service is not None
        assert callable(otp_service.generate_otp)
        assert callable(otp_service.verify_otp)

    def test_otp_generates_valid_codes(self):
        """Verificar que el servicio genera OTPs válidos."""
        from app.security.otp_service import otp_service

        otp = otp_service.generate_otp("test@example.com")

        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_verifies_correctly(self):
        """Verificar que el servicio verifica OTPs correctamente."""
        from app.security.otp_service import otp_service

        otp = otp_service.generate_otp("test@example.com")
        is_valid, error = otp_service.verify_otp("test@example.com", otp)

        assert is_valid is True
        assert error is None


class TestLoggingConfiguration:
    """Tests para verificar que el logging está configurado."""

    def test_logging_setup_exists(self):
        """Verificar que setup_logging existe."""
        from app.security.logging_config import setup_logging

        assert setup_logging is not None
        assert callable(setup_logging)

    def test_main_calls_setup_logging(self):
        """Verificar que main.py llama a setup_logging."""
        from app import main

        # Verificar que main.py llama a setup_logging
        import inspect

        source = inspect.getsource(main)

        assert (
            "setup_logging()" in source
            or "from app.security.logging_config import setup_logging" in source
        )


class TestEnvironmentFileTemplate:
    """Tests para verificar que existe el template de .env.production."""

    def test_env_production_template_exists(self):
        """Verificar que existe el archivo .env.production.example."""
        from pathlib import Path

        env_template = Path(__file__).parent.parent.parent / ".env.production.example"

        # El archivo debería existir después de Fase 1
        # Si no existe, creamos un test que falle para recordarnos
        assert env_template.exists(), (
            ".env.production.example no existe - crear plantilla"
        )

    def test_env_production_template_has_required_vars(self):
        """Verificar que el template tiene las variables requeridas."""
        from pathlib import Path

        env_template = Path(__file__).parent.parent.parent / ".env.production.example"
        content = env_template.read_text()

        # Variables requeridas
        required_vars = [
            "SECRET_KEY=",
            "API_KEYS=",
            "ADMIN_API_KEYS=",
            "ENVIRONMENT=production",
            "REDIS_HOST=",
            "DATABASE_URL=postgresql://",
            "MAIL_SERVER=",
            "OTP_2FA_ENABLED=true",
        ]

        for var in required_vars:
            assert var in content, (
                f"Variable requerida {var} no encontrada en .env.production.example"
            )
