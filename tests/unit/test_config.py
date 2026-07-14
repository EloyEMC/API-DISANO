"""
Tests Unitarios - Fase 2 (Simplificado)
=======================================

Tests unitarios simplificados para verificar lógica básica.
."""

import pytest
from app.config import get_settings
from app.security.otp_service import OTPService
from app.middleware_redis import RedisRateLimitMiddleware


class TestConfigValidation:
    """Tests para validación de configuración."""

    def test_secret_key_required_in_production(self):
        """Verificar que SECRET_KEY es obligatorio en producción."""
        settings = Settings(
            environment="production",
            secret_key="",  # Vacío
            api_keys=["test-key"],
        )

        with pytest.raises(ValueError):
            settings.validate_required()

    def test_api_keys_required_in_production(self):
        """Verificar que API_KEYS es obligatorio en producción."""
        settings = Settings(
            environment="production",
            secret_key="test-secret-32-chars!",
            api_keys=[],  # Vacío
        )

        with pytest.raises(ValueError):
            settings.validate_required()

    def test_no_validation_in_development(self):
        """Verificar que no hay validación en desarrollo."""
        settings = Settings(
            environment="development",
            secret_key="",  # Vacío OK en desarrollo
            api_keys=[],  # Vacío OK en desarrollo
        )

        # No debería lanzar error
        settings.validate_required()

    def test_get_settings_singleton(self):
        """Verificar que get_settings es singleton (cache)."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_parse_api_keys_string(self):
        """Verificar parseo de API_KEYS como string."""
        settings = Settings(environment="development", api_keys="key1,key2,key3")

        assert settings.api_keys_list == ["key1", "key2", "key3"]

    def test_parse_api_keys_list(self):
        """Verificar que API_KEYS como lista funciona."""
        settings = Settings(
            environment="development", api_keys=["key1", "key2", "key3"]
        )

        assert settings.api_keys_list == ["key1", "key2", "key3"]

    def test_is_production_detection(self):
        """Verificar detección de entorno."""
        settings_dev = Settings(environment="development")
        settings_prod = Settings(environment="production")

        assert settings_dev.is_production() is False
        assert settings_prod.is_production() is True


class TestOTPService:
    """Tests para el servicio OTP."""

    def test_otp_generates_valid_code(self):
        """Verificar que OTP generado es válido (6 dígitos)."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)

        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_invalid_email_raises_error(self):
        """Verificar que email inválido lanza ValueError."""
        otp_service = OTPService()

        with pytest.raises(ValueError):
            otp_service.generate_otp("invalid-email")

    def test_otp_constants(self):
        """Verificar constantes del servicio OTP."""
        otp_service = OTPService()

        assert otp_service.otp_expiry_minutes == 10
        assert otp_service.max_attempts == 3
        assert otp_service.otp_length == 6

    def test_otp_status_returns_metadata(self):
        """Verificar que get_otp_status retorna metadatos correctos."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)
        status = otp_service.get_otp_status(email)

        assert status is not None
        assert status["email"] == email
        assert "attempts" in status
        assert "expiry" in status
        assert "verified" in status
        assert "expired" in status

    def test_otp_expired_fails_verification(self):
        """Verificar que OTP expirado falla verificación."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)

        # Forzar expiración
        otp_service.otp_store[email]["expiry"] = datetime.now() - timedelta(minutes=1)

        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert "expired" in error.lower()

    def test_otp_max_attempts_blocks_verification(self):
        """Verificar que máximo intentos bloquea verificación."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)

        # 3 intentos fallidos
        for _ in range(3):
            is_valid, _ = otp_service.verify_otp(email, "000000")

        # El 4to debería fallar porque el OTP fue eliminado
        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert "No OTP found" in error or "Maximum attempts" in error


class TestRateLimiting:
    """Tests para rate limiting."""

    def test_rate_limit_per_client_limit(self):
        """Verificar límite por cliente (30/min)."""
        middleware = RedisRateLimitMiddleware(app=None)

        assert middleware.rate_limit_per_client == 30

    def test_rate_limit_global_limit(self):
        """Verificar límite global (1000/min)."""
        middleware = RedisRateLimitMiddleware(app=None)

        assert middleware.rate_limit_global == 1000

    def test_rate_limit_burst_limit(self):
        """Verificar límite burst (10 requests)."""
        middleware = RedisRateLimitMiddleware(app=None)

        assert middleware.rate_limit_burst == 10

    def test_exempt_paths_configured(self):
        """Verificar que paths exemptos están configurados."""
        middleware = RedisRateLimitMiddleware(app=None)

        assert "/" in middleware.EXEMPT_PATHS
        assert "/health" in middleware.EXEMPT_PATHS


class TestSecurityHeadersMiddleware:
    """Tests para middleware de security headers."""

    def test_security_headers_middleware_exists(self):
        """Verificar que el middleware existe."""
        from app.middleware import SecurityHeadersMiddleware

        assert callable(SecurityHeadersMiddleware)

    def test_middleware_adds_headers(self, client):
        """Verificar que middleware añade headers."""
        response = client.get("/health")

        # Verificar headers de seguridad
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_content_type_nosniff(self, client):
        """Verificar header X-Content-Type-Options: nosniff."""
        response = client.get("/health")

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_deny(self, client):
        """Verificar header X-Frame-Options: DENY."""
        response = client.get("/health")

        assert response.headers["X-Frame-Options"] == "DENY"

    def test_referrer_policy_no_referrer(self, client):
        """Verificar header Referrer-Policy: no-referrer."""
        response = client.get("/health")

        assert response.headers["Referrer-Policy"] == "no-referrer"

    def test_csp_default_src_self(self, client):
        """Verificar CSP usa 'self'."""
        response = client.get("/health")

        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp


class TestRateLimitingMiddlewareRedis:
    """Tests para middleware Redis rate limiting."""

    def test_redis_middleware_exists(self):
        """Verificar que el middleware Redis existe."""
        from app.middleware_redis import RedisRateLimitMiddleware

        assert callable(RedisRateLimitMiddleware)

    def test_in_memory_fallback_exists(self):
        """Verificar que existe fallback in-memory."""
        from app.middleware_redis import RedisRateLimitMiddleware

        middleware = RedisRateLimitMiddleware(app=None)

        # Debería tener rate_limit_store (fallback in-memory)
        assert hasattr(middleware, "rate_limit_store")
        assert middleware.rate_limit_store is not None

    def test_exempt_paths_includes_health(self):
        """Verificar que /health está en exempt paths."""
        from app.middleware_redis import RedisRateLimitMiddleware

        middleware = RedisRateLimitMiddleware(app=None)

        assert "/" in middleware.EXEMPT_PATHS
        assert "/health" in middleware.EXEMPT_PATHS
