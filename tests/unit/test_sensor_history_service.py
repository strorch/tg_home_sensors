"""Unit tests for sensor history service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.models.sensor_reading import SensorReading
from src.bot.services.sensor_history import SensorHistoryService


@pytest.fixture
def history_service() -> SensorHistoryService:
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.fetch_one = AsyncMock()
    mock_db.fetch_all = AsyncMock()
    return SensorHistoryService(mock_db)


@pytest.mark.asyncio
async def test_insert_reading_persists_row(history_service: SensorHistoryService) -> None:
    reading = SensorReading(
        humidity=55.5,
        dht_temperature=22.1,
        lm35_temperature=22.4,
        thermistor_temperature=21.9,
        timestamp=datetime.now(timezone.utc),
    )

    await history_service.insert_reading(reading)

    history_service.db.execute.assert_called_once()
    args, _ = history_service.db.execute.call_args
    assert args[1]["humidity"] == 55.5


@pytest.mark.asyncio
async def test_get_latest_returns_none_when_empty(history_service: SensorHistoryService) -> None:
    history_service.db.fetch_one.return_value = None

    result = await history_service.get_latest()

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_returns_sensor_reading(history_service: SensorHistoryService) -> None:
    recorded_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    history_service.db.fetch_one.return_value = {
        "recorded_at": recorded_at,
        "humidity": 56.0,
        "dht_temperature": 23.4,
        "lm35_temperature": 24.9,
        "thermistor_temperature": 22.7,
    }

    result = await history_service.get_latest()

    assert result is not None
    assert result.humidity == 56.0
    assert result.timestamp.tzinfo is not None


@pytest.mark.asyncio
async def test_get_recent_validates_minutes_and_limit(history_service: SensorHistoryService) -> None:
    with pytest.raises(ValueError, match="minutes"):
        await history_service.get_recent(minutes=0, limit=10)

    with pytest.raises(ValueError, match="limit"):
        await history_service.get_recent(minutes=10, limit=0)


@pytest.mark.asyncio
async def test_get_recent_returns_parsed_readings(history_service: SensorHistoryService) -> None:
    now = datetime.now(timezone.utc)
    history_service.db.fetch_all.return_value = [
        {
            "recorded_at": (now - timedelta(minutes=1)).isoformat(),
            "humidity": 57.0,
            "dht_temperature": 23.5,
            "lm35_temperature": 24.8,
            "thermistor_temperature": 22.6,
        },
        {
            "recorded_at": (now - timedelta(minutes=2)).isoformat(),
            "humidity": 56.0,
            "dht_temperature": 23.4,
            "lm35_temperature": 24.9,
            "thermistor_temperature": 22.7,
        },
    ]

    result = await history_service.get_recent(minutes=60, limit=10)

    assert len(result) == 2
    assert result[0].humidity == 57.0


@pytest.mark.asyncio
async def test_purge_older_than_returns_deleted_count(history_service: SensorHistoryService) -> None:
    history_service.db.fetch_one.return_value = {"count": 42}

    deleted = await history_service.purge_older_than(days=7)

    assert deleted == 42


@pytest.mark.asyncio
async def test_purge_older_than_validates_days(history_service: SensorHistoryService) -> None:
    with pytest.raises(ValueError, match="days"):
        await history_service.purge_older_than(days=0)
