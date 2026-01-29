# Telegram Bot Command Contracts

**Feature**: Arduino Sensor Monitoring Bot  
**Date**: 2026-01-29  
**Purpose**: Define all bot commands, their inputs, outputs, and behaviors

## Command Overview

| Command | Priority | Description | Rate Limited |
|---------|----------|-------------|--------------|
| `/start` | P1 | Initialize user, show welcome message | No |
| `/help` | P1 | Display command help | No |
| `/sensors` | P1 | Get current sensor readings | Yes (3s) |
| `/status` | P1 | Alias for `/sensors` | Yes (3s) |
| `/settings` | P3 | Show current threshold settings | Yes (3s) |
| `/set_humidity_min <value>` | P3 | Set minimum humidity threshold | Yes (3s) |
| `/set_humidity_max <value>` | P3 | Set maximum humidity threshold | Yes (3s) |

---

## Command Specifications

### 1. `/start`

**Purpose**: Initialize user in system and display welcome message.

**User Story**: P1 - Query Current Sensor Readings

**Input**:
- Command: `/start`
- Parameters: None

**Preconditions**:
- User has started conversation with bot

**Processing**:
1. Extract user's `chat_id` from Telegram update
2. Check if user exists in database
3. If new user:
   - Create User record with default thresholds (40%, 60%)
   - Create AlertState record with state "normal"
4. Send welcome message

**Output** (Success):
```
Welcome to Arduino Home Sensors Bot! 🌡️💧

I monitor your Arduino sensors and alert you when humidity levels are unusual.

Available commands:
/sensors - Get current sensor readings
/settings - View your alert thresholds
/set_humidity_min <value> - Set minimum humidity %
/set_humidity_max <value> - Set maximum humidity %
/help - Show this help message

Your current thresholds:
• Min: 40.0%
• Max: 60.0%

You'll receive alerts when humidity goes outside this range.
```

**Error Handling**:
- Database error: "Sorry, unable to initialize your account. Please try again."
- Logs error with context

**Rate Limit**: None

**State Changes**:
- Creates User record if not exists
- Creates AlertState record if not exists

---

### 2. `/help`

**Purpose**: Display help information about available commands.

**User Story**: P1 - Query Current Sensor Readings

**Input**:
- Command: `/help`
- Parameters: None

**Preconditions**: None

**Processing**:
1. Format help message with all available commands

**Output** (Success):
```
Arduino Home Sensors Bot - Help 📖

📊 Monitoring Commands:
/sensors or /status - Get current sensor readings

⚙️ Configuration Commands:
/settings - View your humidity thresholds
/set_humidity_min <value> - Set minimum threshold (0-100)
/set_humidity_max <value> - Set maximum threshold (0-100)

ℹ️ Information:
/help - Show this message
/start - Initialize bot

🔔 Automatic Alerts:
You'll receive automatic notifications when:
• Humidity exceeds your maximum threshold
• Humidity falls below your minimum threshold
• Humidity returns to normal range

⏱️ Alert cooldown: 5 minutes between similar alerts
```

**Error Handling**: None (static message)

**Rate Limit**: None

**State Changes**: None

---

### 3. `/sensors` (and `/status`)

**Purpose**: Retrieve and display current Arduino sensor readings.

**User Story**: P1 - Query Current Sensor Readings

**Input**:
- Command: `/sensors` or `/status`
- Parameters: None

**Preconditions**:
- Arduino is connected and sending data

**Processing**:
1. Check rate limit (max 1 request per 3 seconds)
2. Retrieve latest SensorReading from serial reader service
3. Format readings with emojis and units
4. Include timestamp

**Output** (Success - Arduino Connected):
```
📊 Current Sensor Readings

💧 Humidity: 56.00%
🌡️ DHT Temperature: 23.40°C
🌡️ LM35 Temperature: 24.93°C
🌡️ Thermistor: 22.73°C

📅 Last updated: 2026-01-29 10:30:45 UTC

Your humidity thresholds: 40.0% - 60.0%
✅ Status: Normal
```

**Output** (Success - High Humidity):
```
📊 Current Sensor Readings

💧 Humidity: 72.00%
🌡️ DHT Temperature: 28.50°C
🌡️ LM35 Temperature: 29.10°C
🌡️ Thermistor: 27.80°C

📅 Last updated: 2026-01-29 10:30:45 UTC

Your humidity thresholds: 40.0% - 60.0%
⚠️ Status: HIGH HUMIDITY ALERT
```

**Output** (Arduino Disconnected):
```
❌ Sensor Unavailable

The Arduino sensor is currently disconnected.
Attempting to reconnect...

Please try again in a few moments.
```

**Output** (Rate Limited):
```
⏸️ Please wait 2 more seconds before requesting sensor data again.
```

**Error Handling**:
- Serial disconnected: Return "Sensor Unavailable" message
- No data available yet: "No sensor data available. Waiting for first reading..."
- Rate limit exceeded: Return cooldown message

**Rate Limit**: Yes (1 request per 3 seconds per user)

**State Changes**: None (read-only)

---

### 4. `/settings`

**Purpose**: Display current user-specific threshold settings.

**User Story**: P3 - Configure Alert Thresholds

**Input**:
- Command: `/settings`
- Parameters: None

**Preconditions**:
- User has initialized with `/start`

**Processing**:
1. Check rate limit
2. Retrieve User record from database
3. Format threshold settings

**Output** (Success):
```
⚙️ Your Alert Settings

💧 Humidity Thresholds:
• Minimum: 40.0%
• Maximum: 60.0%

🔔 Alert Behavior:
• You'll be notified when humidity goes outside this range
• Cooldown: 5 minutes between similar alerts
• Recovery notifications when humidity normalizes

To change settings:
/set_humidity_min <value>
/set_humidity_max <value>

Example: /set_humidity_min 35
```

**Error Handling**:
- User not found: Prompt to use `/start` first
- Database error: "Unable to retrieve settings. Please try again."

**Rate Limit**: Yes (1 request per 3 seconds per user)

**State Changes**: None (read-only)

---

### 5. `/set_humidity_min <value>`

**Purpose**: Set minimum humidity threshold for alerts.

**User Story**: P3 - Configure Alert Thresholds

**Input**:
- Command: `/set_humidity_min`
- Parameters: 
  - `value` (required): Float between 0.0 and 100.0

**Preconditions**:
- User has initialized with `/start`

**Processing**:
1. Check rate limit
2. Parse and validate `value` parameter
3. Verify `value` < current `humidity_max`
4. Update User record in database
5. Update `updated_at` timestamp

**Output** (Success):
```
✅ Minimum humidity threshold updated!

New settings:
• Minimum: 35.0%
• Maximum: 60.0%

You'll now receive alerts when humidity falls below 35.0%.
```

**Output** (Invalid Value - Out of Range):
```
❌ Invalid value.

Humidity must be between 0 and 100.
Please try again.

Example: /set_humidity_min 35
```

**Output** (Invalid Value - Greater Than Max):
```
❌ Invalid value.

Minimum (45.0%) must be less than maximum (40.0%).
Current maximum: 40.0%

Please set a lower minimum, or increase maximum first:
/set_humidity_max <value>
```

**Output** (Missing Parameter):
```
❌ Missing humidity value.

Usage: /set_humidity_min <value>
Example: /set_humidity_min 35

Value must be between 0 and 100.
```

**Error Handling**:
- User not found: Prompt to use `/start` first
- Database error: "Unable to update settings. Please try again."
- Invalid parameter format: Return usage example

**Rate Limit**: Yes (1 request per 3 seconds per user)

**State Changes**:
- Updates User.humidity_min
- Updates User.updated_at
- Does NOT reset AlertState (maintains continuity)

---

### 6. `/set_humidity_max <value>`

**Purpose**: Set maximum humidity threshold for alerts.

**User Story**: P3 - Configure Alert Thresholds

**Input**:
- Command: `/set_humidity_max`
- Parameters:
  - `value` (required): Float between 0.0 and 100.0

**Preconditions**:
- User has initialized with `/start`

**Processing**:
1. Check rate limit
2. Parse and validate `value` parameter
3. Verify `value` > current `humidity_min`
4. Update User record in database
5. Update `updated_at` timestamp

**Output** (Success):
```
✅ Maximum humidity threshold updated!

New settings:
• Minimum: 40.0%
• Maximum: 70.0%

You'll now receive alerts when humidity exceeds 70.0%.
```

**Output** (Invalid Value - Out of Range):
```
❌ Invalid value.

Humidity must be between 0 and 100.
Please try again.

Example: /set_humidity_max 70
```

**Output** (Invalid Value - Less Than Min):
```
❌ Invalid value.

Maximum (35.0%) must be greater than minimum (40.0%).
Current minimum: 40.0%

Please set a higher maximum, or decrease minimum first:
/set_humidity_min <value>
```

**Output** (Missing Parameter):
```
❌ Missing humidity value.

Usage: /set_humidity_max <value>
Example: /set_humidity_max 70

Value must be between 0 and 100.
```

**Error Handling**:
- User not found: Prompt to use `/start` first
- Database error: "Unable to update settings. Please try again."
- Invalid parameter format: Return usage example

**Rate Limit**: Yes (1 request per 3 seconds per user)

**State Changes**:
- Updates User.humidity_max
- Updates User.updated_at
- Does NOT reset AlertState (maintains continuity)

---

## Automatic Alert Messages (Not Commands)

These are proactive messages sent by the bot without user request.

### High Humidity Alert

**Trigger**: Humidity exceeds user's `humidity_max` threshold

**Conditions**:
- AlertState.current_state != "high_humidity" OR
- (AlertState.current_state == "high_humidity" AND cooldown expired)

**Message**:
```
⚠️ HIGH HUMIDITY ALERT

Current humidity: 72.50%
Your threshold: ≤ 60.0%

🌡️ Other readings:
• DHT Temp: 28.40°C
• LM35 Temp: 29.10°C
• Thermistor: 27.80°C

📅 2026-01-29 10:30:45 UTC

Consider ventilating the area or using a dehumidifier.
```

**State Changes**:
- Sets AlertState.current_state = "high_humidity"
- Sets AlertState.last_alert_time = now
- Sets AlertState.last_alert_type = "high"

---

### Low Humidity Alert

**Trigger**: Humidity falls below user's `humidity_min` threshold

**Conditions**:
- AlertState.current_state != "low_humidity" OR
- (AlertState.current_state == "low_humidity" AND cooldown expired)

**Message**:
```
⚠️ LOW HUMIDITY ALERT

Current humidity: 28.00%
Your threshold: ≥ 40.0%

🌡️ Other readings:
• DHT Temp: 18.20°C
• LM35 Temp: 19.00°C
• Thermistor: 17.50°C

📅 2026-01-29 10:30:45 UTC

Consider using a humidifier to increase moisture levels.
```

**State Changes**:
- Sets AlertState.current_state = "low_humidity"
- Sets AlertState.last_alert_time = now
- Sets AlertState.last_alert_type = "low"

---

### Recovery Notification

**Trigger**: Humidity returns to acceptable range after alert

**Conditions**:
- AlertState.current_state != "normal" AND
- Humidity is now between humidity_min and humidity_max

**Message**:
```
✅ HUMIDITY BACK TO NORMAL

Current humidity: 52.00%
Your range: 40.0% - 60.0%

🌡️ Current readings:
• DHT Temp: 23.40°C
• LM35 Temp: 24.10°C
• Thermistor: 22.90°C

📅 2026-01-29 11:15:30 UTC

Environment is back to acceptable levels.
```

**State Changes**:
- Sets AlertState.current_state = "normal"
- Clears AlertState.last_alert_time = None
- Clears AlertState.last_alert_type = None

---

### Connection Lost Notification

**Trigger**: Arduino serial connection lost

**Message**:
```
⚠️ SENSOR CONNECTION LOST

The Arduino has been disconnected.
Attempting automatic reconnection...

You can still use bot commands, but sensor data will be unavailable until connection is restored.

I'll notify you when the connection is reestablished.
```

---

### Connection Restored Notification

**Trigger**: Arduino serial connection reestablished after disconnection

**Message**:
```
✅ SENSOR CONNECTION RESTORED

Arduino is now connected and sending data.

📊 Latest readings:
💧 Humidity: 56.00%
🌡️ DHT Temp: 23.40°C
🌡️ LM35 Temp: 24.93°C
🌡️ Thermistor: 22.73°C

Monitoring resumed.
```

---

## Error Response Format

All error responses follow this pattern:

```
❌ [Error Title]

[Explanation of what went wrong]

[Suggestion for resolution or retry guidance]

[Optional: Usage example]
```

---

## Rate Limiting Details

### Configuration
- **Cooldown Period**: 3 seconds per user per command
- **Scope**: Per user (chat_id based)
- **Exempt Commands**: `/start`, `/help`
- **Implementation**: In-memory dictionary with timestamp tracking

### Rate Limit Response
```
⏸️ Please wait {seconds} more second(s) before using this command again.
```

---

## Command Registration (Bot Commands Menu)

These commands appear in Telegram's command autocomplete:

```
start - Initialize bot and show welcome
help - Show available commands
sensors - Get current sensor readings
status - Get current sensor readings
settings - View your alert thresholds
set_humidity_min - Set minimum humidity (0-100)
set_humidity_max - Set maximum humidity (0-100)
```

---

## Testing Contracts

Each command should have tests verifying:

1. **Success Path**: Command with valid input produces expected output
2. **Invalid Input**: Command with invalid parameters returns appropriate error
3. **Missing Parameters**: Command without required parameters returns usage help
4. **Rate Limiting**: Rapid commands are rate limited correctly
5. **State Changes**: Database/state updated correctly after command
6. **Error Handling**: Graceful handling of database errors, serial disconnection
7. **Concurrent Access**: Multiple users can use commands simultaneously

Example test cases for `/set_humidity_min`:
- ✅ Valid value (35.0) within range and less than max
- ❌ Value out of range (150.0)
- ❌ Value greater than or equal to current max
- ❌ Missing value parameter
- ❌ Non-numeric value ("abc")
- ✅ Rate limit enforced after 3 seconds
- ✅ Database updated with new value
- ✅ Timestamp updated
