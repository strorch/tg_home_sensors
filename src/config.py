"""Configuration management using pydantic-settings."""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
    )

    # Telegram Bot
    telegram_bot_token: str = Field(..., description="Telegram bot token from @BotFather")

    # Serial Port
    serial_port: str = Field(..., description="Arduino serial port path")
    serial_baud_rate: int = Field(default=9600, description="Serial baud rate")

    # Database
    database_url: str = Field(
        ..., description="PostgreSQL database URL (e.g., postgresql+asyncpg://...)"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # MCP Server
    mcp_enabled: bool = Field(default=False, description="Enable MCP server entry point")
    mcp_host: str = Field(default="127.0.0.1", description="MCP server bind host")
    mcp_port: int = Field(default=8081, ge=1, le=65535, description="MCP server bind port")
    mcp_api_key: str | None = Field(default=None, description="Bearer token for MCP API access")
    mcp_max_history_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Sensor history retention window in days",
    )

    # Defaults
    default_humidity_min: float = Field(default=40.0, ge=0.0, le=100.0)
    default_humidity_max: float = Field(default=60.0, ge=0.0, le=100.0)


def load_config() -> Config:
    """Load and validate configuration.

    Raises:
        ValidationError: If required config is missing or invalid.
    """
    if not os.getenv("PYTEST_CURRENT_TEST"):
        _load_dotenv()
    return Config()


def _load_dotenv() -> None:
    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        return

    for line in dotenv_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)
