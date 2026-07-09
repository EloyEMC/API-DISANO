"""
Tests Unitarios - Settings Manuales (Sin Env Vars)
===================================================

Tests que usan Settings manuales para evitar pydantic-settings parse errors.
"""

import pytest
from app.config import Settings


class TestSettingsManualCreation:
    """Tests de Settings creados manualmente (sin env vars)."""

    def test_settings_manual_basic(self):
        """Crear Settings manual con valores básicos."""
        settings = Settings(
            environment="testing",
            secret_key="test-key-32-char-minimum-length",
            api_keys=["test-key"],
            admin_api_keys=["test-admin"],
        )

        assert settings.environment == "testing"
        assert settings.secret_key == "test-key-32-char-minimum-length"
        assert len(settings.api_keys_list) == 1
        assert len(settings.admin_api_keys) == 1

    def test_settings_api_keys_string_parsing(self):
        """Parseo de api_keys como string."""
        settings = Settings(environment="testing", api_keys="key1,key2,key3")

        assert settings.api_keys_list == ["key1", "key2", "key3"]

    def test_settings_api_keys_list(self):
        """Parseo de api_keys como lista."""
        settings = Settings(environment="testing", api_keys=["key1", "key2"])

        assert settings.api_keys_list == ["key1", "key2"]

    def test_settings_admin_api_keys_list(self):
        """Parseo de admin_api_keys como lista."""
        settings = Settings(environment="testing", admin_api_keys=["admin1", "admin2"])

        assert settings.admin_api_keys == ["admin1", "admin2"]

    def test_settings_cors_origins_string(self):
        """Parseo de CORS origins como string."""
        settings = Settings(
            environment="testing",
            cors_origins="https://example.com,https://api.test.com",
        )

        assert len(settings.cors_origins_list) == 2
        assert "https://example.com" in settings.cors_origins_list

    def test_settings_rate_limits_default(self):
        """Límites de rate limiting por defecto."""
        settings = Settings(environment="testing")

        assert settings.rate_limit_global == 1000
        assert settings.rate_limit_per_client == 30
        assert settings.rate_limit_burst == 10

    def test_settings_database_path(self):
        """Path de base de datos por defecto."""
        settings = Settings(environment="testing")

        assert settings.database_path == "database/tarifa_disano.db"

    def test_settings_validation_development_empty(self):
        """Validación no requerida en desarrollo."""
        settings = Settings(environment="development", secret_key="", api_keys=[])

        # No debería lanzar error
        settings.validate_required()

    def test_settings_validation_production_with_values(self):
        """Validación pasa en producción con valores válidos."""
        settings = Settings(
            environment="production",
            secret_key="safe-key-32-char-minimum-length",
            api_keys=["production-key"],
        )

        settings.validate_required()

    def test_settings_validation_production_empty_secret(self):
        """Validación falla con SECRET_KEY vacío en producción."""
        settings = Settings(
            environment="production", secret_key="", api_keys=["production-key"]
        )

        with pytest.raises(ValueError) as exc_info:
            settings.validate_required()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_settings_validation_production_empty_api_keys(self):
        """Validación falla con API_KEYS vacío en producción."""
        settings = Settings(
            environment="production",
            secret_key="safe-key-32-char-minimum-length",
            api_keys=[],
        )

        with pytest.raises(ValueError) as exc_info:
            settings.validate_required()

        assert "API_KEYS" in str(exc_info.value)

    def test_settings_is_production_detection(self):
        """Detección de entorno producción."""
        settings_prod = Settings(environment="production")
        settings_dev = Settings(environment="development")

        assert settings_prod.is_production() is True
        assert settings_dev.is_production() is False

    def test_settings_security_defaults(self):
        """Valores de seguridad por defecto."""
        settings = Settings(environment="testing")

        assert settings.rate_limit_enabled is True
        assert settings.security_log_enabled is True
        assert settings.scraping_detection_enabled is True
        assert settings.ban_enabled is True

    def test_settings_cors_defaults(self):
        """Valores CORS por defecto."""
        settings = Settings(environment="testing")

        assert settings.cors_allow_credentials is True
        assert settings.cors_allow_methods == ["*"]
        assert settings.cors_allow_headers == ["*"]


if __name__ == "__main__":
    pytest.main([__file__])
