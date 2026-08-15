#!/usr/bin/env python3
"""Fail-closed, read-only production configuration preflight."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED_PSYCOPG_VERSION = "3.2.10"
DEFAULT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class PreflightResult:
    """The safe-to-display result of a preflight check."""

    ok: bool
    message: str


def _read_environment(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open(encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _valid_postgresql_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    valid_scheme = parsed.scheme in {"postgres", "postgresql"} or bool(
        re.fullmatch(r"postgresql\+[A-Za-z0-9_-]+", parsed.scheme)
    )
    return (
        valid_scheme
        and bool(parsed.hostname)
        and bool(parsed.path and parsed.path != "/")
    )


def load_psycopg() -> tuple[object, str]:
    """Import psycopg and return it with its installed distribution version."""
    psycopg = importlib.import_module("psycopg")
    version = importlib.metadata.version("psycopg")
    return psycopg, version


def connect_read_only(psycopg: object, database_url: str) -> object:
    """Open a bounded connection; callers execute only the read-only probe."""
    return psycopg.connect(database_url, connect_timeout=5)  # type: ignore[attr-defined]


def run_preflight(env_file: Path) -> PreflightResult:
    """Validate production prerequisites without exposing secrets."""
    try:
        mode = stat.S_IMODE(env_file.stat().st_mode)
    except OSError:
        return PreflightResult(False, "environment file is missing or unreadable")

    if mode & 0o077:
        return PreflightResult(
            False, "environment file permissions must be 0600 or stricter"
        )

    try:
        environment = _read_environment(env_file)
    except OSError:
        return PreflightResult(False, "environment file is missing or unreadable")

    database_url = environment.get("DATABASE_URL", "")
    if not database_url:
        return PreflightResult(False, "DATABASE_URL is required")
    if not _valid_postgresql_url(database_url):
        return PreflightResult(False, "DATABASE_URL must be a valid PostgreSQL URL")
    if environment.get("ENVIRONMENT", "") != "production":
        return PreflightResult(False, "ENVIRONMENT must be production")
    if len(environment.get("SECRET_KEY", "")) < 32:
        return PreflightResult(False, "SECRET_KEY must be at least 32 characters")
    if not environment.get("API_KEYS", "").strip():
        return PreflightResult(False, "API_KEYS must not be empty")

    try:
        psycopg, version = load_psycopg()
    except ImportError:
        return PreflightResult(False, "psycopg is not importable")
    except Exception:
        return PreflightResult(False, "psycopg preflight check failed")

    if version != EXPECTED_PSYCOPG_VERSION:
        return PreflightResult(False, "psycopg version must be 3.2.10")

    connection = None
    try:
        connection = connect_read_only(psycopg, database_url)
        with connection.cursor() as cursor:  # type: ignore[attr-defined]
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                return PreflightResult(
                    False, "read-only database connectivity check failed"
                )
    except Exception:
        return PreflightResult(False, "read-only database connectivity check failed")
    finally:
        if connection is not None:
            with contextlib.suppress(Exception):
                connection.close()  # type: ignore[attr-defined]

    return PreflightResult(True, "production preflight passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    args = parser.parse_args()
    result = run_preflight(args.env_file)
    print(result.message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
