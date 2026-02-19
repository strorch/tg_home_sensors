"""Unit tests for MCP tool service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.bot.models.sensor_reading import SensorReading
from src.bot.models.user import User
from src.mcp.server import SensorMCPToolService


@pytest.fixture
def mock_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        chat_id=12345,
        humidity_min=40.0,
        humidity_max=60.0,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def tool_service(mock_user: User) -> SensorMCPToolService:
    user_settings = AsyncMock()
    user_settings.get_user.return_value = mock_user
    user_settings.update_user_threshold = AsyncMock()

    sensor_history = AsyncMock()
    sensor_history.get_latest = AsyncMock()
    sensor_history.get_recent = AsyncMock(return_value=[])

    return SensorMCPToolService(user_settings_service=user_settings, sensor_history_service=sensor_history)


@pytest.mark.asyncio
async def test_get_current_reading_no_data(tool_service: SensorMCPToolService) -> None:
    tool_service.sensor_history_service.get_latest.return_value = None

    result = await tool_service.get_current_reading()

    assert result["status"] == "no_data"
    assert result["reading"] is None
    assert result["is_stale"] is True
    assert result["thresholds"] == {"humidity_min": 40.0, "humidity_max": 60.0}
    tool_service.user_settings_service.get_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_reading_stale(tool_service: SensorMCPToolService) -> None:
    old_reading = SensorReading(
        humidity=50.0,
        dht_temperature=23.4,
        lm35_temperature=24.9,
        thermistor_temperature=22.7,
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=30),
    )
    tool_service.sensor_history_service.get_latest.return_value = old_reading

    result = await tool_service.get_current_reading()

    assert result["status"] == "stale"
    assert result["is_stale"] is True
    assert result["age_seconds"] >= 30
    assert result["thresholds"] == {"humidity_min": 40.0, "humidity_max": 60.0}
    tool_service.user_settings_service.get_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_recent_readings_summary(tool_service: SensorMCPToolService) -> None:
    readings = [
        SensorReading(
            humidity=55.0,
            dht_temperature=23.0,
            lm35_temperature=24.0,
            thermistor_temperature=22.0,
            timestamp=datetime.now(timezone.utc),
        ),
        SensorReading(
            humidity=65.0,
            dht_temperature=24.0,
            lm35_temperature=25.0,
            thermistor_temperature=23.0,
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    tool_service.sensor_history_service.get_recent.return_value = readings

    result = await tool_service.get_recent_readings(minutes=60, limit=100)

    assert result["summary"]["count"] == 2
    assert result["summary"]["avg_humidity"] == 60.0
    assert result["summary"]["min_humidity"] == 55.0
    assert result["summary"]["max_humidity"] == 65.0
    assert result["thresholds"] == {"humidity_min": 40.0, "humidity_max": 60.0}
    tool_service.user_settings_service.get_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_humidity_min_updates_threshold(tool_service: SensorMCPToolService, mock_user: User) -> None:
    updated_user = mock_user.model_copy(update={"humidity_min": 35.0})
    tool_service.user_settings_service.update_user_threshold.return_value = updated_user

    result = await tool_service.set_humidity_min(chat_id=12345, value=35.0)

    assert result["status"] == "ok"
    assert result["humidity_min"] == 35.0
    tool_service.user_settings_service.update_user_threshold.assert_awaited_once_with(
        chat_id=12345,
        humidity_min=35.0,
        humidity_max=60.0,
    )


@pytest.mark.asyncio
async def test_set_humidity_max_validates_range(tool_service: SensorMCPToolService) -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        await tool_service.set_humidity_max(chat_id=12345, value=120.0)


@pytest.mark.asyncio
async def test_get_recent_readings_validates_window(tool_service: SensorMCPToolService) -> None:
    with pytest.raises(ValueError, match="minutes"):
        await tool_service.get_recent_readings(minutes=0, limit=10)
