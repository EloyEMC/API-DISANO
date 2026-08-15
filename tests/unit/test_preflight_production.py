"""Unit tests for the production preflight checks."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "preflight-production.py"


def load_preflight() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("preflight_production", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_environment(
    database_url: str = "postgresql://user:secret@example.test/db",
) -> str:
    return (
        "ENVIRONMENT=production\n"
        f"SECRET_KEY={'s' * 32}\n"
        "API_KEYS=generated-test-key\n"
        f"DATABASE_URL={database_url}\n"
    )


def test_preflight_rejects_missing_database_url(tmp_path: Path) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=production\n")
    env_file.chmod(0o600)

    result = module.run_preflight(env_file)

    assert result.ok is False
    assert result.message == "DATABASE_URL is required"


@pytest.mark.parametrize(
    ("environment", "secret_key", "api_keys", "message"),
    [
        ("production", "s" * 32, "key", None),
        ("staging", "s" * 32, "key", "ENVIRONMENT must be production"),
        ("production", "short", "key", "SECRET_KEY must be at least 32 characters"),
        ("production", "s" * 32, "", "API_KEYS must not be empty"),
    ],
)
def test_preflight_validates_production_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    environment: str,
    secret_key: str,
    api_keys: str,
    message: str | None,
) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"ENVIRONMENT={environment}\nSECRET_KEY={secret_key}\n"
        f"API_KEYS={api_keys}\nDATABASE_URL=postgresql://user:secret@example.test/db\n"
    )
    env_file.chmod(0o600)
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
    monkeypatch.setattr(module, "load_psycopg", lambda: (Mock(), "3.2.10"))
    monkeypatch.setattr(module, "connect_read_only", lambda _psycopg, _url: connection)

    result = module.run_preflight(env_file)

    if message is None:
        assert result.ok is True
    else:
        assert result.ok is False
        assert result.message == message


def test_preflight_rejects_insecure_env_permissions(tmp_path: Path) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(valid_environment())
    env_file.chmod(0o640)

    result = module.run_preflight(env_file)

    assert result.ok is False
    assert result.message == "environment file permissions must be 0600 or stricter"


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg://user:secret@example.test/db",
        "postgresql+asyncpg://user:secret@example.test/db",
    ],
)
def test_preflight_accepts_driver_qualified_postgresql_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    database_url: str,
) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(valid_environment(database_url))
    env_file.chmod(0o600)
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
    monkeypatch.setattr(module, "load_psycopg", lambda: (Mock(), "3.2.10"))
    connect = Mock(return_value=connection)
    monkeypatch.setattr(module, "connect_read_only", connect)

    result = module.run_preflight(env_file)

    assert result.ok is True
    connect.assert_called_once()
    assert connect.call_args.args[1] == database_url


@pytest.mark.parametrize(
    "database_url",
    [
        "mysql://user:secret@example.test/db",
        "postgresql+://user:secret@example.test/db",
        "postgresql+psy copg://user:secret@example.test/db",
        "postgresql+psycopg://user:secret@example.test/",
    ],
)
def test_preflight_rejects_non_postgresql_or_malformed_urls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    database_url: str,
) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(valid_environment(database_url))
    env_file.chmod(0o600)
    connect = Mock()
    monkeypatch.setattr(module, "load_psycopg", Mock())
    monkeypatch.setattr(module, "connect_read_only", connect)

    result = module.run_preflight(env_file)

    assert result.ok is False
    assert result.message == "DATABASE_URL must be a valid PostgreSQL URL"
    connect.assert_not_called()


def test_preflight_accepts_read_only_select_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(valid_environment())
    env_file.chmod(0o600)
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
    monkeypatch.setattr(module, "load_psycopg", lambda: (Mock(), "3.2.10"))
    monkeypatch.setattr(module, "connect_read_only", lambda _psycopg, _url: connection)

    result = module.run_preflight(env_file)

    assert result.ok is True
    connection.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
        "SELECT 1"
    )
    assert "secret" not in result.message


def test_preflight_hides_connection_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(valid_environment())
    env_file.chmod(0o600)
    monkeypatch.setattr(module, "load_psycopg", lambda: (Mock(), "3.2.10"))
    monkeypatch.setattr(
        module, "connect_read_only", Mock(side_effect=RuntimeError("password=secret"))
    )

    result = module.run_preflight(env_file)

    assert result.ok is False
    assert result.message == "read-only database connectivity check failed"
    assert "secret" not in result.message


def test_preflight_requires_exact_pinned_psycopg_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = load_preflight()
    env_file = tmp_path / ".env"
    env_file.write_text(valid_environment())
    env_file.chmod(0o600)
    monkeypatch.setattr(module, "load_psycopg", lambda: (Mock(), "3.2.9"))

    result = module.run_preflight(env_file)

    assert result.ok is False
    assert result.message == "psycopg version must be 3.2.10"


def test_preflight_static_service_wiring() -> None:
    deploy_script = (SCRIPT_PATH.parent / "deploy-hetzner.sh").read_text()
    setup_script = (SCRIPT_PATH.parent / "setup-production.sh").read_text()

    assert 'chmod 600 "$tmp_file"' in deploy_script
    assert "After=network-online.target" in deploy_script
    assert "Wants=network-online.target" in deploy_script
    assert "ExecStartPre=+" in deploy_script
    assert "User=www-data" in deploy_script
    for script in (deploy_script, setup_script):
        assert "secrets.token_urlsafe(32)" in script
        assert 'validate_environment_value "SECRET_KEY" "$SECRET_KEY"' in script
        assert "SECRET_KEY=$SECRET_KEY" in script
        assert 'chmod 600 "$tmp_file"' in script


@pytest.mark.parametrize("script_name", ["deploy-hetzner.sh", "setup-production.sh"])
def test_secret_handling_is_not_logged_or_duplicated(script_name: str) -> None:
    script = (SCRIPT_PATH.parent / script_name).read_text()

    assert 'echo "   API Key: $API_KEY"' not in script
    assert 'echo "  API Key: $API_KEY"' not in script
    assert "X-API-Key: $API_KEY" not in script
    assert "api-disano-credentials.txt" not in script
    assert "api-disano-api-key.txt" not in script
    assert "cat >/root/" not in script


@pytest.mark.parametrize("script_name", ["deploy-hetzner.sh", "setup-production.sh"])
def test_env_write_is_atomic_and_private(script_name: str) -> None:
    script = (SCRIPT_PATH.parent / script_name).read_text()

    assert "umask 077" in script
    assert "mktemp" in script
    assert 'chmod 600 "$tmp_file"' in script
    assert 'chown root:root "$tmp_file"' in script
    assert 'mv -f -- "$tmp_file" "$env_file"' in script


@pytest.mark.parametrize("script_name", ["deploy-hetzner.sh", "setup-production.sh"])
def test_env_values_reject_systemd_parser_injection(script_name: str) -> None:
    script = (SCRIPT_PATH.parent / script_name).read_text()

    assert "validate_environment_value" in script
    assert "CR/LF" in script
    assert 'validate_environment_value "API_KEYS" "$API_KEY"' in script
    assert 'validate_environment_value "SECRET_KEY" "$SECRET_KEY"' in script
    assert 'validate_environment_value "DATABASE_URL" "$DATABASE_URL"' in script


def test_verify_deployment_uses_configured_domain_and_static_preflight_check() -> None:
    script = (SCRIPT_PATH.parent / "verify-deployment.sh").read_text()

    assert 'DOMAIN="${DOMAIN:-}"' in script
    assert 'grep -q "api.eloymartinezcuesta.com"' not in script
    assert 'check "production preflight script is present"' in script
    assert "preflight-production.py" in script
    assert "run_preflight" not in script
