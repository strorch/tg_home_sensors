"""Parser for grouped Arduino JSON messages."""

import json
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from src.sensors.models import SensorReading, SensorStatus, SerialMessage


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


def parse_serial_data(data: str) -> SerialMessage | None:
    """Parse one compact JSON line emitted by the Arduino."""
    payload = None
    try:
        decoded = json.loads(data)
        payload = decoded if isinstance(decoded, dict) else None
    except json.JSONDecodeError:
        payload = None
    return _parse_payload(payload) if payload is not None else None
