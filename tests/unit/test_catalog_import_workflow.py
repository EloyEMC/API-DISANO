import pytest
from pydantic import ValidationError

from app.application.dto.catalog_import import (
    CatalogImportRequest,
    CatalogProductRow,
    row_to_raw_values,
)


def row(**overrides):
    value = {
        "code": "NEW-1",
        "brand": "Brand",
        "web_code": "W1",
        "reference": "R1",
        "ean": "123",
        "description": "New product",
        "pvp": 10.0,
        "estado": "NEW",
        "etim": "ETIM",
        "raee": 1.0,
        "dimensions": {"length_mm": 1},
        "weights": {"gross_kg": 1},
        "volumes": {"dm3": 1},
        "family": {"web": "F"},
        "imagen": "a.jpg",
        "img_url": "https://example/a.jpg",
        "url_ficha_tec": "https://example/f.pdf",
    }
    value.update(overrides)
    return value


def test_catalog_row_is_strict_and_requires_new_status():
    with pytest.raises(ValidationError):
        CatalogProductRow(**row(unknown="nope"))
    with pytest.raises(ValidationError):
        CatalogProductRow(**row(estado="EXISTING"))


def test_canonical_payload_omits_unset_bc3_fields_for_hash_compatibility():
    from app.application.dto.catalog_import import canonical_catalog_payload

    payload = canonical_catalog_payload([CatalogProductRow(**row())])

    assert "bc3_descripcion_corta" not in payload
    assert '"url_ficha_tec"' in payload


def test_catalog_row_accepts_optional_bc3_fields():
    product = CatalogProductRow(
        **row(
            bc3_descripcion_corta="Short",
            bc3_descripcion_larga="Long",
            bc3_descripcion_completa="Complete",
            bc3_product_type="columna",
            bc3_descripcion_corta_ca="Curt",
            bc3_descripcion_larga_ca="Llarg",
            bc3_descripcion_corta_gl="Curta",
            bc3_descripcion_larga_gl="Longa",
        )
    )

    assert product.bc3_descripcion_corta == "Short"
    assert product.bc3_descripcion_larga == "Long"
    assert product.bc3_descripcion_completa == "Complete"
    assert product.bc3_product_type == "columna"
    assert product.bc3_descripcion_corta_ca == "Curt"
    assert product.bc3_descripcion_larga_ca == "Llarg"
    assert product.bc3_descripcion_corta_gl == "Curta"
    assert product.bc3_descripcion_larga_gl == "Longa"


def test_row_to_raw_values_normalizes_long_description_alias():
    values = row_to_raw_values(CatalogProductRow(**row(bc3_descripcion_completa="Complete only")))

    assert values["bc3_descripcion_larga"] == "Complete only"
    assert values["bc3_descripcion_completa"] == "Complete only"


def test_row_to_raw_values_maps_import_owned_bc3_fields_without_timestamp():
    values = row_to_raw_values(
        CatalogProductRow(
            **row(
                bc3_descripcion_corta="Short",
                bc3_descripcion_larga="Long",
                bc3_descripcion_completa="Complete",
                bc3_product_type="columna",
                bc3_descripcion_corta_ca="Curt",
                bc3_descripcion_larga_ca="Llarg",
                bc3_descripcion_corta_gl="Curta",
                bc3_descripcion_larga_gl="Longa",
            )
        )
    )

    assert {
        "bc3_descripcion_corta": values["bc3_descripcion_corta"],
        "bc3_descripcion_larga": values["bc3_descripcion_larga"],
        "bc3_descripcion_completa": values["bc3_descripcion_completa"],
        "bc3_product_type": values["bc3_product_type"],
        "bc3_descripcion_corta_ca": values["bc3_descripcion_corta_ca"],
        "bc3_descripcion_larga_ca": values["bc3_descripcion_larga_ca"],
        "bc3_descripcion_corta_gl": values["bc3_descripcion_corta_gl"],
        "bc3_descripcion_larga_gl": values["bc3_descripcion_larga_gl"],
    } == {
        "bc3_descripcion_corta": "Short",
        "bc3_descripcion_larga": "Long",
        "bc3_descripcion_completa": "Complete",
        "bc3_product_type": "columna",
        "bc3_descripcion_corta_ca": "Curt",
        "bc3_descripcion_larga_ca": "Llarg",
        "bc3_descripcion_corta_gl": "Curta",
        "bc3_descripcion_larga_gl": "Longa",
    }
    assert "bc3_processed_at" not in values


def test_row_to_raw_values_preserves_canonical_new_product_fields():
    values = row_to_raw_values(
        CatalogProductRow(
            **row(
                dto="10%",
                up_log=2.5,
                u_caja=6,
                raee_l=0.25,
                raee_t=1.25,
                dimensions={
                    "length_m": 1.0,
                    "length_mm": 1000,
                    "width_m": 0.5,
                    "width_mm": 500,
                    "height_m": 0.2,
                    "height_mm": 200,
                },
                weights={
                    "gross_kg": 3.0,
                    "gross_g": 3000,
                    "net_kg": 2.5,
                    "net_g": 2500,
                },
                volumes={"dm3": 10.0, "cm3": 10000},
                family={
                    "serie_familia_1": "SERIE",
                    "web": "WEB",
                    "catalog": "CAT",
                    "catalog_ptl": "PTL",
                },
            )
        )
    )

    assert values == {
        "codigo": "NEW-1",
        "marca": "Brand",
        "codigo_web": "W1",
        "referencia": "R1",
        "ean_13": 123,
        "descripcion": "New product",
        "dto": "10%",
        "pvp": 10.0,
        "up_log": 2.5,
        "u_caja": 6,
        "clase_etim": "ETIM",
        "raee_a": 1.0,
        "raee_l": 0.25,
        "raee_t": 1.25,
        "longitud_m": 1.0,
        "longitud_mm": 1000,
        "ancho_m": 0.5,
        "ancho_mm": 500,
        "alto_m": 0.2,
        "altura_mm": 200,
        "peso_bruto_kg": 3.0,
        "peso_bruto_gr": 3000,
        "peso_neto_kg": 2.5,
        "peso_neto_gr": 2500,
        "volumen_dm3": 10.0,
        "cm3": 10000,
        "serie_familia_1": "SERIE",
        "familia_web": "WEB",
        "familia_catalogo": "CAT",
        "familia_catalogo_ptl": "PTL",
        "imagen": "a.jpg",
        "img_url": "https://example/a.jpg",
        "url_ficha_tec": "https://example/f.pdf",
        "bc3_descripcion_corta": None,
        "bc3_descripcion_larga": None,
        "bc3_descripcion_completa": None,
        "bc3_product_type": None,
        "bc3_descripcion_corta_ca": None,
        "bc3_descripcion_larga_ca": None,
        "bc3_descripcion_corta_gl": None,
        "bc3_descripcion_larga_gl": None,
    }


def test_row_to_raw_values_serializes_numeric_ean_as_integer():
    values = row_to_raw_values(CatalogProductRow(**row(ean="8012952193268")))

    assert values["ean_13"] == 8012952193268
    assert isinstance(values["ean_13"], int)


@pytest.mark.parametrize("ean", [None, "", "   "])
def test_row_to_raw_values_serializes_missing_ean_as_none(ean):
    values = row_to_raw_values(CatalogProductRow(**row(ean=ean)))

    assert values["ean_13"] is None


@pytest.mark.parametrize("ean", ["not-a-number", "123.5", "12O3"])
def test_row_to_raw_values_rejects_invalid_or_non_integral_ean(ean):
    product = CatalogProductRow(**row(ean=ean))

    with pytest.raises(ValueError, match="EAN must be a whole number"):
        row_to_raw_values(product)


def test_preview_rejects_duplicate_and_existing_codes_without_writes():
    from app.application.services.catalog_import import CatalogImportService

    class Repo:
        def catalog_import_preview(self, **kwargs):
            return kwargs

        def catalog_import_approve(self, *args, **kwargs):
            return None

        def catalog_import_apply(self, *args, **kwargs):
            return None

        def existing_catalog_codes(self, codes):
            return {"EXISTING"}

    request = CatalogImportRequest(
        source_snapshot_id="workbook-1",
        source_hash="a" * 64,
        github_pr={
            "repository": "acme/catalog",
            "pull_request_number": 1,
            "head_sha": "b" * 40,
        },
        rows=[
            CatalogProductRow(**row(code="DUP")),
            CatalogProductRow(**row(code="DUP")),
            CatalogProductRow(**row(code="EXISTING")),
        ],
    )
    result = CatalogImportService(Repo()).preview(request, "actor")
    assert result["accepted_codes"] == ["DUP"]
    assert {item["reason"] for item in result["rejected"]} == {
        "duplicate_code",
        "existing_code",
    }
