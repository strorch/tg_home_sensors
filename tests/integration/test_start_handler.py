"""Integration tests for /start handler."""

import pytest
from unittest.mock import AsyncMock, patch

from src.bot.handlers.start import start_handler


@pytest.mark.asyncio
async def test_start_new_user(mock_telegram_update, mock_telegram_context):
    """Test /start command for a new user creates user and alert state."""
    # Mock user settings service
    with patch("src.bot.handlers.start.user_settings_service") as mock_service:
        mock_service.get_user = AsyncMock(return_value=None)  # User doesn't exist
        mock_service.create_user = AsyncMock()

        # Execute handler
        await start_handler(mock_telegram_update, mock_telegram_context)

        # Verify user creation was called
        mock_service.create_user.assert_called_once()

        # Verify welcome message was sent
        mock_telegram_update.message.reply_text.assert_called_once()
        message = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Welcome to Arduino Home Sensors Bot" in message
        assert "40.0%" in message  # Default min
        assert "60.0%" in message  # Default max


@pytest.mark.asyncio
async def test_start_existing_user(mock_telegram_update, mock_telegram_context, mock_user):
    """Test /start command for existing user shows welcome without recreating."""
    with patch("src.bot.handlers.start.user_settings_service") as mock_service:
        mock_service.get_user = AsyncMock(return_value=mock_user)
        mock_service.create_user = AsyncMock()

        # Execute handler
        await start_handler(mock_telegram_update, mock_telegram_context)

        # Verify user creation was NOT called
        mock_service.create_user.assert_not_called()

        # Verify welcome message was sent with user's thresholds
        mock_telegram_update.message.reply_text.assert_called_once()
        message = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Welcome to Arduino Home Sensors Bot" in message


@pytest.mark.asyncio
async def test_start_database_error(mock_telegram_update, mock_telegram_context):
    """Test /start command handles database errors gracefully."""
    with patch("src.bot.handlers.start.user_settings_service") as mock_service:
        mock_service.get_user = AsyncMock(side_effect=Exception("Database error"))

        # Execute handler
        await start_handler(mock_telegram_update, mock_telegram_context)

        # Verify error message was sent
        mock_telegram_update.message.reply_text.assert_called_once()
        message = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Sorry" in message or "unable" in message.lower()
