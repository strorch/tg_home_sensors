"""Data parser service for Arduino sensor data."""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from src.bot.models.sensor_reading import SensorReading


SENSOR_FIELD_ALIASES = {
    "humidity": ("humidity",),
    "dht_temperature": ("dht_temperature", "dht_temp"),
    "lm35_temperature": ("lm35_temperature", "lm35_temp"),
    "thermistor_temperature": ("thermistor_temperature", "therm_temp"),
}


def _extract_float(payload: dict[str, Any], field: str) -> Optional[float]:
    """Extract a numeric value for a contract field from payload aliases."""
    for key in SENSOR_FIELD_ALIASES[field]:
        if key in payload:
            try:
                return float(payload[key])
            except (TypeError, ValueError):
                return None
    return None


def _parse_timestamp(payload: dict[str, Any]) -> Optional[datetime]:
    """Parse optional timestamp from payload; default to current UTC time."""
    timestamp_raw = payload.get("timestamp")
    if timestamp_raw is None:
        return datetime.now(timezone.utc)

    if isinstance(timestamp_raw, str):
        try:
            normalized = timestamp_raw.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    return None


def parse_sensor_data(data: str) -> Optional[SensorReading]:
    """Parse Arduino sensor JSON string into SensorReading model.

    Args:
        data: Raw sensor data string from Arduino.

    Returns:
        SensorReading object if parsing succeeds, None otherwise.

    Example:
        >>> data = '{"humidity":56.00,"dht_temperature":23.40,"lm35_temperature":24.93,"thermistor_temperature":22.73}'
        >>> reading = parse_sensor_data(data)
        >>> reading.humidity
        56.0
    """
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    humidity = _extract_float(payload, "humidity")
    dht_temperature = _extract_float(payload, "dht_temperature")
    lm35_temperature = _extract_float(payload, "lm35_temperature")
    thermistor_temperature = _extract_float(payload, "thermistor_temperature")
    timestamp = _parse_timestamp(payload)

    if (
        humidity is None
        or dht_temperature is None
        or lm35_temperature is None
        or thermistor_temperature is None
        or timestamp is None
    ):
        return None

    try:
        reading = SensorReading(
            humidity=humidity,
            dht_temperature=dht_temperature,
            lm35_temperature=lm35_temperature,
            thermistor_temperature=thermistor_temperature,
            timestamp=timestamp,
        )
        return reading
    except (ValueError, Exception):
        # Invalid values or validation error
        return None
