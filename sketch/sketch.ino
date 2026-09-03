#include <Arduino.h>
#include <DHT.h>
#include <SensirionI2cScd4x.h>
#include <Wire.h>

#define DHT_PIN 4
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);
SensirionI2cScd4x scd41;

static void print_float_or_null(float value, bool valid) {
  if (valid) {
    Serial.print(value, 1);
  } else {
    Serial.print(F("null"));
  }
}

static void print_reading(float dht_temperature, float dht_humidity,
                          bool dht_valid, uint16_t co2,
                          float scd41_temperature, float scd41_humidity,
                          bool scd41_valid) {
  Serial.print(F("{\"dht\":{\"temperature_celsius\":"));
  print_float_or_null(dht_temperature, dht_valid);
  Serial.print(F(",\"humidity_percent\":"));
  print_float_or_null(dht_humidity, dht_valid);
  Serial.print(F("},\"scd41\":{\"co2_ppm\":"));
  if (scd41_valid) {
    Serial.print(co2);
  } else {
    Serial.print(F("null"));
  }
  Serial.print(F(",\"temperature_celsius\":"));
  print_float_or_null(scd41_temperature, scd41_valid);
  Serial.print(F(",\"humidity_percent\":"));
  print_float_or_null(scd41_humidity, scd41_valid);
  Serial.println(F("}}"));
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  dht.begin();
  scd41.begin(Wire, SCD41_I2C_ADDR_62);
  scd41.stopPeriodicMeasurement();
  delay(500);
  scd41.startPeriodicMeasurement();
  Serial.println(F("{\"status\":\"started\"}"));
}

void loop() {
  uint16_t co2 = 0;
  float scd41_temperature = 0.0;
  float scd41_humidity = 0.0;
  int16_t error = scd41.readMeasurement(
      co2, scd41_temperature, scd41_humidity);
  float dht_temperature = dht.readTemperature();
  float dht_humidity = dht.readHumidity();
  bool dht_valid = !isnan(dht_temperature) && !isnan(dht_humidity);
  bool scd41_valid = error == 0 && co2 != 0;

  print_reading(dht_temperature, dht_humidity, dht_valid, co2,
                scd41_temperature, scd41_humidity, scd41_valid);
  delay(5000);
}
