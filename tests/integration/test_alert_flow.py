"""Integration tests for alert flow."""

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from telegram.error import Forbidden

from src.bot.models.sensor_reading import SensorReading


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set for PostgreSQL tests")
    return url


async def _setup_database():
    from src.bot.services.database import Database

    db = Database(_database_url())
    await db.connect()
    await db.execute("DELETE FROM alert_states")
    await db.execute("DELETE FROM users")
    return db


@pytest.mark.asyncio
async def test_high_humidity_alert_sent(mock_telegram_context, tmp_path):
    """Test high humidity alert is sent when threshold exceeded."""
    from src.bot.services.user_settings import UserSettingsService
    from src.bot.services.alert_manager import AlertManager

    # Setup database
    db = await _setup_database()

    user_service = UserSettingsService(db)

    # Create user with thresholds
    await user_service.create_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)

    # Create alert manager
    mock_bot = AsyncMock()
    alert_manager = AlertManager(database=db, bot=mock_bot)

    # Simulate high humidity reading
    reading = SensorReading(
        humidity=72.5,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    # Process reading
    await alert_manager.process_reading(reading, chat_id=12345)

    # Verify alert was sent
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args
    assert args[1]["chat_id"] == 12345
    assert "HIGH HUMIDITY ALERT" in args[1]["text"]

    await db.close()


@pytest.mark.asyncio
async def test_low_humidity_alert_sent(mock_telegram_context, tmp_path):
    """Test low humidity alert is sent when below threshold."""
    from src.bot.services.user_settings import UserSettingsService
    from src.bot.services.alert_manager import AlertManager

    db = await _setup_database()

    user_service = UserSettingsService(db)
    await user_service.create_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)

    mock_bot = AsyncMock()
    alert_manager = AlertManager(database=db, bot=mock_bot)

    reading = SensorReading(
        humidity=28.0,
        dht_temperature=18.2,
        lm35_temperature=19.0,
        thermistor_temperature=17.5,
        timestamp=datetime.now(timezone.utc),
    )

    await alert_manager.process_reading(reading, chat_id=12345)

    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args
    assert "LOW HUMIDITY ALERT" in args[1]["text"]

    await db.close()


@pytest.mark.asyncio
async def test_cooldown_prevents_duplicate_alerts(mock_telegram_context, tmp_path):
    """Test cooldown prevents sending alerts too frequently."""
    from src.bot.services.user_settings import UserSettingsService
    from src.bot.services.alert_manager import AlertManager

    db = await _setup_database()

    user_service = UserSettingsService(db)
    await user_service.create_user(chat_id=12345)

    mock_bot = AsyncMock()
    alert_manager = AlertManager(database=db, bot=mock_bot)

    reading = SensorReading(
        humidity=72.5,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    # First alert should be sent
    await alert_manager.process_reading(reading, chat_id=12345)
    assert mock_bot.send_message.call_count == 1

    # Second alert within cooldown should NOT be sent
    mock_bot.reset_mock()
    await alert_manager.process_reading(reading, chat_id=12345)
    mock_bot.send_message.assert_not_called()

    await db.close()


@pytest.mark.asyncio
async def test_recovery_notification_sent(mock_telegram_context, tmp_path):
    """Test recovery notification when humidity returns to normal."""
    from src.bot.services.user_settings import UserSettingsService
    from src.bot.services.alert_manager import AlertManager

    db = await _setup_database()

    user_service = UserSettingsService(db)
    await user_service.create_user(chat_id=12345)

    mock_bot = AsyncMock()
    alert_manager = AlertManager(database=db, bot=mock_bot)

    # First: high humidity alert
    high_reading = SensorReading(
        humidity=72.5,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    await alert_manager.process_reading(high_reading, chat_id=12345)
    assert "HIGH HUMIDITY" in mock_bot.send_message.call_args[1]["text"]

    # Then: humidity returns to normal
    mock_bot.reset_mock()
    normal_reading = SensorReading(
        humidity=52.0,
        dht_temperature=23.4,
        lm35_temperature=24.1,
        thermistor_temperature=22.9,
        timestamp=datetime.now(timezone.utc),
    )

    await alert_manager.process_reading(normal_reading, chat_id=12345)

    # Verify recovery notification sent
    mock_bot.send_message.assert_called_once()
    assert "NORMAL" in mock_bot.send_message.call_args[1]["text"]

    await db.close()


@pytest.mark.asyncio
async def test_multi_user_alert_isolation(mock_telegram_context, tmp_path):
    """Test each user receives only their own alerts."""
    from src.bot.services.user_settings import UserSettingsService
    from src.bot.services.alert_manager import AlertManager

    db = await _setup_database()

    user_service = UserSettingsService(db)

    # Create two users with different thresholds
    await user_service.create_user(chat_id=11111, humidity_min=40.0, humidity_max=60.0)
    await user_service.create_user(chat_id=22222, humidity_min=30.0, humidity_max=70.0)

    mock_bot = AsyncMock()
    alert_manager = AlertManager(database=db, bot=mock_bot)

    # Reading that exceeds user1's threshold but not user2's
    reading = SensorReading(
        humidity=65.0,  # Above 60% (user1) but below 70% (user2)
        dht_temperature=26.0,
        lm35_temperature=26.5,
        thermistor_temperature=25.8,
        timestamp=datetime.now(timezone.utc),
    )

    # Process for user1 - should get alert
    await alert_manager.process_reading(reading, chat_id=11111)
    user1_calls = mock_bot.send_message.call_count

    # Process for user2 - should NOT get alert
    mock_bot.reset_mock()
    await alert_manager.process_reading(reading, chat_id=22222)
    user2_calls = mock_bot.send_message.call_count

    assert user1_calls == 1  # User1 got alert
    assert user2_calls == 0  # User2 did not get alert

    await db.close()


@pytest.mark.asyncio
async def test_blocked_user_removed_stops_retry_spam(mock_telegram_context, tmp_path):
    """Test blocked users are removed and not retried on next reading."""
    from src.bot.services.user_settings import UserSettingsService
    from src.bot.services.alert_manager import AlertManager

    db = await _setup_database()
    user_service = UserSettingsService(db)
    await user_service.create_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)

    mock_bot = AsyncMock()
    mock_bot.send_message.side_effect = Forbidden("Forbidden: bot was blocked by the user")
    alert_manager = AlertManager(database=db, bot=mock_bot)

    reading = SensorReading(
        humidity=72.5,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    await alert_manager.process_reading(reading, chat_id=12345)
    await alert_manager.process_reading(reading, chat_id=12345)

    assert mock_bot.send_message.call_count == 1
    user_row = await db.fetch_one("SELECT * FROM users WHERE chat_id = :chat_id", {"chat_id": 12345})
    assert user_row is None

    await db.close()
