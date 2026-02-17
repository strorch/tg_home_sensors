"""Sensor reading persistence and query service."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import SupportsFloat, cast

from src.bot.models.sensor_reading import SensorReading
from src.bot.services.database import Database


logger = logging.getLogger(__name__)


class SensorHistoryService:
    """Service for storing and querying sensor reading history."""

    def __init__(self, database: Database) -> None:
        """Initialize service with a database dependency."""
        self.db = database

    async def insert_reading(self, reading: SensorReading) -> None:
        """Persist a sensor reading."""
        await self.db.execute(
            """INSERT INTO sensor_readings (
                   recorded_at, humidity, dht_temperature, lm35_temperature, thermistor_temperature
               )
               VALUES (
                   :recorded_at, :humidity, :dht_temperature, :lm35_temperature, :thermistor_temperature
               )""",
            {
                "recorded_at": reading.timestamp.isoformat(),
                "humidity": reading.humidity,
                "dht_temperature": reading.dht_temperature,
                "lm35_temperature": reading.lm35_temperature,
                "thermistor_temperature": reading.thermistor_temperature,
            },
        )

    async def get_latest(self) -> SensorReading | None:
        """Get the most recent persisted reading."""
        row = await self.db.fetch_one(
            """SELECT recorded_at, humidity, dht_temperature, lm35_temperature, thermistor_temperature
               FROM sensor_readings
               ORDER BY recorded_at DESC
               LIMIT 1"""
        )
        if row is None:
            return None
        return self._row_to_reading(row)

    async def get_recent(self, minutes: int, limit: int) -> list[SensorReading]:
        """Get recent readings ordered from newest to oldest."""
        if minutes <= 0:
            raise ValueError("minutes must be greater than 0")
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        rows = await self.db.fetch_all(
            """SELECT recorded_at, humidity, dht_temperature, lm35_temperature, thermistor_temperature
               FROM sensor_readings
               WHERE recorded_at >= :since
               ORDER BY recorded_at DESC
               LIMIT :limit""",
            {"since": since.isoformat(), "limit": limit},
        )
        return [self._row_to_reading(row) for row in rows]

    async def purge_older_than(self, days: int) -> int:
        """Delete records older than retention and return number deleted."""
        if days <= 0:
            raise ValueError("days must be greater than 0")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        row = await self.db.fetch_one(
            """WITH deleted AS (
                   DELETE FROM sensor_readings
                   WHERE recorded_at < :cutoff
                   RETURNING 1
               )
               SELECT COUNT(*)::int AS count FROM deleted""",
            {"cutoff": cutoff.isoformat()},
        )
        if row is None:
            return 0

        deleted_count = int(row["count"])
        logger.debug("Purged %s sensor readings older than %s days", deleted_count, days)
        return deleted_count

    @staticmethod
    def _row_to_reading(row: dict[str, object]) -> SensorReading:
        timestamp_raw = row["recorded_at"]
        if not isinstance(timestamp_raw, str):
            raise ValueError("recorded_at must be ISO timestamp string")

        timestamp = datetime.fromisoformat(timestamp_raw)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        return SensorReading(
            humidity=SensorHistoryService._to_float(row["humidity"], "humidity"),
            dht_temperature=SensorHistoryService._to_float(
                row["dht_temperature"], "dht_temperature"
            ),
            lm35_temperature=SensorHistoryService._to_float(
                row["lm35_temperature"], "lm35_temperature"
            ),
            thermistor_temperature=SensorHistoryService._to_float(
                row["thermistor_temperature"], "thermistor_temperature"
            ),
            timestamp=timestamp,
        )

    @staticmethod
    def _to_float(value: object, field_name: str) -> float:
        try:
            return float(cast(SupportsFloat | str, value))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
