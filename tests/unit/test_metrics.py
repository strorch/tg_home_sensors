"""Prometheus metric mapping tests."""

from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry

from src.sensors.metrics import MetricsHttpServer, SensorMetrics
from src.sensors.models import DhtReading, Scd41Reading, SensorReading


def test_update_reading_exports_all_sensor_values(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
    sensor_reading: SensorReading,
) -> None:
    sensor_metrics.update_reading(sensor_reading)

    assert registry.get_sample_value(
        "home_sensor_temperature_celsius", {"sensor": "dht"}
    ) == pytest.approx(23.4)
    assert registry.get_sample_value(
        "home_sensor_temperature_celsius", {"sensor": "scd41"}
    ) == pytest.approx(24.1)
    assert registry.get_sample_value(
        "home_sensor_humidity_percent", {"sensor": "dht"}
    ) == pytest.approx(48.1)
    assert registry.get_sample_value(
        "home_sensor_humidity_percent", {"sensor": "scd41"}
    ) == pytest.approx(46.8)
    assert registry.get_sample_value("home_sensor_co2_ppm", {"sensor": "scd41"}) == pytest.approx(
        812
    )


def test_health_metrics_start_disconnected(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
) -> None:
    assert registry.get_sample_value("home_sensor_serial_connected") == 0
    assert registry.get_sample_value("home_sensor_mqtt_connected") == 0


def test_update_reading_removes_unavailable_values(
    registry: CollectorRegistry,
    sensor_metrics: SensorMetrics,
    sensor_reading: SensorReading,
) -> None:
    sensor_metrics.update_reading(sensor_reading)
    partial = sensor_reading.model_copy(
        update={
            "dht": DhtReading(temperature_celsius=None, humidity_percent=52.0),
            "scd41": Scd41Reading(
                co2_ppm=900,
                temperature_celsius=24.0,
                humidity_percent=None,
            ),
        }
    )

    sensor_metrics.update_reading(partial)

    assert registry.get_sample_value("home_sensor_temperature_celsius", {"sensor": "dht"}) is None
    assert registry.get_sample_value("home_sensor_humidity_percent", {"sensor": "scd41"}) is None
    assert registry.get_sample_value("home_sensor_humidity_percent", {"sensor": "dht"}) == 52
    assert registry.get_sample_value("home_sensor_co2_ppm", {"sensor": "scd41"}) == 900


def test_metrics_http_server_lifecycle() -> None:
    http_server = MagicMock()
    thread = MagicMock()
    metrics_server = MetricsHttpServer("127.0.0.1", 8100)
    with patch(
        "src.sensors.metrics.start_http_server", return_value=(http_server, thread)
    ) as start:
        metrics_server.start()
        metrics_server.stop()

    start.assert_called_once_with(8100, addr="127.0.0.1")
    http_server.shutdown.assert_called_once_with()
    http_server.server_close.assert_called_once_with()
    thread.join.assert_called_once_with()
