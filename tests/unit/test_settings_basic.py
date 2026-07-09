"""
Tests Unitarios - Config & Settings (Sin Client)
================================================

Tests que NO dependen del client fixture para evitar import settings.
"""

import pytest
from app.config import Settings


class TestSettingsBasic:
    """Tests básicos de Settings sin carga de .env."""

    def test_settings_default_values(self):
        """Verificar valores por defecto de Settings."""
        settings = Settings()

        # Valores por defecto esperados
        assert settings.environment == "development"
        assert settings.secret_key == ""
        assert settings.api_keys == []
        assert settings.admin_api_keys == []
        assert settings.database_path == "database/tarifa_disano.db"
        assert settings.rate_limit_global == 1000
        assert settings.rate_limit_per_client == 30
        assert settings.rate_limit_burst == 10

    def test_settings_with_manual_values(self):
        """Verificar Settings con valores manuales."""
        settings = Settings(
            environment="production",
            secret_key="test-key-32-chars-safe-for-tests!",
            api_keys=["key1", "key2"],
            admin_api_keys=["admin-key"],
        )

        assert settings.environment == "production"
        assert settings.secret_key == "test-key-32-chars-safe-for-tests!"
        assert len(settings.api_keys_list) == 2
        assert len(settings.admin_api_keys) == 1

    def test_api_keys_list_parsing_string(self):
        """Verificar parseo de api_keys como string."""
        settings = Settings(api_keys="key1,key2,key3")

        assert settings.api_keys_list == ["key1", "key2", "key3"]

    def test_api_keys_list_parsing_list(self):
        """Verificar parseo de api_keys como lista."""
        settings = Settings(api_keys=["key1", "key2"])

        assert settings.api_keys_list == ["key1", "key2"]

    def test_admin_api_keys_list_parsing_list(self):
        """Verificar parseo de admin_api_keys como lista."""
        settings = Settings(admin_api_keys=["admin1", "admin2"])

        assert settings.admin_api_keys == ["admin1", "admin2"]

    def test_cors_origins_list_parsing(self):
        """Verificar parseo de CORS origins."""
        settings = Settings(cors_origins="https://example.com,https://api.test.com")

        assert len(settings.cors_origins_list) == 2
        assert "https://example.com" in settings.cors_origins_list

    def test_rate_limit_defaults(self):
        """Verificar límites de rate limiting por defecto."""
        settings = Settings()

        assert settings.rate_limit_global == 1000
        assert settings.rate_limit_per_client == 30
        assert settings.rate_limit_burst == 10

    def test_database_url_defaults(self):
        """Verificar URL de base de datos por defecto."""
        settings = Settings()

        assert settings.database_path == "database/tarifa_disano.db"

    def test_redis_url_not_in_settings(self):
        """Redis URL no está en Settings (usa constante en middleware)."""
        settings = Settings()

        # Redis URL no es parte de Settings, es constante en middleware
        assert not hasattr(settings, "redis_url")


class TestSecurityValidation:
    """Tests de validación de seguridad."""

    def test_validate_required_in_development_empty(self):
        """Validación no requerida en desarrollo con valores vacíos."""
        settings = Settings(environment="development", secret_key="", api_keys=[])

        # No debería lanzar error
        settings.validate_required()

    def test_validate_required_in_production_with_values(self):
        """Validación pasa en producción con valores válidos."""
        settings = Settings(
            environment="production",
            secret_key="safe-key-32-char-minimum-length",
            api_keys=["production-key"],
        )

        settings.validate_required()

    def test_secret_key_length_in_production(self):
        """SECRET_KEY debe tener ≥32 caracteres en producción."""
        settings = Settings(
            environment="production",
            secret_key="short",  # Solo 5 caracteres
        )

        with pytest.raises(ValueError) as exc_info:
            settings.validate_required()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_api_keys_not_empty_in_production(self):
        """API_KEYS no puede estar vacío en producción."""
        settings = Settings(
            environment="production",
            secret_key="safe-key-32-char-minimum-length",
            api_keys=[],
        )

        with pytest.raises(ValueError) as exc_info:
            settings.validate_required()

        assert "API_KEYS" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
