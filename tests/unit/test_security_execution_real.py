"""Behavioral tests for the legacy security middleware module."""

import asyncio
import importlib.util
import json
from pathlib import Path

from fastapi import Request
from starlette.responses import JSONResponse


def load_legacy_security_module():
    """Load app/security.py despite the app.security package name collision."""
    module_path = Path(__file__).parents[2] / "app" / "security.py"
    spec = importlib.util.spec_from_file_location("legacy_security", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


security = load_legacy_security_module()


def make_request(path="/private", headers=None, client=("127.0.0.1", 50000)):
    """Build a minimal HTTP request for direct middleware execution."""
    encoded_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": encoded_headers,
            "client": client,
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


async def ok_response(_request):
    """Return a successful downstream response."""
    return JSONResponse({"ok": True})


def response_body(response):
    """Decode a JSON response body."""
    return json.loads(response.body)


def test_security_module_exports_expected_contract():
    assert callable(security.verify_admin_api_key)
    assert callable(security.get_rate_limit)
    assert security.APIKeyMiddleware
    assert security.RateLimitMiddleware
    assert security.UserAgentMiddleware
    assert security.SecurityHeadersMiddleware


def test_verify_admin_api_key_accepts_configured_production_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_API_KEYS", "first-key,second-key")
    request = make_request(headers={"X-Admin-API-Key": "second-key"})

    assert security.verify_admin_api_key(request) is True


def test_verify_admin_api_key_rejects_missing_production_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

    assert security.verify_admin_api_key(make_request()) is False


def test_api_key_middleware_rejects_missing_key_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    middleware = security.APIKeyMiddleware(ok_response)

    response = asyncio.run(middleware.dispatch(make_request(), ok_response))

    assert response.status_code == 401
    assert response_body(response)["detail"].startswith("API Key is required")


def test_api_key_middleware_accepts_configured_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEYS", "valid-key")
    middleware = security.APIKeyMiddleware(ok_response)
    request = make_request(headers={"X-API-Key": "valid-key"})

    response = asyncio.run(middleware.dispatch(request, ok_response))

    assert response.status_code == 200


def test_rate_limit_middleware_returns_configured_limit(monkeypatch):
    security.rate_limit_store.clear()
    monkeypatch.setattr(security, "get_rate_limit", lambda: 1)
    monkeypatch.setattr(security.time, "time", lambda: 1_000.0)
    middleware = security.RateLimitMiddleware(ok_response)
    request = make_request(headers={"X-API-Key": "limited-key"})

    first_response = asyncio.run(middleware.dispatch(request, ok_response))
    limited_response = asyncio.run(middleware.dispatch(request, ok_response))

    assert first_response.status_code == 200
    assert first_response.headers["X-RateLimit-Limit"] == "1"
    assert limited_response.status_code == 429
    assert limited_response.headers["X-RateLimit-Limit"] == "1"
    assert response_body(limited_response)["limit"] == 1


def test_rate_limit_middleware_handles_request_without_client(monkeypatch):
    security.rate_limit_store.clear()
    monkeypatch.setattr(security, "get_rate_limit", lambda: 2)
    middleware = security.RateLimitMiddleware(ok_response)

    response = asyncio.run(middleware.dispatch(make_request(client=None), ok_response))

    assert response.status_code == 200
    assert len(security.rate_limit_store["unknown-client"]) == 1


def test_user_agent_middleware_blocks_scrapers():
    middleware = security.UserAgentMiddleware(ok_response)
    request = make_request(headers={"User-Agent": "Example Scraper/1.0"})

    response = asyncio.run(middleware.dispatch(request, ok_response))

    assert response.status_code == 403
    assert response_body(response)["detail"] == ("Access denied. Suspicious User-Agent detected.")


def test_security_headers_middleware_adds_production_headers(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    middleware = security.SecurityHeadersMiddleware(ok_response)

    response = asyncio.run(middleware.dispatch(make_request(), ok_response))

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Strict-Transport-Security"] == ("max-age=31536000; includeSubDomains")
