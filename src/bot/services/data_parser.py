"""Data parser service for Arduino sensor data."""
import re
from datetime import datetime, timezone
from typing import Optional

from src.bot.models.sensor_reading import SensorReading


# Regex pattern to match Arduino sensor data format
# Format: "Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C"
SENSOR_PATTERN = re.compile(
    r"Humidity:\s*(?P<humidity>-?\d+\.?\d*)%\s*"
    r"DHT Temp:\s*(?P<dht_temp>-?\d+\.?\d*)C\s*"
    r"LM35:\s*(?P<lm35_temp>-?\d+\.?\d*)C\s*"
    r"Therm:\s*(?P<therm_temp>-?\d+\.?\d*)C"
)


def parse_sensor_data(data: str) -> Optional[SensorReading]:
    """Parse Arduino sensor data string into SensorReading model.
    
    Args:
        data: Raw sensor data string from Arduino.
        
    Returns:
        SensorReading object if parsing succeeds, None otherwise.
        
    Example:
        >>> data = "Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C"
        >>> reading = parse_sensor_data(data)
        >>> reading.humidity
        56.0
    """
    match = SENSOR_PATTERN.search(data)
    if not match:
        return None
    
    try:
        reading = SensorReading(
            humidity=float(match.group("humidity")),
            dht_temperature=float(match.group("dht_temp")),
            lm35_temperature=float(match.group("lm35_temp")),
            thermistor_temperature=float(match.group("therm_temp")),
            timestamp=datetime.now(timezone.utc)
        )
        return reading
    except (ValueError, Exception):
        # Invalid values or validation error
        return None
