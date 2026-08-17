from fastapi.testclient import TestClient


def test_private_bc3_uses_dedicated_credentials(client: TestClient, monkeypatch) -> None:
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
    db_session,
    monkeypatch,
) -> None:
    from app.config import Settings
    import app.interfaces.http.productos as productos_module

    settings = Settings(
        environment="testing",
        api_keys=auth_headers["X-API-Key"],
        bc3_api_keys="test-bc3-key",
    )
    monkeypatch.setattr(productos_module, "get_settings", lambda: settings)
    bc3_headers = {"X-API-Key": "test-bc3-key"}

    from sqlalchemy import text

    row = (
        db_session.execute(
            text(
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
            )
        )
        .mappings()
        .first()
    )
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
