import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "export-openapi.py"


def test_export_openapi_writes_deterministic_documentation_schema(tmp_path: Path) -> None:
    output_path = tmp_path / "openapi.json"
    environment = os.environ.copy()
    environment.pop("ENVIRONMENT", None)
    environment.pop("DOCS_ENABLED", None)

    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output_path)],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )
    first_bytes = output_path.read_bytes()

    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output_path)],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )
    assert output_path.read_bytes() == first_bytes

    document = json.loads(first_bytes)
    assert document["openapi"].startswith("3.")
    assert "/docs" not in document["paths"]
    assert "/openapi.json" not in document["paths"]
    assert first_bytes.decode("utf-8").endswith("\n")


def test_export_openapi_does_not_enable_production_documentation() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"ENVIRONMENT"] = "testing"' in source
    assert '"DOCS_ENABLED"] = "true"' in source
    assert '"production"' not in source
