#!/usr/bin/env python3
"""Export the FastAPI OpenAPI document for documentation builds."""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "openapi.json"


def export_openapi(output_path: Path) -> None:
    """Import the app with docs enabled outside production and write stable JSON."""
    # Testing is explicitly non-production and permits the local SQLite engine.
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DOCS_ENABLED"] = "true"
    os.environ.setdefault("DATABASE_URL", "sqlite:///./database/tarifa_disano.db")

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from app.main import app

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    export_openapi(args.output.resolve())


if __name__ == "__main__":
    main()
