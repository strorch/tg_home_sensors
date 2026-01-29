"""Configuration management using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram Bot
    telegram_bot_token: str = Field(..., description="Telegram bot token from @BotFather")

    # Serial Port
    serial_port: str = Field(..., description="Arduino serial port path")
    serial_baud_rate: int = Field(default=9600, description="Serial baud rate")

    # Database
    database_path: str = Field(default="data/sensors.db", description="SQLite database path")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Defaults
    default_humidity_min: float = Field(default=40.0, ge=0.0, le=100.0)
    default_humidity_max: float = Field(default=60.0, ge=0.0, le=100.0)


def load_config() -> Config:
    """Load and validate configuration.

    Raises:
        ValidationError: If required config is missing or invalid.
    """
    return Config()
