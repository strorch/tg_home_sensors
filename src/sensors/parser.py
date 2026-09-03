"""Parser for supported Arduino sensor messages."""

import json
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.sensors.models import SensorReading, SensorStatus, SerialMessage

SCD41_TEXT_PATTERN = re.compile(
    r"^CO2:\s*(?P<co2>\d+)\s*ppm\s*\|\s*"
    r"Temperature:\s*(?P<temperature>[+-]?\d+(?:\.\d+)?)\s*°?C\s*\|\s*"
    r"Humidity:\s*(?P<humidity>\d+(?:\.\d+)?)\s*%$"
)
SCD41_TEXT_STATUSES = {"SCD41 started", "Waiting for measurement..."}


def _parse_payload(payload: dict[str, Any]) -> SerialMessage | None:
    message: SerialMessage | None = None
    try:
        if "status" in payload:
            message = SensorStatus.model_validate(payload)
        else:
            message = SensorReading.model_validate({**payload, "observed_at": datetime.now(UTC)})
    except ValidationError:
        message = None
    return message


def _parse_scd41_text(data: str) -> SerialMessage | None:
    message: SerialMessage | None = None
    match = SCD41_TEXT_PATTERN.fullmatch(data)
    if match is not None:
        message = _parse_payload(
            {
                "dht": {"temperature_celsius": None, "humidity_percent": None},
                "scd41": {
                    "co2_ppm": match.group("co2"),
                    "temperature_celsius": match.group("temperature"),
                    "humidity_percent": match.group("humidity"),
                },
                "observed_at": datetime.now(UTC),
            }
        )
    elif data in SCD41_TEXT_STATUSES:
        message = SensorStatus(status=data)
    return message


def parse_serial_data(data: str) -> SerialMessage | None:
    """Parse one grouped JSON or SCD41 monitor line emitted by Arduino."""
    payload = None
    try:
        decoded = json.loads(data)
        payload = decoded if isinstance(decoded, dict) else None
    except json.JSONDecodeError:
        payload = None
    message = _parse_payload(payload) if payload is not None else _parse_scd41_text(data)
    return message
