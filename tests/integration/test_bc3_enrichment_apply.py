"""Focused integration coverage for authenticated BC3 enrichment apply."""

from copy import deepcopy
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.dto.bc3_enrichment import (
    BC3_ENRICHMENT_FIELDS,
    hash_bc3_enrichment_items,
)
from app.domain.services.producto import ProductoService
from app.interfaces.http.productos import get_producto_service


class ApplyRepository:
    def __init__(self) -> None:
        self.products = {
            "BC3-001": SimpleNamespace(
                codigo="BC3-001",
                bc3_descripcion_corta="old",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type=None,
            ),
            "BC3-002": SimpleNamespace(
                codigo="BC3-002",
                bc3_descripcion_corta="same",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type=None,
            ),
        }
        self.jobs: dict[str, dict[str, Any]] = {}
        self.writes = 0
        self.fail = False

    def apply_bc3_enrichment(self, items: list[dict], key: str) -> dict[str, Any]:
        request_hash = hash_bc3_enrichment_items(items)
        for job in self.jobs.values():
            if job["key"] == key:
                if job["hash"] != request_hash:
                    raise ValueError(
                        "idempotency key has already been used with a different request"
                    )
                return deepcopy(job["result"])
        before = deepcopy(self.products)
        result = {
            "updated_codes": [],
            "unchanged_codes": [],
            "missing_codes": [],
            "job_id": str(uuid4()),
            "status": "completed",
        }
        try:
            for item in items:
                product = self.products.get(item["codigo"])
                if product is None:
                    result["missing_codes"].append(item["codigo"])
                    continue
                values = {field: item.get(field) for field in BC3_ENRICHMENT_FIELDS}
                if all(getattr(product, field) == value for field, value in values.items()):
                    result["unchanged_codes"].append(item["codigo"])
                else:
                    for field, value in values.items():
                        setattr(product, field, value)
                    result["updated_codes"].append(item["codigo"])
                if self.fail:
                    raise RuntimeError("forced rollback")
            self.jobs[result["job_id"]] = {
                "key": key,
                "hash": request_hash,
                "result": deepcopy(result),
            }
            self.writes += 1
            return result
        except Exception:
            self.products = before
            raise


def _client(client: TestClient, repository: ApplyRepository) -> TestClient:
    app = cast(Any, client).app
    app.dependency_overrides.clear()
    app.dependency_overrides[get_producto_service] = lambda: ProductoService(cast(Any, repository))
    return client


@pytest.fixture
def bc3_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    from app.interfaces.http import productos

    monkeypatch.setattr(
        productos,
        "get_settings",
        lambda: SimpleNamespace(bc3_api_keys_list=["test-bc3-key"]),
    )
    return {"X-API-Key": "test-bc3-key"}


def test_apply_requires_dedicated_bc3_api_key(client: TestClient) -> None:
    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"Idempotency-Key": "apply-001"},
        json={"items": [{"codigo": "BC3-001", "bc3_descripcion_corta": "New"}]},
    )
    assert response.status_code == 401


def test_apply_updates_unchanged_and_missing_items(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    repository = ApplyRepository()
    response = _client(client, repository).post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={**bc3_headers, "Idempotency-Key": "apply-001"},
        json={
            "items": [
                {"codigo": "BC3-001", "bc3_descripcion_corta": "new"},
                {"codigo": "BC3-002", "bc3_descripcion_corta": "same"},
                {"codigo": "BC3-404", "bc3_descripcion_corta": "missing"},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["updated_codes"] == ["BC3-001"]
    assert response.json()["unchanged_codes"] == ["BC3-002"]
    assert response.json()["missing_codes"] == ["BC3-404"]
    assert set(response.json()) == {
        "updated_codes",
        "unchanged_codes",
        "missing_codes",
        "job_id",
        "status",
    }
    assert repository.products["BC3-001"].bc3_descripcion_corta == "new"


def test_apply_replays_same_key_and_rejects_different_hash(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    repository = ApplyRepository()
    test_client = _client(client, repository)
    payload = {"items": [{"codigo": "BC3-001", "bc3_descripcion_corta": "new"}]}
    first = test_client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={**bc3_headers, "Idempotency-Key": "apply-002"},
        json=payload,
    )
    replay = test_client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={**bc3_headers, "Idempotency-Key": "apply-002"},
        json=payload,
    )
    conflict = test_client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={**bc3_headers, "Idempotency-Key": "apply-002"},
        json={"items": [{"codigo": "BC3-001", "bc3_descripcion_corta": "other"}]},
    )
    assert replay.json() == first.json()
    assert repository.writes == 1
    assert conflict.status_code == 409


def test_apply_rolls_back_product_changes_on_failure(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    repository = ApplyRepository()
    repository.fail = True
    with pytest.raises(RuntimeError, match="forced rollback"):
        _client(client, repository).post(
            "/api/productos/bc3/v1/enrichment/apply",
            headers={**bc3_headers, "Idempotency-Key": "apply-003"},
            json={"items": [{"codigo": "BC3-001", "bc3_descripcion_corta": "must-rollback"}]},
        )
    assert repository.products["BC3-001"].bc3_descripcion_corta == "old"
    assert repository.jobs == {}


def test_apply_requires_idempotency_key_and_validates_payload(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    missing_key = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers=bc3_headers,
        json={"items": [{"codigo": "BC3-001"}]},
    )
    invalid_payload = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={**bc3_headers, "Idempotency-Key": "apply-004"},
        json={"items": [{"codigo": "BC3-001", "unknown": "no"}]},
    )
    assert missing_key.status_code == 422
    assert invalid_payload.status_code == 422
