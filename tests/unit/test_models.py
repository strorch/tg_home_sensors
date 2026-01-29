"""Unit tests for data models."""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from src.bot.models.sensor_reading import SensorReading
from src.bot.models.user import User
from src.bot.models.alert_state import AlertState
from src.bot.models.serial_connection import SerialConnection


class TestSensorReading:
    """Tests for SensorReading model."""

    def test_valid_sensor_reading(self) -> None:
        """Test creating a valid sensor reading."""
        now = datetime.now(timezone.utc)
        reading = SensorReading(
            humidity=56.0,
            dht_temperature=23.4,
            lm35_temperature=24.9,
            thermistor_temperature=22.7,
            timestamp=now,
        )

        assert reading.humidity == 56.0
        assert reading.dht_temperature == 23.4
        assert reading.lm35_temperature == 24.9
        assert reading.thermistor_temperature == 22.7
        assert reading.timestamp == now

    def test_humidity_validation(self) -> None:
        """Test humidity must be between 0 and 100."""
        now = datetime.now(timezone.utc)

        with pytest.raises(ValidationError):
            SensorReading(
                humidity=150.0,  # Invalid
                dht_temperature=23.0,
                lm35_temperature=23.0,
                thermistor_temperature=23.0,
                timestamp=now,
            )

    def test_temperature_validation(self) -> None:
        """Test temperature must be between -40 and 125."""
        now = datetime.now(timezone.utc)

        with pytest.raises(ValidationError):
            SensorReading(
                humidity=50.0,
                dht_temperature=150.0,  # Invalid
                lm35_temperature=23.0,
                thermistor_temperature=23.0,
                timestamp=now,
            )

    def test_future_timestamp_validation(self) -> None:
        """Test timestamp cannot be in the future."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        with pytest.raises(ValidationError):
            SensorReading(
                humidity=50.0,
                dht_temperature=23.0,
                lm35_temperature=23.0,
                thermistor_temperature=23.0,
                timestamp=future,
            )

    def test_decimal_rounding(self) -> None:
        """Test values are rounded to 2 decimal places."""
        now = datetime.now(timezone.utc)
        reading = SensorReading(
            humidity=56.12345,
            dht_temperature=23.456789,
            lm35_temperature=24.999,
            thermistor_temperature=22.731,
            timestamp=now,
        )

        assert reading.humidity == 56.12
        assert reading.dht_temperature == 23.46
        assert reading.lm35_temperature == 25.0
        assert reading.thermistor_temperature == 22.73


class TestUser:
    """Tests for User model."""

    def test_valid_user(self) -> None:
        """Test creating a valid user."""
        now = datetime.now(timezone.utc)
        user = User(
            chat_id=12345, humidity_min=40.0, humidity_max=60.0, created_at=now, updated_at=now
        )

        assert user.chat_id == 12345
        assert user.humidity_min == 40.0
        assert user.humidity_max == 60.0

    def test_default_thresholds(self) -> None:
        """Test default humidity thresholds."""
        now = datetime.now(timezone.utc)
        user = User(chat_id=12345, created_at=now, updated_at=now)

        assert user.humidity_min == 40.0
        assert user.humidity_max == 60.0

    def test_chat_id_must_be_positive(self) -> None:
        """Test chat_id must be positive."""
        now = datetime.now(timezone.utc)

        with pytest.raises(ValidationError):
            User(
                chat_id=-1,  # Invalid
                created_at=now,
                updated_at=now,
            )

    def test_humidity_min_less_than_max(self) -> None:
        """Test humidity_max must be greater than humidity_min."""
        now = datetime.now(timezone.utc)

        with pytest.raises(ValidationError):
            User(
                chat_id=12345,
                humidity_min=60.0,
                humidity_max=40.0,  # Invalid: less than min
                created_at=now,
                updated_at=now,
            )


class TestAlertState:
    """Tests for AlertState model."""

    def test_valid_alert_state(self) -> None:
        """Test creating a valid alert state."""
        now = datetime.now(timezone.utc)
        state = AlertState(
            chat_id=12345, current_state="normal", last_alert_time=now, last_alert_type="high"
        )

        assert state.chat_id == 12345
        assert state.current_state == "normal"
        assert state.last_alert_time == now
        assert state.last_alert_type == "high"

    def test_default_state(self) -> None:
        """Test default alert state is normal."""
        state = AlertState(chat_id=12345)

        assert state.current_state == "normal"
        assert state.last_alert_time is None
        assert state.last_alert_type is None

    def test_should_send_alert_on_state_change(self) -> None:
        """Test alert sent when state changes."""
        state = AlertState(chat_id=12345, current_state="normal")

        assert state.should_send_alert("high_humidity") is True

    def test_should_not_send_alert_without_cooldown(self) -> None:
        """Test alert not sent if cooldown hasn't expired."""
        now = datetime.now(timezone.utc)
        state = AlertState(
            chat_id=12345,
            current_state="high_humidity",
            last_alert_time=now,  # Just sent
        )

        assert state.should_send_alert("high_humidity", cooldown_seconds=300) is False

    def test_should_send_alert_after_cooldown(self) -> None:
        """Test alert sent after cooldown expires."""
        past = datetime.now(timezone.utc) - timedelta(seconds=400)
        state = AlertState(chat_id=12345, current_state="high_humidity", last_alert_time=past)

        assert state.should_send_alert("high_humidity", cooldown_seconds=300) is True


class TestSerialConnection:
    """Tests for SerialConnection model."""

    def test_valid_serial_connection(self) -> None:
        """Test creating a valid serial connection."""
        conn = SerialConnection(port="/dev/ttyUSB0", baud_rate=9600)

        assert conn.port == "/dev/ttyUSB0"
        assert conn.baud_rate == 9600
        assert conn.is_connected is False

    def test_calculate_backoff(self) -> None:
        """Test exponential backoff calculation."""
        conn = SerialConnection(port="/dev/ttyUSB0")

        assert conn.calculate_backoff() == 1.0

        conn.reconnect_attempts = 1
        assert conn.calculate_backoff() == 2.0

        conn.reconnect_attempts = 3
        assert conn.calculate_backoff() == 8.0

        conn.reconnect_attempts = 10
        assert conn.calculate_backoff() == 60.0  # Max

    def test_reset_backoff(self) -> None:
        """Test backoff reset on successful connection."""
        conn = SerialConnection(port="/dev/ttyUSB0")
        conn.reconnect_attempts = 5
        conn.backoff_delay = 32.0

        conn.reset_backoff()

        assert conn.reconnect_attempts == 0
        assert conn.backoff_delay == 1.0
        assert conn.is_connected is True

    def test_increment_backoff(self) -> None:
        """Test backoff increment on failed connection."""
        conn = SerialConnection(port="/dev/ttyUSB0")

        conn.increment_backoff()

        assert conn.reconnect_attempts == 1
        assert conn.backoff_delay == 2.0
        assert conn.is_connected is False
