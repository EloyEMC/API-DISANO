"""Approval-bound, insert-only workflow for NEW catalog rows."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from app.application.dto.catalog_import import (
    CatalogImportRequest,
    catalog_payload_hash,
)
from app.application.services.github_approval import (
    GitHubApprovalVerifier,
    UnconfiguredGitHubApprovalVerifier,
)


class CatalogImportService:
    """Coordinate the approval-bound catalog import workflow."""

    def __init__(self, repository: Any, verifier: GitHubApprovalVerifier | None = None) -> None:
        self.repository = repository
        self.verifier = verifier or UnconfiguredGitHubApprovalVerifier()

    def preview(self, request: CatalogImportRequest, actor_id: str) -> dict[str, Any]:
        """Preview accepted and rejected catalog rows."""
        codes = [row.code for row in request.rows]
        existing = self.repository.existing_catalog_codes(codes)
        seen: set[str] = set()
        accepted, rejected = [], []
        for row in request.rows:
            reason = (
                "duplicate_code"
                if row.code in seen
                else "existing_code"
                if row.code in existing
                else None
            )
            if reason:
                rejected.append({"code": row.code, "reason": reason})
            else:
                accepted.append(row)
            seen.add(row.code)
        result = self.repository.catalog_import_preview(
            snapshot_id=str(uuid4()),
            actor_id=actor_id,
            request=request,
            accepted=accepted,
            rejected=rejected,
        )
        return {
            **result,
            "accepted_codes": [row.code for row in accepted],
            "rejected": rejected,
        }

    def approve(
        self, snapshot_id: str, actor_id: str, request: CatalogImportRequest
    ) -> dict[str, Any]:
        """Verify and persist catalog snapshot approval."""
        evidence = self.verifier.verify(request.github_pr)
        self.repository.catalog_import_approve(snapshot_id, actor_id, request.github_pr, evidence)
        return {
            "snapshot_id": snapshot_id,
            "status": "approved",
            "github_approval_count": evidence.approval_count,
            "github_approval_mode": evidence.approval_mode,
        }

    def apply(
        self,
        snapshot_id: str,
        actor_id: str,
        request: CatalogImportRequest,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Apply a catalog snapshot with idempotency."""
        return cast(
            dict[str, Any],
            self.repository.catalog_import_apply(
                snapshot_id=snapshot_id,
                actor_id=actor_id,
                request=request,
                idempotency_key=idempotency_key,
                expected_payload_hash=catalog_payload_hash(request.rows),
            ),
        )
