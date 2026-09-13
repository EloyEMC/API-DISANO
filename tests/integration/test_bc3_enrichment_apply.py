"""Focused integration coverage for the authenticated BC3 enrichment workflow."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.application.dto.bc3_enrichment import (
    BC3_ENRICHMENT_FIELDS,
    hash_bc3_enrichment_items,
)
from app.application.services.github_approval import GitHubApprovalEvidence
from app.domain.services.producto import ProductoService
from app.interfaces.http.productos import get_producto_service

GITHUB_PR = {
    "repository": "acme/catalogue",
    "pull_request_number": 42,
    "head_sha": "a" * 40,
}


class FakeGitHubVerifier:
    def verify(self, reference):
        return GitHubApprovalEvidence(
            reference.repository,
            reference.pull_request_number,
            reference.head_sha,
            1,
            datetime.now(timezone.utc),
        )


class ApplyRepository:
    def __init__(self):
        self.products = {
            "BC3-001": SimpleNamespace(
                codigo="BC3-001",
                imagen="IP_generic.jpg",
                img_url="https://cdn.example/IP_generic.jpg",
                url_ficha_tec="https://cdn.example/old-ficha.pdf",
                bc3_descripcion_corta="old",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type=None,
                bc3_descripcion_corta_ca="Existing Catalan short",
                bc3_descripcion_larga_ca="Existing Catalan long",
                bc3_descripcion_corta_gl="Existing Galician short",
                bc3_descripcion_larga_gl="Existing Galician long",
            )
        }
        self.snapshots = {}
        self.jobs = {}
        self.writes = 0
        self.fail = False

    def get_private_by_codigos(self, codigos):
        return {code: self.products[code] for code in codigos if code in self.products}

    def create_bc3_preview(self, items, actor_id, source_snapshot_id, github_pr):
        self.snapshots["preview-001"] = {
            "items": items,
            "approved": False,
            "github_pr": github_pr,
        }
        return {
            "preview_id": "preview-001",
            "request_hash": hash_bc3_enrichment_items(items),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        }

    def approve_bc3_preview(self, preview_id, actor_id, scope, github_pr, evidence):
        self.snapshots[preview_id]["approved"] = True

    def apply_bc3_enrichment(self, items, key, preview_id, actor_id, github_pr):
        snapshot = self.snapshots.get(preview_id)
        if not snapshot or not snapshot["approved"]:
            raise ValueError("preview is not approved")
        for job in self.jobs.values():
            if job["key"] == key:
                if job["hash"] != hash_bc3_enrichment_items(items):
                    raise ValueError(
                        "idempotency key has already been used with a different request"
                    )
                return deepcopy(job["result"])
        before = deepcopy(self.products)
        try:
            updated, unchanged, missing = [], [], []
            for item in items:
                product = self.products.get(item["codigo"])
                if product is None:
                    missing.append(item["codigo"])
                    continue
                values = {field: item[field] for field in BC3_ENRICHMENT_FIELDS if field in item}
                if all(getattr(product, field) == value for field, value in values.items()):
                    unchanged.append(item["codigo"])
                else:
                    for field, value in values.items():
                        setattr(product, field, value)
                    updated.append(item["codigo"])
                if self.fail:
                    raise RuntimeError("forced rollback")
            result = {
                "updated_codes": updated,
                "unchanged_codes": unchanged,
                "missing_codes": missing,
                "job_id": "job-001",
                "status": "completed",
            }
            self.jobs["job-001"] = {
                "key": key,
                "hash": hash_bc3_enrichment_items(items),
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
    app.dependency_overrides[get_producto_service] = lambda: ProductoService(
        cast(Any, repository), cast(Any, FakeGitHubVerifier())
    )
    return client


@pytest.fixture
def bc3_headers(monkeypatch):
    from app.interfaces.http import productos

    monkeypatch.setattr(
        productos,
        "get_settings",
        lambda: SimpleNamespace(
            bc3_api_keys_list=["test-bc3-key"],
            bc3_approval_keys_list=["test-approval-key"],
            bc3_approval_scope="bc3-enrichment",
        ),
    )
    return {
        "X-API-Key": "test-bc3-key",
        "X-BC3-Actor": "test-actor",
        "X-BC3-Approval-Key": "test-approval-key",
    }


def _payload(items):
    return {"items": items, "github_pr": GITHUB_PR}


def _preview_and_approve(client, repository, headers, items):
    preview = _client(client, repository).post(
        "/api/productos/bc3/v1/enrichment/preview",
        headers=headers,
        json=_payload(items),
    )
    assert preview.status_code == 200
    approval = client.post(
        "/api/productos/bc3/v1/enrichment/approve",
        headers=headers,
        json={"preview_id": preview.json()["preview_id"], "github_pr": GITHUB_PR},
    )
    assert approval.status_code == 200
    return preview.json()["preview_id"]


def test_apply_requires_dedicated_bc3_api_key(client):
    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"Idempotency-Key": "apply-001"},
        json=_payload(
            [
                {"codigo": "BC3-001"},
            ]
        ),
    )
    assert response.status_code == 401


def test_apply_requires_preview_approval_and_updates_product(client, bc3_headers):
    repository = ApplyRepository()
    items = [
        {
            "codigo": "BC3-001",
            "imagen": "IP_22965876-00.jpg",
            "img_url": "https://cdn.example/IP_22965876-00.jpg",
            "url_ficha_tec": "https://cdn.example/new-ficha.pdf",
            "bc3_descripcion_corta": "new",
            "bc3_descripcion_corta_ca": "Curt",
        }
    ]
    preview_id = _preview_and_approve(client, repository, bc3_headers, items)
    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={**bc3_headers, "Idempotency-Key": "apply-001"},
        json={**_payload(items), "preview_id": preview_id},
    )
    assert response.status_code == 200
    assert response.json()["updated_codes"] == ["BC3-001"]
    assert repository.products["BC3-001"].bc3_descripcion_corta == "new"
    assert repository.products["BC3-001"].bc3_descripcion_corta_ca == "Curt"
    assert repository.products["BC3-001"].imagen == "IP_22965876-00.jpg"
    assert repository.products["BC3-001"].img_url == "https://cdn.example/IP_22965876-00.jpg"
    assert repository.products["BC3-001"].url_ficha_tec == "https://cdn.example/new-ficha.pdf"


def test_apply_replays_same_key_and_rejects_different_hash(client, bc3_headers):
    repository = ApplyRepository()
    items = [{"codigo": "BC3-001", "bc3_descripcion_corta": "new"}]
    preview_id = _preview_and_approve(client, repository, bc3_headers, items)
    payload = {**_payload(items), "preview_id": preview_id}
    headers = {**bc3_headers, "Idempotency-Key": "apply-002"}
    first = client.post("/api/productos/bc3/v1/enrichment/apply", headers=headers, json=payload)
    replay = client.post("/api/productos/bc3/v1/enrichment/apply", headers=headers, json=payload)
    conflict = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers=headers,
        json={
            **_payload([{"codigo": "BC3-001", "bc3_descripcion_corta": "other"}]),
            "preview_id": preview_id,
        },
    )
    assert first.status_code == replay.status_code == 200
    assert replay.json() == first.json()
    assert conflict.status_code == 409
    assert repository.writes == 1


def test_apply_rolls_back_product_changes_on_failure(client, bc3_headers):
    repository = ApplyRepository()
    items = [{"codigo": "BC3-001", "bc3_descripcion_corta": "must-rollback"}]
    preview_id = _preview_and_approve(client, repository, bc3_headers, items)
    repository.fail = True
    with pytest.raises(RuntimeError, match="forced rollback"):
        client.post(
            "/api/productos/bc3/v1/enrichment/apply",
            headers={**bc3_headers, "Idempotency-Key": "apply-003"},
            json={**_payload(items), "preview_id": preview_id},
        )
    assert repository.products["BC3-001"].bc3_descripcion_corta == "old"
