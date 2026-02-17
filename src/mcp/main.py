"""MCP server entry point."""

from __future__ import annotations

import logging

from src.bot.utils.logger import setup_logging
from src.config import load_config
from src.mcp.server import create_mcp_server


logger = logging.getLogger(__name__)


def main() -> None:
    """Run streamable HTTP MCP server."""
    config = load_config()
    setup_logging(config.log_level)

    if not config.mcp_enabled:
        raise RuntimeError("MCP is disabled. Set MCP_ENABLED=true to run MCP server.")
    if not config.mcp_api_key:
        raise RuntimeError("MCP_API_KEY is required for MCP server.")

    server = create_mcp_server(config)
    logger.info(
        "Starting MCP server on %s:%s/mcp",
        config.mcp_host,
        config.mcp_port,
    )
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
