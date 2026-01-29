"""Unit tests for serial reader service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.bot.services.serial_reader import SerialReaderService


@pytest.mark.asyncio
async def test_serial_reader_connect():
    """Test serial reader can connect to Arduino."""
    service = SerialReaderService(port="/dev/ttyUSB0", baud_rate=9600)
    
    with patch("serial.Serial") as mock_serial:
        mock_serial.return_value = MagicMock()
        
        await service.connect()
        
        assert service.is_connected()
        mock_serial.assert_called_once_with("/dev/ttyUSB0", 9600, timeout=2.0)


@pytest.mark.asyncio
async def test_serial_reader_read_data():
    """Test serial reader can read sensor data."""
    service = SerialReaderService(port="/dev/ttyUSB0", baud_rate=9600)
    
    with patch("serial.Serial") as mock_serial:
        mock_instance = MagicMock()
        mock_instance.readline.return_value = b"Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C\n"
        mock_serial.return_value = mock_instance
        
        await service.connect()
        reading = await service.read_sensor_data()
        
        assert reading is not None
        assert reading.humidity == 56.0


@pytest.mark.asyncio
async def test_serial_reader_connection_failure():
    """Test serial reader handles connection failure."""
    service = SerialReaderService(port="/dev/ttyUSB0", baud_rate=9600)
    
    with patch("serial.Serial", side_effect=Exception("Connection failed")):
        result = await service.connect()
        
        assert result is False
        assert not service.is_connected()


@pytest.mark.asyncio
async def test_serial_reader_reconnection_backoff():
    """Test serial reader uses exponential backoff for reconnection."""
    service = SerialReaderService(port="/dev/ttyUSB0", baud_rate=9600)
    
    with patch("serial.Serial", side_effect=Exception("Connection failed")):
        # First attempt
        await service.connect()
        assert service.connection_state.reconnect_attempts == 1
        assert service.connection_state.backoff_delay == 2.0
        
        # Second attempt
        await service.connect()
        assert service.connection_state.reconnect_attempts == 2
        assert service.connection_state.backoff_delay == 4.0
        
        # Third attempt
        await service.connect()
        assert service.connection_state.reconnect_attempts == 3
        assert service.connection_state.backoff_delay == 8.0


@pytest.mark.asyncio
async def test_serial_reader_disconnect():
    """Test serial reader can disconnect gracefully."""
    service = SerialReaderService(port="/dev/ttyUSB0", baud_rate=9600)
    
    with patch("serial.Serial") as mock_serial:
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        
        await service.connect()
        await service.disconnect()
        
        mock_instance.close.assert_called_once()
        assert not service.is_connected()


@pytest.mark.asyncio
async def test_serial_reader_get_latest_reading():
    """Test getting latest reading returns cached value."""
    service = SerialReaderService(port="/dev/ttyUSB0", baud_rate=9600)
    
    # Initially None
    assert service.get_latest_reading() is None
    
    # After reading data
    with patch("serial.Serial") as mock_serial:
        mock_instance = MagicMock()
        mock_instance.readline.return_value = b"Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C\n"
        mock_serial.return_value = mock_instance
        
        await service.connect()
        await service.read_sensor_data()
        
        reading = service.get_latest_reading()
        assert reading is not None
        assert reading.humidity == 56.0
