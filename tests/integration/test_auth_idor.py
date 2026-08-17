"""Integration checks for the currently supported authentication and BC3 contract."""

from app.config import Settings


def test_user_and_admin_api_keys_are_distinct() -> None:
    settings = Settings(
        secret_key="test-secret-key",
        api_keys=["test-user-api-key-placeholder"],
        admin_api_keys=["admin"],
    )

    assert set(settings.api_keys_list).isdisjoint(settings.admin_api_keys)


def test_bc3_stats_route_is_publicly_supported(client) -> None:
    response = client.get("/api/bc3/v2/stats")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
