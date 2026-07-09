"""
Conftest.py - Fixtures pytest para API-DISANO.
================================================

Fixtures compartidos para tests siguiendo patrones BC3-Suite:
- SQLite in-memory para tests (NUNCA tocar producción)
- Configuración de testing separada
- Test client FastAPI
- Mocks de APIs externas
- Logging silenciado para tests

BC3-Suite Reference: /Users/eloymartinezcuesta/Documents/BC3-Suite/tests/conftest.py
"""

import pytest
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
import sqlite3

# Cargar variables de entorno de testing
import os

os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-fase2!"
os.environ["API_KEYS"] = "test-api-key-1,test-api-key-2"
os.environ["ADMIN_API_KEYS"] = "test-admin-key-1"


@pytest.fixture(scope="session", autouse=True)
def test_db_path() -> Path:
    """
    Path a la base de datos de testing SQLite.

    Returns:
        Path: Ruta a testing/testing.db

    ⚠️ IMPORTANTE: Nunca usa database/tarifa_disano.db desde tests!
    """
    return Path(__file__).parent.parent / "testing" / "testing.db"


@pytest.fixture(scope="session", autouse=True)
def db_session(test_db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """
    Database session con SQLite in-memory.

    Siempre usa testing/testing.db, nunca producción.

    Args:
        test_db_path: Path a la base de datos de testing

    Yields:
        sqlite3.Connection: Sesión de base de datos

    Example:
        def test_query_productos(db_session):
            cursor = db_session.execute("SELECT * FROM productos LIMIT 1")
            producto = cursor.fetchone()
            assert producto is not None
    """
    # Usar testing/testing.db (COPIA SEGURA de producción)
    connection = sqlite3.connect(test_db_path)

    # Configurar row factory para acceder por nombre
    connection.row_factory = sqlite3.Row

    yield connection

    connection.close()


@pytest.fixture
def client() -> TestClient:
    """
    Test client FastAPI.

    Returns:
        TestClient: Cliente HTTP para testing

    Example:
        def test_health_check(client):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
    """
    # Importar app después de configurar variables
    from app.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    """
    Headers con API key válida para testing.

    Returns:
        dict: Headers con X-API-Key válido

    Example:
        def test_get_productos_con_auth(client, auth_headers):
            response = client.get(
                "/api/productos/",
                headers=auth_headers
            )
            assert response.status_code == 200
    """
    return {"X-API-Key": "test-api-key-1"}


@pytest.fixture
def admin_headers() -> dict:
    """
    Headers con admin API key válida para testing.

    Returns:
        dict: Headers con X-Admin-API-Key válido

    Example:
        def test_crear_producto_admin(client, admin_headers):
            response = client.post(
                "/api/admin/productos",
                json={"codigo": "12345678", "pvp": 19.99},
                headers=admin_headers
            )
            assert response.status_code in [201, 409]  # 201 creado, 409 duplicado
    """
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
    """
    Mock del cliente BC3 Suite para tests.

    NEVER llama a la API real de BC3 Suite desde tests.

    Returns:
        AsyncMock: Cliente BC3 Suite mockeado

    Example:
        async def test_bc3_integration(mock_bc3_suite_client):
            response = await mock_bc3_suite_client.get("/api/productos")
            # Configurar mock según el test
            mock_bc3_suite_client.get.return_value = {"products": [...]}
            result = await response.json()
    """
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def sample_producto_dict() -> dict:
    """
    Diccionario de producto de ejemplo para tests.

    Returns:
        dict: Producto de ejemplo

    Example:
        def test_create_producto(client, admin_headers, sample_producto_dict):
            response = client.post(
                "/api/admin/productos",
                json=sample_producto_dict,
                headers=admin_headers
            )
            assert response.status_code == 201
    """
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
    """
    Mock del cliente API DISANO para tests.

    NEVER llama a la API real de DISANO desde tests.

    Returns:
    Mock: Cliente DISANO API mockeado

    Example:
        def test_producto_from_disano_api(mock_disano_api_client):
            # Configurar mock para devolver producto
            mock_disano_api_client.get.return_value = {
                "codigo": "33036139",
                "descripcion": "Lámpara LED Disano 12W E27",
                "pvp": 15.99
            }
            # Test que usa el mock
            result = mock_disano_api_client.get("/productos/33036139")
            assert result["codigo"] == "33036139"
    """
    mock_client = Mock()
    return mock_client


@pytest.fixture
def sample_producto_row() -> Mock:
    """
    Mock de fila SQLite de producto para tests.

    Returns:
    Mock: Row de producto mockeada

    Example:
        def test_map_row_to_v2(sample_producto_row):
            mapped = map_row_to_v2(sample_producto_row)
            assert mapped["codigo"] == "33036139"
    """
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
