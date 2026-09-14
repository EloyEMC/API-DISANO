"""Focused integration coverage for the authenticated BC3 enrichment preview."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.application.dto.bc3_enrichment import BC3_ENRICHMENT_FIELDS
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
            repository=reference.repository,
            pull_request_number=reference.pull_request_number,
            head_sha=reference.head_sha,
            approval_count=1,
            verified_at=datetime.now(timezone.utc),
        )


class PreviewRepository:
    def __init__(self) -> None:
        self.products = {
            "BC3-001": SimpleNamespace(
                codigo="BC3-001",
                imagen="IP_generic.jpg",
                img_url="https://cdn.example/IP_generic.jpg",
                url_ficha_tec="https://cdn.example/old-ficha.pdf",
                bc3_descripcion_corta="Current short",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type="luminaire",
                bc3_descripcion_corta_ca="Existing Catalan short",
                bc3_descripcion_larga_ca="Existing Catalan long",
                bc3_descripcion_corta_gl="Existing Galician short",
                bc3_descripcion_larga_gl="Existing Galician long",
            ),
            "BC3-002": SimpleNamespace(
                codigo="BC3-002",
                imagen=None,
                img_url=None,
                url_ficha_tec=None,
                bc3_descripcion_corta="Same short",
                bc3_descripcion_larga=None,
                bc3_descripcion_completa=None,
                bc3_product_type=None,
                bc3_descripcion_corta_ca=None,
                bc3_descripcion_larga_ca=None,
                bc3_descripcion_corta_gl=None,
                bc3_descripcion_larga_gl=None,
            ),
        }
        self.write_calls = 0

    def get_private_by_codigos(self, codigos):
        return {code: self.products[code] for code in codigos if code in self.products}

    def create_bc3_preview(self, items, actor_id, source_snapshot_id, github_pr):
        self.write_calls += 1
        return {
            "preview_id": "preview-001",
            "request_hash": "hash-001",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        }


@pytest.fixture
def bc3_headers(monkeypatch):
    from app.interfaces.http import productos

    monkeypatch.setattr(
        productos,
        "get_settings",
        lambda: SimpleNamespace(
            bc3_api_keys_list=["test-bc3-key"],
            bc3_approval_scope="bc3-enrichment",
            bc3_approval_keys_list=["test-approval-key"],
        ),
    )
    return {"X-API-Key": "test-bc3-key", "X-BC3-Actor": "preview-actor"}


def _client(client: TestClient, repository: PreviewRepository) -> TestClient:
    app = cast(Any, client).app
    app.dependency_overrides.clear()
    app.dependency_overrides[get_producto_service] = lambda: ProductoService(
        cast(Any, repository), FakeGitHubVerifier()
    )
    return client


def test_preview_requires_dedicated_bc3_api_key(client):
    response = client.post(
        "/api/productos/bc3/v1/enrichment/preview",
        json={
            "items": [{"codigo": "BC3-001"}],
            "github_pr": GITHUB_PR,
        },
    )
    assert response.status_code == 401


def test_preview_returns_changes_unchanged_items_and_missing_codes(client, bc3_headers):
    repository = PreviewRepository()
    response = _client(client, repository).post(
        "/api/productos/bc3/v1/enrichment/preview",
        headers=bc3_headers,
        json={
            "items": [
                {"codigo": " BC3-001 ", "bc3_descripcion_corta": "New short"},
                {"codigo": "BC3-002", "bc3_descripcion_corta": "Same short"},
                {"codigo": "BC3-404", "bc3_descripcion_corta": "Missing"},
            ],
            "github_pr": GITHUB_PR,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["github_pr"] == GITHUB_PR
    assert data["items"][0]["changes"][0]["field"] == "bc3_descripcion_corta"
    assert data["items"][1]["changes"] == []
    assert data["missing_codes"] == ["BC3-404"]
    assert repository.write_calls == 1


def test_preview_propagates_media_field_changes(client, bc3_headers):
    response = _client(client, PreviewRepository()).post(
        "/api/productos/bc3/v1/enrichment/preview",
        headers=bc3_headers,
        json={
            "items": [
                {
                    "codigo": "BC3-001",
                    "imagen": "IP_22965876-00.jpg",
                    "img_url": "https://cdn.example/IP_22965876-00.jpg",
                    "url_ficha_tec": "https://cdn.example/new-ficha.pdf",
                }
            ],
            "github_pr": GITHUB_PR,
        },
    )

    assert response.status_code == 200
    assert [change["field"] for change in response.json()["items"][0]["changes"]] == [
        "imagen",
        "img_url",
        "url_ficha_tec",
    ]


def test_preview_translation_only_payload_preserves_omitted_fields(client, bc3_headers):
    response = _client(client, PreviewRepository()).post(
        "/api/productos/bc3/v1/enrichment/preview",
        headers=bc3_headers,
        json={
            "items": [{"codigo": "BC3-001", "bc3_descripcion_corta_ca": "Nuevo"}],
            "github_pr": GITHUB_PR,
        },
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["changes"] == [
        {
            "field": "bc3_descripcion_corta_ca",
            "current_value": "Existing Catalan short",
            "proposed_value": "Nuevo",
        }
    ]


def test_preview_validation_rejects_duplicate_codes_unknown_fields_and_missing_pr(
    client, bc3_headers
):
    for payload in (
        {
            "items": [{"codigo": "BC3-001"}, {"codigo": " BC3-001 "}],
            "github_pr": GITHUB_PR,
        },
        {
            "items": [{"codigo": "BC3-001", "not_a_bc3_field": "bad"}],
            "github_pr": GITHUB_PR,
        },
        {"items": [{"codigo": "BC3-001"}]},
    ):
        assert (
            client.post(
                "/api/productos/bc3/v1/enrichment/preview",
                headers=bc3_headers,
                json=payload,
            ).status_code
            == 422
        )


def test_preview_contract_fields_include_ca_and_gl_translations():
    assert set(BC3_ENRICHMENT_FIELDS) == {
        "imagen",
        "img_url",
        "url_ficha_tec",
        "bc3_descripcion_corta",
        "bc3_descripcion_larga",
        "bc3_descripcion_completa",
        "bc3_product_type",
        "bc3_descripcion_corta_ca",
        "bc3_descripcion_larga_ca",
        "bc3_descripcion_corta_gl",
        "bc3_descripcion_larga_gl",
    }
