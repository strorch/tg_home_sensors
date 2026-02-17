"""Authentication helpers for MCP HTTP transport."""

from __future__ import annotations

import secrets
import logging
from dataclasses import dataclass

from pydantic import AnyHttpUrl, TypeAdapter
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class ApiKeyTokenVerifier:
    """Token verifier that accepts a single shared bearer token."""

    api_key: str
    client_id: str = "sensor-mcp-client"

    async def verify_token(self, token: str) -> AccessToken | None:
        """Validate bearer token and return auth metadata when valid."""
        logger.warning("Verifying token: %s %s", token, self.api_key)
        if not secrets.compare_digest(token, self.api_key):
            return None

        return AccessToken(
            token=token,
            client_id=self.client_id,
            scopes=[],
        )


def build_auth_settings(base_url: str) -> AuthSettings:
    """Build minimal auth settings required by FastMCP for token verification."""
    parsed_url = TypeAdapter(AnyHttpUrl).validate_python(base_url)
    return AuthSettings(
        issuer_url=parsed_url,
        resource_server_url=parsed_url,
        required_scopes=[],
    )
