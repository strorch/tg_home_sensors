"""Orchestration for serial readings, metrics, and MQTT."""

import asyncio
import logging

from src.sensors.metrics import SensorMetrics
from src.sensors.models import SensorReading, SensorStatus
from src.sensors.mqtt import MqttPublisher
from src.sensors.serial_reader import SerialReader

logger = logging.getLogger(__name__)


class SensorExporter:
    """Continuously move Arduino readings to configured outputs."""

    def __init__(
        self,
        reader: SerialReader,
        metrics: SensorMetrics,
        mqtt_publisher: MqttPublisher,
    ) -> None:
        self.reader = reader
        self.metrics = metrics
        self.mqtt_publisher = mqtt_publisher

    async def run(self, stop_event: asyncio.Event) -> None:
        try:
            while not stop_event.is_set():
                await self._run_once()
        finally:
            await self.reader.disconnect()
            self.mqtt_publisher.stop()

    async def _run_once(self) -> None:
        if self.reader.is_connected():
            message = await self.reader.read_message()
            self._process_message(message)
        else:
            connected = await self.reader.connect()
            if not connected:
                await asyncio.sleep(self.reader.state.backoff_seconds)

    def _process_message(self, message: SensorReading | SensorStatus | None) -> None:
        if isinstance(message, SensorReading):
            self.metrics.update_reading(message)
            self.mqtt_publisher.publish(message)
        elif isinstance(message, SensorStatus):
            logger.info("Arduino status: %s", message.status)
