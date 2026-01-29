# Research: Arduino Sensor Monitoring Bot

**Feature**: Arduino Sensor Monitoring Bot  
**Date**: 2026-01-29  
**Purpose**: Research technical decisions and best practices for implementation

## Research Questions

### 1. Python Telegram Bot Framework Selection

**Question**: Which Python Telegram bot framework to use: python-telegram-bot or aiogram?

**Decision**: **python-telegram-bot v20+**

**Rationale**:
- More mature and stable (v20+ has excellent async support)
- Better documentation and larger community
- More Pythonic API design with native async/await
- Built-in conversation handlers for stateful interactions
- Extensive middleware support for rate limiting
- Better suited for long-running bots with background tasks
- Active maintenance and regular updates

**Alternatives Considered**:
- **aiogram v3**: Also excellent, but smaller community and less extensive documentation. Better for high-performance scenarios with many concurrent users (10k+), which exceeds our scope of 5-10 users.
- **pyTelegramBotAPI (telebot)**: Simpler but lacks native async support and advanced features we need for concurrent serial I/O.

---

### 2. Serial Communication Library

**Question**: Best approach for reading Arduino serial data continuously while handling Telegram bot operations?

**Decision**: **pyserial with asyncio integration**

**Rationale**:
- PySerial is the standard Python library for serial communication
- Can wrap synchronous serial reads in asyncio.to_thread() to avoid blocking
- Reliable cross-platform support (Linux/macOS/Windows)
- Well-tested and stable for continuous reading
- Simple API for connection management and error handling

**Implementation Pattern**:
```python
async def read_serial_continuously():
    loop = asyncio.get_event_loop()
    while True:
        data = await loop.run_in_executor(None, serial_port.readline)
        await process_sensor_data(data)
```

**Alternatives Considered**:
- **pyserial-asyncio**: Native async wrapper, but adds complexity and is less mature than running pyserial in executor
- **Direct threading**: More complex to manage and harder to integrate with asyncio event loop

---

### 3. User Settings Persistence

**Question**: What storage mechanism for user-specific threshold settings and alert states?

**Decision**: **SQLite with aiosqlite**

**Rationale**:
- Lightweight, serverless, zero-configuration
- Built into Python standard library
- Supports concurrent reads with asyncio via aiosqlite
- ACID compliance ensures data integrity on crashes
- Easy backup (single file)
- Sufficient performance for 5-10 users
- Type-safe queries with proper schema

**Schema Design**:
- `users` table: chat_id (PK), humidity_min, humidity_max, created_at
- `alert_states` table: chat_id (FK), alert_type, last_alert_time, current_state

**Alternatives Considered**:
- **JSON file**: Simpler but lacks transactional integrity, concurrent access issues, no schema validation
- **Redis**: Overkill for this scale, requires external service, adds deployment complexity
- **PostgreSQL**: Too heavy for 5-10 users, requires separate database server

---

### 4. Data Parsing Strategy

**Question**: How to reliably parse Arduino format "Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C"?

**Decision**: **Regex with named capture groups**

**Rationale**:
- Format is consistent and well-structured
- Regex provides robust extraction with validation
- Named groups make code readable and maintainable
- Easy to handle malformed data with try/except
- Performance is sufficient for 1 reading/second

**Pattern**:
```python
pattern = r'Humidity:\s*(?P<humidity>\d+\.\d+)%\s+DHT Temp:\s*(?P<dht_temp>\d+\.\d+)C\s+LM35:\s*(?P<lm35_temp>\d+\.\d+)C\s+Therm:\s*(?P<therm_temp>\d+\.\d+)C'
```

**Alternatives Considered**:
- **String split**: Fragile, breaks on minor format changes, harder to validate
- **Custom parser**: Over-engineering for simple format
- **Pydantic parsing**: Would need preprocessing anyway, regex is more direct

---

### 5. Rate Limiting Implementation

**Question**: How to implement rate limiting for user commands (max 1 command per 3 seconds per user)?

**Decision**: **python-telegram-bot built-in rate limiter with custom decorator**

**Rationale**:
- python-telegram-bot v20+ includes BaseRateLimiter class
- Can implement per-user rate limiting with dict tracking
- Decorator pattern keeps handlers clean
- In-memory tracking sufficient for small user count
- Easy to customize per handler

**Implementation Approach**:
```python
user_last_command = {}  # chat_id -> timestamp

def rate_limit(seconds=3):
    def decorator(func):
        async def wrapper(update, context):
            chat_id = update.effective_chat.id
            now = time.time()
            if chat_id in user_last_command:
                if now - user_last_command[chat_id] < seconds:
                    await update.message.reply_text("Please wait...")
                    return
            user_last_command[chat_id] = now
            return await func(update, context)
        return wrapper
    return decorator
```

**Alternatives Considered**:
- **External library (ratelimit)**: Adds dependency for simple requirement
- **Redis-based limiting**: Overkill for local bot with few users
- **Token bucket algorithm**: More complex than needed for this use case

---

### 6. Alert Cooldown Management

**Question**: How to implement 5-minute cooldown for humidity alerts to prevent spam?

**Decision**: **Database-backed state tracking with timestamp comparison**

**Rationale**:
- Persist alert states in SQLite ensures cooldown survives restarts
- Store last_alert_time per user per alert_type (high/low humidity)
- Check timestamp before sending new alert
- Simple comparison: `current_time - last_alert_time >= 300` (5 minutes)
- Allows separate cooldowns for high vs low humidity

**State Machine**:
- States: NORMAL, HIGH_HUMIDITY_ALERT, LOW_HUMIDITY_ALERT
- Transitions: Only send alert if state changes OR cooldown expired
- Recovery message when returning to NORMAL

**Alternatives Considered**:
- **In-memory tracking**: Lost on restart, can cause duplicate alerts
- **Fixed schedule checking**: Misses rapid threshold crossings, less responsive
- **External task queue**: Unnecessary complexity for simple time-based logic

---

### 7. Error Handling and Reconnection Strategy

**Question**: How to handle Arduino disconnection and reconnect gracefully?

**Decision**: **Exponential backoff with connection health monitoring**

**Rationale**:
- Detect disconnection via SerialException or timeout on read
- Exponential backoff prevents resource exhaustion: 1s, 2s, 4s, 8s, max 60s
- Continue bot operations during disconnection (return "unavailable" message)
- Background task continuously attempts reconnection
- Health check: successful read resets backoff timer
- Notify users on disconnect and reconnect

**Implementation Pattern**:
```python
async def maintain_serial_connection():
    backoff = 1
    while True:
        try:
            await connect_serial()
            backoff = 1  # Reset on success
            await read_serial_continuously()
        except SerialException:
            await notify_users_disconnected()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
```

**Alternatives Considered**:
- **Fixed retry interval**: Can overwhelm system if issue is persistent
- **Circuit breaker pattern**: Too complex for simple serial connection
- **No automatic reconnection**: Requires manual intervention, reduces reliability

---

### 8. Logging Strategy

**Question**: What logging approach for sensor readings, alerts, and user interactions?

**Decision**: **Structured logging with Python's logging module**

**Rationale**:
- Standard library, no additional dependencies
- Structured format with JSON for easy parsing
- Separate log levels: DEBUG (development), INFO (production)
- Rotating file handler to manage disk space
- Log context: timestamp, user_id, command, sensor_values, alert_type
- Critical errors also sent to admin via Telegram

**Log Structure**:
```json
{
  "timestamp": "2026-01-29T10:30:00Z",
  "level": "INFO",
  "event": "sensor_reading",
  "data": {
    "humidity": 56.0,
    "dht_temp": 23.4,
    "lm35_temp": 24.93,
    "therm_temp": 22.73
  }
}
```

**Alternatives Considered**:
- **structlog**: More features but adds dependency, overkill for this scale
- **Plain text logs**: Harder to parse and analyze programmatically
- **External logging service**: Unnecessary for local deployment

---

### 9. Configuration Management

**Question**: How to manage .env configuration with validation and type safety?

**Decision**: **pydantic-settings with BaseSettings**

**Rationale**:
- Type-safe configuration with automatic validation
- Environment variable parsing with defaults
- Fail-fast on missing required variables
- IDE autocomplete support
- Easy to test with mock environments
- Integrates seamlessly with Pydantic models

**Configuration Model**:
```python
class Settings(BaseSettings):
    telegram_bot_token: str
    serial_port: str
    serial_baud_rate: int = 9600
    database_path: str = "data/bot.db"
    log_level: str = "INFO"
    default_humidity_min: float = 40.0
    default_humidity_max: float = 60.0
    alert_cooldown_seconds: int = 300
    
    class Config:
        env_file = ".env"
```

**Alternatives Considered**:
- **python-dotenv + manual parsing**: No type safety, manual validation required
- **configparser**: INI format less common, no environment variable support
- **YAML config**: Requires external file, less secure than env vars for secrets

---

## Technology Stack Summary

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Bot Framework | python-telegram-bot | 20+ |
| Serial I/O | pyserial | 3.5+ |
| Async Serial | asyncio.to_thread | (stdlib) |
| Database | SQLite + aiosqlite | 3.40+ |
| Configuration | pydantic-settings | 2.0+ |
| Data Models | pydantic | 2.0+ |
| Testing | pytest + pytest-asyncio | 8.0+ |
| Mocking | pytest-mock | 3.12+ |
| Coverage | pytest-cov | 4.1+ |
| Linting | ruff | 0.1+ |
| Type Checking | mypy | 1.8+ |
| Package Manager | uv | latest |

---

## Best Practices Applied

### Async I/O Patterns
- Use asyncio event loop for all I/O operations
- Run blocking serial reads in thread executor
- Never block the main event loop
- Use asyncio.gather() for concurrent operations

### Error Resilience
- Graceful degradation when Arduino disconnected
- Validate all user inputs
- Handle malformed sensor data without crashing
- Comprehensive exception handling with context logging

### Testing Strategy
- Mock Telegram Update objects for handler tests
- Mock serial port for unit tests
- Integration tests with in-memory SQLite
- Fixture-based test data
- Test both success and failure paths

### Security
- Never log sensitive data (bot token)
- Validate all user inputs before processing
- Rate limit all handlers
- Use parameterized SQL queries (prevent injection)
- .env file in .gitignore

### Performance
- Connection pooling for database (aiosqlite)
- Efficient regex compilation (compile once, use many)
- Memory-bounded data structures (no unbounded queues)
- Periodic cleanup of old alert states

---

## Open Questions / Future Considerations

### Out of Scope for MVP
1. **Multi-Arduino support**: Current design assumes single Arduino; would require connection pooling
2. **Historical data storage**: Not storing sensor readings beyond current value
3. **Web dashboard**: Telegram-only interface for MVP
4. **User authentication**: Relying on Telegram user IDs, no additional auth
5. **Temperature alerts**: Only humidity alerts in current scope
6. **Data export**: No CSV/JSON export functionality yet
7. **Graphing/visualization**: Text-only sensor data display

### Potential Future Enhancements
- Add temperature threshold alerts (similar to humidity)
- Support multiple Arduinos with device identification
- Store historical sensor data with time-series queries
- Web dashboard for data visualization
- Configurable alert cooldown periods per user
- SMS/email notifications in addition to Telegram
- Sensor calibration interface via bot commands
