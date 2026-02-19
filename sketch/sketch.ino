#include <Arduino.h>
#include <DHT.h>
#include <math.h>

// -------------------- Pins / Sensors --------------------
#define DHT_PIN 4
#define DHT_TYPE DHT11       // change to DHT22 if you use that
#define LM35_PIN A0
#define THERMISTOR_PIN A1

DHT dht(DHT_PIN, DHT_TYPE);

// -------------------- Constants --------------------
// If you want better LM35 accuracy, measure your board Vcc and set this.
// For a USB-powered Uno it might be ~4.8-5.1V.
const float ADC_VREF_mV = 5000.0f;
const float ADC_RESOLUTION = 1024.0f;

// Thermistor parameters (as in your sketch)
const float THERMISTOR_FIXED_RESISTOR = 10000.0f; // ohms
const float THERMISTOR_NOMINAL_RESISTANCE = 10000.0f; // R0 at 25C, ohms
const float THERMISTOR_NOMINAL_TEMPERATURE = 25.0f;   // °C
const float THERMISTOR_BETA = 3950.0f;                // Beta value

// -------------------- Helpers --------------------
static bool isValidFloat(float v) {
  // NaN check: NaN is the only float that is not equal to itself
  if (v != v) return false;
  // Simple sanity for DHT values; adjust if needed
  return true;
}

static float read_lm35_temperature_c(bool &ok) {
  int adc = analogRead(LM35_PIN);
  // Convert ADC -> mV -> °C (LM35 = 10 mV/°C)
  float mV = (adc * ADC_VREF_mV) / ADC_RESOLUTION;
  float tempC = mV / 10.0f;

  ok = true; // analogRead always returns a number; you can add range checks if desired
  return tempC;
}

static float read_thermistor_temperature_c(bool &ok) {
  int Vo = analogRead(THERMISTOR_PIN);

  // Protect against extremes (avoid division by zero / log nonsense)
  if (Vo <= 0 || Vo >= 1023) {
    ok = false;
    return NAN;
  }

  // Voltage divider: Vout = Vcc * (R_therm / (R_fixed + R_therm))
  // Solve for R_therm:
  float R_therm = THERMISTOR_FIXED_RESISTOR * ( (1023.0f / (float)Vo) - 1.0f );
  if (R_therm <= 0.0f) {
    ok = false;
    return NAN;
  }

  // Beta equation:
  // 1/T = 1/T0 + (1/B) * ln(R/R0)
  float T0 = THERMISTOR_NOMINAL_TEMPERATURE + 273.15f;
  float invT = (1.0f / T0) + (1.0f / THERMISTOR_BETA) * log(R_therm / THERMISTOR_NOMINAL_RESISTANCE);
  if (invT <= 0.0f) {
    ok = false;
    return NAN;
  }

  float tempK = 1.0f / invT;
  float tempC = tempK - 273.15f;

  ok = true;
  return tempC;
}

static void print_json_reading(float humidity, bool humOk,
                               float dhtTemp,  bool dhtOk,
                               float lm35Temp, bool lmOk,
                               float thermTemp, bool thermOk) {
  Serial.print(F("{\"humidity\":"));
  if (humOk && isValidFloat(humidity)) Serial.print(humidity, 2);
  else Serial.print(F("null"));

  Serial.print(F(",\"dht_temperature\":"));
  if (dhtOk && isValidFloat(dhtTemp)) Serial.print(dhtTemp, 2);
  else Serial.print(F("null"));

  Serial.print(F(",\"lm35_temperature\":"));
  if (lmOk && isValidFloat(lm35Temp)) Serial.print(lm35Temp, 2);
  else Serial.print(F("null"));

  Serial.print(F(",\"thermistor_temperature\":"));
  if (thermOk && isValidFloat(thermTemp)) Serial.print(thermTemp, 2);
  else Serial.print(F("null"));

  Serial.println(F("}"));
}

// -------------------- Arduino --------------------
void setup() {
  Serial.begin(9600);
  dht.begin();

  // Optional: a short boot message
  Serial.println(F("{\"status\":\"boot\"}"));
}

void loop() {
  // DHT reads can be slow; DHT11 often needs ~1-2s between reads
  delay(2000);

  bool humOk = true, dhtOk = true, lmOk = true, thermOk = true;

  float humidity = dht.readHumidity();
  float dhtTemp = dht.readTemperature(); // °C

  if (humidity != humidity) humOk = false; // NaN
  if (dhtTemp != dhtTemp) dhtOk = false;   // NaN

  float lm35Temp = read_lm35_temperature_c(lmOk);
  float thermTemp = read_thermistor_temperature_c(thermOk);

  print_json_reading(humidity, humOk, dhtTemp, dhtOk, lm35Temp, lmOk, thermTemp, thermOk);
}
