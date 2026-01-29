"""Integration tests for /sensors handler."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.bot.handlers.sensors import sensors_handler


@pytest.mark.asyncio
async def test_sensors_normal_reading(mock_telegram_update, mock_telegram_context, 
                                     mock_sensor_reading, mock_user):
    """Test /sensors with normal humidity reading."""
    with patch("src.bot.handlers.sensors.serial_reader_service") as mock_serial, \
         patch("src.bot.handlers.sensors.user_settings_service") as mock_user_service:
        
        mock_serial.get_latest_reading = AsyncMock(return_value=mock_sensor_reading)
        mock_user_service.get_user = AsyncMock(return_value=mock_user)
        
        # Execute handler
        await sensors_handler(mock_telegram_update, mock_telegram_context)
        
        # Verify message was sent
        mock_telegram_update.message.reply_text.assert_called_once()
        message = mock_telegram_update.message.reply_text.call_args[0][0]
        
        # Verify content
        assert "56.00%" in message  # Humidity
        assert "23.40°C" in message  # DHT temp
        assert "24.93°C" in message or "24.9°C" in message  # LM35 temp
        assert "22.73°C" in message or "22.7°C" in message  # Thermistor
        assert "Normal" in message or "normal" in message


@pytest.mark.asyncio
async def test_sensors_high_humidity(mock_telegram_update, mock_telegram_context, mock_user):
    """Test /sensors with high humidity shows alert status."""
    from src.bot.models.sensor_reading import SensorReading
    
    high_reading = SensorReading(
        humidity=75.0,  # Above max of 60%
        dht_temperature=28.5,
        lm35_temperature=29.1,
        thermistor_temperature=27.8,
        timestamp=datetime.now(timezone.utc)
    )
    
    with patch("src.bot.handlers.sensors.serial_reader_service") as mock_serial, \
         patch("src.bot.handlers.sensors.user_settings_service") as mock_user_service:
        
        mock_serial.get_latest_reading = AsyncMock(return_value=high_reading)
        mock_user_service.get_user = AsyncMock(return_value=mock_user)
        
        # Execute handler
        await sensors_handler(mock_telegram_update, mock_telegram_context)
        
        # Verify message contains alert
        message = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "75.0%" in message or "75.00%" in message
        assert "HIGH" in message or "ALERT" in message


@pytest.mark.asyncio
async def test_sensors_arduino_disconnected(mock_telegram_update, mock_telegram_context):
    """Test /sensors when Arduino is disconnected."""
    with patch("src.bot.handlers.sensors.serial_reader_service") as mock_serial:
        mock_serial.get_latest_reading = AsyncMock(return_value=None)
        
        # Execute handler
        await sensors_handler(mock_telegram_update, mock_telegram_context)
        
        # Verify error message
        message = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Unavailable" in message or "disconnected" in message
