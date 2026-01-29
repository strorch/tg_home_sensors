"""Unit tests for alert manager service."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.bot.services.alert_manager import AlertManager
from src.bot.models.sensor_reading import SensorReading
from src.bot.models.alert_state import AlertState


@pytest.fixture
def alert_manager():
    """Create alert manager instance."""
    mock_db = MagicMock()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    return AlertManager(database=mock_db, bot=mock_bot)


@pytest.mark.asyncio
async def test_detect_high_humidity_threshold_breach(alert_manager, mock_user):
    """Test alert manager detects humidity above max threshold."""
    reading = SensorReading(
        humidity=75.0,  # Above max of 60%
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    alert_state = AlertState(chat_id=12345, current_state="normal")

    should_alert = await alert_manager.check_threshold(reading, mock_user, alert_state)

    assert should_alert is True


@pytest.mark.asyncio
async def test_detect_low_humidity_threshold_breach(alert_manager, mock_user):
    """Test alert manager detects humidity below min threshold."""
    reading = SensorReading(
        humidity=28.0,  # Below min of 40%
        dht_temperature=18.2,
        lm35_temperature=19.0,
        thermistor_temperature=17.5,
        timestamp=datetime.now(timezone.utc),
    )

    alert_state = AlertState(chat_id=12345, current_state="normal")

    should_alert = await alert_manager.check_threshold(reading, mock_user, alert_state)

    assert should_alert is True


@pytest.mark.asyncio
async def test_normal_humidity_no_alert(alert_manager, mock_user):
    """Test no alert when humidity is within range."""
    reading = SensorReading(
        humidity=50.0,  # Within 40-60% range
        dht_temperature=23.4,
        lm35_temperature=24.1,
        thermistor_temperature=22.9,
        timestamp=datetime.now(timezone.utc),
    )

    alert_state = AlertState(chat_id=12345, current_state="normal")

    should_alert = await alert_manager.check_threshold(reading, mock_user, alert_state)

    assert should_alert is False


@pytest.mark.asyncio
async def test_cooldown_prevents_duplicate_alerts(alert_manager, mock_user):
    """Test cooldown prevents sending alerts too frequently."""
    reading = SensorReading(
        humidity=75.0,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    # Alert was sent 1 minute ago (within cooldown)
    recent_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    alert_state = AlertState(
        chat_id=12345,
        current_state="high_humidity",
        last_alert_time=recent_time,
        last_alert_type="high",
    )

    should_alert = await alert_manager.check_threshold(reading, mock_user, alert_state)

    assert should_alert is False


@pytest.mark.asyncio
async def test_cooldown_expired_allows_alert(alert_manager, mock_user):
    """Test alert sent after cooldown period expires."""
    reading = SensorReading(
        humidity=75.0,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    # Alert was sent 6 minutes ago (cooldown expired)
    old_time = datetime.now(timezone.utc) - timedelta(seconds=360)
    alert_state = AlertState(
        chat_id=12345,
        current_state="high_humidity",
        last_alert_time=old_time,
        last_alert_type="high",
    )

    should_alert = await alert_manager.check_threshold(reading, mock_user, alert_state)

    assert should_alert is True


@pytest.mark.asyncio
async def test_state_transition_normal_to_high(alert_manager, mock_user):
    """Test state transition from normal to high humidity."""
    reading = SensorReading(
        humidity=75.0,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    new_state = alert_manager.determine_state(reading, mock_user)

    assert new_state == "high_humidity"


@pytest.mark.asyncio
async def test_state_transition_normal_to_low(alert_manager, mock_user):
    """Test state transition from normal to low humidity."""
    reading = SensorReading(
        humidity=28.0,
        dht_temperature=18.2,
        lm35_temperature=19.0,
        thermistor_temperature=17.5,
        timestamp=datetime.now(timezone.utc),
    )

    new_state = alert_manager.determine_state(reading, mock_user)

    assert new_state == "low_humidity"


@pytest.mark.asyncio
async def test_state_transition_high_to_normal(alert_manager, mock_user):
    """Test recovery from high humidity to normal."""
    reading = SensorReading(
        humidity=52.0,  # Back to normal range
        dht_temperature=23.4,
        lm35_temperature=24.1,
        thermistor_temperature=22.9,
        timestamp=datetime.now(timezone.utc),
    )

    new_state = alert_manager.determine_state(reading, mock_user)

    assert new_state == "normal"


@pytest.mark.asyncio
async def test_format_high_humidity_alert(alert_manager, mock_user):
    """Test high humidity alert message formatting."""
    reading = SensorReading(
        humidity=72.5,
        dht_temperature=28.4,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc),
    )

    message = alert_manager.format_high_humidity_alert(reading, mock_user)

    assert "HIGH HUMIDITY ALERT" in message
    assert "72.5%" in message or "72.50%" in message
    assert "60.0%" in message  # Max threshold
    assert "28.4" in message or "28.40" in message


@pytest.mark.asyncio
async def test_format_low_humidity_alert(alert_manager, mock_user):
    """Test low humidity alert message formatting."""
    reading = SensorReading(
        humidity=28.0,
        dht_temperature=18.2,
        lm35_temperature=19.0,
        thermistor_temperature=17.5,
        timestamp=datetime.now(timezone.utc),
    )

    message = alert_manager.format_low_humidity_alert(reading, mock_user)

    assert "LOW HUMIDITY ALERT" in message
    assert "28.0%" in message or "28.00%" in message
    assert "40.0%" in message  # Min threshold
    assert "humidifier" in message.lower()


@pytest.mark.asyncio
async def test_format_recovery_notification(alert_manager, mock_user):
    """Test recovery notification message formatting."""
    reading = SensorReading(
        humidity=52.0,
        dht_temperature=23.4,
        lm35_temperature=24.1,
        thermistor_temperature=22.9,
        timestamp=datetime.now(timezone.utc),
    )

    message = alert_manager.format_recovery_notification(reading, mock_user)

    assert "NORMAL" in message or "BACK TO NORMAL" in message
    assert "52.0%" in message or "52.00%" in message
    assert "40.0%" in message and "60.0%" in message  # Range
