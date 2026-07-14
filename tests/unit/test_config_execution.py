"""
Tests Unitarios - Config Execution (TDD + AAA + BC3-Suite)
============================================

Tests que importan Settings con TDD real para app/config.py.
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.
."""

import pytest


class TestConfigSettingsRequiredFields:
    """Tests de campos obligatorios en Settings (TDD + AAA)."""

    def test_settings_secret_key_required_validation(self):
        """
        RED: Settings debe fallar sin SECRET_KEY válido.

        AAA Pattern:
        - Arrange: Configurar SECRET_KEY vacío
        - Act: Crear Settings
        - Assert: Debe lanzar ValueError
        ."""
        # Arrange
        from app.config import Settings

        # Act & Assert - SECRET_KEY vacío debe lanzar ValueError
        with pytest.raises(ValueError):
            Settings(secret_key="")

    def test_settings_api_keys_required_validation(self):
        """
        GREEN: Settings debe fallar sin API_KEYS válidos.
        """
        # Arrange
        from app.config import Settings

        # Act & Assert - API_KEYS vacío debe lanzar ValueError
        with pytest.raises(ValueError):
            Settings(api_keys=[])

    def test_settings_valid_configuration(self):
        """
        GREEN: Settings válidos funcionan.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(
            secret_key="test-secret-key-32-chars-safe", api_keys=["key1", "key2"]
        )

        # Assert
        assert settings.secret_key == "test-secret-key-32-chars-safe"
        assert settings.api_keys_list == ["key1", "key2"]


class TestConfigFieldValidators:
    """Tests de field validators en Settings (TDD + AAA)."""

    def test_api_keys_parser_from_string(self):
        """
        RED: Field validator parsea API_KEYS de string a lista.

        AAA Pattern:
        - Arrange: Crear Settings con API_KEYS como string
        - Act: Validar parseo vía api_keys_list
        - Assert: Debe retornar lista con 2 keys
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys="key1,key2,key3")

        # Assert - api_keys_list debe ser lista
        assert isinstance(settings.api_keys_list, list)
        assert len(settings.api_keys_list) == 3
        assert "key1" in settings.api_keys_list
        assert "key2" in settings.api_keys_list
        assert "key3" in settings.api_keys_list

    def test_api_keys_parser_from_list(self):
        """
        GREEN: Field validator acepta API_KEYS como lista.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["keyA", "keyB"])

        # Assert - api_keys_list debe ser lista sin cambios
        assert isinstance(settings.api_keys_list, list)
        assert len(settings.api_keys_list) == 2

    def test_admin_api_keys_parser_from_string(self):
        """
        GREEN: Field validator parsea ADMIN_API_KEYS de string a lista.
        ."""
        # Arrange & Act
        import os

        os.environ["ADMIN_API_KEYS"] = "admin-key-1,admin-key-2"

        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["key"])

        # Assert - admin_api_keys debe ser lista parseada
        admin_keys = (
            settings.admin_api_keys
            if isinstance(settings.admin_api_keys, list)
            else [settings.admin_api_keys]
        )
        assert isinstance(admin_keys, list)
        assert len(admin_keys) == 2
        assert "admin-key-1" in admin_keys
        assert "admin-key-2" in admin_keys

    def test_cors_origins_parser_from_string(self):
        """
        GREEN: Field validator parsea CORS_ORIGINS de string a lista.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(
            secret_key="test",
            api_keys=["key"],
            cors_origins="http://localhost:3000,http://localhost:8080",
        )

        # Assert - cors_origins_list debe ser lista
        assert isinstance(settings.cors_origins_list, list)
        assert len(settings.cors_origins_list) == 2


class TestConfigProperties:
    """Tests de properties en Settings (TDD + AAA)."""

    def test_is_production_returns_false_in_development(self):
        """
        RED: is_production() retorna False en development.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(
            secret_key="test", api_keys=["key"], environment="development"
        )

        # Assert
        assert settings.is_production() is False

    def test_is_production_returns_true_in_production(self):
        """
        GREEN: is_production() retorna True en production.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(
            secret_key="test-prod", api_keys=["key"], environment="production"
        )

        # Assert
        assert settings.is_production() is True

    def test_api_keys_list_property_returns_list(self):
        """
        GREEN: api_keys_list property retorna lista correctamente.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["key1", "key2"])

        # Assert
        assert isinstance(settings.api_keys_list, list)
        assert len(settings.api_keys_list) == 2

    def test_validate_required_passes_with_valid_config(self):
        """
        GREEN: validate_required() pasa con configuración válida en producción.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(
            secret_key="test-prod-secret-key-32",
            api_keys=["key1", "key2"],
            environment="production",
        )

        # Act & Assert - validate_required() NO debe lanzar ValueError
        settings.validate_required()  # No exception = PASS

    def test_validate_required_fails_without_secret_key_in_production(self):
        """
        RED: validate_required() falla sin SECRET_KEY en producción.
        ."""
        # Arrange
        from app.config import Settings

        settings = Settings(
            secret_key="", api_keys=["key1", "key2"], environment="production"
        )

        # Act & Assert - validate_required() debe lanzar ValueError
        with pytest.raises(ValueError, match="SECRET_KEY es obligatorio"):
            settings.validate_required()


class TestConfigDefaultValues:
    """Tests de valores default en Settings (TDD + AAA)."""

    def test_default_api_title(self):
        """
        GREEN: api_title tiene default razonable.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["key"])

        # Assert
        assert settings.api_title == "API Disano"

    def test_default_api_version(self):
        """
        GREEN: api_version tiene default razonable.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["key"])

        # Assert
        assert settings.api_version == "1.0.0"

    def test_default_rate_limit_values(self):
        """
        GREEN: rate_limit tiene defaults razonables.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["key"])

        # Assert
        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_per_client == 30
        assert settings.rate_limit_global == 1000

    def test_default_cors_configuration(self):
        """
        GREEN: CORS tiene defaults razonables.
        ."""
        # Arrange & Act
        from app.config import Settings

        settings = Settings(secret_key="test", api_keys=["key"])

        # Assert
        assert "*" in settings.cors_origins_list
        assert settings.cors_allow_credentials is True
        assert "*" in settings.cors_allow_methods


if __name__ == "__main__":
    pytest.main([__file__])
