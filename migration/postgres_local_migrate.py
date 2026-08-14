"""Import the local SQLite productos table into a local PostgreSQL database."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import math
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit

from migration.local_backup import BackupError, normalize_local_postgres_url, verify

PRODUCT_COLUMNS = [
    "MARCA",
    "CÓDIGO",
    "CÓDIGO WEB",
    "REFERENCIA",
    "EAN 13",
    "DESCRIPCION",
    "U.P.LOG",
    "U.CAJA",
    "DTO.",
    "CLASE ETIM",
    "RAEE_A",
    "RAEE_L",
    "RAEE_T",
    "Peso bruto KG",
    "Peso bruto GR",
    "Peso neto KG",
    "Peso neto GR",
    "Longitud M",
    "Longitud MM",
    "Ancho M",
    "Ancho MM",
    "Alto M",
    "Altura MM",
    "Volumen DM3",
    "CM3",
    "Serie_familia_1",
    "Familia_WEB",
    "Familia_Catalogo",
    "Familia_Catalogo_PTL",
    "imagen",
    "Url_ficha_tec",
    "descontinuado",
    "descripcion_corta",
    "img_url",
    "PVP_26_01_26",
    "bc3_descripcion_corta",
    "bc3_descripcion_larga",
    "bc3_product_type",
    "bc3_processed_at",
    "bc3_descripcion_completa",
]
SCHEMA_PATH = Path(__file__).with_name("04_postgres_schema.sql")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class VerificationError(RuntimeError):
    """Raised when verification cannot prove source/target equivalence."""


@dataclass(frozen=True)
class VerificationResult:
    null_source_keys: int = 0
    duplicate_source_keys: int = 0
    duplicate_target_keys: int = 0
    missing_target_keys: int = 0
    extra_target_keys: int = 0
    content_digest_mismatches: int = 0

    @property
    def is_valid(self) -> bool:
        return not any(vars(self).values())


def _count(result: VerificationResult, field: str) -> VerificationResult:
    return replace(result, **{field: getattr(result, field) + 1})


def _canonical_value(value: Any) -> bytes:
    if value is None:
        return b"N"
    if isinstance(value, bool):
        return b"B1" if value else b"B0"
    if isinstance(value, int):
        return b"I" + str(value).encode("ascii")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise VerificationError("unsupported non-finite float value")
        return b"F" + repr(value).encode("ascii")
    if isinstance(value, Decimal):
        return b"D" + format(value, "f").encode("utf-8")
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"S" + str(len(encoded)).encode("ascii") + b":" + encoded
    if isinstance(value, bytes):
        return b"Y" + value.hex().encode("ascii")
    if isinstance(value, datetime):
        return b"T" + value.isoformat().encode("utf-8")
    if isinstance(value, date):
        return b"A" + value.isoformat().encode("ascii")
    if isinstance(value, time):
        return b"H" + value.isoformat().encode("utf-8")
    raise VerificationError(f"unsupported row value type: {type(value).__name__}")


def canonical_row_hash(row: Iterable[Any]) -> str:
    """Hash a row deterministically without retaining or logging its contents."""
    digest = hashlib.sha256()
    for value in row:
        encoded = _canonical_value(value)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _values_equal(source_value: Any, target_value: Any) -> bool:
    if isinstance(source_value, datetime) and isinstance(target_value, str):
        try:
            return source_value == datetime.fromisoformat(target_value)
        except ValueError:
            return False
    if isinstance(source_value, str) and isinstance(target_value, datetime):
        try:
            return datetime.fromisoformat(source_value) == target_value
        except ValueError:
            return False
    return _canonical_value(source_value) == _canonical_value(target_value)


def _rows_equal(source_row: tuple[Any, ...], target_row: tuple[Any, ...]) -> bool:
    if len(source_row) != len(target_row):
        return False
    return all(
        _values_equal(source_value, target_value)
        for source_value, target_value in zip(source_row, target_row, strict=True)
    )


def compare_sorted_keys(
    source_keys: Iterable[Any], target_keys: Iterable[Any]
) -> VerificationResult:
    """Compare sorted key streams while retaining only counters and lookahead."""
    source, target = iter(source_keys), iter(target_keys)
    end = object()
    source_key, target_key = next(source, end), next(target, end)
    previous_source = previous_target = end
    result = VerificationResult()
    while source_key is not end or target_key is not end:
        if source_key is end:
            result = _count(result, "extra_target_keys")
            target_key = next(target, end)
            continue
        if target_key is end:
            result = _count(result, "missing_target_keys")
            source_key = next(source, end)
            continue
        if source_key is None:
            result = _count(result, "null_source_keys")
            source_key = next(source, end)
            continue
        if source_key == previous_source:
            result = _count(result, "duplicate_source_keys")
        if target_key == previous_target:
            result = _count(result, "duplicate_target_keys")
        previous_source, previous_target = source_key, target_key
        if source_key == target_key:
            source_key, target_key = next(source, end), next(target, end)
        else:
            source_value = cast(Any, source_key)
            target_value = cast(Any, target_key)
            if source_value < target_value:
                result = _count(result, "missing_target_keys")
                source_key = next(source, end)
            else:
                result = _count(result, "extra_target_keys")
                target_key = next(target, end)

    return result


def _next_row(
    iterator: Iterator[tuple[Any, ...]], key_index: int
) -> tuple[Any, tuple[Any, ...]] | None:
    try:
        row = next(iterator)
    except StopIteration:
        return None
    if key_index >= len(row):
        raise VerificationError("row does not contain the configured key column")
    return row[key_index], row


def verify_source_target_rows(
    source_rows: Iterable[tuple[Any, ...]],
    target_rows: Iterable[tuple[Any, ...]],
    key_index: int = 0,
) -> VerificationResult:
    """Verify sorted row streams in one pass with bounded row memory."""
    source, target = iter(source_rows), iter(target_rows)
    source_item, target_item = (
        _next_row(source, key_index),
        _next_row(target, key_index),
    )
    previous_source = previous_target = object()
    result = VerificationResult()
    while source_item is not None or target_item is not None:
        if source_item is None:
            result = _count(result, "extra_target_keys")
            target_item = _next_row(target, key_index)
            continue
        if target_item is None:
            result = _count(result, "missing_target_keys")
            source_item = _next_row(source, key_index)
            continue
        source_key, source_row = source_item
        target_key, target_row = target_item
        if source_key is None:
            result = _count(result, "null_source_keys")
        if source_key == previous_source:
            result = _count(result, "duplicate_source_keys")
        if target_key == previous_target:
            result = _count(result, "duplicate_target_keys")
        previous_source, previous_target = source_key, target_key
        if source_key == target_key:
            if not _rows_equal(source_row, target_row):
                result = _count(result, "content_digest_mismatches")
            source_item, target_item = (
                _next_row(source, key_index),
                _next_row(target, key_index),
            )
        elif source_key is None or source_key < target_key:
            result = _count(result, "missing_target_keys")
            source_item = _next_row(source, key_index)
        else:
            result = _count(result, "extra_target_keys")
            target_item = _next_row(target, key_index)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-path", type=Path, required=True)
    parser.add_argument("--postgres-url", required=True)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--postgres-backup", type=Path)
    parser.add_argument("--postgres-backup-manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.batch_size < 1:
        parser.error("--batch-size must be greater than zero")
    validate_local_postgres_url(args.postgres_url)
    return args


def validate_local_postgres_url(postgres_url: str) -> None:
    """Apply the same strict local PostgreSQL URL policy as the backup tool."""
    try:
        normalize_local_postgres_url(postgres_url)
    except BackupError as exc:
        raise ValueError(
            f"--postgres-url is invalid for local PostgreSQL: {exc}"
        ) from exc


def discover_source_metadata(sqlite_path: Path) -> list[str]:
    with sqlite3.connect(sqlite_path) as connection:
        rows = connection.execute("PRAGMA table_info(productos)").fetchall()
    if not rows:
        raise ValueError("SQLite source has no productos table")
    return [str(row[1]) for row in rows]


def _quote_sqlite_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


@contextmanager
def _open_source_snapshot(
    sqlite_path: Path,
) -> Iterator[tuple[list[str], int, sqlite3.Connection]]:
    """Open one immutable, read-only view of the SQLite source."""
    uri = f"{sqlite_path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        rows = connection.execute("PRAGMA table_info(productos)").fetchall()
        if not rows:
            raise ValueError("SQLite source has no productos table")
        columns = [str(row[1]) for row in rows]
        if columns != PRODUCT_COLUMNS:
            raise ValueError(
                "SQLite productos schema does not match the explicit 40-column mapping"
            )
        count = int(connection.execute("SELECT COUNT(*) FROM productos").fetchone()[0])
        yield columns, count, connection
    finally:
        connection.close()


def _load_source(sqlite_path: Path) -> tuple[list[str], int]:
    with _open_source_snapshot(sqlite_path) as (columns, count, _):
        return columns, count


def require_verified_postgres_backup(
    backup: Path | None, manifest_path: Path | None
) -> None:
    if backup is None or manifest_path is None:
        raise BackupError(
            "a verified PostgreSQL backup artifact and manifest are required before migration writes"
        )
    try:
        verify(backup, manifest_path)
    except (BackupError, OSError) as exc:
        raise BackupError(f"verified PostgreSQL backup is required: {exc}") from exc


def _connect_postgres(postgres_url: str) -> Any:
    try:
        psycopg = importlib.import_module("psycopg")
    except ImportError as exc:
        raise RuntimeError("psycopg is required for a non-dry-run import") from exc
    parsed = urlsplit(postgres_url)
    if "+" in parsed.scheme:
        postgres_url = urlunsplit(
            (
                parsed.scheme.split("+", 1)[0],
                parsed.netloc,
                parsed.path,
                parsed.query,
                parsed.fragment,
            )
        )
    return psycopg.connect(postgres_url)


def _read_batches(
    connection: sqlite3.Connection, batch_size: int
) -> Iterator[list[tuple[Any, ...]]]:
    columns_sql = ", ".join(
        _quote_sqlite_identifier(column) for column in PRODUCT_COLUMNS
    )
    cursor = connection.execute(f"SELECT {columns_sql} FROM productos")
    while batch := cursor.fetchmany(batch_size):
        yield batch


def _read_sorted_rows(
    connection: sqlite3.Connection, batch_size: int
) -> Iterator[tuple[Any, ...]]:
    columns_sql = ", ".join(
        _quote_sqlite_identifier(column) for column in PRODUCT_COLUMNS
    )
    cursor = connection.execute(
        f'SELECT {columns_sql} FROM productos ORDER BY "CÓDIGO"'
    )
    while batch := cursor.fetchmany(batch_size):
        yield from batch


def _read_cursor_rows(cursor: Any, batch_size: int) -> Iterator[tuple[Any, ...]]:
    while batch := cursor.fetchmany(batch_size):
        yield from batch


def import_products(
    sqlite_path: Path,
    postgres_url: str,
    batch_size: int,
    postgres_backup: Path | None = None,
    postgres_backup_manifest: Path | None = None,
) -> int:
    validate_local_postgres_url(postgres_url)
    require_verified_postgres_backup(postgres_backup, postgres_backup_manifest)
    pg_connection = _connect_postgres(postgres_url)
    try:
        with (
            pg_connection,
            pg_connection.cursor() as cursor,
            _open_source_snapshot(sqlite_path) as (_, source_count, sqlite_connection),
        ):
            cursor.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
            placeholders = ", ".join(["%s"] * len(PRODUCT_COLUMNS))
            columns_sql = ", ".join(f'"{column}"' for column in PRODUCT_COLUMNS)
            statement = (
                f'INSERT INTO "productos" ({columns_sql}) VALUES ({placeholders}) ON CONFLICT ("CÓDIGO") DO UPDATE SET '
                + ", ".join(
                    f'"{column}" = EXCLUDED."{column}"'
                    for column in PRODUCT_COLUMNS
                    if column != "CÓDIGO"
                )
            )
            imported = 0
            for batch in _read_batches(sqlite_connection, batch_size):
                cursor.executemany(statement, batch)
                imported += len(batch)
            cursor.execute(f'SELECT {columns_sql} FROM "productos" ORDER BY "CÓDIGO"')

            result = verify_source_target_rows(
                _read_sorted_rows(sqlite_connection, batch_size),
                _read_cursor_rows(cursor, batch_size),
                key_index=1,
            )
            if not result.is_valid or source_count != imported:
                raise RuntimeError("source/target row verification failed")
        return imported
    except Exception:
        if not getattr(pg_connection, "closed", False):
            pg_connection.rollback()
        raise
    finally:
        pg_connection.close()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    columns, source_count = _load_source(args.sqlite_path)
    if args.dry_run:
        print(
            f"Dry run: source contains {source_count} productos rows and {len(columns)} columns"
        )
        return 0
    imported = import_products(
        args.sqlite_path,
        args.postgres_url,
        args.batch_size,
        args.postgres_backup,
        args.postgres_backup_manifest,
    )
    print(f"Imported {imported} productos rows into local PostgreSQL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
