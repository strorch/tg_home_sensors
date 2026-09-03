# Arduino home sensors exporter

This project reads grouped JSON from an Arduino, exports every DHT and SCD41 value to
Prometheus, and can publish the complete reading to MQTT. Grafana provides dashboards and
alerting, including direct Telegram notifications.

The application Telegram bot, MCP server, database, LM35, and thermistor support have been
removed.

## Data flow

```text
DHT + SCD41 -> Arduino JSON -> serial exporter -> Prometheus -> Grafana -> Telegram alerts
                                      |
                                      +----------> MQTT (optional)
```

The exporter exposes:

| Sensor | Values |
| --- | --- |
| DHT | temperature in °C, relative humidity in % |
| SCD41 | CO₂ in ppm, temperature in °C, relative humidity in % |

## Arduino firmware

Flash [`sketch/sketch.ino`](sketch/sketch.ino). It expects a DHT11 data pin on digital pin 4
and an SCD41 on the I²C bus. Install the Arduino libraries `DHT sensor library`,
`Sensirion I2C SCD4x`, and their dependencies first.

The sketch emits one compact JSON object every five seconds at 115200 baud:

```json
{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1},"scd41":{"co2_ppm":812,"temperature_celsius":24.1,"humidity_percent":46.8}}
```

Startup status is also valid JSON, for example `{"status":"started"}`. Unavailable measurements
are emitted as `null`; the exporter still publishes every available value from the other sensor:

```json
{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1},"scd41":{"co2_ppm":null,"temperature_celsius":null,"humidity_percent":null}}
```

Unavailable Prometheus series are removed instead of retaining stale values, while MQTT keeps
the explicit `null` fields.

For an Arduino Uno, connect the SCD41 to `3.3V`, `GND`, `SDA/A4`, and `SCL/A5`. Leave the DHT
connected on pin 4. The old LM35 and thermistor connections on `A0` and `A1` are no longer used.

## Local Python run

```bash
cp .env.example .env
uv sync
uv run python -m src.main
```

Set `SERIAL_PORT` in `.env` to the Arduino port, such as `/dev/ttyACM0`. Useful endpoints and
topics are:

- Prometheus exposition: `http://localhost:8000/metrics`
- MQTT topic: `home/sensors/environment` (retained, QoS 1)

MQTT uses the same grouped structure and adds the exporter timestamp:

```json
{"dht":{"temperature_celsius":23.4,"humidity_percent":48.1},"scd41":{"co2_ppm":812,"temperature_celsius":24.1,"humidity_percent":46.8},"observed_at":"2026-09-02T12:00:00Z"}
```

Set `MQTT_ENABLED=false` when MQTT is not needed. An unavailable MQTT broker does not stop
Prometheus collection.

## Local Docker stack

The base stack starts the exporter, Prometheus, Grafana, and Mosquitto without requiring a
serial device to exist:

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Grafana: `http://localhost:3000` (`admin` / `admin` by default)
- Prometheus: `http://localhost:9090`
- exporter metrics: `http://localhost:8000/metrics`
- Mosquitto: `localhost:1883`

`MQTT_HOST_PORT` changes the host-facing Mosquitto port without changing the broker port used
inside the Compose network.

The `Home sensors` Grafana dashboard and Prometheus data source are provisioned automatically.
To give the exporter access to a Linux serial device, use the hardware override:

```bash
docker compose -f docker-compose.yml -f docker-compose.hardware.yml up --build
```

The Docker stack enables MQTT by default. To inspect its payloads:

```bash
docker compose exec mosquitto \
  mosquitto_sub -h localhost -t home/sensors/environment -v
```

## Prometheus metrics

| Metric | Labels | Meaning |
| --- | --- | --- |
| `home_sensor_temperature_celsius` | `sensor=dht|scd41` | both temperatures |
| `home_sensor_humidity_percent` | `sensor=dht|scd41` | both humidity readings |
| `home_sensor_co2_ppm` | `sensor=scd41` | SCD41 CO₂ concentration |
| `home_sensor_last_reading_timestamp_seconds` | none | last complete reading time |
| `home_sensor_serial_connected` | none | Arduino connection state |
| `home_sensor_parse_errors_total` | none | rejected serial messages |
| `home_sensor_read_errors_total` | none | serial I/O failures |
| `home_sensor_mqtt_connected` | none | MQTT connection state |
| `home_sensor_mqtt_publish_errors_total` | none | MQTT publication failures |

## Grafana Telegram alerts

Telegram delivery is owned entirely by Grafana; there is no Telegram code or token in the
exporter.

1. In Grafana, open **Alerts & IRM → Alerting → Notification configuration → Contact points**.
2. Add a **Telegram** contact point using the bot API token and destination chat ID, then use
   **Test** before saving.
3. Create Grafana-managed alert rules from Prometheus queries and assign that contact point.

Good initial alert expressions are:

```promql
home_sensor_co2_ppm{sensor="scd41"} > 1000
home_sensor_temperature_celsius{sensor=~"dht|scd41"} < 10 or home_sensor_temperature_celsius{sensor=~"dht|scd41"} > 30
home_sensor_humidity_percent{sensor=~"dht|scd41"} < 30 or home_sensor_humidity_percent{sensor=~"dht|scd41"} > 70
time() - home_sensor_last_reading_timestamp_seconds > 30
home_sensor_serial_connected == 0
up{job="home-sensors"} == 0
absent(home_sensor_co2_ppm{sensor="scd41"})
```

Adjust thresholds and pending periods in Grafana for the room being monitored. Keep the bot
token out of version control; enter it in Grafana's secured contact-point field.

## Development checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest --cov=src
docker compose config --quiet
```
