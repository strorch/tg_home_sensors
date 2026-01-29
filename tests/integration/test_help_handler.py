"""Integration tests for /help handler."""

import pytest

from src.bot.handlers.start import help_handler


@pytest.mark.asyncio
async def test_help_message_content(mock_telegram_update, mock_telegram_context):
    """Test /help command returns comprehensive help message."""
    # Execute handler
    await help_handler(mock_telegram_update, mock_telegram_context)

    # Verify help message was sent
    mock_telegram_update.message.reply_text.assert_called_once()
    message = mock_telegram_update.message.reply_text.call_args[0][0]

    # Verify key sections are present
    assert "Help" in message or "help" in message
    assert "/sensors" in message or "/status" in message
    assert "/settings" in message
    assert "/set_humidity_min" in message
    assert "/set_humidity_max" in message


@pytest.mark.asyncio
async def test_help_message_formatting(mock_telegram_update, mock_telegram_context):
    """Test /help command message is properly formatted."""
    # Execute handler
    await help_handler(mock_telegram_update, mock_telegram_context)

    # Verify message was sent
    mock_telegram_update.message.reply_text.assert_called_once()
    message = mock_telegram_update.message.reply_text.call_args[0][0]

    # Verify formatting elements
    assert "📊" in message or "⚙️" in message  # Contains emojis
    assert len(message) > 100  # Reasonably comprehensive
