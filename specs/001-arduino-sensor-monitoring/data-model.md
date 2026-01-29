# Data Model: Arduino Sensor Monitoring Bot

**Feature**: Arduino Sensor Monitoring Bot  
**Date**: 2026-01-29  
**Purpose**: Define entities, their attributes, relationships, and validation rules

## Entity Definitions

### 1. SensorReading

**Description**: Represents a single data point from Arduino containing all sensor measurements at a specific timestamp.

**Attributes**:
- `humidity: float` - Humidity percentage (0.0-100.0)
- `dht_temperature: float` - DHT sensor temperature in Celsius
- `lm35_temperature: float` - LM35 sensor temperature in Celsius
- `thermistor_temperature: float` - Thermistor temperature in Celsius
- `timestamp: datetime` - When the reading was captured (UTC)

**Validation Rules**:
- `humidity` must be between 0.0 and 100.0
- All temperature values must be between -40.0 and 125.0 (reasonable sensor range)
- `timestamp` must not be in the future
- All numeric values must have at most 2 decimal places

**State Transitions**: N/A (immutable value object)

**Relationships**:
- None (value object, not persisted)

**Pydantic Model**:
```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class SensorReading(BaseModel):
    humidity: float = Field(ge=0.0, le=100.0)
    dht_temperature: float = Field(ge=-40.0, le=125.0)
    lm35_temperature: float = Field(ge=-40.0, le=125.0)
    thermistor_temperature: float = Field(ge=-40.0, le=125.0)
    timestamp: datetime
    
    @field_validator('timestamp')
    @classmethod
    def timestamp_not_future(cls, v):
        if v > datetime.utcnow():
            raise ValueError('Timestamp cannot be in the future')
        return v
    
    @field_validator('humidity', 'dht_temperature', 'lm35_temperature', 'thermistor_temperature')
    @classmethod
    def round_to_two_decimals(cls, v):
        return round(v, 2)
```

---

### 2. User

**Description**: Represents a Telegram user with personalized alert threshold settings.

**Attributes**:
- `chat_id: int` - Telegram chat ID (primary key)
- `humidity_min: float` - Minimum acceptable humidity threshold (%)
- `humidity_max: float` - Maximum acceptable humidity threshold (%)
- `created_at: datetime` - When user first interacted with bot
- `updated_at: datetime` - Last time settings were modified

**Validation Rules**:
- `chat_id` must be positive integer
- `humidity_min` must be between 0.0 and 100.0
- `humidity_max` must be between 0.0 and 100.0
- `humidity_min` must be less than `humidity_max`
- Default values: `humidity_min=40.0`, `humidity_max=60.0`

**State Transitions**: N/A (settings are mutable via commands)

**Relationships**:
- One-to-one with AlertState (each user has one alert state)

**Database Schema**:
```sql
CREATE TABLE users (
    chat_id INTEGER PRIMARY KEY,
    humidity_min REAL NOT NULL DEFAULT 40.0,
    humidity_max REAL NOT NULL DEFAULT 60.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (humidity_min >= 0.0 AND humidity_min <= 100.0),
    CHECK (humidity_max >= 0.0 AND humidity_max <= 100.0),
    CHECK (humidity_min < humidity_max)
);
```

**Pydantic Model**:
```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    chat_id: int = Field(gt=0)
    humidity_min: float = Field(default=40.0, ge=0.0, le=100.0)
    humidity_max: float = Field(default=60.0, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime
    
    @field_validator('humidity_max')
    @classmethod
    def max_greater_than_min(cls, v, info):
        if 'humidity_min' in info.data and v <= info.data['humidity_min']:
            raise ValueError('humidity_max must be greater than humidity_min')
        return v
```

---

### 3. AlertState

**Description**: Tracks current alert status for a user to prevent duplicate notifications and manage cooldown periods.

**Attributes**:
- `chat_id: int` - Telegram chat ID (foreign key to User)
- `current_state: str` - Current alert status: "normal", "high_humidity", "low_humidity"
- `last_alert_time: datetime | None` - Timestamp of last alert sent (null if never alerted)
- `last_alert_type: str | None` - Type of last alert: "high", "low", null

**Validation Rules**:
- `chat_id` must reference existing User
- `current_state` must be one of: "normal", "high_humidity", "low_humidity"
- `last_alert_type` must be one of: "high", "low", or null
- `last_alert_time` must not be in the future

**State Transitions**:
```
NORMAL → HIGH_HUMIDITY: When humidity > humidity_max
NORMAL → LOW_HUMIDITY: When humidity < humidity_min
HIGH_HUMIDITY → NORMAL: When humidity returns to acceptable range
LOW_HUMIDITY → NORMAL: When humidity returns to acceptable range
HIGH_HUMIDITY → LOW_HUMIDITY: Rare but possible (e.g., sensor malfunction)
```

**Transition Rules**:
- Send alert only if:
  1. State is changing (e.g., NORMAL → HIGH_HUMIDITY), OR
  2. State unchanged but cooldown expired (current_time - last_alert_time >= 300s)
- Send recovery message when transitioning to NORMAL
- Update `last_alert_time` and `last_alert_type` on every alert sent

**Relationships**:
- Many-to-one with User (foreign key: chat_id)

**Database Schema**:
```sql
CREATE TABLE alert_states (
    chat_id INTEGER PRIMARY KEY,
    current_state TEXT NOT NULL DEFAULT 'normal',
    last_alert_time TEXT,
    last_alert_type TEXT,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
    CHECK (current_state IN ('normal', 'high_humidity', 'low_humidity')),
    CHECK (last_alert_type IN ('high', 'low') OR last_alert_type IS NULL)
);
```

**Pydantic Model**:
```python
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class AlertState(BaseModel):
    chat_id: int = Field(gt=0)
    current_state: Literal["normal", "high_humidity", "low_humidity"] = "normal"
    last_alert_time: Optional[datetime] = None
    last_alert_type: Optional[Literal["high", "low"]] = None
    
    def should_send_alert(
        self, 
        new_state: Literal["normal", "high_humidity", "low_humidity"],
        cooldown_seconds: int = 300
    ) -> bool:
        """Determine if an alert should be sent based on state and cooldown."""
        # State changed - always send
        if new_state != self.current_state:
            return True
        
        # State unchanged but in alert state
        if new_state != "normal":
            if self.last_alert_time is None:
                return True
            
            # Check if cooldown expired
            elapsed = (datetime.utcnow() - self.last_alert_time).total_seconds()
            return elapsed >= cooldown_seconds
        
        return False
```

---

### 4. SerialConnection

**Description**: Represents the configuration and state of the Arduino serial connection.

**Attributes**:
- `port: str` - Serial port path (e.g., "/dev/ttyUSB0", "COM3")
- `baud_rate: int` - Baud rate for communication (e.g., 9600)
- `timeout: float` - Read timeout in seconds (default: 2.0)
- `is_connected: bool` - Current connection status
- `last_successful_read: datetime | None` - Timestamp of last successful data read
- `reconnect_attempts: int` - Number of consecutive reconnection attempts
- `backoff_delay: float` - Current backoff delay for reconnection (seconds)

**Validation Rules**:
- `port` must not be empty string
- `baud_rate` must be one of: 9600, 19200, 38400, 57600, 115200
- `timeout` must be positive float
- `backoff_delay` must be between 1.0 and 60.0 seconds

**State Transitions**:
```
DISCONNECTED → CONNECTING: Attempting connection
CONNECTING → CONNECTED: Successful connection established
CONNECTING → DISCONNECTED: Connection failed
CONNECTED → DISCONNECTED: Connection lost (error or timeout)
```

**Reconnection Logic**:
- Backoff starts at 1 second
- Doubles on each failed attempt: 1s → 2s → 4s → 8s → 16s → 32s → 60s (max)
- Resets to 1 second on successful connection

**Relationships**:
- None (singleton configuration object)

**Pydantic Model**:
```python
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

class SerialConnection(BaseModel):
    port: str = Field(min_length=1)
    baud_rate: Literal[9600, 19200, 38400, 57600, 115200] = 9600
    timeout: float = Field(default=2.0, gt=0)
    is_connected: bool = False
    last_successful_read: Optional[datetime] = None
    reconnect_attempts: int = Field(default=0, ge=0)
    backoff_delay: float = Field(default=1.0, ge=1.0, le=60.0)
    
    def calculate_backoff(self) -> float:
        """Calculate exponential backoff delay."""
        delay = min(2 ** self.reconnect_attempts, 60.0)
        return max(delay, 1.0)
    
    def reset_backoff(self):
        """Reset backoff on successful connection."""
        self.reconnect_attempts = 0
        self.backoff_delay = 1.0
        self.is_connected = True
    
    def increment_backoff(self):
        """Increment backoff on failed connection."""
        self.reconnect_attempts += 1
        self.backoff_delay = self.calculate_backoff()
        self.is_connected = False
```

---

## Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
│  (Telegram)     │
├─────────────────┤
│ chat_id (PK)    │
│ humidity_min    │
│ humidity_max    │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ 1
         ▼
┌─────────────────┐
│   AlertState    │
├─────────────────┤
│ chat_id (PK,FK) │
│ current_state   │
│ last_alert_time │
│ last_alert_type │
└─────────────────┘

┌──────────────────┐
│  SensorReading   │
│  (Value Object)  │
├──────────────────┤
│ humidity         │
│ dht_temperature  │
│ lm35_temperature │
│ thermistor_temp  │
│ timestamp        │
└──────────────────┘
        ▲
        │ produces
        │
┌──────────────────┐
│ SerialConnection │
│   (Singleton)    │
├──────────────────┤
│ port             │
│ baud_rate        │
│ is_connected     │
│ backoff_delay    │
└──────────────────┘
```

---

## Data Flow

### Sensor Reading Flow
```
Arduino → Serial Port → SerialConnection → Data Parser → SensorReading → AlertManager
                                                                             ↓
                                                    (check thresholds) User + AlertState
                                                                             ↓
                                                                      Send Alert (if needed)
```

### User Command Flow
```
Telegram User → Bot Handler → UserSettings Service → User (DB)
                   ↓
              Reply Message
```

### Alert Decision Flow
```
SensorReading (new) → Get User Settings → Calculate if in threshold
                           ↓
                    Get AlertState
                           ↓
                 Should send alert? (state + cooldown check)
                           ↓
                      Update AlertState
                           ↓
                    Send Telegram Message
```

---

## Database Indexes

### Performance Optimization

```sql
-- Primary keys automatically indexed
-- chat_id in users (PK)
-- chat_id in alert_states (PK)

-- Additional indexes not needed due to small scale (5-10 users)
-- All queries are simple lookups by chat_id (O(1) with PK index)
```

---

## Data Validation Summary

| Entity | Validation Layer | Checks |
|--------|-----------------|---------|
| SensorReading | Pydantic | Range checks, decimal precision, timestamp validation |
| User | Pydantic + DB | Range checks, min < max constraint, positive chat_id |
| AlertState | Pydantic + DB | Enum validation, FK constraint, state consistency |
| SerialConnection | Pydantic | Port non-empty, valid baud rates, positive timeout |

---

## Migration Strategy

### Initial Schema Setup
```sql
-- Run on first startup
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    humidity_min REAL NOT NULL DEFAULT 40.0,
    humidity_max REAL NOT NULL DEFAULT 60.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (humidity_min >= 0.0 AND humidity_min <= 100.0),
    CHECK (humidity_max >= 0.0 AND humidity_max <= 100.0),
    CHECK (humidity_min < humidity_max)
);

CREATE TABLE IF NOT EXISTS alert_states (
    chat_id INTEGER PRIMARY KEY,
    current_state TEXT NOT NULL DEFAULT 'normal',
    last_alert_time TEXT,
    last_alert_type TEXT,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
    CHECK (current_state IN ('normal', 'high_humidity', 'low_humidity')),
    CHECK (last_alert_type IN ('high', 'low') OR last_alert_type IS NULL)
);
```

### User Initialization
- When user sends `/start`, create User and AlertState records if not exist
- Use `INSERT OR IGNORE` to handle race conditions
- Initialize with default threshold values from configuration
