# PostgreSQL Activation Checklist

**Status:** Activation has not occurred. This checklist is an approval-gated operational record; it does not deploy automatically.

Use placeholders for all secrets, hosts, tokens, and revisions. Never copy a real password, token, or complete production connection URL into this document or its evidence.

**Production boundary:** API Disano uses PostgreSQL internally. BC3 Suite accesses API Disano only through the documented HTTPS endpoints; it never connects directly to the API's database.

## 1. Preconditions and approval gate

- [ ] Confirm the intended activation window, operator, and communication channel.
- [ ] Confirm the target application and database are explicitly identified as `<APPLICATION_TARGET>` and `<DATABASE_TARGET>`.
- [ ] Confirm the operator has the approved access path and a current rollback owner.
- [ ] Confirm local validation is complete: PostgreSQL database `api_disano_local` contains 8,288 imported products and parity was verified; BC3 preview, apply, replay, conflict, status, and missing-code flows were validated locally.
- [ ] Obtain explicit human approval to activate PostgreSQL for the target. Record `<APPROVAL_REFERENCE>`.
- [ ] **Do not proceed without approval. No automatic deployment is authorized by this checklist.**

## 2. Immutable release and clean candidate

- [ ] Record the immutable reviewed release/Git revision as `<IMMUTABLE_REVISION>` (commit SHA or signed release identifier).
- [ ] Confirm the candidate is at `<IMMUTABLE_REVISION>`, not a moving branch or tag.
- [ ] Confirm the working tree and intended release candidate are clean; no unreviewed tracked, untracked, generated, or configuration changes are present.
- [ ] Retain the revision and clean-candidate evidence with `<ACTIVATION_RECORD>`.

## 3. Backup and manifest verification

- [ ] Select a backup destination separate from the source database and confirm sufficient storage.
- [ ] Create the PostgreSQL backup using the repository tooling in `migration/local_backup.py`, with credentials supplied through the approved local credential mechanism rather than embedded secrets.
- [ ] Retain the generated custom-format dump and adjacent JSON manifest as `<POSTGRES_BACKUP>` and `<POSTGRES_BACKUP_MANIFEST>`.
- [ ] Verify the dump against its manifest using the same tooling before activation.
- [ ] Confirm the manifest identifies the supplied backup and its SHA-256 checksum matches. Reject any missing, tampered, or unverifiable backup.
- [ ] Record backup path, manifest path, checksum, creation time, and verification result in `<ACTIVATION_RECORD>`.

The repository runbook documents backup preparation and verification in `docs/BACKUP_ROLLBACK_RUNBOOK.md`. The backup tool does not restore automatically.

## 4. PostgreSQL schema, import, and parity

- [ ] Confirm the target schema is the reviewed PostgreSQL schema and the application can connect using the approved target configuration.
- [ ] Confirm the import completed transactionally and the target contains exactly 8,288 products.
- [ ] Re-run the approved source/target parity check and retain its output; counts, product identifiers, and required mapped fields must agree.
- [ ] Confirm primary-key uniqueness and required BC3 columns are present.
- [ ] If any schema, import, count, uniqueness, or parity check fails: stop before changing application configuration and use the abort decision in Section 7.

## 5. DATABASE_URL change, only after approval

- [ ] After approval, backup verification, and database checks pass, change only the application `DATABASE_URL` through the approved configuration mechanism.
- [ ] Confirm `DATABASE_URL` is present and uses a valid PostgreSQL URL with a host and database name. SQLite paths are not valid production configuration.
- [ ] Use a placeholder-only example when documenting the change:

  ```text
  DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
  ```

- [ ] Do not place real secrets in files, examples, logs, tickets, shell history, or evidence.
- [ ] Record the configuration change time and `<CONFIG_CHANGE_REFERENCE>` without recording secret values.

## 6. Read-only health, API, and BC3 contract checks

- [ ] Run `python3 scripts/preflight-production.py --env-file <APPROVED_PRODUCTION_ENV_FILE>` as the authorized operator. It must report `production preflight passed` before startup or readiness checks continue.
- [ ] Confirm the preflight validates the protected environment file, production marker, secret configuration, pinned `psycopg` version, and PostgreSQL connectivity without exposing `DATABASE_URL`.
- [ ] If the preflight exits non-zero, stop activation and apply Section 7. Do not bypass the preflight or substitute a SQLite database path.
- [ ] Perform read-only connectivity and application health checks against `<APPLICATION_TARGET>`; retain status, timestamp, and request identifiers without secrets.
- [ ] Perform read-only API smoke checks for the approved health endpoint and representative product list/detail requests.
- [ ] Confirm responses preserve required product fields, including `codigo`, `descripcion`, `marca`, `bc3_descripcion_corta`, `bc3_product_type`, and `bc3_descripcion_completa`.
- [ ] Run the approved BC3 contract checks for preview, apply, replay, conflict, status, and missing-code behavior. Do not mutate production data as part of a read-only check.
- [ ] Confirm expected status codes, response shape, and error behavior; retain sanitized request/response summaries and test results.

## 7. Abort and rollback decision points

Abort activation immediately if approval is absent, the revision is not immutable, the candidate is not clean, the backup or manifest cannot be verified, PostgreSQL parity fails, credentials/configuration are exposed, health checks fail, or any BC3 contract check is incompatible or unexpectedly mutating.

At each abort point:

1. Stop the activation sequence and do not continue to later steps.
2. Keep the prior application configuration unchanged when the `DATABASE_URL` change has not yet been made.
3. Notify `<ROLLBACK_OWNER>` and record the failed check, evidence, timestamp, and decision in `<ACTIVATION_RECORD>`.

Database rollback and application release rollback are separate decisions:

- **Database rollback:** requires an explicit human decision, a selected and independently verified backup, an approved maintenance procedure, and a separate restore verification. `migration/local_backup.py` does not perform restores.
- **Application release rollback:** requires an explicit human decision to return the application to `<PREVIOUS_IMMUTABLE_REVISION>` and separately restore or reselect the approved application configuration. Do not infer that an application rollback restores database state.
- Do not execute an unlisted deployment, restore, VPS, or production command based on this checklist.

## 8. Post-activation monitoring and retained evidence

- [ ] Monitor read-only health, API error rates, latency, database connectivity, and representative BC3 responses during `<MONITORING_WINDOW>`.
- [ ] Check for missing products, unexpected empty results, schema errors, connection failures, and BC3 contract regressions.
- [ ] Define and record the owner and decision time for any alert; apply Section 7 if an abort criterion is met.
- [ ] Retain: approval reference, immutable revision, clean-candidate evidence, backup and manifest checksums, parity output, sanitized health/API/BC3 results, configuration-change reference, monitoring observations, timestamps, and final activation decision.

## Non-goals

- This checklist does not execute deployment, activation, restoration, or rollback commands.
- No VPS commands are executed by this checklist.
- No production/VPS infrastructure details, scopes, credentials, hosts, tokens, or real secrets are defined here.
- Local validation is evidence for readiness; it is not evidence that a VPS or production deployment has occurred.
