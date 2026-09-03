"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration for serial input, metrics, and optional MQTT output."""

    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

    serial_port: str = Field(min_length=1)
    serial_baud_rate: int = Field(default=115200, gt=0)
    serial_timeout_seconds: float = Field(default=2.0, gt=0)
    metrics_host: str = "0.0.0.0"
    metrics_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    mqtt_enabled: bool = False
    mqtt_host: str | None = None
    mqtt_port: int = Field(default=1883, ge=1, le=65535)
    mqtt_topic: str = Field(default="home/sensors/environment", min_length=1)
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_tls: bool = False
    mqtt_client_id: str = Field(default="home-sensors-exporter", min_length=1)

    @model_validator(mode="after")
    def validate_mqtt(self) -> Self:
        if self.mqtt_enabled and not self.mqtt_host:
            raise ValueError("MQTT_HOST is required when MQTT_ENABLED is true")
        return self


def _load_dotenv() -> None:
    path = Path(".env")
    if path.exists():
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, value = stripped.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def load_config() -> Config:
    """Load local environment values and validate them."""
    if not os.getenv("PYTEST_CURRENT_TEST"):
        _load_dotenv()
    return Config()  # type: ignore[call-arg]
