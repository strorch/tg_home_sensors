"""MQTT payload and publication tests."""

import json
from unittest.mock import MagicMock, patch

import paho.mqtt.client as mqtt

from src.config import Config
from src.sensors.metrics import SensorMetrics
from src.sensors.models import DhtReading, SensorReading
from src.sensors.mqtt import MqttPublisher, serialize_reading


def test_serialize_reading_keeps_sensor_groups(sensor_reading: SensorReading) -> None:
    payload = json.loads(serialize_reading(sensor_reading))

    assert payload["dht"] == {
        "temperature_celsius": 23.4,
        "humidity_percent": 48.1,
    }
    assert payload["scd41"] == {
        "co2_ppm": 812,
        "temperature_celsius": 24.1,
        "humidity_percent": 46.8,
    }
    assert payload["observed_at"] == "2026-09-02T12:00:00Z"


def test_serialize_reading_preserves_unavailable_values(sensor_reading: SensorReading) -> None:
    partial = sensor_reading.model_copy(
        update={"dht": DhtReading(temperature_celsius=None, humidity_percent=48.1)}
    )

    payload = json.loads(serialize_reading(partial))

    assert payload["dht"]["temperature_celsius"] is None
    assert payload["dht"]["humidity_percent"] == 48.1


def test_publish_uses_retained_qos_one(
    sensor_metrics: SensorMetrics,
    sensor_reading: SensorReading,
) -> None:
    config = Config(serial_port="test", mqtt_enabled=True, mqtt_host="broker")
    publisher = MqttPublisher(config, sensor_metrics)
    client = MagicMock()
    client.publish.return_value.rc = mqtt.MQTT_ERR_SUCCESS
    publisher.client = client

    publisher.publish(sensor_reading)

    client.publish.assert_called_once_with(
        "home/sensors/environment",
        serialize_reading(sensor_reading),
        qos=1,
        retain=True,
    )


def test_start_configures_and_connects_client(sensor_metrics: SensorMetrics) -> None:
    config = Config(
        serial_port="test",
        mqtt_enabled=True,
        mqtt_host="broker",
        mqtt_username="user",
        mqtt_password="pass",
        mqtt_tls=True,
    )
    publisher = MqttPublisher(config, sensor_metrics)
    with patch("src.sensors.mqtt.mqtt.Client") as client_class:
        publisher.start()

    client = client_class.return_value
    client.username_pw_set.assert_called_once_with("user", "pass")
    client.tls_set.assert_called_once_with()
    client.connect_async.assert_called_once_with("broker", 1883)
    client.loop_start.assert_called_once_with()
    assert publisher.client is client


def test_start_failure_is_counted(
    sensor_metrics: SensorMetrics,
) -> None:
    config = Config(serial_port="test", mqtt_enabled=True, mqtt_host="broker")
    publisher = MqttPublisher(config, sensor_metrics)
    with patch.object(publisher, "_start_client", side_effect=OSError):
        publisher.start()

    value = sensor_metrics.mqtt_publish_errors._value.get()
    assert value == 1


def test_publish_failure_is_counted(
    sensor_metrics: SensorMetrics,
    sensor_reading: SensorReading,
) -> None:
    config = Config(serial_port="test", mqtt_enabled=True, mqtt_host="broker")
    publisher = MqttPublisher(config, sensor_metrics)
    publisher.client = MagicMock()
    publisher.client.publish.side_effect = RuntimeError

    publisher.publish(sensor_reading)

    assert sensor_metrics.mqtt_publish_errors._value.get() == 1


def test_callbacks_and_stop_update_connection(sensor_metrics: SensorMetrics) -> None:
    publisher = MqttPublisher(Config(serial_port="test"), sensor_metrics)
    client = MagicMock()
    publisher.client = client

    publisher._on_connect(client)
    assert sensor_metrics.mqtt_connected._value.get() == 1
    publisher._on_disconnect(client)
    publisher.stop()

    assert sensor_metrics.mqtt_connected._value.get() == 0
    client.disconnect.assert_called_once_with()
    client.loop_stop.assert_called_once_with()
