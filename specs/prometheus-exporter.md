# Home sensors exporter specification

## Scope

- Retain the DHT sensor and replace LM35/thermistor readings with SCD41.
- Accept newline-delimited, sensor-grouped JSON from Arduino at 115200 baud.
- Expose every DHT and SCD41 measurement to Prometheus.
- Optionally publish complete readings to MQTT without making MQTT a dependency of metrics.
- Use Grafana for dashboards, alert rules, and direct Telegram notification delivery.
- Remove the application Telegram bot, MCP API, PostgreSQL storage, migrations, and their
  configuration.

## Serial contract

A reading uses this grouped form:

```json
{
  "dht": {
    "temperature_celsius": 23.4,
    "humidity_percent": 48.1
  },
  "scd41": {
    "co2_ppm": 812,
    "temperature_celsius": 24.1,
    "humidity_percent": 46.8
  }
}
```

Any measurement may be `null` when that sensor is unavailable. The reading is accepted when at
least one measurement is valid; unavailable Prometheus series are removed and MQTT preserves
the null fields. Firmware status objects contain a non-empty `status` string. Invalid readings
are discarded and counted. The exporter adds a UTC `observed_at` timestamp after validation.

## Operations

The exporter reconnects to serial input with capped exponential backoff. Prometheus remains
available during Arduino or MQTT outages and exports connection/error health metrics. MQTT
messages use retained QoS 1 delivery and preserve the grouped sensor structure.

The local Compose topology contains the exporter, Prometheus, Grafana, and Mosquitto. Grafana
provisions the Prometheus data source and overview dashboard. Telegram credentials and alert
thresholds are configured in Grafana so secrets do not enter this repository.
