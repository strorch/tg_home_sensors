"""Serial reader service for Arduino communication."""

import asyncio
import logging
from typing import Optional
import serial

from src.bot.models.sensor_reading import SensorReading
from src.bot.models.serial_connection import SerialConnection
from src.bot.services.data_parser import parse_sensor_data


logger = logging.getLogger(__name__)


class SerialReaderService:
    """Service to read sensor data from Arduino via serial connection."""

    def __init__(self, port: str, baud_rate: int = 9600, timeout: float = 2.0) -> None:
        """Initialize serial reader service.

        Args:
            port: Serial port path (e.g., "/dev/ttyUSB0").
            baud_rate: Baud rate for communication.
            timeout: Read timeout in seconds.
        """
        self.connection_state = SerialConnection(port=port, baud_rate=baud_rate, timeout=timeout)
        self._serial: Optional[serial.Serial] = None
        self._latest_reading: Optional[SensorReading] = None

    async def connect(self) -> bool:
        """Connect to Arduino serial port.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            logger.info(
                "Connecting to Arduino serial port: "
                f"port={self.connection_state.port}, "
                f"baud_rate={self.connection_state.baud_rate}, "
                f"timeout={self.connection_state.timeout}s"
            )
            # Run serial connection in thread pool (blocking I/O)
            self._serial = await asyncio.to_thread(
                serial.Serial,
                self.connection_state.port,
                self.connection_state.baud_rate,
                timeout=self.connection_state.timeout,
            )

            self.connection_state.reset_backoff()
            logger.info(
                f"Connected to Arduino on {self.connection_state.port} "
                f"at {self.connection_state.baud_rate} baud"
            )
            return True

        except Exception as e:
            self.connection_state.increment_backoff()
            logger.error(
                f"Failed to connect to Arduino: {e}. "
                f"Backoff delay: {self.connection_state.backoff_delay}s"
            )
            return False

    async def disconnect(self) -> None:
        """Disconnect from Arduino serial port."""
        if self._serial and self._serial.is_open:
            await asyncio.to_thread(self._serial.close)
            self._serial = None
            self.connection_state.is_connected = False
            logger.info("Disconnected from Arduino")

    async def read_sensor_data(self) -> Optional[SensorReading]:
        """Read one line of sensor data from Arduino.

        Returns:
            SensorReading if data parsed successfully, None otherwise.
        """
        if not self._serial or not self._serial.is_open:
            return None

        try:
            # Read line in thread pool (blocking I/O)
            line_bytes = await asyncio.to_thread(self._serial.readline)
            line = line_bytes.decode("utf-8", errors="ignore").strip()

            if not line:
                return None

            # Parse sensor data
            reading = parse_sensor_data(line)
            if reading:
                self._latest_reading = reading
                self.connection_state.last_successful_read = reading.timestamp
                self.connection_state.is_connected = True
                logger.debug(f"Read sensor data: {reading}")

            return reading

        except Exception as e:
            logger.error(f"Error reading sensor data: {e}")
            self.connection_state.is_connected = False
            return None

    async def run(self, stop_event: asyncio.Event) -> None:
        """Continuously read sensor data and reconnect on failure.

        Args:
            stop_event: Event used to signal loop shutdown.
        """
        while not stop_event.is_set():
            if not self.is_connected():
                connected = await self.connect()
                if not connected:
                    await asyncio.sleep(self.connection_state.backoff_delay)
                    continue

            reading = await self.read_sensor_data()
            if reading is None:
                # Avoid tight loop when no data is available.
                await asyncio.sleep(0.1)

    def get_latest_reading(self) -> Optional[SensorReading]:
        """Get the most recent sensor reading.

        Returns:
            Latest SensorReading or None if no data available.
        """
        return self._latest_reading

    def is_connected(self) -> bool:
        """Check if serial connection is active.

        Returns:
            True if connected, False otherwise.
        """
        return self._serial is not None and self._serial.is_open


# Global serial reader service instance (initialized in main.py)
serial_reader_service: Optional[SerialReaderService] = None
