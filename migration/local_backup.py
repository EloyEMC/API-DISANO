"""Local-only backup and verification helpers.

This module intentionally contains no restore or deployment operations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


class BackupError(RuntimeError):
    """Raised when a backup operation cannot be completed safely."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_path(backup_path: Path) -> Path:
    return backup_path.with_name(f"{backup_path.name}.json")


def _prepare_output_dir(source: Path, output_dir: Path) -> Path:
    source_resolved = source.expanduser().resolve(strict=True)
    if not source_resolved.is_file():
        raise BackupError(f"Source is not a regular file: {source}")
    output_dir = output_dir.expanduser().resolve()
    if source_resolved == output_dir or source_resolved.parent == output_dir:
        raise BackupError(
            "Refusing ambiguous source/output paths; choose a separate output directory"
        )
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BackupError(f"Cannot create output directory {output_dir}") from exc
    if source_resolved.parent == output_dir or source_resolved in output_dir.parents:
        raise BackupError(
            "Refusing ambiguous source/output paths; source must be outside output directory"
        )
    return output_dir


def _sqlite_integrity(path: Path) -> str:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        raise BackupError(f"SQLite integrity check failed for {path.name}") from exc
    if not result or result[0] != "ok":
        raise BackupError(
            f"SQLite integrity check failed for {path.name}: database is not valid"
        )
    return "ok"


def sqlite_backup(source: Path, output_dir: Path) -> tuple[Path, Path]:
    """Create a SQLite backup using SQLite's online backup API."""
    source = source.expanduser()
    output_dir = _prepare_output_dir(source, output_dir)
    _sqlite_integrity(source)
    backup_path = output_dir / f"sqlite-{_timestamp()}.db"
    try:
        with (
            sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True) as source_db,
            sqlite3.connect(backup_path) as destination_db,
        ):
            source_db.backup(destination_db)
            destination_db.commit()
    except (sqlite3.Error, OSError) as exc:
        backup_path.unlink(missing_ok=True)
        raise BackupError(
            f"SQLite backup failed; no usable backup was created: {exc}"
        ) from exc

    integrity = _sqlite_integrity(backup_path)
    manifest_path = _manifest_path(backup_path)
    manifest = {
        "format": "sqlite",
        "backup": backup_path.name,
        "sha256": _sha256(backup_path),
        "integrity_check": integrity,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return backup_path, manifest_path


def normalize_local_postgres_url(url: str) -> tuple[str, str | None]:
    """Validate and sanitize an explicitly local PostgreSQL URL."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise BackupError("PostgreSQL URL has an invalid host or port") from exc

    valid_scheme = parsed.scheme in {"postgres", "postgresql"} or (
        parsed.scheme.startswith("postgresql+")
        and len(parsed.scheme) > len("postgresql+")
    )
    if not valid_scheme:
        raise BackupError("PostgreSQL URL must use a PostgreSQL scheme")
    if hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise BackupError("PostgreSQL backup permits explicit loopback hosts only")
    if port is not None and not 1 <= port <= 65535:
        raise BackupError("PostgreSQL URL has an invalid port")

    password = unquote(parsed.password) if parsed.password is not None else None
    safe_netloc = hostname
    if ":" in safe_netloc:
        safe_netloc = f"[{safe_netloc}]"
    if parsed.username is not None:
        safe_netloc = f"{parsed.username}@{safe_netloc}"
    if port is not None:
        safe_netloc += f":{port}"
    safe_url = urlunsplit(
        (parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment)
    )
    return safe_url, password


def _local_postgres_url(url: str) -> tuple[str, str | None]:
    """Backward-compatible private alias for the shared URL normalizer."""
    return normalize_local_postgres_url(url)


def postgres_backup(url: str, output_dir: Path) -> tuple[Path, Path]:
    """Create a local PostgreSQL custom-format dump with pg_dump."""
    safe_url, password = normalize_local_postgres_url(url)
    output_dir = output_dir.expanduser().resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BackupError(f"Cannot create output directory {output_dir}") from exc
    if not shutil_which("pg_dump"):
        raise BackupError(
            "pg_dump is unavailable; install PostgreSQL client tools locally"
        )

    backup_path = output_dir / f"postgres-{_timestamp()}.dump"
    command = [
        "pg_dump",
        "--format=custom",
        "--file",
        str(backup_path),
        "--dbname",
        safe_url,
    ]
    env = os.environ.copy()
    if password is not None:
        env["PGPASSWORD"] = password
    try:
        result = subprocess.run(
            command, env=env, capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise BackupError("Could not execute pg_dump") from exc
    finally:
        if password is not None:
            env["PGPASSWORD"] = ""
    if result.returncode != 0:
        backup_path.unlink(missing_ok=True)
        raise BackupError(f"pg_dump failed with exit status {result.returncode}")
    if not backup_path.is_file() or backup_path.stat().st_size == 0:
        backup_path.unlink(missing_ok=True)
        raise BackupError("pg_dump completed without producing a non-empty dump")

    manifest_path = _manifest_path(backup_path)
    manifest = {
        "format": "postgresql-custom",
        "backup": backup_path.name,
        "sha256": _sha256(backup_path),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return backup_path, manifest_path


def shutil_which(command: str) -> str | None:
    """Small indirection to keep dependency checks straightforward in tests."""
    import shutil

    return shutil.which(command)


def _verify_postgres_archive(backup: Path) -> None:
    """Validate a PostgreSQL custom dump without connecting to a database."""
    if not shutil_which("pg_restore"):
        raise BackupError(
            "pg_restore is unavailable; install PostgreSQL client tools locally"
        )
    try:
        result = subprocess.run(
            ["pg_restore", "--list", str(backup)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BackupError("Could not execute pg_restore") from exc
    if result.returncode != 0:
        raise BackupError(f"pg_restore failed with exit status {result.returncode}")


def verify(backup: Path, manifest_path: Path) -> None:
    """Verify a backup manifest and validate its format-specific structure."""
    try:
        if not backup.is_file():
            raise OSError("backup is not a regular file")
        with backup.open("rb"):
            pass
    except (OSError, TypeError) as exc:
        raise BackupError("Backup artifact is missing or unreadable") from exc

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["sha256"]
        backup_format = manifest["format"]
        manifest_backup = manifest["backup"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise BackupError("Manifest is missing or invalid") from exc
    if manifest_backup != backup.name:
        raise BackupError("Manifest does not identify the supplied backup")
    try:
        checksum = _sha256(backup)
    except OSError as exc:
        raise BackupError("Backup artifact is missing or unreadable") from exc
    if checksum != expected:
        raise BackupError("Backup checksum does not match manifest; reject this backup")
    if backup_format == "sqlite":
        _sqlite_integrity(backup)
    elif backup_format == "postgresql-custom":
        _verify_postgres_archive(backup)
    else:
        raise BackupError("Manifest format is unsupported")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local-only backup and verification tool"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sqlite_parser = subparsers.add_parser("sqlite-backup")
    sqlite_parser.add_argument("--source", type=Path, required=True)
    sqlite_parser.add_argument("--output-dir", type=Path, required=True)

    postgres_parser = subparsers.add_parser("postgres-backup")
    postgres_parser.add_argument("--url", required=True)
    postgres_parser.add_argument("--output-dir", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--backup", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "sqlite-backup":
            backup, manifest = sqlite_backup(args.source, args.output_dir)
        elif args.command == "postgres-backup":
            backup, manifest = postgres_backup(args.url, args.output_dir)
        else:
            verify(args.backup, args.manifest)
            print("Backup verified; no restore was performed.")
            return 0
    except BackupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Backup created: {backup.name}")
    print(f"Manifest created: {manifest.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
