import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from migration.local_backup import (
    BackupError,
    build_parser,
    normalize_local_postgres_url,
    postgres_backup,
    sqlite_backup,
    verify,
)


def create_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("INSERT INTO items (name) VALUES ('local')")


def test_cli_parser_exposes_backup_subcommands() -> None:
    parser = build_parser()

    assert (
        parser.parse_args(
            ["sqlite-backup", "--source", "source.db", "--output-dir", "backups"]
        ).command
        == "sqlite-backup"
    )
    assert (
        parser.parse_args(
            [
                "postgres-backup",
                "--url",
                "postgresql://localhost/db",
                "--output-dir",
                "backups",
            ]
        ).command
        == "postgres-backup"
    )
    assert (
        parser.parse_args(["verify", "--backup", "backup.db", "--manifest", "backup.json"]).command
        == "verify"
    )


def test_sqlite_backup_writes_online_backup_manifest_and_valid_checksum(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    output_dir = tmp_path / "backups"
    create_database(source)

    backup, manifest_path = sqlite_backup(source, output_dir)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert backup.suffix == ".db"
    assert manifest["format"] == "sqlite"
    assert manifest["backup"] == backup.name
    assert manifest["integrity_check"] == "ok"
    verify(backup, manifest_path)


def test_verify_rejects_tampered_sqlite_backup(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    output_dir = tmp_path / "backups"
    create_database(source)
    backup, manifest_path = sqlite_backup(source, output_dir)
    backup.write_bytes(backup.read_bytes() + b"tampered")

    with pytest.raises(BackupError, match="checksum"):
        verify(backup, manifest_path)


def test_verify_rejects_corrupt_sqlite_even_with_updated_checksum(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    output_dir = tmp_path / "backups"
    create_database(source)
    backup, manifest_path = sqlite_backup(source, output_dir)
    backup.write_bytes(b"not a sqlite database")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib

    manifest["sha256"] = hashlib.sha256(backup.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(BackupError, match="integrity"):
        verify(backup, manifest_path)


def test_postgres_backup_rejects_nonlocal_url(tmp_path: Path) -> None:
    from migration.local_backup import postgres_backup

    with pytest.raises(BackupError, match="loopback"):
        postgres_backup("postgresql://user:secret@example.com/db", tmp_path / "backups")


def test_postgres_url_normalizer_preserves_driver_qualified_scheme() -> None:
    normalized, password = normalize_local_postgres_url(
        "postgresql+psycopg://user:secret@localhost:5433/db"
    )

    assert normalized == "postgresql+psycopg://user@localhost:5433/db"
    assert password == "secret"


def test_postgres_backup_uses_sanitized_url_and_pgpassword_only(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "backups"
    received_env: dict[str, str] = {}

    def run_postgres_command(command: list[str], **kwargs: object) -> Mock:
        if command[0] == "pg_dump":
            received_env.update(kwargs["env"])
            Path(command[command.index("--file") + 1]).write_bytes(b"custom-format-dump")
        return Mock(returncode=0)

    with (
        patch(
            "migration.local_backup.shutil_which",
            side_effect=lambda command: f"/usr/bin/{command}",
        ),
        patch("migration.local_backup.subprocess.run", side_effect=run_postgres_command) as run,
    ):
        backup, manifest = postgres_backup(
            "postgresql://backup:encoded%20secret@localhost:5432/app", output_dir
        )

    command = run.call_args_list[0].args[0]
    assert command[command.index("--dbname") + 1] == ("postgresql://backup@localhost:5432/app")
    assert "encoded%20secret" not in " ".join(command)
    assert received_env["PGPASSWORD"] == "encoded secret"
    assert backup.is_file() and backup.stat().st_size > 0
    assert manifest.is_file() and manifest.stat().st_size > 0
    assert run.call_args_list[1].args[0] == ["pg_restore", "--list", str(backup)]


def test_postgres_backup_cleans_artifacts_when_archive_verification_fails(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "backups"

    def run_postgres_command(command: list[str], **_: object) -> Mock:
        if command[0] == "pg_dump":
            Path(command[command.index("--file") + 1]).write_bytes(b"custom-format-dump")
            return Mock(returncode=0)
        return Mock(returncode=2)

    with (
        patch(
            "migration.local_backup.shutil_which",
            side_effect=lambda command: f"/usr/bin/{command}",
        ),
        patch("migration.local_backup.subprocess.run", side_effect=run_postgres_command),
        pytest.raises(BackupError, match="pg_restore failed with exit status 2"),
    ):
        postgres_backup("postgresql://backup:secret@localhost/app", output_dir)

    assert list(output_dir.iterdir()) == []


@pytest.mark.parametrize("returncode,contents", [(2, b"partial"), (0, b"")])
def test_postgres_backup_cleans_failed_or_empty_dump(
    tmp_path: Path, returncode: int, contents: bytes
) -> None:
    output_dir = tmp_path / "backups"

    def create_dump(command: list[str], **_: object) -> Mock:
        Path(command[command.index("--file") + 1]).write_bytes(contents)
        return Mock(returncode=returncode)

    with (
        patch("migration.local_backup.shutil_which", return_value="/usr/bin/pg_dump"),
        patch("migration.local_backup.subprocess.run", side_effect=create_dump),
        pytest.raises(BackupError),
    ):
        postgres_backup("postgresql://backup:secret@localhost/app", output_dir)

    assert list(output_dir.iterdir()) == []


def test_postgres_backup_cleans_dump_when_manifest_creation_fails(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "backups"

    def create_dump(command: list[str], **_: object) -> Mock:
        Path(command[command.index("--file") + 1]).write_bytes(b"custom-format-dump")
        return Mock(returncode=0)

    with (
        patch("migration.local_backup.shutil_which", return_value="/usr/bin/pg_dump"),
        patch("migration.local_backup.subprocess.run", side_effect=create_dump),
        patch("migration.local_backup.Path.write_text", side_effect=OSError("disk full")),
        pytest.raises(BackupError, match="creating local files"),
    ):
        postgres_backup("postgresql://backup:secret@localhost/app", output_dir)

    assert list(output_dir.iterdir()) == []


def test_verify_rejects_missing_postgres_backup_with_stable_error(
    tmp_path: Path,
) -> None:
    missing_backup = tmp_path / "missing.dump"
    manifest = tmp_path / "missing.dump.json"
    manifest.write_text(
        json.dumps(
            {
                "format": "postgresql-custom",
                "backup": missing_backup.name,
                "sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(BackupError, match="Backup artifact is missing or unreadable"):
        verify(missing_backup, manifest)


def test_sqlite_backup_rejects_output_directory_containing_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    create_database(source)

    with pytest.raises(BackupError, match="ambiguous"):
        sqlite_backup(source, tmp_path)


def create_postgres_artifact(tmp_path: Path) -> tuple[Path, Path]:
    backup = tmp_path / "postgres.dump"
    backup.write_bytes(b"custom-format-dump")
    manifest = tmp_path / "postgres.dump.json"
    manifest.write_text(
        json.dumps(
            {
                "format": "postgresql-custom",
                "backup": backup.name,
                "sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    return backup, manifest


def test_verify_postgres_dump_lists_archive_without_database_connection(
    tmp_path: Path,
) -> None:
    backup, manifest = create_postgres_artifact(tmp_path)
    completed = Mock(returncode=0)

    with (
        patch("migration.local_backup.shutil_which", return_value="/usr/bin/pg_restore"),
        patch("migration.local_backup.subprocess.run", return_value=completed) as run,
    ):
        verify(backup, manifest)

    run.assert_called_once_with(
        ["pg_restore", "--list", str(backup)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_verify_postgres_dump_rejects_checksum_before_structural_validation(
    tmp_path: Path,
) -> None:
    backup, manifest = create_postgres_artifact(tmp_path)
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_data["sha256"] = "0" * 64
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

    with (
        patch("migration.local_backup.shutil_which") as which,
        pytest.raises(BackupError, match="checksum"),
    ):
        verify(backup, manifest)

    which.assert_not_called()


def test_verify_postgres_dump_fails_when_pg_restore_is_unavailable(
    tmp_path: Path,
) -> None:
    backup, manifest = create_postgres_artifact(tmp_path)

    with (
        patch("migration.local_backup.shutil_which", return_value=None),
        pytest.raises(BackupError, match="pg_restore is unavailable"),
    ):
        verify(backup, manifest)


def test_verify_postgres_dump_fails_on_nonzero_pg_restore_exit(
    tmp_path: Path,
) -> None:
    backup, manifest = create_postgres_artifact(tmp_path)

    with (
        patch("migration.local_backup.shutil_which", return_value="/usr/bin/pg_restore"),
        patch(
            "migration.local_backup.subprocess.run",
            return_value=Mock(returncode=2),
        ),
        pytest.raises(BackupError, match="pg_restore failed with exit status 2"),
    ):
        verify(backup, manifest)


def test_verify_postgres_dump_fails_on_pg_restore_execution_error(
    tmp_path: Path,
) -> None:
    backup, manifest = create_postgres_artifact(tmp_path)

    with (
        patch("migration.local_backup.shutil_which", return_value="/usr/bin/pg_restore"),
        patch(
            "migration.local_backup.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
        pytest.raises(BackupError, match="Could not execute pg_restore"),
    ):
        verify(backup, manifest)
