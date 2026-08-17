from app.config import Settings


def test_production_rate_limit_uses_settings_contract():
    settings = Settings(environment="production", rate_limit_per_client=75)

    assert settings.rate_limit_per_client == 75


def test_rate_limit_reader_uses_rate_limit_per_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("RATE_LIMIT_PER_CLIENT", "75")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "5")

    from app import middleware
    from app.config import get_settings

    get_settings.cache_clear()
    assert middleware.get_rate_limit() == 75


def test_development_wildcard_cors_disables_credentials():
    from app.main import app

    cors = next(
        middleware
        for middleware in app.user_middleware
        if getattr(middleware.cls, "__name__", "") == "CORSMiddleware"
    )

    assert cors.kwargs["allow_origins"] == ["*"]
    assert cors.kwargs["allow_credentials"] is False
