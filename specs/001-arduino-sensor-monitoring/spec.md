# Feature Specification: Arduino Sensor Monitoring Bot

**Feature Branch**: `001-arduino-sensor-monitoring`  
**Created**: 2026-01-29  
**Status**: Draft  
**Input**: User description: "Create telegram bot which will work with information from arduino sensors. It should retrieve sensors info via user command. Also if humidity is too high or too low it should send message to user about it. Arduino pushes data in format like this 'Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C' every second. Serial (port, baud) should be configurable via .env file."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Current Sensor Readings (Priority: P1)

As a user, I want to request current sensor readings from my Arduino via a Telegram command, so I can check temperature and humidity anytime from anywhere.

**Why this priority**: This is the core functionality - users need to be able to retrieve sensor data on demand. Without this, there's no value in having the bot.

**Independent Test**: Can be fully tested by sending a `/sensors` or `/status` command to the bot and verifying it returns current readings in a readable format. Delivers immediate value by providing remote sensor access.

**Acceptance Scenarios**:

1. **Given** the bot is running and Arduino is connected, **When** user sends `/sensors` command, **Then** bot responds with current humidity, DHT temperature, LM35 temperature, and thermistor readings
2. **Given** the bot is running and Arduino is connected, **When** user sends `/status` command, **Then** bot responds with formatted sensor data and timestamp
3. **Given** multiple users are subscribed, **When** any user requests sensor data, **Then** each user receives only their own request response

---

### User Story 2 - Automatic Humidity Alerts (Priority: P2)

As a user, I want to receive automatic alerts when humidity levels are outside acceptable range, so I can take action to protect my equipment or environment without constantly checking.

**Why this priority**: This provides proactive monitoring value, turning the bot from a passive query tool into an active monitoring system. It's the second most important feature as it enables autonomous operation.

**Independent Test**: Can be tested by simulating or waiting for humidity readings that exceed thresholds, then verifying the bot sends alert messages automatically without user intervention.

**Acceptance Scenarios**:

1. **Given** humidity threshold is set (e.g., 40-60%), **When** humidity goes above 60%, **Then** bot sends alert message "⚠️ High humidity detected: 65.00%"
2. **Given** humidity threshold is set, **When** humidity goes below 40%, **Then** bot sends alert message "⚠️ Low humidity detected: 35.00%"
3. **Given** humidity has been out of range for multiple readings, **When** new readings continue to be out of range, **Then** bot does not spam user (implements cooldown period)
4. **Given** humidity was out of range and has returned to normal, **When** reading is back within thresholds, **Then** bot sends recovery message "✅ Humidity back to normal: 50.00%"

---

### User Story 3 - Configure Alert Thresholds (Priority: P3)

As a user, I want to configure my own humidity alert thresholds via Telegram commands, so I can customize monitoring to my specific needs without editing configuration files.

**Why this priority**: This adds user customization and flexibility, but the bot can work with default/hardcoded thresholds initially. It's an enhancement that improves UX.

**Independent Test**: Can be tested by sending threshold configuration commands and verifying alerts trigger at the newly configured levels.

**Acceptance Scenarios**:

1. **Given** user wants to set thresholds, **When** user sends `/set_humidity_min 30`, **Then** bot confirms "✅ Minimum humidity threshold set to 30%"
2. **Given** user wants to set thresholds, **When** user sends `/set_humidity_max 70`, **Then** bot confirms "✅ Maximum humidity threshold set to 70%"
3. **Given** user sends invalid threshold, **When** user sends `/set_humidity_min 150`, **Then** bot responds with error "❌ Invalid value. Humidity must be between 0-100%"
4. **Given** user wants to check current settings, **When** user sends `/settings`, **Then** bot displays current min/max thresholds

---

### Edge Cases

- What happens when Arduino is disconnected or serial communication fails?
  - Bot should detect connection loss and notify user
  - Bot should attempt reconnection with exponential backoff
  - Commands should return "Sensor unavailable" message

- What happens when Arduino sends malformed data?
  - Bot should log parsing errors
  - Bot should skip invalid readings without crashing
  - Bot should alert user if multiple consecutive failures occur

- What happens when multiple Arduino data updates arrive while processing?
  - Bot should process latest reading and discard older ones
  - Bot should maintain processing queue to prevent memory issues

- What happens if user spams commands?
  - Bot should implement rate limiting per user
  - Bot should respond with "Please wait X seconds" message

- What happens when bot restarts?
  - Bot should reconnect to Arduino automatically
  - Bot should resume monitoring without user intervention
  - Alert states should be persisted to avoid duplicate alerts

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST continuously read sensor data from Arduino via serial connection every second
- **FR-002**: System MUST parse Arduino data format "Humidity: XX.XX%  DHT Temp: XX.XXC  LM35: XX.XXC  Therm: XX.XXC"
- **FR-003**: System MUST respond to user commands with current sensor readings within 2 seconds
- **FR-004**: System MUST monitor humidity levels and detect when values exceed configured thresholds
- **FR-005**: System MUST send automatic alert messages to users when humidity thresholds are breached
- **FR-006**: System MUST implement alert cooldown to prevent message spam (minimum 5 minutes between same-type alerts)
- **FR-007**: System MUST send recovery notification when humidity returns to normal range
- **FR-008**: System MUST allow configuration of serial port and baud rate via .env file
- **FR-009**: System MUST support multiple Telegram users receiving sensor data
- **FR-010**: System MUST handle Arduino disconnection gracefully with reconnection attempts
- **FR-011**: System MUST validate all incoming sensor data and skip malformed readings
- **FR-012**: System MUST log all sensor readings, alerts, and user interactions
- **FR-013**: System MUST implement rate limiting for user commands (max 1 command per 3 seconds per user)
- **FR-014**: System MUST allow users to configure humidity min/max thresholds via Telegram commands
- **FR-015**: System MUST persist user-specific threshold settings across bot restarts
- **FR-016**: System MUST support standard Telegram bot commands: `/start`, `/help`, `/sensors`, `/status`

### Key Entities *(include if feature involves data)*

- **SensorReading**: Represents a single data point from Arduino containing humidity percentage, DHT temperature, LM35 temperature, and thermistor temperature, along with timestamp
- **User**: Represents a Telegram user with unique chat ID and personalized alert thresholds (humidity min/max)
- **AlertState**: Tracks current alert status (normal, high humidity, low humidity) per user to prevent duplicate notifications and manage cooldown periods
- **SerialConnection**: Represents connection to Arduino with port, baud rate, connection status, and reconnection state

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve current sensor readings via Telegram command within 2 seconds 95% of the time
- **SC-002**: System detects and alerts on humidity threshold breaches within 5 seconds of occurrence
- **SC-003**: Bot maintains continuous operation for 24+ hours without manual intervention or crashes
- **SC-004**: System successfully reconnects to Arduino within 30 seconds after temporary disconnection
- **SC-005**: Users receive no more than 1 alert per 5-minute period for the same alert condition (no spam)
- **SC-006**: Bot processes Arduino data updates (1 per second) without memory leaks or performance degradation
- **SC-007**: 100% of malformed sensor data is gracefully handled without bot crashes
- **SC-008**: User commands are rate-limited to prevent abuse (max 20 commands per minute per user)

## Assumptions *(mandatory)*

- Arduino is pre-programmed and sends data in the specified format consistently
- Arduino sends data at approximately 1-second intervals over serial connection
- Users have Telegram accounts and know their chat IDs or can use /start command
- Default humidity thresholds will be 40% (min) and 60% (max) unless user configures otherwise
- Serial connection is local (Arduino connected directly to machine running the bot)
- Only humidity monitoring requires alerts; temperature is informational only
- Bot runs on a system with persistent storage for user settings
- System time is accurate for timestamp generation
- Users understand basic Telegram bot interaction patterns
