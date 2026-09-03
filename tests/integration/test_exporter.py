"""Exporter data-flow tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry

from src.sensors.exporter import SensorExporter
from src.sensors.metrics import SensorMetrics
from src.sensors.models import SensorReading, SensorStatus


def test_complete_reading_updates_metrics_and_mqtt(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
    sensor_reading: SensorReading,
) -> None:
    publisher = MagicMock()
    exporter = SensorExporter(MagicMock(), sensor_metrics, publisher)

    exporter._process_message(sensor_reading)

    assert registry.get_sample_value("home_sensor_co2_ppm", {"sensor": "scd41"}) == 812
    publisher.publish.assert_called_once_with(sensor_reading)


def test_status_message_does_not_publish(sensor_metrics: SensorMetrics) -> None:
    publisher = MagicMock()
    exporter = SensorExporter(MagicMock(), sensor_metrics, publisher)

    exporter._process_message(SensorStatus(status="started"))

    publisher.publish.assert_not_called()


@pytest.mark.asyncio
async def test_run_stops_dependencies(sensor_metrics: SensorMetrics) -> None:
    reader = MagicMock()
    reader.disconnect = AsyncMock()
    publisher = MagicMock()
    stop_event = asyncio.Event()
    stop_event.set()

    await SensorExporter(reader, sensor_metrics, publisher).run(stop_event)

    reader.disconnect.assert_awaited_once_with()
    publisher.stop.assert_called_once_with()


@pytest.mark.asyncio
async def test_run_once_processes_connected_reader(
    sensor_metrics: SensorMetrics,
    sensor_reading: SensorReading,
) -> None:
    reader = MagicMock()
    reader.is_connected.return_value = True
    reader.read_message = AsyncMock(return_value=sensor_reading)
    publisher = MagicMock()

    await SensorExporter(reader, sensor_metrics, publisher)._run_once()

    publisher.publish.assert_called_once_with(sensor_reading)


@pytest.mark.asyncio
async def test_run_once_retries_disconnected_reader(sensor_metrics: SensorMetrics) -> None:
    reader = MagicMock()
    reader.is_connected.return_value = False
    reader.connect = AsyncMock(return_value=False)
    reader.state.backoff_seconds = 2
    with patch("src.sensors.exporter.asyncio.sleep", new=AsyncMock()) as sleep:
        await SensorExporter(reader, sensor_metrics, MagicMock())._run_once()

    sleep.assert_awaited_once_with(2)
