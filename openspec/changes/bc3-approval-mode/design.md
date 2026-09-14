# Design: Explicit approval mode

`Settings.bc3_approval_mode` is a validated literal with default `github_review`. `GitHubApprovalVerifier` receives the mode and performs common immutable identity checks before branching: review mode performs current-review-state counting; sole mode returns evidence with `approval_count=None` and `verified_at`.

Both workflow constructors inject the same configured mode. Approval repositories persist `approval_mode` on preview/snapshot creation and approval. Repository apply checks the persisted mode against current configuration as part of the pre-write eligibility predicate; missing legacy values are normalized as `github_review`. The ORM allows nullable legacy rows while new writes are explicit.

Migration 09 is additive and only adds/backfills the mode columns, leaving migrations 07/08 unchanged. DTOs expose nullable counts and explicit mode where needed. Tests cover unit policy, both constructor paths, persistence, conflict ordering, and PostgreSQL migration execution.
