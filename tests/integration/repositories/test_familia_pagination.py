"""Integration tests for Familia repository pagination methods."""

from sqlalchemy.orm import Session
from app.infrastructure.repositories.familia import SQLAlchemyFamiliaRepository


def test_familia_repository_pagination_basic(sqlalchemy_session: Session) -> None:
    ."""Test familia repository pagination with basic pagination."""
    repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

    dto: dict = {"page": 1, "per_page": 10, "offset": 0, "sort": None, "filters": {}}

    items, total = repo.buscar_familias_paginado(dto)

    assert len(items) <= 10
    assert total >= len(items)
    assert total > 0  # Should have at least some families


def test_familia_repository_pagination_with_filters(
    sqlalchemy_session: Session,
) -> None:
    """Test familia repository pagination with filters applied."""
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
    # Verify that search results contain the search term
    for item in items:
        assert "iluminación" in item.nombre.lower()


def test_familia_repository_sorting(sqlalchemy_session: Session) -> None:
    """Test familia repository sorting by name."""
    repo = SQLAlchemyFamiliaRepository(sqlalchemy_session)

    dto: dict = {
        "page": 1,
        "per_page": 10,
        "offset": 0,
        "sort": "nombre:asc",
        "filters": {},
    }

    items, _ = repo.buscar_familias_paginado(dto)

    # Verify sorting (names should be in ascending order)
    nombres = [item.nombre for item in items]
    assert nombres == sorted(nombres)


def test_familia_repository_text_search(sqlalchemy_session: Session) -> None:
    """Test familia repository text search functionality."""
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
    # Verify that search results contain LED in family name
    for item in items:
        assert "led" in item.nombre.lower()
