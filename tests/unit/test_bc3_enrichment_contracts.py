from typing import Any

import pytest
from pydantic import ValidationError

from app.application.dto.bc3_enrichment import (
    BC3EnrichmentChange,
    BC3EnrichmentItem,
    BC3EnrichmentPreviewItem,
    BC3EnrichmentPreviewRequest,
    BC3EnrichmentPreviewResponse,
    MAX_BC3_ENRICHMENT_BATCH_SIZE,
    hash_bc3_enrichment_items,
)


def _item(codigo: str = "BC3-001") -> BC3EnrichmentItem:
    return BC3EnrichmentItem(
        codigo=codigo,
        bc3_descripcion_corta="Short description",
    )


def _item_payload(codigo: str = "BC3-001") -> dict[str, str]:
    return {"codigo": codigo, "bc3_descripcion_corta": "Short description"}


def test_preview_request_normalizes_codigo_before_contract_use() -> None:
    request = BC3EnrichmentPreviewRequest(
        items=[BC3EnrichmentItem(codigo="  BC3-001  ", bc3_descripcion_corta="Short description")]
    )

    assert request.items[0].codigo == "BC3-001"


def test_preview_request_rejects_codes_duplicate_after_normalization() -> None:
    with pytest.raises(ValidationError, match="duplicate codigo"):
        BC3EnrichmentPreviewRequest(
            items=[
                _item("BC3-001"),
                _item(" BC3-001 "),
            ]
        )


@pytest.mark.parametrize(
    "items",
    [
        [],
        [_item(f"BC3-{index:03d}") for index in range(MAX_BC3_ENRICHMENT_BATCH_SIZE + 1)],
    ],
    ids=["empty", "over_maximum"],
)
def test_preview_request_enforces_batch_bounds(items: list[BC3EnrichmentItem]) -> None:
    with pytest.raises(ValidationError):
        BC3EnrichmentPreviewRequest(items=items)


@pytest.mark.parametrize(
    "model, payload",
    [
        (BC3EnrichmentItem, {**_item_payload(), "name": "not a BC3 field"}),
        (
            BC3EnrichmentPreviewRequest,
            {"items": [_item_payload()], "unexpected": "not a BC3 field"},
        ),
    ],
    ids=["item", "request"],
)
def test_contracts_reject_non_bc3_fields(model: Any, payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        model.model_validate(payload)


def test_request_hash_is_deterministic_for_equivalent_mapping_order() -> None:
    first = [{"codigo": "BC3-001", "bc3_descripcion_corta": "Short", "bc3_product_type": None}]
    second = [{"bc3_product_type": None, "bc3_descripcion_corta": "Short", "codigo": "BC3-001"}]

    assert hash_bc3_enrichment_items(first) == hash_bc3_enrichment_items(second)


def test_preview_response_exposes_only_items_and_missing_codes() -> None:
    response = BC3EnrichmentPreviewResponse(
        items=[
            BC3EnrichmentPreviewItem(
                codigo="BC3-001",
                changes=[
                    BC3EnrichmentChange(
                        field="bc3_descripcion_corta",
                        current_value=None,
                        proposed_value="Short description",
                    )
                ],
            )
        ],
        missing_codes=["BC3-404"],
    )

    assert set(response.model_dump()) == {"items", "missing_codes"}
    assert response.model_dump()["missing_codes"] == ["BC3-404"]
    assert response.model_dump()["items"][0]["codigo"] == "BC3-001"
