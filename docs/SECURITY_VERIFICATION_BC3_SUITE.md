# BC3-Suite Security Verification

Security verification for the API-DISANO integration boundary with BC3-Suite was completed on 2026-08-15. This record covers the reviewed repository state and does not represent a deployment or external notification.

## Integration boundary

- BC3-Suite consumes API-DISANO through HTTP only.
- API-DISANO owns its database; BC3-Suite does not connect to or share that database.
- Product mutations use the protected `/api/admin/productos` contract.
- Clients send `X-Admin-API-Key` with the configured administrator key. API-DISANO validates it against `ADMIN_API_KEYS`; the key must not be committed or logged.

See the [product HTTP interface](../app/interfaces/http/productos.py), [API-key validation](../app/security/api_key.py), and [application settings](../app/config.py).

## Security changes verified

| Commit | Purpose |
| --- | --- |
| [`b877ecd`](https://github.com/EloyEMC/API-DISANO/commit/b877ecd) | Harden legacy security middleware. |
| [`fab590f`](https://github.com/EloyEMC/API-DISANO/commit/fab590f) | Align the security guide with the legacy migration. |
| [`619342f`](https://github.com/EloyEMC/API-DISANO/commit/619342f) | Resolve scoped Ruff findings. |
| [`4fd3a98`](https://github.com/EloyEMC/API-DISANO/commit/4fd3a98) | Align authentication and Redis verification tests. |
| [`f52ee7e`](https://github.com/EloyEMC/API-DISANO/commit/f52ee7e) | Remove an unused OTP test local. |

## Verification evidence

- Test suite: 125 tests passed.
- Ruff: 0 findings.
- Bandit: 0 findings across 1,094 lines of code.
- Test output included one unrelated Pydantic deprecation warning.

## Operational notes for BC3-Suite

- Use the configured API base URL and the HTTP endpoints; do not configure API-DISANO database access in BC3-Suite.
- Send the administrator key only in the `X-Admin-API-Key` header for product mutation requests.
- Store the key in the consumer's secret configuration, never in source code, request logs, or user-visible errors.
- Treat an HTTP 403 response as a missing or invalid administrator key and stop the mutation; do not retry with ordinary API credentials.
- Coordinate key rotation between API-DISANO configuration and BC3-Suite secret configuration before retiring the previous key.
