"""Unit tests for data parser service."""

from datetime import datetime, timezone

from src.bot.services.data_parser import parse_sensor_data


def test_parse_valid_sensor_data():
    """Test parsing valid Arduino JSON sensor data."""
    data = (
        '{"humidity":56.00,"dht_temperature":23.40,'
        '"lm35_temperature":24.93,"thermistor_temperature":22.73}'
    )

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.humidity == 56.0
    assert reading.dht_temperature == 23.4
    assert reading.lm35_temperature == 24.93
    assert reading.thermistor_temperature == 22.73
    assert isinstance(reading.timestamp, datetime)


def test_parse_with_extra_whitespace():
    """Test parsing handles JSON with leading/trailing whitespace."""
    data = (
        '  {"humidity":56.00,"dht_temperature":23.40,'
        '"lm35_temperature":24.93,"thermistor_temperature":22.73}  '
    )

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.humidity == 56.0


def test_parse_malformed_data_missing_humidity():
    """Test parsing returns None when required field is missing."""
    data = '{"dht_temperature":23.40,"lm35_temperature":24.93,"thermistor_temperature":22.73}'

    reading = parse_sensor_data(data)

    assert reading is None


def test_parse_malformed_data_invalid_format():
    """Test parsing returns None for invalid JSON."""
    data = "Random text that doesn't match pattern"

    reading = parse_sensor_data(data)

    assert reading is None


def test_parse_out_of_range_humidity():
    """Test parsing validates humidity range."""
    data = (
        '{"humidity":150.00,"dht_temperature":23.40,'
        '"lm35_temperature":24.93,"thermistor_temperature":22.73}'
    )

    # Should return None or raise error for invalid humidity
    reading = parse_sensor_data(data)

    assert reading is None


def test_parse_negative_temperature():
    """Test parsing handles negative temperatures."""
    data = (
        '{"humidity":45.00,"dht_temperature":-5.20,'
        '"lm35_temperature":-3.10,"thermistor_temperature":-4.50}'
    )

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.dht_temperature == -5.2
    assert reading.lm35_temperature == -3.1
    assert reading.thermistor_temperature == -4.5


def test_parse_decimal_precision():
    """Test parsing rounds values to 2 decimal places."""
    data = (
        '{"humidity":56.12345,"dht_temperature":23.45678,'
        '"lm35_temperature":24.99999,"thermistor_temperature":22.73123}'
    )

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.humidity == 56.12  # Rounded from 56.12345
    assert reading.dht_temperature == 23.46  # Rounded from 23.45678


def test_parse_with_alias_keys_and_timestamp():
    """Test parser supports alias keys and optional ISO timestamp."""
    data = (
        '{"humidity":56.0,"dht_temp":23.4,"lm35_temp":24.93,'
        '"therm_temp":22.73,"timestamp":"2026-02-08T10:30:00Z"}'
    )

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.dht_temperature == 23.4
    assert reading.timestamp == datetime(2026, 2, 8, 10, 30, tzinfo=timezone.utc)
