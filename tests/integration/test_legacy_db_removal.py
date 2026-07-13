"""Integration tests to verify legacy database connection removed

Tests that hexagonal database connection is used instead of legacy sqlite3
"""

import inspect


class TestLegacyDatabaseRemoval:
    """Tests to verify legacy database connection has been removed"""

    def test_no_sqlite3_import_in_hexagonal_code(self):
        """Test that hexagonal code doesn't import sqlite3"""
        # Check domain layer
        import app.domain.services.producto
        import app.domain.repositories.producto

        for module in [app.domain.services.producto, app.domain.repositories.producto]:
            source = inspect.getsource(module)
            assert "sqlite3" not in source.lower(), (
                f"{module.__name__} still uses sqlite3"
            )

    def test_no_direct_sqlite_in_hexagonal_http(self):
        """Test that hexagonal HTTP layer doesn't use sqlite3"""
        import app.interfaces.http.productos as productos_http
        import app.interfaces.http.familias as familias_http
        import app.interfaces.http.bc3 as bc3_http

        for module in [productos_http, familias_http, bc3_http]:
            source = inspect.getsource(module)
            assert "sqlite3" not in source.lower(), (
                f"{module.__name__} still uses sqlite3"
            )

    def test_infrastructure_uses_sqlalchemy(self):
        """Test that infrastructure uses SQLAlchemy instead of sqlite3"""
        import app.infrastructure.repositories.producto
        import app.infrastructure.repositories.familia

        for module in [
            app.infrastructure.repositories.producto,
            app.infrastructure.repositories.familia,
        ]:
            source = inspect.getsource(module)
            assert "from sqlalchemy" in source or "import sqlalchemy" in source, (
                f"{module.__name__} doesn't use SQLAlchemy"
            )

    def test_legacy_database_module_removed(self):
        """Test that legacy app.database module is not imported"""
        try:
            import app.database

            # If it exists, check if it's still being used
            import app.main

            source = inspect.getsource(app.main)
            assert "from app.database" not in source, (
                "main.py still imports app.database"
            )
        except ImportError:
            # Best case: module doesn't exist
            pass

    def test_hexagonal_database_connection_used(self):
        """Test that hexagonal database connection is used"""
        import app.interfaces.http.productos as productos_http

        source = inspect.getsource(productos_http)

        # Should use hexagonal database connection patterns
        hexagonal_patterns = [
            "get_db_dependency",  # Hexagonal DI pattern
            "SessionLocal",  # Alternative hexagonal pattern
            "get_db_session",  # Alternative hexagonal pattern
        ]

        has_hexagonal = any(pattern in source for pattern in hexagonal_patterns)
        assert has_hexagonal, "HTTP layer doesn't use hexagonal database connection"
