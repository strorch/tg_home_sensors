"""Application lifecycle tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Config
from src.main import _create_exporter, main
from src.sensors.metrics import SensorMetrics


def test_create_exporter_uses_serial_config(sensor_metrics: SensorMetrics) -> None:
    config = Config(
        serial_port="test-port",
        serial_baud_rate=57600,
        serial_timeout_seconds=1.5,
    )

    exporter = _create_exporter(config, sensor_metrics)

    assert exporter.reader.port == "test-port"
    assert exporter.reader.baud_rate == 57600
    assert exporter.reader.timeout == 1.5


@pytest.mark.asyncio
async def test_main_starts_and_stops_services() -> None:
    config = Config(serial_port="test")
    exporter = MagicMock()
    exporter.run = AsyncMock()
    with (
        patch("src.main.load_config", return_value=config),
        patch("src.main.SensorMetrics"),
        patch("src.main.MetricsHttpServer") as server_class,
        patch("src.main._create_exporter", return_value=exporter),
        patch("src.main._install_signal_handlers"),
    ):
        await main()

    exporter.mqtt_publisher.start.assert_called_once_with()
    exporter.run.assert_awaited_once()
    server_class.return_value.start.assert_called_once_with()
    server_class.return_value.stop.assert_called_once_with()
