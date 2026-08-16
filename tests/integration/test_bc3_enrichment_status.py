"""Focused integration coverage for authenticated BC3 enrichment job status."""

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.domain.services.producto import ProductoService
from app.interfaces.http.productos import get_producto_service


class StatusRepository:
    def __init__(self) -> None:
        self.write_calls = 0
        self.statuses = {
            "job-001": {
                "job_id": "job-001",
                "status": "completed",
                "total_items": 3,
                "updated_items": 1,
                "unchanged_items": 1,
                "missing_items": 1,
                "created_at": datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc),
                "completed_at": datetime(2026, 8, 16, 10, 1, tzinfo=timezone.utc),
                "items": [
                    {"codigo": "BC3-002", "result_status": "unchanged", "error_message": None},
                    {"codigo": "BC3-001", "result_status": "updated", "error_message": None},
                    {"codigo": "BC3-404", "result_status": "missing", "error_message": "not found"},
                ],
                "idempotency_key": "must-not-leak",
                "request_hash": "must-not-leak",
                "requested_by": "must-not-leak",
                "source_pdf_hash": "must-not-leak",
                "ai_model": "must-not-leak",
                "bc3_descripcion_corta": "must-not-leak",
            }
        }

    def get_bc3_enrichment_job_status(self, job_id: str) -> dict[str, Any] | None:
        return self.statuses.get(job_id)

    def save(self, producto: Any) -> None:
        self.write_calls += 1
        raise AssertionError("status retrieval must not write")

    def apply_bc3_enrichment(self, *args: Any, **kwargs: Any) -> None:
        self.write_calls += 1
        raise AssertionError("status retrieval must not apply")


@pytest.fixture
def bc3_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    from app.interfaces.http import productos

    monkeypatch.setattr(
        productos,
        "get_settings",
        lambda: SimpleNamespace(bc3_api_keys_list=["test-bc3-key"]),
    )
    return {"X-API-Key": "test-bc3-key"}


def _client(client: TestClient, repository: StatusRepository) -> TestClient:
    app = cast(Any, client).app
    app.dependency_overrides.clear()
    app.dependency_overrides[get_producto_service] = lambda: ProductoService(cast(Any, repository))
    return client


def test_status_requires_dedicated_bc3_api_key(client: TestClient) -> None:
    response = client.get("/api/productos/bc3/v1/enrichment/jobs/job-001")

    assert response.status_code == 401


def test_status_returns_safe_audit_projection(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    response = _client(client, StatusRepository()).get(
        "/api/productos/bc3/v1/enrichment/jobs/job-001", headers=bc3_headers
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == "job-001"
    assert payload["status"] == "completed"
    assert payload["total_items"] == 3
    assert payload["updated_items"] == 1
    assert payload["unchanged_items"] == 1
    assert payload["missing_items"] == 1
    assert set(payload) == {
        "job_id",
        "status",
        "total_items",
        "updated_items",
        "unchanged_items",
        "missing_items",
        "created_at",
        "completed_at",
        "items",
    }
    assert "must-not-leak" not in response.text


def test_status_items_have_deterministic_codigo_order(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    response = _client(client, StatusRepository()).get(
        "/api/productos/bc3/v1/enrichment/jobs/job-001", headers=bc3_headers
    )

    assert response.status_code == 200
    assert [item["codigo"] for item in response.json()["items"]] == [
        "BC3-001",
        "BC3-002",
        "BC3-404",
    ]


def test_status_returns_404_for_unknown_job(
    client: TestClient, bc3_headers: dict[str, str]
) -> None:
    response = _client(client, StatusRepository()).get(
        "/api/productos/bc3/v1/enrichment/jobs/unknown", headers=bc3_headers
    )

    assert response.status_code == 404


def test_status_does_not_write(client: TestClient, bc3_headers: dict[str, str]) -> None:
    repository = StatusRepository()

    response = _client(client, repository).get(
        "/api/productos/bc3/v1/enrichment/jobs/job-001", headers=bc3_headers
    )

    assert response.status_code == 200
    assert repository.write_calls == 0
