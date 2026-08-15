# Local PostgreSQL migration harness

This is a local-only preparation and import harness. The locally observed SQLite source contains **8,288 products across 40 columns**.

## Dry run (recommended first)

From the repository root:

```bash
python3 migration/postgres_local_migrate.py \
  --sqlite-path database/tarifa_disano.db \
  --postgres-url postgresql://localhost/api_disano_local \
  --batch-size 500 \
  --dry-run
```

The harness accepts only local PostgreSQL hosts (`localhost`, `127.0.0.1`, or `::1`). It has no non-local override. It never prints the PostgreSQL URL, credentials, raw rows, or secrets.

## Safe migration sequence

Before any write, complete this sequence against local resources only:

1. **Back up** the PostgreSQL target with `migration/local_backup.py postgres-backup`.
2. **Verify** the dump and its adjacent manifest with `migration/local_backup.py verify`.
3. **Migrate transactionally** only after verification, supplying both paths:

   ```bash
   python3 migration/postgres_local_migrate.py \
     --sqlite-path database/tarifa_disano.db \
     --postgres-url postgresql://localhost/api_disano_local \
     --postgres-backup <LOCAL_POSTGRES_DUMP_PATH> \
     --postgres-backup-manifest <LOCAL_POSTGRES_DUMP_PATH>.json
   ```

4. **Verify counts and keys**: the importer checks source/destination counts and duplicate primary keys before committing.
5. **Retain the verified rollback artifact** (dump and manifest) with the pinned revision and migration evidence.

The importer refuses all PostgreSQL writes when either backup path is missing or verification fails. `--dry-run` performs no PostgreSQL write and does not require a backup.

## Health precondition

The local importer accepts only a loopback PostgreSQL URL. The official runtime has a separate, fail-closed contract: `DATABASE_URL` is required and must be a valid PostgreSQL URL with a host and database name. SQLite paths are not valid runtime configuration.

Before treating a production candidate as ready, an authorized operator must run the committed read-only preflight against the approved production environment file:

```bash
python3 scripts/preflight-production.py --env-file <APPROVED_PRODUCTION_ENV_FILE>
```

The preflight also checks the production environment marker, secret configuration, the pinned `psycopg` version, and PostgreSQL connectivity with `SELECT 1`. It exits non-zero without printing the connection URL when any requirement fails. The production service wiring runs this preflight before startup.

After the preflight passes, verify that `GET /health` returns HTTP 200 with `status: ok`. The endpoint runs a minimal read-only PostgreSQL connectivity query. If PostgreSQL is unavailable, it returns HTTP 503 without exposing the connection URL or exception details. Do not consider the service ready while either check fails.

The deployment verifier is observational: it uses `curl --fail` for the health check and does not stop or restart processes.

## Local import

Create or select a local database named `api_disano_local`, then run the safe sequence above:

```bash
python3 migration/postgres_local_migrate.py \
  --sqlite-path database/tarifa_disano.db \
  --postgres-url postgresql://localhost/api_disano_local \
  --batch-size 500
```

The importer creates the PostgreSQL schema, copies only `productos` using the explicit 40-column mapping, and uses bounded batches. The schema and product writes are transactional: failures roll back the PostgreSQL transaction. It verifies the source and destination product counts and checks primary-key uniqueness. SQLite enrichment job audit data is not imported.

The schema is also available for an explicit local smoke test:

```bash
psql postgresql://localhost/api_disano_local \
  --file migration/04_postgres_schema.sql
```

The existing `migration/run_migration.sh` remains **SQLite-only**. It is not a PostgreSQL migration command.

## Scope and safety

This harness has not migrated production or the VPS. Do not point it at deployment infrastructure or production environment files. The PostgreSQL target must be a local database such as `api_disano_local`.
