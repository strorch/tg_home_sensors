"""Unit tests for MCP auth helpers."""

import pytest

from src.mcp.auth import ApiKeyTokenVerifier, build_auth_settings


@pytest.mark.asyncio
async def test_api_key_token_verifier_accepts_valid_token() -> None:
    verifier = ApiKeyTokenVerifier(api_key="secret-key")

    token = await verifier.verify_token("secret-key")

    assert token is not None
    assert token.client_id == "sensor-mcp-client"
    assert token.scopes == []


@pytest.mark.asyncio
async def test_api_key_token_verifier_rejects_invalid_token() -> None:
    verifier = ApiKeyTokenVerifier(api_key="secret-key")

    token = await verifier.verify_token("wrong-key")

    assert token is None


def test_build_auth_settings_uses_base_url() -> None:
    settings = build_auth_settings("http://127.0.0.1:8081")

    assert str(settings.issuer_url) == "http://127.0.0.1:8081/"
    assert str(settings.resource_server_url) == "http://127.0.0.1:8081/"
    assert settings.required_scopes == []
