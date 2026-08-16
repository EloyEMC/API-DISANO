from fastapi import FastAPI

from app.config import Settings
from app.interfaces.http.productos import router


PRIVATE_FIELDS = {
    "dto",
    "up_log",
    "u_caja",
    "clase_etim",
    "peso_bruto_kg",
    "peso_bruto_gr",
    "peso_neto_kg",
    "peso_neto_gr",
    "longitud_m",
    "longitud_mm",
    "ancho_m",
    "ancho_mm",
    "alto_m",
    "altura_mm",
    "volumen_dm3",
    "cm3",
}


def _openapi_document() -> dict:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app.openapi()


def _schema(document: dict, reference: dict) -> dict:
    return document["components"]["schemas"][reference["$ref"].rsplit("/", 1)[-1]]


def test_bc3_api_keys_setting_accepts_string_and_list_without_exposure() -> None:
    string_settings = Settings(environment="testing", bc3_api_keys="bc3-key-a, bc3-key-b")
    list_settings = Settings(environment="testing", bc3_api_keys=["bc3-key-c"])

    assert string_settings.bc3_api_keys_list == ["bc3-key-a", "bc3-key-b"]
    assert list_settings.bc3_api_keys_list == ["bc3-key-c"]


def test_production_docs_are_disabled_by_default() -> None:
    assert Settings(environment="production").docs_enabled is False


def test_development_docs_remain_enabled_when_configured() -> None:
    assert Settings(environment="development", docs_enabled=True).docs_enabled is True


def test_openapi_lists_public_and_private_read_contracts_with_pagination() -> None:
    document = _openapi_document()
    paths = document["paths"]

    assert {
        "/api/productos/v1",
        "/api/productos/v1/{codigo}",
        "/api/productos/v3",
        "/api/productos/bc3/v1",
        "/api/productos/bc3/v1/{codigo}",
    } <= paths.keys()

    public_page = _schema(
        document,
        paths["/api/productos/v1"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ],
    )
    public_item = _schema(
        document,
        paths["/api/productos/v1/{codigo}"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"],
    )
    private_page = _schema(
        document,
        paths["/api/productos/bc3/v1"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ],
    )
    private_item = _schema(
        document,
        paths["/api/productos/bc3/v1/{codigo}"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"],
    )

    assert set(public_page["properties"]) == {
        "items",
        "pagination",
        "filters_applied",
        "sorting_applied",
    }
    assert set(public_item["properties"]) & {"codigo", "descripcion", "marca", "pvp"} == {
        "codigo",
        "descripcion",
        "marca",
        "pvp",
    }
    assert PRIVATE_FIELDS.isdisjoint(public_item["properties"])
    assert set(private_item["properties"]) >= PRIVATE_FIELDS
    assert private_page["properties"]["items"]["items"]["$ref"].endswith("ProductoBC3Response")


def test_openapi_documents_enrichment_requests_responses_security_and_replay_contract() -> None:
    document = _openapi_document()
    paths = document["paths"]
    enrichment_prefix = "/api/productos/bc3/v1/enrichment"
    preview = paths[f"{enrichment_prefix}/preview"]["post"]
    apply = paths[f"{enrichment_prefix}/apply"]["post"]
    status = paths[f"{enrichment_prefix}/jobs/{{job_id}}"]["get"]

    operations = (
        paths["/api/productos/bc3/v1"]["get"],
        paths["/api/productos/bc3/v1/{codigo}"]["get"],
        preview,
        apply,
        status,
    )
    for operation in operations:
        assert operation["security"]
        assert set(operation["security"][0]) == {"APIKeyHeader"}

    idempotency = next(
        parameter for parameter in apply["parameters"] if parameter["name"] == "Idempotency-Key"
    )
    assert idempotency["in"] == "header"
    assert idempotency["required"] is True

    preview_request = _schema(
        document,
        preview["requestBody"]["content"]["application/json"]["schema"],
    )
    preview_response = _schema(
        document,
        preview["responses"]["200"]["content"]["application/json"]["schema"],
    )
    apply_response = _schema(
        document,
        apply["responses"]["200"]["content"]["application/json"]["schema"],
    )
    status_response = _schema(
        document,
        status["responses"]["200"]["content"]["application/json"]["schema"],
    )

    assert set(preview_request["properties"]) == {"items"}
    assert set(preview_response["properties"]) == {"items", "missing_codes"}
    assert set(apply_response["properties"]) == {
        "updated_codes",
        "unchanged_codes",
        "job_id",
        "status",
        "missing_codes",
    }
    assert set(status_response["properties"]) == {
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

    schemes = document["components"]["securitySchemes"].values()
    assert any(scheme["type"] == "apiKey" and scheme["name"] == "X-API-Key" for scheme in schemes)
    assert "bc3-key-a" not in str(document)
    assert "bc3-key-c" not in str(document)
