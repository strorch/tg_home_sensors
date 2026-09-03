"""Home sensor exporter entry point."""

import asyncio
import logging
import signal

from src.config import Config, load_config
from src.sensors.exporter import SensorExporter
from src.sensors.metrics import MetricsHttpServer, SensorMetrics
from src.sensors.mqtt import MqttPublisher
from src.sensors.serial_reader import SerialReader

logger = logging.getLogger(__name__)


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(stop_signal, stop_event.set)
        except NotImplementedError:
            signal.signal(stop_signal, lambda *_args: stop_event.set())


def _create_exporter(config: Config, metrics: SensorMetrics) -> SensorExporter:
    reader = SerialReader(
        config.serial_port,
        config.serial_baud_rate,
        config.serial_timeout_seconds,
        metrics,
    )
    return SensorExporter(reader, metrics, MqttPublisher(config, metrics))


async def main() -> None:
    """Start the metrics endpoint and process Arduino readings until stopped."""
    config = load_config()
    logging.basicConfig(
        level=config.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    metrics = SensorMetrics()
    server = MetricsHttpServer(config.metrics_host, config.metrics_port)
    exporter = _create_exporter(config, metrics)
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)
    server.start()
    exporter.mqtt_publisher.start()
    logger.info("Prometheus metrics available on %s:%s", config.metrics_host, config.metrics_port)
    try:
        await exporter.run(stop_event)
    finally:
        server.stop()


if __name__ == "__main__":
    asyncio.run(main())
