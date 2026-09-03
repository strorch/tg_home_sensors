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


@pytest.mark.parametrize("status", ["SCD41 started", "Waiting for measurement..."])
def test_parse_scd41_text_status(status: str) -> None:
    message = parse_serial_data(status)

    assert isinstance(message, SensorStatus)
    assert message.status == status


def test_parse_scd41_text_reading() -> None:
    message = parse_serial_data("CO2: 1522 ppm | Temperature: 31.0 C | Humidity: 35.4 %")

    assert isinstance(message, SensorReading)
    assert message.dht.temperature_celsius is None
    assert message.dht.humidity_percent is None
    assert message.scd41.co2_ppm == 1522
    assert message.scd41.temperature_celsius == 31.0
    assert message.scd41.humidity_percent == 35.4


def test_parse_partial_reading_with_null_values() -> None:
    message = parse_serial_data(
        '{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1},'
        '"scd41":{"co2_ppm":null,"temperature_celsius":null,'
        '"humidity_percent":null}}'
    )

    assert isinstance(message, SensorReading)
    assert message.dht.temperature_celsius == 23.4
    assert message.scd41.co2_ppm is None


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "CO2: broken",
        "CO2: 1522 ppm | Temperature: 31.0 C | Humidity: 135.4 %",
        "[]",
        '{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1}}',
        '{"status":""}',
        (
            '{"dht":{"temperature_celsius":null,"humidity_percent":null},'
            '"scd41":{"co2_ppm":null,"temperature_celsius":null,'
            '"humidity_percent":null}}'
        ),
        (
            '{"dht":{"temperature_celsius":23.4,"humidity_percent":101},'
            '"scd41":{"co2_ppm":812,"temperature_celsius":24.1,'
            '"humidity_percent":46.8}}'
        ),
    ],
)
def test_reject_invalid_message(payload: str) -> None:
    assert parse_serial_data(payload) is None
