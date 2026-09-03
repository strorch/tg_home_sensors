"""Sensor readings received from Arduino."""

from datetime import UTC, datetime

from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class DhtReading(BaseModel):
    """Temperature and humidity reported by the DHT sensor."""

    temperature_celsius: float | None = Field(ge=-40.0, le=125.0)
    humidity_percent: float | None = Field(ge=0.0, le=100.0)

    @field_validator("temperature_celsius", "humidity_percent")
    @classmethod
    def round_measurement(cls, value: float | None) -> float | None:
        result = round(value, 2) if value is not None else None
        return result


class Scd41Reading(BaseModel):
    """CO2, temperature, and humidity reported by the SCD41."""

    co2_ppm: int | None = Field(ge=0, le=40000)
    temperature_celsius: float | None = Field(ge=-10.0, le=60.0)
    humidity_percent: float | None = Field(ge=0.0, le=100.0)

    @field_validator("temperature_celsius", "humidity_percent")
    @classmethod
    def round_measurement(cls, value: float | None) -> float | None:
        result = round(value, 2) if value is not None else None
        return result


class SensorReading(BaseModel):
    """Available measurements from both attached sensor types."""

    dht: DhtReading
    scd41: Scd41Reading
    observed_at: datetime

    @model_validator(mode="after")
    def has_measurement(self) -> Self:
        values = (
            self.dht.temperature_celsius,
            self.dht.humidity_percent,
            self.scd41.co2_ppm,
            self.scd41.temperature_celsius,
            self.scd41.humidity_percent,
        )
        if all(value is None for value in values):
            raise ValueError("at least one sensor measurement is required")
        return self

    @field_validator("observed_at")
    @classmethod
    def timestamp_not_future(cls, value: datetime) -> datetime:
        if value > datetime.now(UTC):
            raise ValueError("observed_at cannot be in the future")
        return value


class SensorStatus(BaseModel):
    """Non-measurement status message from Arduino."""

    status: str = Field(min_length=1)


SerialMessage = SensorReading | SensorStatus
