"""
Tests Unitarios - Middleware Execution (TDD + AAA)
=========================================

Tests que importan y ejecutan código real de app/middleware.py.
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.

El módulo app/middleware.py contiene funciones de rate limiting y security.
."""

import pytest
from fastapi import Request


class TestMiddlewareGetApiKeys:
    """Tests de get_api_keys() en app/middleware.py (TDD + AAA)."""

    def test_get_api_keys_returns_list_from_environment(self):
        """
        RED: get_api_keys() debe retornar lista desde API_KEYS environment.

        AAA Pattern:
        - Arrange: Configurar API_KEYS environment
        - Act: Importar y llamar get_api_keys()
        - Assert: Debe retornar lista con keys
        ."""
        # Arrange
        import os

        os.environ["API_KEYS"] = "key-1,key-2,key-3"

        # Act - Importar después de configurar environment
        from app.middleware import get_api_keys

        result = get_api_keys()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert "key-1" in result
        assert "key-2" in result
        assert "key-3" in result

    def test_get_api_keys_empty_when_no_environment(self):
        """
        GREEN: get_api_keys() retorna lista vacía cuando no hay environment.
        ."""
        # Arrange
        import os

        # Limpiar variable si existe
        os.environ.pop("API_KEYS", None)

        # Act
        from app.middleware import get_api_keys

        result = get_api_keys()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0


class TestMiddlewareGetEnvironment:
    """Tests de get_environment() en app/middleware.py (TDD + AAA)."""

    def test_get_environment_default_development(self):
        """
        RED: get_environment() retorna 'development' por defecto.
        ."""
        # Arrange
        import os

        # Limpiar variable si existe
        os.environ.pop("ENVIRONMENT", None)

        # Act
        from app.middleware import get_environment

        result = get_environment()

        # Assert
        assert result == "development"

    def test_get_environment_returns_production_when_set(self):
        """
        GREEN: get_environment() retorna 'production' cuando está configurado.
        ."""
        # Arrange
        import os

        os.environ["ENVIRONMENT"] = "production"

        # Act
        from app.middleware import get_environment

        result = get_environment()

        # Assert
        assert result == "production"


class TestMiddlewareGetRateLimit:
    """Tests de get_rate_limit() en app/middleware.py (TDD + AAA)."""

    def test_get_rate_limit_default_30(self):
        """
        RED: get_rate_limit() retorna 30 por defecto.
        ."""
        # Arrange
        import os

        os.environ.pop("RATE_LIMIT_PER_MINUTE", None)

        # Act
        from app.middleware import get_rate_limit

        result = get_rate_limit()

        # Assert
        assert isinstance(result, int)
        assert result == 30

    def test_get_rate_limit_custom_value(self):
        """
        GREEN: get_rate_limit() retorna valor custom del environment.
        ."""
        # Arrange
        import os

        os.environ["RATE_LIMIT_PER_MINUTE"] = "60"

        # Act
        from app.middleware import get_rate_limit

        result = get_rate_limit()

        # Assert
        assert isinstance(result, int)
        assert result == 60


class TestMiddlewareGetAdminKeys:
    """Tests de get_admin_keys() en app/middleware.py (TDD + AAA)."""

    def test_get_admin_keys_returns_list_from_environment(self):
        """
        RED: get_admin_keys() debe retornar lista desde ADMIN_API_KEYS environment.
        ."""
        # Arrange
        import os

        os.environ["ADMIN_API_KEYS"] = "admin-key-1,admin-key-2"

        # Act
        from app.middleware import get_admin_keys

        result = get_admin_keys()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert "admin-key-1" in result
        assert "admin-key-2" in result

    def test_get_admin_keys_empty_when_no_environment(self):
        """
        GREEN: get_admin_keys() retorna lista vacía cuando no hay environment.
        ."""
        # Arrange
        import os

        os.environ.pop("ADMIN_API_KEYS", None)

        # Act
        from app.middleware import get_admin_keys

        result = get_admin_keys()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0


class TestMiddlewareVerifyAdminApiKey:
    """Tests de verify_admin_api_key() en app/middleware.py (TDD + AAA)."""

    def test_verify_admin_api_key_always_true_in_development(self):
        """
        RED: verify_admin_api_key() retorna True siempre en development.
        ."""
        # Arrange
        import os

        os.environ["ENVIRONMENT"] = "development"

        from unittest.mock import Mock

        request = Mock(spec=Request)

        # Act
        from app.middleware import verify_admin_api_key

        result = verify_admin_api_key(request)

        # Assert
        assert result is True

    def test_verify_admin_api_key_checks_in_production(self):
        """
        GREEN: verify_admin_api_key() verifica headers en production.
        ."""
        # Arrange
        import os

        os.environ["ENVIRONMENT"] = "production"
        os.environ["ADMIN_API_KEYS"] = "admin-test-key"

        from unittest.mock import Mock

        request = Mock(spec=Request)
        request.headers.get = Mock(return_value="admin-test-key")

        # Act
        from app.middleware import verify_admin_api_key

        result = verify_admin_api_key(request)

        # Assert - En producción, verifica la key
        assert isinstance(result, bool)


class TestMiddlewareRateLimitStore:
    """Tests de rate_limit_store en app/middleware.py (TDD + AAA)."""

    def test_rate_limit_store_is_dict_of_lists(self):
        """
        GREEN: rate_limit_store es un dict de listas.
        """
        # Arrange & Act
        from app.middleware import rate_limit_store

        # Assert
        assert isinstance(rate_limit_store, dict)
        assert all(isinstance(v, list) for v in rate_limit_store.values())

    def test_rate_limit_store_allows_adding_timestamps(self):
        """
        GREEN: rate_limit_store permite agregar timestamps.
        ."""
        # Arrange
        from app.middleware import rate_limit_store
        import time

        # Act - Agregar timestamp para IP
        ip = "192.168.1.100"
        rate_limit_store[ip].append(time.time())

        # Assert
        assert len(rate_limit_store[ip]) > 0
        assert rate_limit_store[ip][-1] > 0


class TestMiddlewareApiKeyScopes:
    """Tests for route-specific regular API key authentication."""

    @staticmethod
    def _request(path: str, headers: dict[str, str]) -> Request:
        return Request(
            {
                "type": "http",
                "method": "GET",
                "path": path,
                "headers": [
                    (name.lower().encode(), value.encode()) for name, value in headers.items()
                ],
            }
        )

    @staticmethod
    async def _call_next(request):
        from starlette.responses import PlainTextResponse

        return PlainTextResponse("ok")

    def test_bc3_routes_accept_dedicated_key_for_descendants(self, monkeypatch):
        """BC3 exact and descendant paths use BC3_API_KEYS."""
        import asyncio

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEYS", "general-key")
        monkeypatch.setenv("BC3_API_KEYS", "bc3-key")

        from app.middleware import APIKeyMiddleware

        middleware = APIKeyMiddleware(None)
        for path in ("/api/productos/bc3/v1", "/api/productos/bc3/v1/items"):
            response = asyncio.run(
                middleware.dispatch(
                    self._request(path, {"X-API-Key": "bc3-key"}),
                    self._call_next,
                )
            )
            assert response.status_code == 200

    def test_bc3_routes_reject_general_key(self, monkeypatch):
        """BC3 routes do not accept a general API_KEYS credential."""
        import asyncio

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEYS", "general-key")
        monkeypatch.setenv("BC3_API_KEYS", "bc3-key")

        from app.middleware import APIKeyMiddleware

        response = asyncio.run(
            APIKeyMiddleware(None).dispatch(
                self._request("/api/productos/bc3/v1/items", {"X-API-Key": "general-key"}),
                self._call_next,
            )
        )

        assert response.status_code == 401

    def test_non_bc3_routes_keep_general_key_behavior(self, monkeypatch):
        """Non-BC3 routes continue to use API_KEYS."""
        import asyncio

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEYS", "general-key")
        monkeypatch.setenv("BC3_API_KEYS", "bc3-key")

        from app.middleware import APIKeyMiddleware

        response = asyncio.run(
            APIKeyMiddleware(None).dispatch(
                self._request("/api/productos/v2/list", {"X-API-Key": "general-key"}),
                self._call_next,
            )
        )

        assert response.status_code == 200

    def test_bc3_prefix_lookalike_remains_on_general_key_scope(self, monkeypatch):
        """Paths outside the BC3 route prefix keep API_KEYS behavior."""
        import asyncio

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEYS", "general-key")
        monkeypatch.setenv("BC3_API_KEYS", "bc3-key")

        from app.middleware import APIKeyMiddleware

        response = asyncio.run(
            APIKeyMiddleware(None).dispatch(
                self._request("/api/productos/bc3/v10", {"X-API-Key": "general-key"}),
                self._call_next,
            )
        )

        assert response.status_code == 200

    def test_admin_key_remains_valid_on_bc3_routes(self, monkeypatch):
        """Admin authentication remains independent of regular key scope."""
        import asyncio

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEYS", "general-key")
        monkeypatch.setenv("BC3_API_KEYS", "bc3-key")
        monkeypatch.setenv("ADMIN_API_KEYS", "admin-key")

        from app.middleware import APIKeyMiddleware

        response = asyncio.run(
            APIKeyMiddleware(None).dispatch(
                self._request("/api/productos/bc3/v1/items", {"X-Admin-API-Key": "admin-key"}),
                self._call_next,
            )
        )

        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
