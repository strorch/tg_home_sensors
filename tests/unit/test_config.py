"""Unit tests for configuration management."""

import pytest
from pydantic import ValidationError
from src.config import Config


def test_config_requires_telegram_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that telegram_bot_token is required."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("SERIAL_PORT", "/dev/ttyUSB0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    assert "telegram_bot_token" in str(exc_info.value)


def test_config_requires_serial_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that serial_port is required."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.delenv("SERIAL_PORT", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    assert "serial_port" in str(exc_info.value)


def test_config_with_valid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config loads successfully with required values."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234")
    monkeypatch.setenv("SERIAL_PORT", "/dev/ttyUSB0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")

    config = Config()

    assert config.telegram_bot_token == "123456:ABC-DEF1234"
    assert config.serial_port == "/dev/ttyUSB0"
    assert config.serial_baud_rate == 9600  # Default
    assert config.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert config.log_level == "INFO"  # Default


def test_config_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that default values are applied correctly."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("SERIAL_PORT", "/dev/ttyUSB0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")

    config = Config()

    assert config.default_humidity_min == 40.0
    assert config.default_humidity_max == 60.0


def test_config_custom_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that custom values override defaults."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("SERIAL_PORT", "/dev/ttyACM0")
    monkeypatch.setenv("SERIAL_BAUD_RATE", "115200")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DEFAULT_HUMIDITY_MIN", "30.0")
    monkeypatch.setenv("DEFAULT_HUMIDITY_MAX", "70.0")

    config = Config()

    assert config.serial_port == "/dev/ttyACM0"
    assert config.serial_baud_rate == 115200
    assert config.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert config.log_level == "DEBUG"
    assert config.default_humidity_min == 30.0
    assert config.default_humidity_max == 70.0


def test_config_humidity_thresholds_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test humidity threshold validation."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("SERIAL_PORT", "/dev/ttyUSB0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    monkeypatch.setenv("DEFAULT_HUMIDITY_MIN", "150.0")  # Invalid: > 100

    with pytest.raises(ValidationError) as exc_info:
        Config()

    assert "default_humidity_min" in str(exc_info.value)
