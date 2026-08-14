"""Health endpoint checks without requiring a live database."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok_when_database_query_succeeds() -> None:
    connection = MagicMock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection

    with patch("app.main.engine", engine):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-disano"}
    connection.execute.assert_called_once()
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"


def test_health_returns_service_unavailable_when_query_fails() -> None:
    connection = MagicMock()
    connection.execute.side_effect = RuntimeError("database unavailable")
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection

    with patch("app.main.engine", engine):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "service": "api-disano",
    }


def test_health_returns_service_unavailable_without_database_details() -> None:
    engine = MagicMock()
    engine.connect.side_effect = RuntimeError(
        "postgresql://user:password@example.invalid/db is unavailable"
    )

    with patch("app.main.engine", engine):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "service": "api-disano",
    }
    assert "DATABASE_URL" not in response.text
    assert "password" not in response.text
    assert "example.invalid" not in response.text
