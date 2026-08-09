"""API-DISANO release module.

This module is part of the reviewed BC3/PostgreSQL release.
"""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def provision_bc3_enrichment_schema(test_db_path: Path) -> None:
    """Provision the durable BC3 tables for this integration module."""
    migration = Path(__file__).parents[2] / "migration" / "03_add_bc3_enrichment_jobs.sql"
    with sqlite3.connect(test_db_path) as connection:
        connection.executescript(migration.read_text(encoding="utf-8"))
        connection.execute("DELETE FROM bc3_enrichment_job_items")
        connection.execute("DELETE FROM bc3_enrichment_jobs")
        connection.commit()


def test_private_bc3_uses_dedicated_credentials(client: TestClient, monkeypatch) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(
        environment="testing",
        api_keys=["client-test-key"],
        bc3_api_keys=["bc3-test-key"],
    )
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)

    client_key = client.get("/api/productos/bc3/v1", headers={"X-API-Key": "client-test-key"})
    bc3_key = client.get("/api/productos/bc3/v1", headers={"X-API-Key": "bc3-test-key"})

    assert client_key.status_code == 401
    assert bc3_key.status_code == 200


def test_private_bc3_runtime_reads_raw_product_fields(
    client: TestClient,
    auth_headers: dict,
    db_session: sqlite3.Connection,
    monkeypatch,
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(
        environment="testing",
        api_keys=auth_headers["X-API-Key"],
        bc3_api_keys="test-bc3-key",
    )
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    bc3_headers = {"X-API-Key": "test-bc3-key"}

    row = db_session.execute(
        """
    SELECT "CÓDIGO" AS codigo
    FROM productos
    WHERE "DTO." IS NOT NULL
      AND "U.P.LOG" IS NOT NULL
      AND "U.CAJA" IS NOT NULL
      AND "Peso bruto KG" IS NOT NULL
      AND "Longitud M" IS NOT NULL
      AND "CM3" IS NOT NULL
    LIMIT 1
    """
    ).fetchone()
    assert row is not None
    codigo = row["codigo"]

    unauthenticated = client.get(f"/api/productos/bc3/v1/{codigo}")
    assert unauthenticated.status_code == 401

    detail = client.get(f"/api/productos/bc3/v1/{codigo}", headers=bc3_headers)
    assert detail.status_code == 200
    detail_data = detail.json()
    for field in ("dto", "up_log", "u_caja", "peso_bruto_kg", "longitud_m", "cm3"):
        assert detail_data[field] is not None

    listing = client.get(
        "/api/productos/bc3/v1",
        params={"buscar": codigo, "per_page": 1},
        headers=bc3_headers,
    )
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert items and items[0]["codigo"] == codigo
    assert items[0]["dto"] is not None
    assert items[0]["up_log"] is not None

    public = client.get(f"/api/productos/v1/{codigo}")
    assert public.status_code == 200
    public_data = public.json()
    assert "dto" not in public_data
    assert "up_log" not in public_data
    assert "peso_bruto_kg" not in public_data


def test_private_bc3_enrichment_preview_is_read_only_and_reports_changes(
    client: TestClient,
    auth_headers: dict,
    db_session: sqlite3.Connection,
    monkeypatch,
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="preview-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    headers = {"X-API-Key": "preview-key"}
    codigo = db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 1').fetchone()[0]
    before = db_session.execute(
        'SELECT bc3_descripcion_corta, bc3_product_type FROM productos WHERE "CÓDIGO" = ?',
        (codigo,),
    ).fetchone()

    response = client.post(
        "/api/productos/bc3/v1/enrichment/preview",
        headers=headers,
        json={"items": [{"codigo": codigo, "bc3_descripcion_corta": "Preview text"}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["missing_codes"] == []
    assert payload["items"][0]["codigo"] == codigo
    assert payload["items"][0]["changes"] == [
        {
            "field": "bc3_descripcion_corta",
            "current_value": before[0],
            "proposed_value": "Preview text",
        }
    ]
    assert "pvp" not in str(payload)
    assert "dto" not in str(payload)
    assert (
        db_session.execute(
            'SELECT bc3_descripcion_corta, bc3_product_type FROM productos WHERE "CÓDIGO" = ?',
            (codigo,),
        ).fetchone()
        == before
    )


def test_private_bc3_enrichment_preview_validation_and_authentication(
    client: TestClient, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="preview-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    endpoint = "/api/productos/bc3/v1/enrichment/preview"
    valid = {"X-API-Key": "preview-key"}

    assert client.post(endpoint, json={"items": []}, headers=valid).status_code == 422
    assert (
        client.post(
            endpoint,
            json={"items": [{"codigo": "A"}, {"codigo": "A"}]},
            headers=valid,
        ).status_code
        == 422
    )
    assert (
        client.post(
            endpoint,
            json={"items": [{"codigo": "A", "pvp": 1}]},
            headers=valid,
        ).status_code
        == 422
    )
    missing = client.post(
        endpoint,
        json={"items": [{"codigo": "does-not-exist", "bc3_product_type": "x"}]},
        headers=valid,
    )
    assert missing.status_code == 200
    assert missing.json()["missing_codes"] == ["does-not-exist"]
    assert client.post(endpoint, json={"items": [{"codigo": "A"}]}).status_code == 401


def test_private_bc3_enrichment_apply_updates_only_allowed_fields(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    codigo = db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 1').fetchone()[0]
    current = db_session.execute(
        'SELECT bc3_descripcion_corta, bc3_product_type FROM productos WHERE "CÓDIGO" = ?',
        (codigo,),
    ).fetchone()
    short_value = "Applied text" if current[0] != "Applied text" else "Applied text 2"
    type_value = "luminaria" if current[1] != "luminaria" else "luminaria 2"

    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"X-API-Key": "apply-key", "Idempotency-Key": "test-apply-key"},
        json={
            "items": [
                {
                    "codigo": codigo,
                    "bc3_descripcion_corta": short_value,
                    "bc3_product_type": type_value,
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["updated_codes"] == [codigo]
    assert response.json()["unchanged_codes"] == []
    assert response.json()["status"] == "completed"
    job_id = response.json()["job_id"]
    assert (
        db_session.execute(
            "SELECT status FROM bc3_enrichment_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()[0]
        == "completed"
    )
    row = db_session.execute(
        'SELECT bc3_descripcion_corta, bc3_product_type, bc3_processed_at FROM productos WHERE "CÓDIGO" = ?',
        (codigo,),
    ).fetchone()
    assert tuple(row)[:2] == (short_value, type_value)
    assert row[2] is not None


def test_private_bc3_enrichment_apply_replay_is_unchanged(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    codigo = db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 1').fetchone()[0]
    current = db_session.execute(
        'SELECT bc3_product_type FROM productos WHERE "CÓDIGO" = ?', (codigo,)
    ).fetchone()[0]
    value = "replay-value" if current != "replay-value" else "replay-value-2"
    payload = {"items": [{"codigo": codigo, "bc3_product_type": value}]}
    headers = {"X-API-Key": "apply-key"}

    headers["Idempotency-Key"] = "test-apply-key"
    first = client.post("/api/productos/bc3/v1/enrichment/apply", headers=headers, json=payload)
    second = client.post("/api/productos/bc3/v1/enrichment/apply", headers=headers, json=payload)

    assert first.status_code == second.status_code == 200
    assert first.json()["updated_codes"] == [codigo]
    assert second.json() == first.json()


def test_private_bc3_enrichment_apply_reports_mixed_changed_and_unchanged(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    codes = [
        row[0] for row in db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 2').fetchall()
    ]
    assert len(codes) == 2
    current = db_session.execute(
        'SELECT bc3_product_type FROM productos WHERE "CÓDIGO" = ?', (codes[1],)
    ).fetchone()[0]

    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"X-API-Key": "apply-key", "Idempotency-Key": "test-apply-key"},
        json={
            "items": [
                {"codigo": codes[0], "bc3_product_type": "mixed-change"},
                {"codigo": codes[1], "bc3_product_type": current},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["updated_codes"] == [codes[0]]
    assert response.json()["unchanged_codes"] == [codes[1]]


def test_private_bc3_enrichment_apply_missing_code_performs_zero_writes(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    codigo = db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 1').fetchone()[0]
    before = db_session.execute(
        'SELECT bc3_descripcion_corta, bc3_product_type, bc3_processed_at FROM productos WHERE "CÓDIGO" = ?',
        (codigo,),
    ).fetchone()

    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"X-API-Key": "apply-key", "Idempotency-Key": "test-apply-key"},
        json={
            "items": [
                {"codigo": codigo, "bc3_descripcion_corta": "new"},
                {"codigo": "missing-code", "bc3_product_type": "x"},
            ]
        },
    )

    assert response.status_code == 404
    assert "missing-code" in str(response.json())
    assert (
        db_session.execute(
            'SELECT bc3_descripcion_corta, bc3_product_type, bc3_processed_at FROM productos WHERE "CÓDIGO" = ?',
            (codigo,),
        ).fetchone()
        == before
    )
    assert tuple(
        db_session.execute("SELECT status, missing_items FROM bc3_enrichment_jobs").fetchone()
    ) == ("failed", 1)


def test_private_bc3_enrichment_apply_rejects_idempotency_conflict(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    codigo = db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 1').fetchone()[0]
    headers = {"X-API-Key": "apply-key", "Idempotency-Key": "conflict-key"}
    first = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers=headers,
        json={"items": [{"codigo": codigo, "bc3_product_type": "one"}]},
    )
    second = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers=headers,
        json={"items": [{"codigo": codigo, "bc3_product_type": "two"}]},
    )
    assert first.status_code == 200
    assert second.status_code == 409


def test_private_bc3_enrichment_apply_rejects_unauthenticated_and_forbidden_fields(
    client: TestClient, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    endpoint = "/api/productos/bc3/v1/enrichment/apply"
    payload = {"items": [{"codigo": "A", "pvp": 10}]}

    assert client.post(endpoint, json=payload).status_code == 401
    assert (
        client.post(endpoint, headers={"X-API-Key": "apply-key"}, json=payload).status_code == 422
    )


def test_private_bc3_enrichment_apply_requires_idempotency_key(
    client: TestClient, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="apply-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)

    response = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"X-API-Key": "apply-key"},
        json={"items": [{"codigo": "A"}]},
    )

    assert response.status_code == 422


def test_private_bc3_enrichment_job_status_returns_completed_audit(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="status-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    codigo = db_session.execute('SELECT "CÓDIGO" FROM productos LIMIT 1').fetchone()[0]
    apply = client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"X-API-Key": "status-key", "Idempotency-Key": "status-key-1"},
        json={"items": [{"codigo": codigo, "bc3_product_type": "status-type"}]},
    )
    assert apply.status_code == 200
    response = client.get(
        f"/api/productos/bc3/v1/enrichment/jobs/{apply.json()['job_id']}",
        headers={"X-API-Key": "status-key"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["items"] == [
        {"codigo": codigo, "result_status": "updated", "error_message": None}
    ]
    assert not {"bc3_product_type", "source_pdf_hash", "ai_model", "confidence"} & set(
        response.json()["items"][0]
    )


def test_private_bc3_enrichment_job_status_returns_failed_missing_code(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="status-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    client.post(
        "/api/productos/bc3/v1/enrichment/apply",
        headers={"X-API-Key": "status-key", "Idempotency-Key": "status-key-2"},
        json={"items": [{"codigo": "missing-status-code", "bc3_product_type": "x"}]},
    )
    job_id = db_session.execute(
        "SELECT job_id FROM bc3_enrichment_jobs WHERE idempotency_key = ?",
        ("status-key-2",),
    ).fetchone()[0]
    response = client.get(
        f"/api/productos/bc3/v1/enrichment/jobs/{job_id}",
        headers={"X-API-Key": "status-key"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["missing_items"] == 1
    assert response.json()["items"][0]["result_status"] == "missing"


def test_private_bc3_enrichment_job_status_requires_auth_and_known_job(
    client: TestClient, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="status-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    endpoint = "/api/productos/bc3/v1/enrichment/jobs/unknown-job"
    assert client.get(endpoint).status_code == 401
    assert client.get(endpoint, headers={"X-API-Key": "status-key"}).status_code == 404


def test_private_bc3_enrichment_job_status_does_not_expose_sensitive_fields(
    client: TestClient, db_session: sqlite3.Connection, monkeypatch
) -> None:
    """Test."""
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(environment="testing", bc3_api_keys="status-key")
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    db_session.execute(
        """
        INSERT INTO bc3_enrichment_jobs
            (job_id, idempotency_key, request_hash, status, total_items,
             updated_items, unchanged_items, missing_items)
        VALUES (?, ?, ?, 'failed', 1, 0, 0, 1)
        """,
        ("sensitive-job", "sensitive-key", "hash"),
    )
    db_session.execute(
        """
        INSERT INTO bc3_enrichment_job_items
            (job_id, codigo, bc3_descripcion_corta, source_pdf_hash, ai_model,
             confidence, result_status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, 'failed', ?)
        """,
        (
            "sensitive-job",
            "CODE",
            "secret proposed text",
            "secret hash",
            "secret model",
            0.9,
            "failed",
        ),
    )
    db_session.commit()
    response = client.get(
        "/api/productos/bc3/v1/enrichment/jobs/sensitive-job",
        headers={"X-API-Key": "status-key"},
    )
    assert response.status_code == 200
    assert set(response.json()["items"][0]) == {
        "codigo",
        "result_status",
        "error_message",
    }
    assert "secret proposed text" not in response.text
    assert "secret hash" not in response.text
    assert "secret model" not in response.text
