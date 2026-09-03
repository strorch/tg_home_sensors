"""Grouped sensor JSON parser tests."""

import pytest

from src.sensors.models import SensorReading, SensorStatus
from src.sensors.parser import parse_serial_data

VALID_READING = (
    '{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1},'
    '"scd41":{"co2_ppm":812,"temperature_celsius":24.1,'
    '"humidity_percent":46.8}}'
)


def test_parse_complete_grouped_reading() -> None:
    message = parse_serial_data(VALID_READING)

    assert isinstance(message, SensorReading)
    assert message.dht.temperature_celsius == 23.4
    assert message.dht.humidity_percent == 48.1
    assert message.scd41.co2_ppm == 812
    assert message.scd41.temperature_celsius == 24.1
    assert message.scd41.humidity_percent == 46.8


def test_parse_status_message() -> None:
    message = parse_serial_data('{"status":"waiting_for_measurement"}')

    assert isinstance(message, SensorStatus)
    assert message.status == "waiting_for_measurement"


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1}}',
        '{"status":""}',
        (
            '{"dht":{"temperature_celsius":23.4,"humidity_percent":101},'
            '"scd41":{"co2_ppm":812,"temperature_celsius":24.1,'
            '"humidity_percent":46.8}}'
        ),
    ],
)
def test_reject_invalid_message(payload: str) -> None:
    assert parse_serial_data(payload) is None
