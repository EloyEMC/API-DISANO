"""API-DISANO release module.

This module is part of the reviewed BC3/PostgreSQL release.
"""

import json
import os
import subprocess
import sys

from fastapi import FastAPI

from app.config import Settings
from app.interfaces.http.productos import router


def test_bc3_api_keys_setting_accepts_string_and_list_without_exposure():
    """Test."""
    string_settings = Settings(environment="testing", bc3_api_keys="bc3-key-a, bc3-key-b")
    list_settings = Settings(environment="testing", bc3_api_keys=["bc3-key-c"])

    assert string_settings.bc3_api_keys_list == ["bc3-key-a", "bc3-key-b"]
    assert list_settings.bc3_api_keys_list == ["bc3-key-c"]


def test_production_docs_enabled_configures_public_urls():
    """Test."""
    environment = os.environ.copy()
    environment.update({"ENVIRONMENT": "production", "DOCS_ENABLED": "true"})
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import asyncio, json; from app.main import app; "
                "root = next(route.endpoint for route in app.routes if route.path == '/'); "
                "print(json.dumps([app.docs_url, app.redoc_url, app.openapi_url, "
                "asyncio.run(root())['endpoints']['documentacion']]))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert json.loads(result.stdout.strip()) == [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/docs",
    ]


def test_openapi_documents_versioned_contracts_and_api_key_authentication():
    """Test."""
    app = FastAPI()
    app.include_router(router, prefix="/api")

    document = app.openapi()
    assert "/api/productos/v1" in document["paths"]
    assert "/api/productos/v1/{codigo}" in document["paths"]
    assert "/api/productos/v3" in document["paths"]
    assert "/api/productos/bc3/v1" in document["paths"]
    assert "/api/productos/bc3/v1/{codigo}" in document["paths"]
    preview_path = document["paths"]["/api/productos/bc3/v1/enrichment/preview"]["post"]
    apply_path = document["paths"]["/api/productos/bc3/v1/enrichment/apply"]["post"]
    assert apply_path["security"]
    idempotency_header = next(
        parameter
        for parameter in apply_path["parameters"]
        if parameter["name"] == "Idempotency-Key"
    )
    assert idempotency_header["in"] == "header"
    assert idempotency_header["required"] is True
    assert apply_path["requestBody"]["content"]["application/json"]["schema"]
    assert apply_path["responses"]["200"]["content"]["application/json"]["schema"]
    assert preview_path["security"]
    assert preview_path["requestBody"]["content"]["application/json"]["schema"]
    assert preview_path["responses"]["200"]["content"]["application/json"]["schema"]
    schemes = document["components"]["securitySchemes"].values()
    assert any(scheme["type"] == "apiKey" and scheme["name"] == "X-API-Key" for scheme in schemes)
    assert document["paths"]["/api/productos/bc3/v1"]["get"]["security"]
    assert document["paths"]["/api/productos/bc3/v1/{codigo}"]["get"]["security"]
    request_ref = preview_path["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_ref = preview_path["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    request_schema = document["components"]["schemas"][request_ref.rsplit("/", 1)[-1]]
    response_schema = document["components"]["schemas"][response_ref.rsplit("/", 1)[-1]]
    assert set(request_schema["properties"]) == {"items"}
    assert set(response_schema["properties"]) == {"items", "missing_codes"}
    apply_response_ref = apply_path["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    apply_response_schema = document["components"]["schemas"][apply_response_ref.rsplit("/", 1)[-1]]
    assert set(apply_response_schema["properties"]) == {
        "updated_codes",
        "unchanged_codes",
        "job_id",
        "status",
        "missing_codes",
    }
    assert all(
        secret not in str(preview_path) for secret in ("pvp", "dto", "up_log", "u_caja", "raee")
    )
    assert "bc3-key-a" not in str(document)
    assert "bc3-key-c" not in str(document)
