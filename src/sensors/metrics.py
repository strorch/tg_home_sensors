"""Prometheus metrics for sensor readings and exporter health."""

from collections.abc import Sequence
from threading import Thread
from typing import Protocol

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, start_http_server

from src.sensors.models import SensorReading


class HttpServer(Protocol):
    """Subset of the HTTP server API used during shutdown."""

    def shutdown(self) -> None: ...

    def server_close(self) -> None: ...


def _gauge(
    name: str,
    description: str,
    registry: CollectorRegistry,
    labels: Sequence[str] = (),
) -> Gauge:
    return Gauge(name, description, labels, registry=registry)


def _counter(name: str, description: str, registry: CollectorRegistry) -> Counter:
    return Counter(name, description, registry=registry)


def _update_labeled(gauge: Gauge, sensor: str, value: float | int | None) -> None:
    if value is None:
        try:
            gauge.remove(sensor)
        except KeyError:
            pass
    else:
        gauge.labels(sensor=sensor).set(value)


class SensorMetrics:
    """Own and update the exporter's Prometheus collectors."""

    def __init__(self, registry: CollectorRegistry = REGISTRY) -> None:
        sensor_label = ["sensor"]
        self.temperature = _gauge(
            "home_sensor_temperature_celsius", "Temperature", registry, sensor_label
        )
        self.humidity = _gauge(
            "home_sensor_humidity_percent", "Relative humidity", registry, sensor_label
        )
        self.co2 = _gauge("home_sensor_co2_ppm", "CO2 concentration", registry, sensor_label)
        self.last_reading = _gauge(
            "home_sensor_last_reading_timestamp_seconds", "Last accepted reading", registry
        )
        self.serial_connected = _gauge(
            "home_sensor_serial_connected", "Arduino serial connection", registry
        )
        self.parse_errors = _counter(
            "home_sensor_parse_errors_total", "Invalid serial messages", registry
        )
        self.read_errors = _counter(
            "home_sensor_read_errors_total", "Serial read failures", registry
        )
        self.mqtt_connected = _gauge("home_sensor_mqtt_connected", "MQTT connection", registry)
        self.mqtt_publish_errors = _counter(
            "home_sensor_mqtt_publish_errors_total", "MQTT publish failures", registry
        )

    def update_reading(self, reading: SensorReading) -> None:
        _update_labeled(self.temperature, "dht", reading.dht.temperature_celsius)
        _update_labeled(self.temperature, "scd41", reading.scd41.temperature_celsius)
        _update_labeled(self.humidity, "dht", reading.dht.humidity_percent)
        _update_labeled(self.humidity, "scd41", reading.scd41.humidity_percent)
        _update_labeled(self.co2, "scd41", reading.scd41.co2_ppm)
        self.last_reading.set(reading.observed_at.timestamp())


class MetricsHttpServer:
    """Lifecycle wrapper around the Prometheus HTTP server."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._server: HttpServer | None = None
        self._thread: Thread | None = None

    def start(self) -> None:
        server, thread = start_http_server(self.port, addr=self.host)
        self._server = server
        self._thread = thread

    def stop(self) -> None:
        if self._server is not None and self._thread is not None:
            self._server.shutdown()
            self._server.server_close()
            self._thread.join()
