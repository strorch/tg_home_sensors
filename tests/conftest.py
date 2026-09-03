"""Shared fixtures for exporter tests."""

from datetime import UTC, datetime

import pytest
from prometheus_client import CollectorRegistry

from src.sensors.metrics import SensorMetrics
from src.sensors.models import DhtReading, Scd41Reading, SensorReading


@pytest.fixture
def sensor_reading() -> SensorReading:
    return SensorReading(
        dht=DhtReading(temperature_celsius=23.4, humidity_percent=48.1),
        scd41=Scd41Reading(
            co2_ppm=812,
            temperature_celsius=24.1,
            humidity_percent=46.8,
        ),
        observed_at=datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
    )


@pytest.fixture
def registry() -> CollectorRegistry:
    return CollectorRegistry()


@pytest.fixture
def sensor_metrics(registry: CollectorRegistry) -> SensorMetrics:
    return SensorMetrics(registry)
