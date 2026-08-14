# Local Backup and Rollback Preparation Runbook

**Status: NO DEPLOY.** This slice is local-only. Do not run it against a VPS, production configuration, deployment target, or active production database.

## Scope and safety

- Use a local copy or a local development database only.
- The backup tool creates backups and verifies them; it has no restore command.
- Never place passwords, tokens, or full connection URLs in logs, tickets, shell history, or this document.
- Restoration is a separate manual operation requiring an explicit human-selected backup and an independent change decision.

## Preflight

1. Confirm the current host is the intended local workstation and that no production/VPS credentials or deployment context are active.
2. Pin the release or source revision immutably before any migration work:

   ```text
   RELEASE_PIN=<immutable-commit-sha-or-signed-release-id>
   ```

   Record the exact reviewed revision; do not use a moving branch or tag as the rollback reference.
3. Confirm the local source database exists and is not the live production database.
4. Select an output directory separate from the source database. Do not place backups beside the source database.
5. Confirm the operator has enough local disk space and can read the source and write the backup directory.

## Local SQLite backup

```bash
python3 migration/local_backup.py sqlite-backup \
  --source <LOCAL_SQLITE_SOURCE_PATH> \
  --output-dir <LOCAL_BACKUP_DIRECTORY>
```

The command uses SQLite's online backup API, creates a timestamped `.db`, and writes an adjacent JSON manifest containing the SHA-256 checksum and `PRAGMA integrity_check` result. It fails closed if the source is invalid, paths are ambiguous, or the backup fails integrity validation.

## Local PostgreSQL backup

Only loopback PostgreSQL URLs are accepted (`localhost`, `127.0.0.1`, or `::1`). Keep credentials out of command history where possible; use the local PostgreSQL client credential mechanism rather than embedding a password.

```bash
python3 migration/local_backup.py postgres-backup \
  --url 'postgresql://<LOCAL_USER>@localhost:<LOCAL_PORT>/<LOCAL_DATABASE>' \
  --output-dir <LOCAL_BACKUP_DIRECTORY>
```

This invokes local `pg_dump` with a subprocess argument list, writes a timestamped custom-format dump, and creates a checksum manifest. It does not support a nonlocal override and fails if `pg_dump` is unavailable.

## Verification

SQLite backup:

```bash
python3 migration/local_backup.py verify \
  --backup <LOCAL_SQLITE_BACKUP_PATH> \
  --manifest <LOCAL_SQLITE_BACKUP_PATH>.json
```

PostgreSQL custom-format dump:

```bash
python3 migration/local_backup.py verify \
  --backup <LOCAL_POSTGRES_DUMP_PATH> \
  --manifest <LOCAL_POSTGRES_DUMP_PATH>.json
```

Verification checks the manifest checksum first. For SQLite it then runs `PRAGMA integrity_check`; for PostgreSQL custom-format dumps it then runs the read-only structural command `pg_restore --list <backup>` without `--dbname` or any database connection. PostgreSQL verification fails closed when `pg_restore` is unavailable, cannot execute, or exits non-zero. Verification never restores automatically. Reject a tampered or unverifiable backup.

## Required migration order

For a local PostgreSQL migration, follow this exact order:

1. Back up the PostgreSQL target.
2. Verify the dump and manifest with the command above; this includes the checksum and read-only `pg_restore --list` structural validation.
3. Run `postgres_local_migrate.py` transactionally, passing both `--postgres-backup` and `--postgres-backup-manifest`.
4. Verify product counts and primary-key uniqueness after the migration.
5. Retain the verified dump, manifest, pinned revision, and verification evidence as the rollback artifact.

The migration refuses to open a PostgreSQL write transaction unless the supplied artifact passes the shared verifier. A dry run is read-only and may run without a backup. Never substitute an unverified file or skip the manifest.

## Manual restoration only

Rollback is **not** implemented by `migration/local_backup.py`. After an explicit human decision, maintenance window, release pin, and independent verification of the selected backup, use placeholders and local connection details only:

SQLite (manual, operator-owned procedure):

```text
<LOCAL_SQLITE_RESTORE_PROCEDURE> <EXPLICITLY_SELECTED_BACKUP> <LOCAL_TARGET_DATABASE>
```

PostgreSQL custom-format dump (operator checklist; no restore command is provided here):

- Record the explicit human decision and maintenance window for this rollback.
- Re-run verification for the selected dump and confirm its checksum and `pg_restore --list` structural result.
- Confirm the target is a local loopback PostgreSQL instance and that the release pin matches the intended rollback revision.
- Stop application writers as appropriate and confirm the target connection details independently.
- Use an operator-owned, non-mechanical PostgreSQL restoration procedure with the selected dump; review the procedure before execution.
- Retain the restoration output and post-operation checks for review.

Do not execute restoration from this runbook mechanically. Never substitute a production/VPS URL for a placeholder in this document.

## Post-operation health checks

After any separately authorized local restoration or migration:

1. Re-run the backup verification or an equivalent checksum/integrity check.
2. Check database connectivity and schema/version expectations.
3. Run the application's offline/unit test suite and a local smoke test.
4. Inspect logs for errors without exposing credentials or connection URLs.
5. Confirm the pinned release is the revision under test and that no deployment occurred.

## Existing migration script defects

Do **not** use `migration/run_migration.sh` for PostgreSQL. It is an older migration script and is not a safe replacement for this local-only tool. Known defects include:

- hard-coded workstation paths and virtual-environment paths;
- raw `cp` backup instead of SQLite's online backup API;
- no SHA-256 manifest and only a redirected SQLite integrity command;
- an automatic rollback path that copies a selected file without an explicit operator workflow;
- SQLite CLI/SQL assumptions throughout, so it cannot back up or restore PostgreSQL;
- migration and rollback actions are combined in one executable flow rather than separated into preparation and human-authorized restoration.

This runbook therefore documents preparation only. **No deployment is authorized or performed by this change.**
