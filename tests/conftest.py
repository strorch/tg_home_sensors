"""Shared test configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.effective_chat = MagicMock()
    update.effective_chat.id = 12345
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_telegram_context():
    """Create a mock Telegram Context object."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.args = []
    return context


@pytest.fixture
def mock_sensor_reading():
    """Create a mock SensorReading."""
    from src.bot.models.sensor_reading import SensorReading

    return SensorReading(
        humidity=56.0,
        dht_temperature=23.4,
        lm35_temperature=24.9,
        thermistor_temperature=22.7,
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user():
    """Create a mock User."""
    from src.bot.models.user import User

    now = datetime.now(timezone.utc)
    return User(chat_id=12345, humidity_min=40.0, humidity_max=60.0, created_at=now, updated_at=now)


@pytest.fixture
def mock_alert_state():
    """Create a mock AlertState."""
    from src.bot.models.alert_state import AlertState

    return AlertState(
        chat_id=12345, current_state="normal", last_alert_time=None, last_alert_type=None
    )
