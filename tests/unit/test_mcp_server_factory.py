"""Unit tests for MCP server factory."""

import pytest

from src.config import Config
from src.mcp.server import create_mcp_server


def test_create_mcp_server_requires_api_key() -> None:
    config = Config(
        telegram_bot_token="test-token",
        serial_port="/dev/null",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/test_db",
        mcp_enabled=True,
        mcp_api_key=None,
        mcp_host="127.0.0.1",
        mcp_port=18081,
    )

    with pytest.raises(ValueError, match="MCP_API_KEY"):
        create_mcp_server(config)
