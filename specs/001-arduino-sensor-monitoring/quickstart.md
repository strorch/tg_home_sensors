# Quickstart Guide: Arduino Sensor Monitoring Bot

**Feature**: Arduino Sensor Monitoring Bot  
**Date**: 2026-01-29  
**Purpose**: Quick setup and usage guide for developers and users

## For Developers

### Prerequisites

- Python 3.11 or higher
- uv package manager installed
- Arduino connected via USB serial port
- Telegram Bot Token (from @BotFather)

### Setup (5 minutes)

1. **Clone and navigate to project**:
   ```bash
   cd /path/to/tg_home_sensors
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Create configuration file**:
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` with your settings**:
   ```env
   # Required: Get from @BotFather on Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   
   # Required: Your Arduino serial port
   # Examples:
   #   Linux: /dev/ttyUSB0 or /dev/ttyACM0
   #   macOS: /dev/cu.usbserial-1410 or /dev/cu.usbmodem14201
   #   Windows: COM3 or COM4
   SERIAL_PORT=/dev/ttyUSB0
   
   # Required: Baud rate (must match Arduino)
   SERIAL_BAUD_RATE=9600
   
   # Optional: Defaults shown
   DATABASE_PATH=data/bot.db
   LOG_LEVEL=INFO
   DEFAULT_HUMIDITY_MIN=40.0
   DEFAULT_HUMIDITY_MAX=60.0
   ALERT_COOLDOWN_SECONDS=300
   ```

5. **Find your serial port** (if unknown):
   
   Linux/macOS:
   ```bash
   ls /dev/tty.*
   # or
   ls /dev/ttyUSB*
   ```
   
   Windows:
   ```bash
   # Check Device Manager → Ports (COM & LPT)
   ```

6. **Run tests** (optional but recommended):
   ```bash
   uv run pytest
   ```

7. **Start the bot**:
   ```bash
   uv run python src/main.py
   ```

8. **Verify it's working**:
   - Open Telegram
   - Search for your bot by username
   - Send `/start`
   - Send `/sensors` to test sensor reading

### Expected Output on Startup

```
2026-01-29 10:30:00 - INFO - Bot starting...
2026-01-29 10:30:01 - INFO - Database initialized at data/bot.db
2026-01-29 10:30:01 - INFO - Connecting to Arduino on /dev/ttyUSB0 at 9600 baud
2026-01-29 10:30:02 - INFO - Arduino connected successfully
2026-01-29 10:30:02 - INFO - First sensor reading: Humidity=56.0%, Temp=23.4°C
2026-01-29 10:30:02 - INFO - Bot started successfully as @YourBotName
2026-01-29 10:30:02 - INFO - Waiting for messages...
```

### Troubleshooting

**"Permission denied" on serial port (Linux)**:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

**Arduino not sending data**:
- Check serial monitor in Arduino IDE first
- Verify baud rate matches (9600)
- Confirm Arduino is sending valid JSON per line with required keys:
  `humidity`, `dht_temperature`, `lm35_temperature`, `thermistor_temperature`

**Bot not responding**:
- Check bot token is correct
- Verify bot is not already running (only one instance allowed)
- Check logs in console for errors

**Database errors**:
- Ensure `data/` directory exists or is created by bot
- Check file permissions for database file

---

## For End Users

### Getting Started

1. **Find the bot on Telegram**: Search for `@YourBotName`

2. **Start conversation**: Send `/start`

3. **Check your sensors**: Send `/sensors` or `/status`

### Available Commands

| Command | What It Does |
|---------|-------------|
| `/start` | Initialize the bot and see welcome message |
| `/help` | Show all available commands |
| `/sensors` | Get current sensor readings |
| `/status` | Same as `/sensors` |
| `/settings` | View your humidity alert thresholds |
| `/set_humidity_min 30` | Set minimum humidity to 30% |
| `/set_humidity_max 70` | Set maximum humidity to 70% |

### Understanding Readings

When you send `/sensors`, you'll see:

```
📊 Current Sensor Readings

💧 Humidity: 56.00%           ← Current moisture level in air
🌡️ DHT Temperature: 23.40°C   ← DHT22 sensor reading
🌡️ LM35 Temperature: 24.93°C  ← LM35 analog sensor reading
🌡️ Thermistor: 22.73°C        ← Thermistor reading

📅 Last updated: 2026-01-29 10:30:45 UTC

Your humidity thresholds: 40.0% - 60.0%
✅ Status: Normal
```

**What's normal?**
- **Humidity**: 30-60% is comfortable for most homes
- **Temperature**: Varies by preference, 20-25°C is typical

### Automatic Alerts

You'll automatically receive messages when:

1. **Humidity too high** (exceeds your max threshold):
   ```
   ⚠️ HIGH HUMIDITY ALERT
   Current humidity: 72.50%
   Your threshold: ≤ 60.0%
   ```

2. **Humidity too low** (below your min threshold):
   ```
   ⚠️ LOW HUMIDITY ALERT
   Current humidity: 28.00%
   Your threshold: ≥ 40.0%
   ```

3. **Humidity returns to normal**:
   ```
   ✅ HUMIDITY BACK TO NORMAL
   Current humidity: 52.00%
   Your range: 40.0% - 60.0%
   ```

### Customizing Your Thresholds

**Default settings**: 40% - 60% humidity

**To change**:
1. Send `/set_humidity_min 35` (sets minimum to 35%)
2. Send `/set_humidity_max 65` (sets maximum to 65%)
3. Verify with `/settings`

**Tips**:
- Minimum must be less than maximum
- Values must be between 0 and 100
- Adjust based on your comfort and environment needs
- Different rooms may need different levels (basement vs. bedroom)

### Alert Frequency

- You won't be spammed! Alerts have a **5-minute cooldown**
- If humidity stays out of range, you'll get reminded every 5 minutes
- When humidity returns to normal, you'll get one recovery message

---

## Quick Reference

### Common Tasks

**Check current humidity**:
```
/sensors
```

**Set comfortable home range (40-60%)**:
```
/set_humidity_min 40
/set_humidity_max 60
```

**Set basement range (higher humidity OK)**:
```
/set_humidity_min 30
/set_humidity_max 70
```

**Set computer room range (lower humidity)**:
```
/set_humidity_min 35
/set_humidity_max 55
```

### Health & Comfort Zones

| Humidity Level | Comfort | Health Impact |
|---------------|---------|---------------|
| < 30% | Dry | Dry skin, respiratory irritation, static |
| 30-40% | Good | Comfortable for most |
| 40-60% | **Ideal** | **Optimal for health and comfort** |
| 60-70% | Humid | Can feel sticky, mold risk increases |
| > 70% | Very Humid | High mold/mildew risk, uncomfortable |

---

## Arduino Setup Reference

### Expected Data Format

Your Arduino must send one JSON object per line:
```
{"humidity":56.00,"dht_temperature":23.40,"lm35_temperature":24.93,"thermistor_temperature":22.73}
```

### Sample Arduino Code

```cpp
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define LM35_PIN A0
#define THERMISTOR_PIN A1

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float humidity = dht.readHumidity();
  float dhtTemp = dht.readTemperature();
  
  int lm35Reading = analogRead(LM35_PIN);
  float lm35Temp = (lm35Reading * 5.0 / 1024.0) * 100;
  
  int thermistorReading = analogRead(THERMISTOR_PIN);
  float thermistorTemp = /* your thermistor calculation */;
  
  // IMPORTANT: Build JSON once, then write it as a single line
  char payload[128];
  int written = snprintf(
    payload,
    sizeof(payload),
    "{\"humidity\":%.2f,\"dht_temperature\":%.2f,\"lm35_temperature\":%.2f,\"thermistor_temperature\":%.2f}",
    humidity,
    dhtTemp,
    lm35Temp,
    thermistorTemp
  );

  if (written > 0 && written < (int)sizeof(payload)) {
    Serial.println(payload);
  }
  
  delay(1000);  // Send every second
}
```

---

## What's Next?

After basic setup, consider:

1. **Run 24/7**: Set up bot to run as system service (systemd on Linux)
2. **Monitor logs**: Check for connection issues or errors
3. **Backup settings**: Your database is in `data/bot.db` - back it up regularly
4. **Add more users**: Each user can have their own threshold settings
5. **Expand features**: Temperature alerts, historical data, graphs (future versions)

---

## Getting Help

**Bot not working?**
1. Check console logs for error messages
2. Verify Arduino is connected and sending data
3. Confirm `.env` settings are correct
4. Try `/start` command to reinitialize

**Need support?**
- Check documentation in `specs/001-arduino-sensor-monitoring/`
- Review logs in console output
- Test Arduino separately in Arduino IDE serial monitor

**Feature requests or bugs?**
- Document in project issues
- Include: what you tried, what happened, what you expected
