"""Asynchronous Arduino serial reader."""

import asyncio
import logging
from dataclasses import dataclass

import serial

from src.sensors.metrics import SensorMetrics
from src.sensors.models import SerialMessage
from src.sensors.parser import parse_serial_data

logger = logging.getLogger(__name__)


@dataclass
class ConnectionState:
    """Serial connection and retry state."""

    reconnect_attempts: int = 0

    @property
    def backoff_seconds(self) -> float:
        return min(float(2**self.reconnect_attempts), 60.0)


class SerialReader:
    """Read and validate newline-delimited Arduino messages."""

    def __init__(
        self,
        port: str,
        baud_rate: int,
        timeout: float,
        metrics: SensorMetrics,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.metrics = metrics
        self.state = ConnectionState()
        self._serial: serial.Serial | None = None

    async def connect(self) -> bool:
        connected = False
        try:
            self._serial = await asyncio.to_thread(
                serial.Serial,
                self.port,
                self.baud_rate,
                timeout=self.timeout,
            )
            self.state.reconnect_attempts = 0
            self.metrics.serial_connected.set(1)
            logger.info("Connected to Arduino on %s at %s baud", self.port, self.baud_rate)
            connected = True
        except (serial.SerialException, OSError, ValueError) as error:
            self.state.reconnect_attempts += 1
            self.metrics.serial_connected.set(0)
            logger.warning("Arduino connection failed: %s", error)
        return connected

    async def disconnect(self) -> None:
        if self._serial is not None:
            await asyncio.to_thread(self._serial.close)
            self._serial = None
        self.metrics.serial_connected.set(0)

    async def read_message(self) -> SerialMessage | None:
        message = None
        connection = self._serial
        if connection is not None and connection.is_open:
            try:
                raw = await asyncio.to_thread(connection.readline)
                line = raw.decode("utf-8", errors="ignore").strip()
                message = parse_serial_data(line) if line else None
                if line and message is None:
                    self.metrics.parse_errors.inc()
            except (serial.SerialException, OSError, UnicodeError):
                self.metrics.read_errors.inc()
                logger.exception("Arduino serial read failed")
                await self.disconnect()
        return message

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open
