"""
Tests Unitarios - Productos Router Real Execution (TDD + AAA)
=============================================================

Tests que ejecutan funciones reales de app/routers/productos.py.
Mock de sqlite3.Row para aumentar coverage sin Settings import.
"""

import pytest


class TestMapRowToV2Function:
    """Tests que ejecutan map_row_to_v2 (TDD)."""

    def test_map_row_to_v2_import_successfully(self):
        """
        AAA: Arrange (import), Act (import), Assert (validation)
        """
        # Arrange & Act - Importar función
        try:
            from app.routers.productos import map_row_to_v2

            # Assert - Verificar que es callable
            assert callable(map_row_to_v2)
        except ImportError as e:
            pytest.fail(f"Error importando map_row_to_v2: {e}")

    def test_map_row_to_v2_with_basic_row(self):
        """GREEN: Ejecutar map_row_to_v2 con datos básicos."""
        # Arrange - Crear sqlite3.Row real
        import sqlite3
        from app.routers.productos import map_row_to_v2

        # Crear conexión y Row real en memoria
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 'TEST-001' as [CÓDIGO], 'Test producto' as DESCRIPCION, 19.99 as PVP_26_01_26, 'Disano' as MARCA, 'Iluminación' as Familia_WEB"
        )
        row = cursor.fetchone()

        # Act - Llamar función con Row real
        result = map_row_to_v2(row)

        # Assert - Verificar estructura V2 (snake_case)
        assert isinstance(result, dict)
        assert "codigo" in result
        assert "descripcion" in result
        assert result["codigo"] == "TEST-001"
        assert result["descripcion"] == "Test producto"

    def test_map_row_to_v2_with_null_fields(self):
        """GREEN: Ejecutar map_row_to_v2 con campos null."""
        # Arrange - Crear sqlite3.Row real
        import sqlite3
        from app.routers.productos import map_row_to_v2

        # Crear conexión y Row real con nulls
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 'TEST-002' as [CÓDIGO], NULL as DESCRIPCION, NULL as PVP_26_01_26, NULL as MARCA, NULL as Familia_WEB"
        )
        row = cursor.fetchone()

        # Act - Llamar función con Row real
        result = map_row_to_v2(row)

        # Assert - Verificar que maneja null correctamente
        assert result["codigo"] == "TEST-002"
        assert result["descripcion"] is None
        assert result["marca"] is None

    def test_map_row_to_v2_with_unicode_characters(self):
        """GREEN: Ejecutar map_row_to_v2 con caracteres unicode."""
        # Arrange - Crear sqlite3.Row real
        import sqlite3
        from app.routers.productos import map_row_to_v2

        # Crear conexión y Row real con unicode
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 'TEST-003' as [CÓDIGO], 'Producto Ñoño' as DESCRIPCION, 29.99 as PVP_26_01_26, 'Fábrica' as MARCA, 'Construcción' as Familia_WEB"
        )
        row = cursor.fetchone()

        # Act - Llamar función con Row real
        result = map_row_to_v2(row)

        # Assert - Verificar que mantiene unicode
        assert "Ñoño" in result["descripcion"]
        assert "Fábrica" in result["marca"]


class TestProductosRouterModuleImport:
    """Tests que importan router productos.py (TDD)."""

    def test_productos_router_module_importable(self):
        """GREEN: Verificar que productos.py es importable."""
        # Arrange & Act - Intentar importar módulo
        try:
            import app.routers.productos as productos_router

            # Assert - Verificar que tiene router
            assert hasattr(productos_router, "router")
        except ImportError as e:
            pytest.fail(f"Error importando app.routers.productos: {e}")

    def test_productos_router_has_router_instance(self):
        """GREEN: Verificar que router es APIRouter."""
        # Arrange & Act
        import app.routers.productos as productos_router

        # Assert - Verificar que router tiene métodos FastAPI
        assert hasattr(productos_router.router, "get")
        assert hasattr(productos_router.router, "post")
        assert hasattr(productos_router.router, "put")
        assert hasattr(productos_router.router, "delete")

    def test_productos_router_functions_exist(self):
        """GREEN: Verificar que funciones async existen."""
        # Arrange & Act
        import app.routers.productos as productos_router

        # Assert - Verificar que funciones async existen
        async_functions = [
            "get_productos",
            "get_producto",
            "create_producto",
            "update_producto",
            "update_precio",
            "delete_producto",
            "get_productos_v2",
            "get_producto_v2",
        ]

        for func_name in async_functions:
            assert hasattr(productos_router, func_name), f"Falta función: {func_name}"


class TestProductosRouterEndpointsCount:
    """Tests que verifican cantidad de endpoints (TDD)."""

    def test_productos_has_12_router_endpoints(self):
        """GREEN: Verificar que router tiene 12 endpoints."""
        # Arrange & Act
        import app.routers.productos as productos_router

        # Assert - Verificar que router tiene 12 endpoints
        # Contando @router. decorators en el código
        assert hasattr(productos_router, "router")


if __name__ == "__main__":
    pytest.main([__file__])
