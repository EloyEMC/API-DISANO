"""Current architecture and route contracts for the migrated application."""

import inspect
from pathlib import Path


def test_hexagonal_architecture_structure() -> None:
    root = Path(__file__).parents[2]
    required_paths = (
        "app/interfaces/http",
        "app/application/dto",
        "app/domain/entities",
        "app/domain/repositories",
        "app/domain/services",
        "app/infrastructure/database",
        "app/infrastructure/models",
        "app/infrastructure/repositories",
    )

    for relative_path in required_paths:
        assert (root / relative_path).is_dir(), f"Architecture path missing: {relative_path}"


def test_current_http_routes_are_functional(client) -> None:
    for path in ("/api/productos/v2/list?buscar=test&limit=1", "/api/familias/"):
        assert client.get(path).status_code == 200
    assert client.get("/api/bc3/v2/stats").status_code == 200


def test_versioned_product_routes_are_available(client) -> None:
    assert client.get("/api/productos/v1?per_page=1").status_code == 200
    assert client.get("/api/productos/v3?per_page=1").status_code == 200


def test_http_modules_use_dependency_injection() -> None:
    from app.interfaces.http import bc3, familias, productos

    for module in (productos, familias, bc3):
        source = inspect.getsource(module)
        assert "Depends" in source or "def get_" in source


def test_domain_services_do_not_use_sqlite_directly() -> None:
    from app.domain.services import familia, producto

    for module in (producto, familia):
        assert "sqlite3" not in inspect.getsource(module).lower()


def test_domain_entities_expose_current_required_attributes() -> None:
    from app.domain.entities.familia import FamiliaEntity
    from app.domain.entities.producto import ProductoEntity

    producto = ProductoEntity(codigo="TEST", descripcion="Test", marca="Brand", pvp=99.99)
    familia = FamiliaEntity(
        nombre="Test", total_productos=2, con_bc3=1, con_imagen=1, descontinuados=0
    )

    assert (producto.codigo, producto.descripcion) == ("TEST", "Test")
    assert familia.get_bc3_coverage_percentage() == 50.0
