# BC3-Suite API Client Contract

## Scope

This document defines the private API-DISANO contract consumed by BC3-Suite.
The base URL is the deployed API-DISANO URL. All paths below include the `/api` prefix.

## Authentication

Send the dedicated BC3 credential in every request:

```http
X-API-Key: <BC3 credential>
```

The credential is configured server-side as `BC3_API_KEYS` and in BC3-Suite as
`DISANO_API_KEY`. Do not commit it or include it in logs.

The general `API_KEYS` credential is not valid for BC3 routes.

## Product endpoints

### List products

```http
GET /api/productos/bc3/v1?page=1&per_page=20&buscar=<term>&marca=<brand>&familia=<family>
```

- `page`: 1-based page number; default `1`.
- `per_page`: page size from `1` to `100`; default `20`.
- `buscar`, `marca`, `familia`: optional filters.

Returns the private BC3 product page contract. The exact response schema is also
published in the deployment's OpenAPI document at `/openapi.json`.

### Get one product

```http
GET /api/productos/bc3/v1/{codigo}
```

Returns one product in the private BC3 contract. A missing product returns `404`.

## Enrichment workflow

The workflow is bounded to at most 100 items per request. Each item must contain a
non-empty `codigo` and may contain only these enrichment fields:

- `bc3_descripcion_corta`
- `bc3_descripcion_larga`
- `bc3_descripcion_completa`
- `bc3_product_type`

Unknown JSON fields and duplicate product codes are rejected.

### Preview changes (read-only)

```http
POST /api/productos/bc3/v1/enrichment/preview
Content-Type: application/json
X-API-Key: <BC3 credential>
```

Request:

```json
{
  "items": [
    {
      "codigo": "33036139",
      "bc3_descripcion_corta": "LED 12W E27",
      "bc3_descripcion_larga": "Luminaria LED de 12W con base E27",
      "bc3_descripcion_completa": null,
      "bc3_product_type": "luminaria"
    }
  ]
}
```

Response:

```json
{
  "items": [
    {
      "codigo": "33036139",
      "changes": [
        {
          "field": "bc3_descripcion_corta",
          "current_value": "Old value",
          "proposed_value": "LED 12W E27"
        }
      ]
    }
  ],
  "missing_codes": []
}
```

Preview never persists catalog changes.

### Apply changes (transactional and idempotent)

```http
POST /api/productos/bc3/v1/enrichment/apply
Content-Type: application/json
X-API-Key: <BC3 credential>
Idempotency-Key: <unique key for this exact payload>
```

The request body is the same as preview. The `Idempotency-Key` is required,
1–200 characters, and must be reused only to replay the exact same payload.

Response:

```json
{
  "updated_codes": ["33036139"],
  "unchanged_codes": [],
  "job_id": "<job id>",
  "status": "completed",
  "missing_codes": []
}
```

Important outcomes:

- `200`: transaction accepted and durable result returned.
- `404`: one or more requested products do not exist.
- `409`: the idempotency key was used with a different payload, or another job is
  currently in progress.
- `422`: invalid request, duplicate codes, too many items, or unknown fields.

### Read apply status

```http
GET /api/productos/bc3/v1/enrichment/jobs/{job_id}
X-API-Key: <BC3 credential>
```

Response fields:

- `job_id`
- `status`
- `total_items`
- `updated_items`
- `unchanged_items`
- `missing_items`
- `created_at`
- `completed_at`
- `items[]` with `codigo`, `result_status`, and optional `error_message`

A missing job returns `404`.

## Recommended BC3-Suite sequence

1. Send `preview` for a batch.
2. Review `items[].changes` and `missing_codes`.
3. Send `apply` with a new idempotency key.
4. Persist the returned `job_id`.
5. Read the job endpoint and record the final status.
6. On a network retry, reuse the same idempotency key and identical body; do not
   generate a new key for the same logical operation.

## Operational checks

- API health: `GET /health`.
- OpenAPI schema: `GET /openapi.json`.
- Authentication failures return `401`.
- Do not send the BC3 credential in query parameters.
