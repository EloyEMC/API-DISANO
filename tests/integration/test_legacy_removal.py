"""Integration tests to verify legacy routers removed

Tests that hexagonal architecture routers still work after removing legacy routers
"""

import inspect


class TestLegacyRouterRemoval:
    """Tests to verify legacy routers have been replaced with hexagonal architecture"""

    def test_hexagonal_productos_router_works(self, client):
        """Test that hexagonal productos router works"""
        response = client.get("/api/productos/v2/list?buscar=test&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_hexagonal_familias_router_works(self, client):
        """Test that hexagonal familias router works"""
        response = client.get("/api/familias/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total_familias" in stats

    def test_hexagonal_bc3_router_works(self, client):
        """Test that hexagonal bc3 router works"""
        response = client.get("/api/bc3/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total" in stats

    def test_no_legacy_router_imports_in_main(self):
        """Test that main.py doesn't import legacy routers"""
        import app.main

        source = inspect.getsource(app.main)
        assert "from app.routers import" not in source
        assert "legacy" not in source.lower()

    def test_all_hexagonal_endpoints_accessible(self, client):
        """Test that all hexagonal endpoints are accessible"""
        # Productos endpoints
        productos_response = client.get("/api/productos/")
        assert productos_response.status_code == 200

        # V2 endpoints
        v2_response = client.get("/api/productos/v2/list?buscar=test&limit=1")
        assert v2_response.status_code == 200

        # Familias endpoints
        familias_response = client.get("/api/familias/")
        assert familias_response.status_code == 200

        # BC3 endpoints (stats is the root endpoint for BC3)
        bc3_response = client.get("/api/bc3/stats")
        assert bc3_response.status_code == 200
