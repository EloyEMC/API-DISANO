# Proposal: Explicit BC3 sole-maintainer approval mode

## Problem
A deployment owned by one maintainer needs an explicit opt-in approval path without weakening the existing GitHub review default or the durable preview/apply bindings.

## Outcome
Add `bc3_approval_mode` with `github_review` as the default and `sole_maintainer` as an opt-in mode. Both modes retain dedicated approval credentials, actor binding, payload/source/PR repository-number-head SHA checks, expiry, replay protection, and persisted audit metadata. Sole-maintainer mode removes only the independent GitHub review-count requirement.

## Scope
Configuration, both BC3 and catalog-import verifier construction paths, snapshot persistence/migration, approval/apply validation, DTO projections, tests, and client contract documentation.

## Non-goals
No comment requirement, second reviewer, aliasing of approval modes, expiry expansion, deployment, commits, or remote operations.
