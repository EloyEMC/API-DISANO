# RAEE Integration — API-DISANO ↔ BC3-Suite

> Status: code changes applied (2026-08-03). The DB view change is **deploy-only**
> (run the script on the VPS DB). Until deployed, BC3-Suite RAE columns stay 0.

## What is RAEE?

**RAEE** = *Residuos de Aparatos Eléctricos y Electrónicos* (WEEE). A per-product
recycling fee DISANO publishes alongside the price:

- `RAEE_A` — aparatos (electrical appliances)
- `RAEE_L` — lámparas (lamps)
- `RAEE_T` — total (≈ A + L)

Data is already in the `productos` table (confirmed populated 2026-08:
`RAEE_A` 7112/8288 rows non-zero, e.g. `0.7`; `RAEE_L` 6965/8288, e.g. `0.2`).

## Why this change

BC3-Suite's presupuesto editor shows two read-only RAE columns (RAE A / RAE L),
persists them on each line, and prints them in the PDF (SDD change
`presupuesto-editor-ux`, spec R-4.a/R-4.b/R-4.c/R-5). For that, BC3-Suite reads
RAEE from the **live** DISANO API at two moments: when a product is added, and on
"Actualizar PVP".

**Problem found (2026-08-03):** the live API did NOT expose RAEE, by construction,
in 4 layers:

| Layer (API-DISANO) | Before | After |
|---|---|---|
| `productos` table (model `producto.py`) | ✅ had `RAEE_A/L/T` | unchanged |
| `productos_clean` **view** (model `producto_clean.py`) — the active repo source | ❌ no RAEE | ✅ `raee_a/l/t` |
| `ProductoEntity` (serialized to JSON) | ❌ no RAEE | ✅ `raee_a/l/t` |
| `ProductoModelClean.to_entity()` | ❌ no mapping | ✅ maps RAEE |

So `/api/productos/{codigo}` and the search endpoint returned no RAEE → BC3-Suite
always got 0.

## Changes

### API-DISANO (this project)

1. **`app/infrastructure/models/producto_clean.py`** — added `raee_a`, `raee_l`,
   `raee_t` columns to `ProductoModelClean` + mapped them in `to_entity()`.
2. **`app/domain/entities/producto.py`** — added `raee_a`, `raee_l`, `raee_t`
   `Optional[float]` fields to `ProductoEntity`.
3. **`scripts/add_raee_to_productos_clean.py`** — idempotent, additive script that
   injects the 3 RAEE columns into the `productos_clean` view. It READS the current
   view SQL (so the date-stamped PVP column `[PVP_26_01_26]` and any prod-only
   columns are preserved) and inserts `RAEE_A as raee_a, RAEE_L as raee_l,
   RAEE_T as raee_t` before `FROM productos`. Re-running is a no-op.

### BC3-Suite (consumer)

4. **`app/utils/response_handler.py`** — `parse_product_detail` now extracts
   `raee_a`/`raee_l` (lowercase-first, uppercase fallback) into the parsed product.
5. **`app/blueprints/presupuesto/routes/product_search.py`** +
   **`app/blueprints/presupuesto/routes/pvp_update.py`** — RAE reads are
   lowercase-first (`raee_a`) with uppercase fallback, matching what the API +
   parser now produce. (Old code read `RAEE_A` only → always 0.)

## Deploy order (IMPORTANT)

1. **API-DISANO first** (VPS):
   ```bash
   cd /var/www/API-DISANO        # or wherever it lives on the VPS
   git pull                       # get the model/entity/script changes
   python scripts/add_raee_to_productos_clean.py --db <path/to/tarifa_disano.db>
   # restart the API service (gunicorn/uvicorn) so the model changes load
   ```
   Verify: `GET /api/productos/<code>` JSON now contains `raee_a`/`raee_l`.
2. **BC3-Suite** (VPS): deploy the branch `feature/presupuesto-editor-ux` and run
   `flask db upgrade` (the `20260803_add_raee_to_lineas` migration is additive).

If you deploy BC3-Suite before the API, RAE columns render but read 0 until the
API side is done — harmless, no errors.

## Verification (done on dev DB)

- View script applied idempotently; `productos_clean` now projects
  `raee_a`/`raee_l`/`raee_t`.
- Sample: `('11253300', pvp=150.0, raee_a=0.7, raee_l=0.2, raee_t=0.9)`.
- BC3-Suite: 30 RAE-relevant tests green; `parse_product_detail` extracts RAEE.

## Rollback

- **API view:** recreate `productos_clean` without the 3 RAEE expressions (the
  script's source SQL is printed on dry-run; re-run the original `CREATE VIEW`).
  No table data is touched at any point.
- **BC3-Suite:** `flask db downgrade` drops only the 2 new `raee_*` columns.
