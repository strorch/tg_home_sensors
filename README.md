# Arduino Home Sensors Bot 🌡️💧

Telegram bot that monitors Arduino sensor data via serial connection, providing on-demand readings and automatic humidity threshold alerts.

## Features

- 📊 **Query Sensors**: Get current readings (humidity + 3 temperature sensors) via `/sensors` command
- 🚨 **Automatic Alerts**: Receive notifications when humidity exceeds your thresholds
- ⚙️ **Customizable**: Configure min/max humidity thresholds via bot commands
- 🔄 **Auto-Reconnect**: Gracefully handles Arduino disconnections with exponential backoff
- 🕒 **Smart Cooldown**: 5-minute alert cooldown prevents notification spam

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv package manager](https://github.com/astral-sh/uv)
- Arduino connected via USB serial port
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Installation

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure the bot**:
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram token and serial port
   ```

3. **Find your Arduino serial port**:
   ```bash
   # macOS
   ls /dev/cu.usbserial* /dev/cu.usbmodem*
   
   # Linux
   ls /dev/ttyUSB* /dev/ttyACM*
   
   # Windows - check Device Manager → Ports (COM & LPT)
   ```

4. **Run the bot**:
   ```bash
   uv run python src/main.py
   ```

5. **Start chatting**:
   - Open Telegram and find your bot
   - Send `/start` to initialize
   - Send `/sensors` to get readings

### Arduino Data Format

Your Arduino must send data in this format every second:
```
Humidity: 56.00%  DHT Temp: 23.40C  LM35: 24.93C  Therm: 22.73C
```

Example Arduino code is provided in the [Quickstart Guide](specs/001-arduino-sensor-monitoring/quickstart.md).

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize your account with default thresholds |
| `/help` | Show help message |
| `/sensors` or `/status` | Get current sensor readings |
| `/settings` | View your humidity thresholds |
| `/set_humidity_min <value>` | Set minimum humidity (0-100) |
| `/set_humidity_max <value>` | Set maximum humidity (0-100) |

## Development

### Run Tests
```bash
uv run pytest --cov=src
```

### Lint & Format
```bash
uv run ruff check .
uv run ruff format .
```

### Type Check
```bash
uv run mypy src/
```

### Docker (PostgreSQL)
```bash
docker compose up --build
```

Notes:
- The container uses PostgreSQL via `DATABASE_URL` in `docker-compose.yml`.
- If you need Arduino access, uncomment the `devices` mapping and set `SERIAL_PORT`.

### VS Code Dev Container
- Open the repository in VS Code and choose **Reopen in Container**.
- The dev container uses Docker Compose and the PostgreSQL service automatically.

### Migrations (Alembic)
```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tg_home_sensors
uv run alembic upgrade head
```

## Troubleshooting

### Permission Denied (Linux)
Add your user to the dialout group:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Arduino Not Sending Data
Check serial monitor (9600 baud) to verify data format matches expected pattern.

### Bot Not Responding
- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Check bot logs for errors
- Ensure bot has been started with `/start` command

## Project Structure

```
src/
├── bot/
│   ├── handlers/     # Telegram command handlers
│   ├── services/     # Business logic (serial, alerts, settings)
│   ├── models/       # Data models (SensorReading, User, AlertState)
│   └── utils/        # Helper functions (rate limiting, logging)
├── config.py         # Configuration management
└── main.py           # Bot entry point

tests/
├── unit/             # Unit tests
├── integration/      # Integration tests
└── fixtures/         # Test fixtures
```

## Technical Details

- **Language**: Python 3.11+
- **Bot Framework**: python-telegram-bot v20+
- **Serial I/O**: pyserial with asyncio
- **Database**: PostgreSQL via SQLAlchemy (async)
- **Testing**: pytest with 80%+ coverage target

For detailed technical documentation, see [Implementation Plan](specs/001-arduino-sensor-monitoring/plan.md).

## License

See LICENSE file for details.
