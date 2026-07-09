"""
Conftest.py - Fixtures pytest para API-DISANO
===============================================

Fixtures compartidos para tests siguiendo patrones BC3-Suite.
Parchea get_settings() para evitar pydantic-settings bloqueo.
"""

import pytest
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
import sqlite3
import os


# STEP 1: Limpiar variables de entorno problemáticas
for var in ["SECRET_KEY", "API_KEYS", "ADMIN_API_KEYS", "ENVIRONMENT"]:
    os.environ.pop(var, None)

# STEP 2: Configurar variables de entorno limpias
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-safe-testing"
os.environ["API_KEYS"] = "test-api-key-1,test-api-key-2"
os.environ["ADMIN_API_KEYS"] = "test-admin-key-1"

# STEP 3: Parchear get_settings ANTES de importar app.main
_original_get_settings = None


def _patch_get_settings():
    """Parchear get_settings para retornar Settings manual en tests."""
    from app.config import Settings

    return Settings(
        environment="testing",
        secret_key="test-secret-key-32-chars-safe-testing",
        api_keys="test-api-key-1,test-api-key-2",
        admin_api_keys=["test-admin-key-1"],
    )


# Importar app.config y parchear
import app.config

_original_get_settings = app.config.get_settings
app.config.get_settings = _patch_get_settings


@pytest.fixture(scope="session", autouse=True)
def test_db_path() -> Path:
    """
    Path a la base de datos de testing SQLite.

    Returns:
        Path: Ruta a testing/testing.db

    ⚠️ IMPORTANTE: Nunca usa database/tarifa_disano.db desde tests!
    """
    return Path(__file__).parent.parent / "testing" / "testing.db"


@pytest.fixture
def db_session(test_db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """
    Database session con SQLite in-memory.

    Siempre usa testing/testing.db, nunca producción.

    Args:
        test_db_path: Path a la base de datos de testing

    Yields:
        sqlite3.Connection: Sesión de base de datos
    """
    connection = sqlite3.connect(test_db_path)
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


@pytest.fixture
def client() -> TestClient:
    """
    Test client FastAPI con get_settings parcheado.

    Returns:
        TestClient: Cliente HTTP para testing
    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    """Headers con API key válida para testing."""
    return {"X-API-Key": "test-api-key-1"}


@pytest.fixture
def admin_headers() -> dict:
    """Headers con admin API key válida para testing."""
    return {"X-Admin-API-Key": "test-admin-key-1"}


@pytest.fixture
def invalid_auth_headers() -> dict:
    """Headers con API key inválida para testing negativo."""
    return {"X-API-Key": "invalid-api-key-123456"}


@pytest.fixture
def no_auth_headers() -> dict:
    """Headers sin API key para testing negativo."""
    return {}


@pytest.fixture
def mock_bc3_suite_client() -> AsyncMock:
    """Mock del cliente BC3 Suite para tests."""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def sample_producto_dict() -> dict:
    """Diccionario de producto de ejemplo para tests."""
    return {
        "codigo": "33036139",
        "marca": "Disano",
        "descripcion": "Lámpara LED Disano 12W E27",
        "pvp": 15.99,
        "familia_web": "Iluminación",
        "descontinuado": False,
        "bc3_descripcion_corta": "Lámpara LED 12W",
        "url_imagen": "https://example.com/image.jpg",
    }


@pytest.fixture
def mock_disano_api_client() -> Mock:
    """Mock del cliente API DISANO para tests."""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def sample_producto_row() -> Mock:
    """Mock de fila SQLite de producto para tests."""
    row = Mock()
    row.keys.return_value = [
        "CÓDIGO",
        "DESCRIPCION",
        "PVP_26_01_26",
        "MARCA",
        "Familia_WEB",
        "bc3_descripcion_corta",
    ]
    row.__getitem__ = lambda key: {
        "CÓDIGO": "33036139",
        "DESCRIPCION": "Lámpara LED Disano 12W E27",
        "PVP_26_01_26": 15.99,
        "MARCA": "Disano",
        "Familia_WEB": "Iluminación",
        "bc3_descripcion_corta": "Lámpara LED 12W",
    }.get(key)
    return row


@pytest.fixture
def sample_v2_producto_dict() -> dict:
    """Producto V2 de ejemplo para tests."""
    return {
        "codigo": "33036139",
        "marca": "Disano",
        "descripcion": "Lámpara LED Disano 12W E27",
        "pvp": 15.99,
        "familia_web": "Iluminación",
        "descontinuado": False,
        "bc3_descripcion_corta": "Lámpara LED 12W",
        "url_imagen": "https://example.com/image.jpg",
    }


@pytest.fixture
def mock_rate_limit_store() -> dict:
    """Mock del store de rate limiting para tests."""
    from collections import defaultdict

    return defaultdict(list)
