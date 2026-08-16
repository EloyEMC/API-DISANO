# API client contract

Use the versioned routes below for product clients and BC3 integrations. The generated OpenAPI document is the source of truth for schemas and is available only when documentation is enabled.

## Quick path

1. Send `X-API-Key` on every authenticated request.
2. Use `/api/productos/v1` or `/api/productos/v3` for public products.
3. Use `/api/productos/bc3/v1` for private BC3 reads and enrichment operations.
4. Discover the schema at `/openapi.json` (or interactively at `/docs`) when documentation is enabled.

## Documentation and configuration

Production documentation is **disabled by default**. Set `DOCS_ENABLED=true` explicitly to expose `/docs`, `/redoc`, and `/openapi.json`; local development remains enabled by default. The root response advertises `/docs` only when it is enabled.

| Setting | Contract |
|---|---|
| `DOCS_ENABLED` | Optional boolean. Production defaults to `false`; set it explicitly to enable discovery routes. |
| `API_KEY_HEADER` | Header name used by the API-key dependency; the committed default is `X-API-Key`. |
| `BC3_API_KEYS` | Dedicated credentials for private BC3 routes. Configure them through the deployment secret manager. |
| `API_KEYS` | General API credentials used by the existing application middleware. They do not replace `BC3_API_KEYS` for the private contract. |

Never put credentials, tokens, or database connection values in this document, URLs, examples, or source control.

## Product reads

### Public routes

- `GET /api/productos/v1`
- `GET /api/productos/v1/{codigo}`
- `GET /api/productos/v3` (compatibility alias of the public v1 list contract)

The list accepts `page` (default `1`, minimum `1`), `per_page` (default `20`, maximum `100`), and optional `buscar`, `marca`, and `familia` filters. List responses contain `items`, `pagination`, `filters_applied`, and `sorting_applied`. Detail responses contain one product.

Public product fields include identity, descriptions, classification, family/catalog, media, price, status, RAEE, and BC3 descriptive fields. Public responses intentionally exclude private BC3 discount and logistics fields such as `dto`, `up_log`, `u_caja`, dimensions, volume, and weights.

### Private BC3 routes

- `GET /api/productos/bc3/v1`
- `GET /api/productos/bc3/v1/{codigo}`

These routes require a value from `BC3_API_KEYS` in the `X-API-Key` header. They use the same pagination and filters as public lists, but return the richer `ProductoBC3Response` contract, including the private discount and logistics fields. A missing product returns `404`.

## Enrichment workflow

All enrichment routes require the dedicated BC3 API key.

### Preview

`POST /api/productos/bc3/v1/enrichment/preview`

Request body:

```json
{"items":[{"codigo":"PRODUCT-CODE","bc3_descripcion_corta":"...","bc3_descripcion_larga":"...","bc3_descripcion_completa":"...","bc3_product_type":"..."}]}
```

The batch contains 1–100 unique product codes. Unknown fields are rejected. Preview is read-only and returns `items` with field-level `changes` plus `missing_codes`; it does not write products.

### Apply

`POST /api/productos/bc3/v1/enrichment/apply`

Send the same bounded request shape and a required non-empty `Idempotency-Key` header. Apply validates the complete batch before writing and changes only the four BC3 enrichment fields. Changed rows receive `bc3_processed_at`; the transaction commits atomically or rolls back. The response contains `updated_codes`, `unchanged_codes`, `missing_codes`, `job_id`, and `status`.

Idempotency behavior is deterministic:

- Repeating the same key with the same normalized payload returns the stored result without another write.
- Reusing a key with a different payload returns `409 Conflict`.
- A batch containing missing codes creates a failed durable job and performs zero product writes.

### Job status

`GET /api/productos/bc3/v1/enrichment/jobs/{job_id}`

Use the BC3 key to read the safe status projection. It contains job counters, timestamps, status, and per-item `codigo`, `result_status`, and `error_message`. It does not expose request payloads, credentials, or internal audit data. Unknown job IDs return `404`.

Apply is synchronous in the committed contract; the job record provides durable status and audit projection rather than an active background-worker promise.

## Errors and discovery

Validation failures use FastAPI's standard `422` response. Missing products or jobs return `404`; an idempotency payload conflict returns `409`; missing or invalid BC3 credentials return `401`. Error details are safe API messages and must not be treated as a data schema.

OpenAPI discovery is configuration-dependent: check `/openapi.json` first, then `/docs` or `/redoc` for human-readable exploration. When production documentation is disabled, those routes are intentionally unavailable; authenticated product routes remain the integration contract.

## Compatibility boundary

Legacy unversioned product routes remain available for existing consumers, but new clients should pin `/v1`, `/v3`, or `/bc3/v1`. Do not infer private fields or enrichment behavior from legacy response shapes.
