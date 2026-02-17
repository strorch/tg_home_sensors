"""Integration tests for MCP streamable HTTP auth behavior."""

from unittest.mock import AsyncMock

from starlette.testclient import TestClient

from src.config import Config
from src.mcp.server import create_mcp_server


def _test_config() -> Config:
    return Config(
        telegram_bot_token="test-token",
        serial_port="/dev/null",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/test_db",
        mcp_enabled=True,
        mcp_api_key="secret-key",
        mcp_host="127.0.0.1",
        mcp_port=18081,
    )


def test_mcp_server_requires_authorization(monkeypatch) -> None:
    connect_mock = AsyncMock()
    close_mock = AsyncMock()
    monkeypatch.setattr("src.mcp.server.Database.connect", connect_mock)
    monkeypatch.setattr("src.mcp.server.Database.close", close_mock)

    server = create_mcp_server(_test_config())
    app = server.streamable_http_app()

    with TestClient(app) as client:
        response = client.get("/mcp")

    assert response.status_code == 401


def test_mcp_server_accepts_valid_authorization(monkeypatch) -> None:
    connect_mock = AsyncMock()
    close_mock = AsyncMock()
    monkeypatch.setattr("src.mcp.server.Database.connect", connect_mock)
    monkeypatch.setattr("src.mcp.server.Database.close", close_mock)

    server = create_mcp_server(_test_config())
    app = server.streamable_http_app()

    with TestClient(app) as client:
        response = client.get(
            "/mcp",
            headers={"Authorization": "Bearer secret-key"},
        )

    assert response.status_code != 401
