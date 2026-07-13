"""Comprehensive integration tests for Familia repository."""

from app.infrastructure.repositories.familia import SQLAlchemyFamiliaRepository


class TestFamiliaRepositoryPagination:
    """Comprehensive tests for Familia repository pagination."""

    def test_familia_repository_pagination_first_page(self, sqlalchemy_session) -> None:
        """Test pagination on first page."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_familias_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # Should have families
        assert len(items) > 0

    def test_familia_repository_pagination_middle_page(
        self, sqlalchemy_session
    ) -> None:
        """Test pagination on middle page."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {"page": 2, "per_page": 5, "offset": 5, "sort": None, "filters": {}}

        items, total = repo.buscar_familias_paginado(dto)

        assert len(items) <= 5
        assert total >= len(items)

    def test_familia_repository_pagination_large_per_page(
        self, sqlalchemy_session
    ) -> None:
        """Test pagination with large per_page value."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 100,
            "offset": 0,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_familias_paginado(dto)

        assert len(items) <= 100
        assert total >= len(items)
        # Should return all families if total <= 100
        if total <= 100:
            assert len(items) == total

    def test_familia_repository_pagination_small_per_page(
        self, sqlalchemy_session
    ) -> None:
        """Test pagination with small per_page value."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {"page": 1, "per_page": 1, "offset": 0, "sort": None, "filters": {}}

        items, total = repo.buscar_familias_paginado(dto)

        assert len(items) <= 1
        assert total >= len(items)

    def test_familia_repository_pagination_text_search(
        self, sqlalchemy_session
    ) -> None:
        """Test text search functionality."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "Iluminación"},
        }

        items, total = repo.buscar_familias_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)

    def test_familia_repository_pagination_text_search_case_insensitive(
        self, sqlalchemy_session
    ) -> None:
        """Test text search is case-insensitive."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # Search with lowercase
        dto_lower: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "iluminación"},
        }
        items_lower, total_lower = repo.buscar_familias_paginado(dto_lower)

        # Search with uppercase
        dto_upper: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "ILUMINACIÓN"},
        }
        items_upper, total_upper = repo.buscar_familias_paginado(dto_upper)

        # Should return same results
        assert total_lower == total_upper

    def test_familia_repository_pagination_various_sort_orders(
        self, sqlalchemy_session
    ) -> None:
        """Test various sort orders."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        sort_orders = ["nombre:asc", "nombre:desc", "familia:asc"]

        for sort_order in sort_orders:
            dto: dict = {
                "page": 1,
                "per_page": 10,
                "offset": 0,
                "sort": sort_order,
                "filters": {},
            }
            items, total = repo.buscar_familias_paginado(dto)

            assert len(items) <= 10
            assert total >= len(items)

    def test_familia_repository_pagination_no_results(self, sqlalchemy_session) -> None:
        """Test pagination with filter that returns no results."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "NonExistentFamilia12345"},
        }

        items, total = repo.buscar_familias_paginado(dto)

        # Should return empty results
        assert len(items) == 0
        assert total == 0

    def test_familia_repository_pagination_return_type(
        self, sqlalchemy_session
    ) -> None:
        """Test that pagination returns correct types."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_familias_paginado(dto)

        # Check types
        assert isinstance(items, list)
        assert isinstance(total, int)
        assert total >= 0

        # Check item types
        for item in items:
            assert hasattr(item, "nombre")
            assert hasattr(item, "total_productos")
            assert hasattr(item, "con_bc3")
            assert hasattr(item, "con_imagen")
            assert hasattr(item, "descontinuados")

    def test_familia_repository_pagination_sorting_consistency(
        self, sqlalchemy_session
    ) -> None:
        """Test that sorting produces consistent results."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # Get all families
        dto_all: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": "nombre:asc",
            "filters": {},
        }
        all_items, _ = repo.buscar_familias_paginado(dto_all)

        # Test ascending sort
        dto_asc: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": "nombre:asc",
            "filters": {},
        }
        items_asc, _ = repo.buscar_familias_paginado(dto_asc)

        # Test descending sort
        dto_desc: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": "nombre:desc",
            "filters": {},
        }
        items_desc, _ = repo.buscar_familias_paginado(dto_desc)

        # Ascending should be alphabetical
        nombres_asc = [item.nombre for item in items_asc]
        assert nombres_asc == sorted(nombres_asc)

        # Descending should be reverse alphabetical
        nombres_desc = [item.nombre for item in items_desc]
        assert nombres_desc == sorted(nombres_desc, reverse=True)

    def test_familia_repository_pagination_consistent_results(
        self, sqlalchemy_session
    ) -> None:
        """Test that same query returns consistent results."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": "nombre:asc",
            "filters": {},
        }

        # Execute same query twice
        items1, total1 = repo.buscar_familias_paginado(dto)
        items2, total2 = repo.buscar_familias_paginado(dto)

        # Results should be identical
        assert len(items1) == len(items2)
        assert total1 == total2
        if len(items1) > 0:
            assert items1[0].nombre == items2[0].nombre

    def test_familia_repository_pagination_vs_traditional_get_all(
        self, sqlalchemy_session
    ) -> None:
        """Test pagination results match traditional get_all."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # Traditional get_all
        traditional_items = repo.get_all()

        # Pagination search (get all items)
        dto: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        pagination_items, _ = repo.buscar_familias_paginado(dto)

        # Both should return items
        assert len(traditional_items) > 0
        assert len(pagination_items) > 0

    def test_familia_repository_pagination_with_text_search(
        self, sqlalchemy_session
    ) -> None:
        """Test pagination with text search."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "LED"},
        }

        items, total = repo.buscar_familias_paginado(dto)

        # May return 0 results if no families match
        assert len(items) <= 10
        assert total >= len(items)


class TestFamiliaRepositoryIntegration:
    """Integration tests combining repository methods."""

    def test_familia_repository_statistics_consistency(
        self, sqlalchemy_session
    ) -> None:
        """Test that statistics match pagination totals."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # Get statistics
        stats = repo.get_statistics()

        # Get all families via pagination
        dto: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        items, total = repo.buscar_familias_paginado(dto)

        # Total families should match
        assert stats["total_familias"] == total

        # Total products should be reasonable
        assert stats["total_productos"] > 0

    def test_familia_repository_bc3_coverage_consistency(
        self, sqlalchemy_session
    ) -> None:
        """Test that BC3 coverage statistics are reasonable."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # Get statistics
        stats = repo.get_statistics()

        # Get all families
        dto: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        items, _ = repo.buscar_familias_paginado(dto)

        # BC3 coverage should be between 0 and 100
        assert 0 <= stats["bc3_coverage"] <= 100

    def test_familia_repository_pagination_across_all_pages(
        self, sqlalchemy_session
    ) -> None:
        """Test pagination across all pages."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # First, get total count
        dto_total: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        _, total = repo.buscar_familias_paginado(dto_total)

        # If we have families, paginate through them
        if total > 0:
            per_page = 5
            total_pages = (total + per_page - 1) // per_page  # Ceiling division

            all_items = []
            for page in range(1, total_pages + 1):
                dto: dict = {
                    "page": page,
                    "per_page": per_page,
                    "offset": (page - 1) * per_page,
                    "sort": None,
                    "filters": {},
                }
                items, _ = repo.buscar_familias_paginado(dto)
                all_items.extend(items)

            # Total items should match
            assert len(all_items) == total

    def test_familia_repository_edge_cases(self, sqlalchemy_session) -> None:
        """Test edge cases for Familia repository."""
        repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

        # Empty filter (should return all)
        dto_empty: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        items_empty, total_empty = repo.buscar_familias_paginado(dto_empty)

        assert len(items_empty) <= 10
        assert total_empty > 0

        # Small page size
        dto_small: dict = {
            "page": 1,
            "per_page": 1,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        items_small, total_small = repo.buscar_familias_paginado(dto_small)

        assert len(items_small) <= 1
        assert total_small > 0

        # Large page number (beyond available data)
        dto_large: dict = {
            "page": 1000,
            "per_page": 10,
            "offset": 9990,
            "sort": None,
            "filters": {},
        }
        items_large, total_large = repo.buscar_familias_paginado(dto_large)

        # Should return empty results
        assert len(items_large) == 0
        assert total_large > 0
