"""Unit tests for data parser service."""

from datetime import datetime

from src.bot.services.data_parser import parse_sensor_data


def test_parse_valid_sensor_data():
    """Test parsing valid Arduino sensor data."""
    data = "Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C"

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.humidity == 56.0
    assert reading.dht_temperature == 23.4
    assert reading.lm35_temperature == 24.93
    assert reading.thermistor_temperature == 22.73
    assert isinstance(reading.timestamp, datetime)


def test_parse_with_extra_whitespace():
    """Test parsing handles extra whitespace."""
    data = "Humidity:  56.00%   DHT Temp:  23.40C   LM35:  24.93C   Therm:  22.73C"

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.humidity == 56.0


def test_parse_malformed_data_missing_humidity():
    """Test parsing returns None for malformed data."""
    data = "DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C"

    reading = parse_sensor_data(data)

    assert reading is None


def test_parse_malformed_data_invalid_format():
    """Test parsing returns None for completely invalid format."""
    data = "Random text that doesn't match pattern"

    reading = parse_sensor_data(data)

    assert reading is None


def test_parse_out_of_range_humidity():
    """Test parsing validates humidity range."""
    data = "Humidity: 150.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C"

    # Should return None or raise error for invalid humidity
    reading = parse_sensor_data(data)

    assert reading is None


def test_parse_negative_temperature():
    """Test parsing handles negative temperatures."""
    data = "Humidity: 45.00%  DHT Temp: -5.20C  LM35: -3.10C  Therm: -4.50C"

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.dht_temperature == -5.2
    assert reading.lm35_temperature == -3.1
    assert reading.thermistor_temperature == -4.5


def test_parse_decimal_precision():
    """Test parsing rounds values to 2 decimal places."""
    data = "Humidity: 56.12345%  DHT Temp: 23.45678C  LM35: 24.99999C  Therm: 22.73123C"

    reading = parse_sensor_data(data)

    assert reading is not None
    assert reading.humidity == 56.12  # Rounded from 56.12345
    assert reading.dht_temperature == 23.46  # Rounded from 23.45678
