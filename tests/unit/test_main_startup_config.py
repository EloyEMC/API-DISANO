"""Startup configuration contract tests."""

from unittest.mock import Mock

import pytest


@pytest.mark.parametrize(
    "environment,secret_key,api_keys,should_fail",
    [
        ("production", "", [], True),
        ("production", "short", ["api-key"], True),
        ("production", "s" * 32, [], True),
        ("development", "", [], False),
        ("testing", "short", [], False),
    ],
)
def test_startup_configuration_fails_closed_only_in_production(
    monkeypatch, environment, secret_key, api_keys, should_fail
):
    import app.main as main

    settings = Mock(environment=environment, secret_key=secret_key, api_keys=api_keys)
    if should_fail:
        settings.validate_required.side_effect = ValueError("Missing required production settings")

    monkeypatch.setattr(main, "get_settings", lambda: settings)

    if should_fail:
        with pytest.raises(ValueError, match="Missing required production settings"):
            main.validate_startup_configuration()
    else:
        main.validate_startup_configuration()
        settings.validate_required.assert_called_once()
