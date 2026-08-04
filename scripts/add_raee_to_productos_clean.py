#!/usr/bin/env python3
"""
Add RAEE columns to the `productos_clean` view (idempotent, additive).

Why a script (not a hardcoded DROP/CREATE):
  The `productos_clean` view selects a date-stamped PVP column
  (e.g. `[PVP_26_01_26]`) that changes when DISANO republishes prices, plus
  other columns that may differ between dev/prod. Hardcoding a full view
  definition would freeze the wrong PVP or drop prod-only columns.

  This script instead READS the current view SQL, INJECTS the three RAEE
  column expressions right before `FROM productos`, and recreates the view.
  Existing columns (including the live PVP column) are preserved untouched.
  It is IDEMPOTENT: if `raee_a` is already projected, it does nothing.

RAEE data lives in the `productos` table:
  RAEE_A (aparatos), RAEE_L (lamparas), RAEE_T (total ~= A + L).
  Confirmed populated: ~7112/8288 rows non-zero for RAEE_A (2026-08).

Effect:
  After running this, `/api/productos/{codigo}` and the product search
  endpoint expose `raee_a` / `raee_l` / `raee_t` (lowercase, via
  ProductoModelClean -> ProductoEntity -> model_dump()), which the BC3-Suite
  presupuesto editor consumes for the RAE columns (R-4.a / R-4.b / R-5).

Usage:
  python scripts/add_raee_to_productos_clean.py [--db path/to/tarifa_disano.db]

  Default DB: database/tarifa_disano.db (override with DISANO_DB env or --db).

Safe: purely additive view change. No table data is touched. Reversible by
recreating the view without the RAEE columns (see bottom of this file).
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

VIEW_NAME = "productos_clean"
SOURCE_TABLE = "productos"
# Injected column expressions (source column -> clean alias).
RAEE_EXPRS = ["RAEE_A as raee_a", "RAEE_L as raee_l", "RAEE_T as raee_t"]
RAEE_ALIASES = {"raee_a", "raee_l", "raee_t"}


def get_view_sql(con: sqlite3.Connection) -> str | None:
    row = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (VIEW_NAME,)
    ).fetchone()
    return row[0] if row else None


def aliases_in_view(view_sql: str) -> set[str]:
    """Best-effort extraction of projected aliases from the view SELECT list."""
    m = re.search(r"SELECT\s+(.*?)\s+FROM\s+", view_sql, re.S | re.I)
    if not m:
        return set()
    select_list = m.group(1)
    aliases: set[str] = set()
    for raw in select_list.split(","):
        token = raw.strip()
        # "X as alias" -> alias ; bare column -> column
        am = re.search(r"\bas\s+([A-Za-z_][\w]*)\s*$", token, re.I)
        aliases.add(am.group(1) if am else re.sub(r"[\[\]]", "", token).strip())
    return aliases


def inject_raee(view_sql: str) -> str:
    """Insert the RAEE column expressions before `FROM productos`."""
    pattern = re.compile(r"(\s+FROM\s+" + SOURCE_TABLE + r"\b)", re.I)
    addition = ",\n    " + ",\n    ".join(RAEE_EXPRS)
    new_sql, n = pattern.subn(addition + r"\1", view_sql, count=1)
    if n != 1:
        raise RuntimeError(
            "Could not locate `FROM productos` in the view SQL; aborting (no changes)."
        )
    return new_sql


def main() -> int:
    default_db = os.environ.get("DISANO_DB", "database/tarifa_disano.db")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=default_db, help="Path to tarifa_disano.db")
    ap.add_argument("--dry-run", action="store_true", help="Print new SQL, do not apply")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        return 2

    con = sqlite3.connect(args.db)
    try:
        # 0. Sanety: source columns exist in productos.
        src_cols = {c[1] for c in con.execute(f"PRAGMA table_info({SOURCE_TABLE})").fetchall()}
        missing = {"RAEE_A", "RAEE_L", "RAEE_T"} - src_cols
        if missing:
            print(f"ERROR: {SOURCE_TABLE} lacks RAEE columns: {sorted(missing)}", file=sys.stderr)
            return 3

        view_sql = get_view_sql(con)
        if not view_sql:
            print(f"ERROR: view `{VIEW_NAME}` not found in {args.db}", file=sys.stderr)
            return 4

        present = aliases_in_view(view_sql) & RAEE_ALIASES
        if RAEE_ALIASES.issubset(present):
            print(f"OK: `{VIEW_NAME}` already projects {sorted(RAEE_ALIASES)} — nothing to do.")
            return 0

        new_sql = inject_raee(view_sql)
        print("New view SQL:\n" + new_sql + "\n")

        if args.dry_run:
            print("DRY-RUN: no changes applied.")
            return 0

        con.execute(f"DROP VIEW IF EXISTS {VIEW_NAME}")
        con.executescript(new_sql)
        con.commit()

        # Verify
        cols = [c[1] for c in con.execute(f"PRAGMA table_info({VIEW_NAME})").fetchall()]
        added = [c for c in ("raee_a", "raee_l", "raee_t") if c in cols]
        print(f"DONE. `{VIEW_NAME}` now projects: {added}")
        if set(added) != RAEE_ALIASES:
            print(f"WARN: expected {sorted(RAEE_ALIASES)}, got {added}", file=sys.stderr)
            return 5
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
