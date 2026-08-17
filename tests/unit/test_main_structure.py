"""Structural checks for the current FastAPI composition root."""

from pathlib import Path


MAIN_PATH = Path(__file__).parents[2] / "app" / "main.py"


def test_main_module_exists():
    assert MAIN_PATH.is_file()


def test_main_imports_current_hexagonal_interfaces():
    content = MAIN_PATH.read_text()
    assert "from app.interfaces.http import" in content
    assert "from app.infrastructure.database.connection import engine" in content
    assert "from app.middleware import" in content


def test_main_composes_current_routers():
    content = MAIN_PATH.read_text()
    assert 'app.include_router(productos_http.router, prefix="/api"' in content
    assert 'app.include_router(familias_http.router, prefix="/api"' in content
    assert 'app.include_router(bc3_http.router, prefix="/api"' in content


def test_main_exposes_root_and_health_routes():
    content = MAIN_PATH.read_text()
    assert '@app.get("/")' in content
    assert "async def root" in content
    assert '@app.get("/health")' in content
    assert "async def health_check" in content


def test_main_creates_fastapi_and_security_configuration():
    content = MAIN_PATH.read_text()
    assert "app = FastAPI(" in content
    assert "CORSMiddleware" in content
    assert "SecurityHeadersMiddleware" in content
    assert "register_exception_handlers(app)" in content
