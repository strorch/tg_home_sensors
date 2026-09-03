"""Configuration tests."""

import pytest
from pydantic import ValidationError

from src.config import Config


def test_config_defaults_to_arduino_baud_rate() -> None:
    config = Config(serial_port="/dev/ttyACM0")

    assert config.serial_baud_rate == 115200
    assert config.metrics_port == 8000
    assert config.mqtt_enabled is False


def test_config_requires_mqtt_host_when_enabled() -> None:
    with pytest.raises(ValidationError, match="MQTT_HOST"):
        Config(serial_port="/dev/ttyACM0", mqtt_enabled=True)


def test_config_accepts_mqtt_output() -> None:
    config = Config(
        serial_port="/dev/ttyACM0",
        mqtt_enabled=True,
        mqtt_host="mosquitto",
    )

    assert config.mqtt_topic == "home/sensors/environment"
    assert config.mqtt_host == "mosquitto"
