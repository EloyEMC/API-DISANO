# Specification: BC3 approval mode

## Configuration
- **Given** no `BC3_APPROVAL_MODE` is configured, **when** settings load, **then** mode is `github_review`.
- **Given** an invalid mode, **when** settings load, **then** validation fails.
- Settings **MUST** expose only `github_review` and `sole_maintainer` as accepted values.

## Verification
- **Given** either mode, **when** an approval is verified, **then** token, expected repository, PR number, exact head SHA, and PR repository identity are checked.
- **Given** `github_review`, **when** reviews do not satisfy the configured count, **then** verification fails.
- **Given** `sole_maintainer`, **when** the PR identity is valid, **then** verification succeeds without requiring an independent review.
- The verifier **MUST NOT** claim a fake review; sole-mode evidence **MUST** use nullable approval count and a verification timestamp.

## Persistence and workflow
- **Given** a preview, **when** persisted, **then** its approval mode is snapshotted explicitly.
- **Given** an old snapshot without a mode, **when** read, **then** it is treated as `github_review`.
- **Given** apply configuration differs from the snapshot mode, **when** apply starts, **then** it returns the safe conflict response before any product write.
- Dedicated approval key and actor/preview binding **MUST** remain mandatory in both modes.
- Wrong key, actor, payload hash, source/hash, PR repository/number/SHA, drift, expiry, replay, and mode mismatch **MUST** be rejected.
- Catalog-import expiry boundaries **MUST** remain unchanged.

## Integration
- Both BC3 and catalog-import verifier constructors **MUST** pass the configured mode consistently.
