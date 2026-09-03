"""Optional MQTT publication of complete sensor readings."""

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from src.config import Config
from src.sensors.metrics import SensorMetrics
from src.sensors.models import SensorReading

logger = logging.getLogger(__name__)


def serialize_reading(reading: SensorReading) -> str:
    """Serialize the grouped sensor payload for MQTT."""
    payload = reading.model_dump(mode="json")
    return json.dumps(payload, separators=(",", ":"))


class MqttPublisher:
    """Maintain an MQTT connection and publish retained readings."""

    def __init__(self, config: Config, metrics: SensorMetrics) -> None:
        self.config = config
        self.metrics = metrics
        self.client: mqtt.Client | None = None

    def start(self) -> None:
        if self.config.mqtt_enabled:
            try:
                self._start_client()
            except (OSError, RuntimeError, ValueError):
                self.metrics.mqtt_publish_errors.inc()
                logger.exception("MQTT startup failed; Prometheus export remains active")

    def _start_client(self) -> None:
        client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=self.config.mqtt_client_id)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        self._configure_security(client)
        client.connect_async(self.config.mqtt_host or "", self.config.mqtt_port)
        client.loop_start()
        self.client = client

    def _configure_security(self, client: mqtt.Client) -> None:
        if self.config.mqtt_username:
            client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
        if self.config.mqtt_tls:
            client.tls_set()

    def publish(self, reading: SensorReading) -> None:
        if self.client is not None:
            try:
                result = self.client.publish(
                    self.config.mqtt_topic,
                    serialize_reading(reading),
                    qos=1,
                    retain=True,
                )
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    self.metrics.mqtt_publish_errors.inc()
            except (OSError, RuntimeError, ValueError):
                self.metrics.mqtt_publish_errors.inc()
                logger.exception("MQTT publish failed; Prometheus export remains active")

    def stop(self) -> None:
        if self.client is not None:
            self.client.disconnect()
            self.client.loop_stop()
            self.client = None
        self.metrics.mqtt_connected.set(0)

    def _on_connect(self, _client: mqtt.Client, *_args: Any) -> None:
        self.metrics.mqtt_connected.set(1)
        logger.info("Connected to MQTT broker")

    def _on_disconnect(self, _client: mqtt.Client, *_args: Any) -> None:
        self.metrics.mqtt_connected.set(0)
        logger.warning("Disconnected from MQTT broker")
