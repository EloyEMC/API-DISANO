import json
from types import TracebackType
from typing import Any

import pytest

from app.application.services.github_approval import (
    GitHubApprovalReference,
    GitHubApprovalUnavailable,
    GitHubApprovalVerifier,
)


def test_github_approval_reference_requires_immutable_identity() -> None:
    reference = GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )

    assert reference.repository == "acme/catalog"
    assert reference.pull_request_number == 42
    assert reference.head_sha == "a" * 40


@pytest.mark.parametrize(
    "reference",
    [
        {"repository": "acme/catalog", "pull_request_number": 42, "head_sha": ""},
        {"repository": "acme/catalog", "pull_request_number": 0, "head_sha": "a" * 40},
    ],
)
def test_github_approval_reference_rejects_invalid_identity(
    reference: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        GitHubApprovalReference(**reference)


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def _verifier(responses: list[object]) -> GitHubApprovalVerifier:
    def opener(*args: object, **kwargs: object) -> _Response:
        del args, kwargs
        return _Response(responses.pop(0))

    return GitHubApprovalVerifier(
        token="t" * 20,
        expected_repository="acme/catalog",
        opener=opener,
    )


def _pull_request() -> dict[str, object]:
    return {
        "number": 42,
        "base": {"repo": {"full_name": "acme/catalog"}},
        "head": {"sha": "a" * 40},
    }


def _review(review_id: int, state: str, submitted_at: str) -> dict[str, object]:
    return {
        "id": review_id,
        "state": state,
        "submitted_at": submitted_at,
        "user": {"id": 7},
    }


def test_github_verifier_accepts_approved_immutable_head() -> None:
    reference = GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )
    evidence = _verifier(
        [_pull_request(), [_review(1, "APPROVED", "2025-01-01T00:00:00Z")]]
    ).verify(reference)
    assert evidence.approval_count == 1
    assert evidence.head_sha == reference.head_sha


def test_github_verifier_uses_latest_review_state_not_response_order() -> None:
    reference = GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )
    with pytest.raises(GitHubApprovalUnavailable, match="required approval"):
        _verifier(
            [
                _pull_request(),
                [
                    _review(2, "COMMENTED", "2025-01-02T00:00:00Z"),
                    _review(1, "APPROVED", "2025-01-01T00:00:00Z"),
                ],
            ]
        ).verify(reference)


def test_github_verifier_rejects_unapproved_pr() -> None:
    reference = GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )
    with pytest.raises(GitHubApprovalUnavailable, match="required approval"):
        _verifier([_pull_request(), [_review(1, "COMMENTED", "2025-01-01T00:00:00Z")]]).verify(
            reference
        )


@pytest.mark.parametrize(
    "reference,pull_request",
    [
        (
            GitHubApprovalReference(
                repository="other/catalog", pull_request_number=42, head_sha="a" * 40
            ),
            {},
        ),
        (
            GitHubApprovalReference(
                repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
            ),
            {
                "number": 43,
                "base": {"repo": {"full_name": "acme/catalog"}},
                "head": {"sha": "a" * 40},
            },
        ),
        (
            GitHubApprovalReference(
                repository="acme/catalog", pull_request_number=42, head_sha="b" * 40
            ),
            _pull_request(),
        ),
    ],
)
def test_github_verifier_rejects_wrong_repo_pr_or_head(
    reference: GitHubApprovalReference, pull_request: dict[str, object]
) -> None:
    responses: list[object] = [] if reference.repository != "acme/catalog" else [pull_request]
    with pytest.raises(GitHubApprovalUnavailable):
        _verifier(responses).verify(reference)


def test_sole_maintainer_verifier_rejects_response_missing_pr_number() -> None:
    reference = GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )
    pull_request = _pull_request()
    del pull_request["number"]

    with pytest.raises(GitHubApprovalUnavailable, match="identity"):
        GitHubApprovalVerifier(
            token="t" * 20,
            expected_repository="acme/catalog",
            approval_mode="sole_maintainer",
            opener=lambda *args, **kwargs: _Response(pull_request),
        ).verify(reference)


def test_sole_maintainer_verifier_keeps_identity_evidence_without_review_count() -> None:
    reference = GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )

    evidence = GitHubApprovalVerifier(
        token="t" * 20,
        expected_repository="acme/catalog",
        approval_mode="sole_maintainer",
        opener=lambda *args, **kwargs: _Response(_pull_request()),
    ).verify(reference)

    assert evidence.approval_mode == "sole_maintainer"
    assert evidence.approval_count is None
    assert evidence.repository == reference.repository
    assert evidence.pull_request_number == reference.pull_request_number
    assert evidence.head_sha == reference.head_sha


def test_unconfigured_verifier_fails_closed() -> None:
    verifier = GitHubApprovalVerifier()

    with pytest.raises(GitHubApprovalUnavailable):
        verifier.verify(
            GitHubApprovalReference(
                repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
            )
        )
