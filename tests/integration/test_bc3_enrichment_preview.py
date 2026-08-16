"""Focused integration coverage for the authenticated BC3 enrichment preview."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.application.dto.bc3_enrichment import BC3_ENRICHMENT_FIELDS
from app.domain.services.producto import ProductoService
from app.interfaces.http.productos import get_producto_service


class PreviewRepository:
    def __init__(self) -> None:
        self.products = {
            "BC3-001": SimpleNamespace(
                codigo="BC3-001",
                descripcion="Existing product",
                marca="ACME",
                bc3_descripcion_corta="Current short",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type="luminaire",
            ),
            "BC3-002": SimpleNamespace(
                codigo="BC3-002",
                descripcion="Unchanged product",
                marca="ACME",
                bc3_descripcion_corta="Same short",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type=None,
            ),
        }
        self.write_calls = 0

    def get_private_by_codigos(self, codigos: list[str]) -> dict[str, SimpleNamespace]:
        return {codigo: self.products[codigo] for codigo in codigos if codigo in self.products}

    def save(self, producto: Any) -> None:
        self.write_calls += 1
        raise AssertionError("preview must not write")


@pytest.fixture
def bc3_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    from app.interfaces.http import productos

    monkeypatch.setattr(
        productos,
        "get_settings",
        lambda: SimpleNamespace(bc3_api_keys_list=["test-bc3-key"]),
    )
    return {"X-API-Key": "test-bc3-key"}


def _client(client: TestClient, repository: PreviewRepository) -> TestClient:
    app = cast(Any, client).app
    app.dependency_overrides.clear()
    app.dependency_overrides[get_producto_service] = lambda: ProductoService(cast(Any, repository))
    return client


def test_preview_requires_dedicated_bc3_api_key(client: TestClient) -> None:
    response = client.post(
        "/api/productos/bc3/v1/enrichment/preview",
        json={"items": [{"codigo": "BC3-001"}]},
    )

    assert response.status_code == 401


def test_preview_returns_changes_unchanged_items_and_missing_codes(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    repository = PreviewRepository()
    response = _client(client, repository).post(
        "/api/productos/bc3/v1/enrichment/preview",
        headers=bc3_headers,
        json={
            "items": [
                {
                    "codigo": " BC3-001 ",
                    "bc3_descripcion_corta": "New short",
                    "bc3_product_type": "luminaire",
                },
                {"codigo": "BC3-002", "bc3_descripcion_corta": "Same short"},
                {"codigo": "BC3-404", "bc3_descripcion_corta": "Missing"},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "codigo": "BC3-001",
                "changes": [
                    {
                        "field": "bc3_descripcion_corta",
                        "current_value": "Current short",
                        "proposed_value": "New short",
                    }
                ],
            },
            {"codigo": "BC3-002", "changes": []},
        ],
        "missing_codes": ["BC3-404"],
    }
    assert repository.write_calls == 0


def test_preview_validation_rejects_duplicate_codes_and_unknown_fields(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    for items in (
        [{"codigo": "BC3-001"}, {"codigo": " BC3-001 "}],
        [{"codigo": "BC3-001", "not_a_bc3_field": "bad"}],
    ):
        response = client.post(
            "/api/productos/bc3/v1/enrichment/preview",
            headers=bc3_headers,
            json={"items": items},
        )
        assert response.status_code == 422


def test_preview_contract_fields_are_the_only_compared_fields() -> None:
    assert set(BC3_ENRICHMENT_FIELDS) == {
        "bc3_descripcion_corta",
        "bc3_descripcion_larga",
        "bc3_descripcion_completa",
        "bc3_product_type",
    }
