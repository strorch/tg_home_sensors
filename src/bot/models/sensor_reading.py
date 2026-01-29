"""SensorReading data model."""
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class SensorReading(BaseModel):
    """Represents a single data point from Arduino sensors.
    
    Attributes:
        humidity: Humidity percentage (0.0-100.0).
        dht_temperature: DHT sensor temperature in Celsius.
        lm35_temperature: LM35 sensor temperature in Celsius.
        thermistor_temperature: Thermistor temperature in Celsius.
        timestamp: When the reading was captured (UTC).
    """
    
    humidity: float = Field(ge=0.0, le=100.0)
    dht_temperature: float = Field(ge=-40.0, le=125.0)
    lm35_temperature: float = Field(ge=-40.0, le=125.0)
    thermistor_temperature: float = Field(ge=-40.0, le=125.0)
    timestamp: datetime
    
    @field_validator('timestamp')
    @classmethod
    def timestamp_not_future(cls, v: datetime) -> datetime:
        """Ensure timestamp is not in the future.
        
        Args:
            v: Timestamp value to validate.
            
        Returns:
            Validated timestamp.
            
        Raises:
            ValueError: If timestamp is in the future.
        """
        if v > datetime.now(timezone.utc):
            raise ValueError('Timestamp cannot be in the future')
        return v
    
    @field_validator('humidity', 'dht_temperature', 'lm35_temperature', 
                    'thermistor_temperature')
    @classmethod
    def round_to_two_decimals(cls, v: float) -> float:
        """Round numeric values to 2 decimal places.
        
        Args:
            v: Value to round.
            
        Returns:
            Rounded value.
        """
        return round(v, 2)
