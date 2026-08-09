"""Import the local SQLite productos table into a local PostgreSQL database."""

from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-path", type=Path, required=True)
    parser.add_argument("--postgres-url", required=True)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.batch_size < 1:
        parser.error("--batch-size must be greater than zero")
    validate_local_postgres_url(args.postgres_url)
    return args


def validate_local_postgres_url(postgres_url: str) -> None:
    """Reject network PostgreSQL targets; this harness is local-only."""
    parsed = urlparse(postgres_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("--postgres-url must use a PostgreSQL URL")
    if parsed.hostname not in (None, *LOCAL_HOSTS):
        raise ValueError("only local PostgreSQL hosts are allowed")


def discover_source_metadata(sqlite_path: Path) -> list[str]:
    """Return SQLite productos columns in their declared order."""
    with sqlite3.connect(sqlite_path) as connection:
        rows = connection.execute("PRAGMA table_info(productos)").fetchall()
    if not rows:
        raise ValueError("SQLite source has no productos table")
    return [str(row[1]) for row in rows]


def _quote_sqlite_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _load_source(sqlite_path: Path) -> tuple[list[str], int]:
    columns = discover_source_metadata(sqlite_path)
    if columns != PRODUCT_COLUMNS:
        raise ValueError(
            "SQLite productos schema does not match the explicit 40-column mapping"
        )
    try:
        with sqlite3.connect(sqlite_path) as connection:
            count = int(
                connection.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            )
    except sqlite3.Error as exc:
        raise ValueError("could not count rows in the SQLite productos table") from exc
    return columns, count


def _connect_postgres(postgres_url: str) -> Any:
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 is required for a non-dry-run import") from exc
    return psycopg2.connect(postgres_url)


def _read_batches(
    connection: sqlite3.Connection, batch_size: int
) -> Iterator[list[tuple[Any, ...]]]:
    columns_sql = ", ".join(
        _quote_sqlite_identifier(column) for column in PRODUCT_COLUMNS
    )
    cursor = connection.execute(f"SELECT {columns_sql} FROM productos")
    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            return
        yield batch


def import_products(sqlite_path: Path, postgres_url: str, batch_size: int) -> int:
    """Create the schema and import only productos, atomically."""
    _, source_count = _load_source(sqlite_path)
    pg_connection = _connect_postgres(postgres_url)
    try:
        with pg_connection, pg_connection.cursor() as cursor:
            cursor.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
            placeholders = ", ".join(["%s"] * len(PRODUCT_COLUMNS))
            columns_sql = ", ".join(f'"{column}"' for column in PRODUCT_COLUMNS)
            statement = (
                f'INSERT INTO "productos" ({columns_sql}) VALUES ({placeholders}) '
                'ON CONFLICT ("CÓDIGO") DO UPDATE SET '
                + ", ".join(
                    f'"{column}" = EXCLUDED."{column}"'
                    for column in PRODUCT_COLUMNS
                    if column != "CÓDIGO"
                )
            )
            imported = 0
            with sqlite3.connect(sqlite_path) as sqlite_connection:
                for batch in _read_batches(sqlite_connection, batch_size):
                    from psycopg2.extras import execute_batch

                    execute_batch(cursor, statement, batch, page_size=batch_size)
                    imported += len(batch)
            cursor.execute('SELECT COUNT(*) FROM "productos"')
            destination_count = int(cursor.fetchone()[0])
            cursor.execute(
                'SELECT COUNT(*) - COUNT(DISTINCT "CÓDIGO") FROM "productos"'
            )
            duplicate_count = int(cursor.fetchone()[0])
            if destination_count != source_count or duplicate_count != 0:
                raise RuntimeError(
                    "product count or primary-key uniqueness verification failed"
                )
        return imported
    except Exception:
        pg_connection.rollback()
        raise
    finally:
        pg_connection.close()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    columns, source_count = _load_source(args.sqlite_path)
    if args.dry_run:
        print(
            f"Dry run: source contains {source_count} productos rows "
            f"and {len(columns)} columns"
        )
        return 0
    imported = import_products(args.sqlite_path, args.postgres_url, args.batch_size)
    print(f"Imported {imported} productos rows into local PostgreSQL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
