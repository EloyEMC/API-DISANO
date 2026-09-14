"""Injectable, fail-closed GitHub pull-request approval verification."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field, field_validator


class GitHubApprovalUnavailable(RuntimeError):
    """Raised when approval evidence cannot be obtained safely."""


class GitHubApprovalReference(BaseModel):
    """Immutable identity of the pull request that approved a preview."""

    repository: str = Field(..., min_length=1, max_length=255)
    pull_request_number: int = Field(..., gt=0)
    head_sha: str = Field(..., min_length=40, max_length=64)

    @field_validator("repository")
    @classmethod
    def validate_repository(cls, value: str) -> str:
        """Validate the owner/name repository form."""
        value = value.strip()
        if value.count("/") != 1 or any(not part for part in value.split("/")):
            raise ValueError("repository must use the owner/name form")
        return value

    @field_validator("head_sha")
    @classmethod
    def validate_head_sha(cls, value: str) -> str:
        """Normalize and validate a hexadecimal commit SHA."""
        value = value.strip().lower()
        if any(character not in "0123456789abcdef" for character in value):
            raise ValueError("head_sha must be hexadecimal")
        return value


@dataclass(frozen=True)
class GitHubApprovalEvidence:
    """Safe, persisted metadata returned by a successful verifier."""

    repository: str
    pull_request_number: int
    head_sha: str
    approval_count: int | None
    verified_at: datetime
    approval_mode: Literal["github_review", "sole_maintainer"] = "github_review"


class GitHubApprovalVerifier:
    """Verify a PR head and its current approved review state through GitHub API."""

    def __init__(
        self,
        token: str | None = None,
        expected_repository: str | None = None,
        api_base_url: str = "https://api.github.com",
        opener: Callable[..., Any] = urlopen,
        required_approvals: int = 1,
        approval_mode: Literal["github_review", "sole_maintainer"] = "github_review",
    ) -> None:
        if approval_mode not in {"github_review", "sole_maintainer"}:
            raise ValueError("Unsupported GitHub approval mode")
        self.token = token.strip() if token else None
        self.expected_repository = expected_repository.strip() if expected_repository else None
        parsed_api_url = urlparse(api_base_url)
        if parsed_api_url.scheme not in {"http", "https"} or not parsed_api_url.netloc:
            raise ValueError("GitHub API URL must use http or https")
        self.api_base_url = api_base_url.rstrip("/")
        self.opener = opener
        self.required_approvals = required_approvals
        self.approval_mode = approval_mode

    def verify(self, reference: GitHubApprovalReference) -> GitHubApprovalEvidence:
        """Verify the immutable PR identity and configured approval policy."""
        if not self.token or not self.expected_repository:
            raise GitHubApprovalUnavailable("GitHub approval verifier is not configured")
        if reference.repository != self.expected_repository:
            raise GitHubApprovalUnavailable("GitHub repository does not match expected repository")

        pull_request = self._get_json(
            f"{self.api_base_url}/repos/{quote(reference.repository, safe='/')}/pulls/"
            f"{reference.pull_request_number}"
        )
        if not isinstance(pull_request, dict):
            raise GitHubApprovalUnavailable("GitHub pull request response is invalid")
        repository = pull_request.get("base", {}).get("repo", {}).get("full_name")
        pull_request_number = pull_request.get("number")
        head_sha = pull_request.get("head", {}).get("sha")
        if (
            repository != reference.repository
            or pull_request_number != reference.pull_request_number
            or head_sha != reference.head_sha
        ):
            raise GitHubApprovalUnavailable("GitHub pull request identity does not match preview")

        if self.approval_mode == "sole_maintainer":
            return GitHubApprovalEvidence(
                repository=reference.repository,
                pull_request_number=reference.pull_request_number,
                head_sha=reference.head_sha,
                approval_count=None,
                verified_at=datetime.now(timezone.utc),
                approval_mode=self.approval_mode,
            )

        reviews = self._get_json(
            f"{self.api_base_url}/repos/{quote(reference.repository, safe='/')}/pulls/"
            f"{reference.pull_request_number}/reviews"
        )
        if not isinstance(reviews, list) or any(not isinstance(review, dict) for review in reviews):
            raise GitHubApprovalUnavailable("GitHub review response is invalid")
        latest_review_by_user: dict[str, dict[str, Any]] = {}
        for review in sorted(reviews, key=self._review_sort_key):
            user_data = review.get("user")
            if not isinstance(user_data, dict):
                raise GitHubApprovalUnavailable("GitHub review response is invalid")
            user = user_data.get("id") or user_data.get("login")
            if user is not None:
                latest_review_by_user[str(user)] = review

        approval_count = sum(
            review.get("state") == "APPROVED" for review in latest_review_by_user.values()
        )
        if approval_count < self.required_approvals:
            raise GitHubApprovalUnavailable("GitHub pull request does not have required approval")
        return GitHubApprovalEvidence(
            repository=reference.repository,
            pull_request_number=reference.pull_request_number,
            head_sha=reference.head_sha,
            approval_count=approval_count,
            verified_at=datetime.now(timezone.utc),
            approval_mode=self.approval_mode,
        )

    @staticmethod
    def _review_sort_key(review: dict[str, Any]) -> tuple[str, int]:
        submitted_at = review.get("submitted_at")
        review_id = review.get("id")
        if not isinstance(submitted_at, str) or not isinstance(review_id, int):
            raise GitHubApprovalUnavailable("GitHub review response is invalid")
        return submitted_at, review_id

    def _get_json(self, url: str) -> Any:
        # The base URL is scheme-validated in the constructor; the path contains
        # only validated repository and numeric PR components.
        request = Request(  # noqa: S310
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="GET",
        )
        try:
            with self.opener(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            TypeError,
        ) as exc:
            raise GitHubApprovalUnavailable("GitHub approval evidence is unavailable") from exc


class UnconfiguredGitHubApprovalVerifier(GitHubApprovalVerifier):
    """Named default useful for dependency injection and explicit fail-closed behavior."""

    def __init__(self) -> None:
        super().__init__()
