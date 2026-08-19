"""Conftest.py - Fixtures pytest para API-DISANO.

Fixtures compartidos para tests siguiendo patrones BC3-Suite.
Parchea get_settings() para evitar bloqueo de pydantic-settings.
"""

import os
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# FIX: Asegurar que importamos el proyecto API-DISANO correcto
# y no otro proyecto 'app' que pueda estar en sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force import for coverage measurement


# STEP 1: Limpiar variables de entorno problemáticas
for var in ["SECRET_KEY", "API_KEYS", "ADMIN_API_KEYS", "ENVIRONMENT"]:
    os.environ.pop(var, None)

# STEP 2: Configurar variables de entorno limpias
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-placeholder"
os.environ["API_KEYS"] = "test-api-key-placeholder,test-api-key-placeholder-2"
os.environ["ADMIN_API_KEYS"] = '["test-admin-api-key-placeholder"]'

_database_url = os.environ.get("DATABASE_URL")
if not _database_url or not urlparse(_database_url).scheme.startswith("postgresql"):
    raise RuntimeError(
        "Tests require DATABASE_URL to point to PostgreSQL; "
        "SQLite is not supported by the test backend."
    )
os.environ["DATABASE_URL"] = _database_url

from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.infrastructure.database.connection as connection_module  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def postgres_product_seed() -> None:
    """Seed one sanitized product for schema-only PostgreSQL test runs."""
    from sqlalchemy import text

    with connection_module.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO "productos" (
                    "CÓDIGO", "MARCA", "DESCRIPCION", "Familia_WEB",
                    "DTO.", "U.P.LOG", "U.CAJA", "Peso bruto KG",
                    "Longitud M", "CM3", "PVP_26_01_26", "bc3_descripcion_corta",
                    "bc3_descripcion_larga", "bc3_descripcion_completa", "bc3_product_type"
                )
                SELECT
                    :codigo, :marca, :descripcion, :familia,
                    :dto, :up_log, :u_caja, :peso_bruto_kg,
                    :longitud_m, :cm3, :pvp, :bc3_descripcion_corta,
                    :bc3_descripcion_larga, :bc3_descripcion_completa, :bc3_product_type
                WHERE NOT EXISTS (
                    SELECT 1 FROM "productos"
                    WHERE "DTO." IS NOT NULL
                      AND "U.P.LOG" IS NOT NULL
                      AND "U.CAJA" IS NOT NULL
                      AND "Peso bruto KG" IS NOT NULL
                      AND "Longitud M" IS NOT NULL
                      AND "CM3" IS NOT NULL
                )
                ON CONFLICT ("CÓDIGO") DO NOTHING
                """
            ),
            {
                "codigo": "33036139",
                "marca": "Test Brand",
                "descripcion": "Sanitized BC3 integration fixture",
                "familia": "Test Family",
                "dto": "0",
                "up_log": 1.0,
                "u_caja": 1,
                "peso_bruto_kg": 0.5,
                "longitud_m": 0.1,
                "cm3": 1.0,
                "pvp": 1.0,
                "bc3_descripcion_corta": "Sanitized fixture",
                "bc3_descripcion_larga": "Sanitized fixture long description",
                "bc3_descripcion_completa": "Sanitized fixture complete description",
                "bc3_product_type": "sanitized-test-product",
            },
        )


@pytest.fixture(scope="session", autouse=True)
def test_db_path() -> str:
    """Return the PostgreSQL URL configured for the test session."""
    return _database_url


@pytest.fixture
def db_session():
    """Provide a raw connection to the configured PostgreSQL test database."""
    connection = connection_module.engine.connect()
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def sqlalchemy_session() -> Generator[Session, None, None]:
    """Provide a SQLAlchemy ORM session for repository tests."""

    engine = connection_module.engine
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture(autouse=True)
def clear_app_dependency_overrides() -> Generator[None, None, None]:
    """Clear shared FastAPI overrides and cached settings after each test."""
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    from app.main import app

    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """Test client FastAPI con get_settings parcheado.

    Returns:
        TestClient: Cliente HTTP para testing

    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def mock_db_connection() -> Mock:
    """Compatibility mock for legacy security endpoint tests."""
    return Mock()


@pytest.fixture
def auth_headers() -> dict:
    """Headers con API key válida para testing."""
    return {"X-API-Key": "test-api-key-placeholder"}


@pytest.fixture
def admin_headers() -> dict:
    """Headers con admin API key válida para testing."""
    return {"X-Admin-API-Key": "test-admin-api-key-placeholder"}


@pytest.fixture
def invalid_auth_headers() -> dict:
    """Headers con API key inválida para testing negativo."""
    return {"X-API-Key": "invalid-api-key-placeholder"}


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
    """Mock de fila de producto para tests."""
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


# =============================================================================
# PYTEST CONFIGURE - COVERAGE FIX
# =============================================================================


def pytest_configure(config):
    """Forzar import explícito para pytest-cov detection."""
    # Importar módulos que deben medir coverage (hexagonal architecture)
    from app.interfaces.http import productos as productos_http

    # Forzar carga de módulos antes de tests
    productos_http.router  # Acceder a router para garantizar carga
