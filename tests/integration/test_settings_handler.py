"""Integration tests for settings command handlers."""

import os
import pytest
from unittest.mock import AsyncMock, patch
from telegram import Update, User as TelegramUser
from telegram.ext import ContextTypes

from src.bot.services.database import Database
from src.bot.services.user_settings import UserSettingsService


# Mock rate limiter to bypass rate limiting in tests
def mock_rate_limit(seconds=3):
    """Mock rate limiter that does nothing."""

    def decorator(func):
        return func

    return decorator


async def create_test_db(tmp_path):
    """Helper to create database with test user."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set for PostgreSQL tests")

    db = Database(database_url)
    await db.connect()
    await db.execute("DELETE FROM alert_states")
    await db.execute("DELETE FROM users")
    user_service = UserSettingsService(db)
    await user_service.create_or_update_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)
    return db, user_service


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_settings_display_current_thresholds(tmp_path):
    """Test /settings displays current user thresholds."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import settings_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await settings_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "⚙️" in response
    assert "Alert Settings" in response
    assert "40.0%" in response
    assert "60.0%" in response
    assert "/set_humidity_min" in response
    assert "/set_humidity_max" in response

    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_min_valid_value(tmp_path):
    """Test /set_humidity_min with valid value."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_min_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["35"]

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_min_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "✅" in response
    assert "35.0%" in response
    assert "60.0%" in response

    user = await user_service.get_user(12345)
    assert user.humidity_min == 35.0
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_min_out_of_range(tmp_path):
    """Test /set_humidity_min with out of range value."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_min_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["150"]

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_min_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "❌" in response
    assert "0 and 100" in response

    user = await user_service.get_user(12345)
    assert user.humidity_min == 40.0
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_min_greater_than_max(tmp_path):
    """Test /set_humidity_min with value greater than current max."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_min_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["65"]

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_min_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "❌" in response
    assert "less than maximum" in response
    assert "60.0%" in response

    user = await user_service.get_user(12345)
    assert user.humidity_min == 40.0
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_min_missing_parameter(tmp_path):
    """Test /set_humidity_min without value parameter."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_min_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_min_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "❌" in response
    assert "Missing" in response
    assert "Usage:" in response
    assert "/set_humidity_min" in response
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_max_valid_value(tmp_path):
    """Test /set_humidity_max with valid value."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_max_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["70"]

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_max_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "✅" in response
    assert "70.0%" in response
    assert "40.0%" in response

    user = await user_service.get_user(12345)
    assert user.humidity_max == 70.0
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_max_out_of_range(tmp_path):
    """Test /set_humidity_max with out of range value."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_max_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["-10"]

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_max_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "❌" in response
    assert "0 and 100" in response

    user = await user_service.get_user(12345)
    assert user.humidity_max == 60.0
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_max_less_than_min(tmp_path):
    """Test /set_humidity_max with value less than current min."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_max_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["35"]

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_max_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "❌" in response
    assert "greater than minimum" in response
    assert "40.0%" in response

    user = await user_service.get_user(12345)
    assert user.humidity_max == 60.0
    await db.close()


@pytest.mark.asyncio
@patch("src.bot.handlers.settings.rate_limit", mock_rate_limit)
async def test_set_humidity_max_missing_parameter(tmp_path):
    """Test /set_humidity_max without value parameter."""
    db, user_service = await create_test_db(tmp_path)

    from src.bot.handlers.settings import set_humidity_max_handler

    update = AsyncMock(spec=Update)
    update.effective_user = TelegramUser(id=12345, first_name="Test", is_bot=False)
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []

    with patch("src.bot.services.user_settings.user_settings_service", user_service):
        await set_humidity_max_handler(update, context)

    response = update.message.reply_text.call_args[0][0]
    assert "❌" in response
    assert "Missing" in response
    assert "Usage:" in response
    assert "/set_humidity_max" in response
    await db.close()
