"""Serial reader tests."""

from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry

from src.sensors.metrics import SensorMetrics
from src.sensors.models import SensorReading, SensorStatus
from src.sensors.serial_reader import SerialReader


def make_reader(metrics: SensorMetrics) -> SerialReader:
    return SerialReader("/dev/ttyACM0", 115200, 2.0, metrics)


@pytest.mark.asyncio
async def test_connect_uses_configured_serial_settings(sensor_metrics: SensorMetrics) -> None:
    reader = make_reader(sensor_metrics)
    with patch("serial.Serial") as serial_class:
        serial_class.return_value = MagicMock(is_open=True)

        connected = await reader.connect()

    assert connected is True
    serial_class.assert_called_once_with("/dev/ttyACM0", 115200, timeout=2.0)


@pytest.mark.asyncio
async def test_read_complete_grouped_message(sensor_metrics: SensorMetrics) -> None:
    reader = make_reader(sensor_metrics)
    reader._serial = MagicMock(is_open=True)
    reader._serial.readline.return_value = (
        b'{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1},'
        b'"scd41":{"co2_ppm":812,"temperature_celsius":24.1,'
        b'"humidity_percent":46.8}}\n'
    )

    message = await reader.read_message()

    assert isinstance(message, SensorReading)
    assert message.scd41.co2_ppm == 812


@pytest.mark.asyncio
async def test_read_status_does_not_count_parse_error(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
) -> None:
    reader = make_reader(sensor_metrics)
    reader._serial = MagicMock(is_open=True)
    reader._serial.readline.return_value = b'{"status":"started"}\n'

    message = await reader.read_message()

    assert isinstance(message, SensorStatus)
    assert registry.get_sample_value("home_sensor_parse_errors_total") == 0


@pytest.mark.asyncio
async def test_invalid_line_counts_parse_error(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
) -> None:
    reader = make_reader(sensor_metrics)
    reader._serial = MagicMock(is_open=True)
    reader._serial.readline.return_value = b"invalid\n"

    message = await reader.read_message()

    assert message is None
    assert registry.get_sample_value("home_sensor_parse_errors_total") == 1


@pytest.mark.asyncio
async def test_connect_failure_updates_backoff(sensor_metrics: SensorMetrics) -> None:
    reader = make_reader(sensor_metrics)
    with patch("serial.Serial", side_effect=OSError):
        connected = await reader.connect()

    assert connected is False
    assert reader.state.reconnect_attempts == 1
    assert reader.state.backoff_seconds == 2


@pytest.mark.asyncio
async def test_read_failure_disconnects(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
) -> None:
    reader = make_reader(sensor_metrics)
    reader._serial = MagicMock(is_open=True)
    reader._serial.readline.side_effect = OSError

    message = await reader.read_message()

    assert message is None
    assert reader.is_connected() is False
    assert registry.get_sample_value("home_sensor_read_errors_total") == 1
