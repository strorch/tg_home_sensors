#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11

#define ADC_VREF_mV    5000.0
#define ADC_RESOLUTION 1023.0

#define PIN_LM35 A0
const int ThermistorPin = A1;

float R1 = 10000.0;
int Vo;
float logR2, R2, T;

float c1 = 1.009249522e-03;
float c2 = 2.378405444e-04;
float c3 = 2.019202697e-07;

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

bool read_dht(float &humidity, float &temperature) {
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    return false;
  }

  return true;
}

bool read_lm35(float &temperature) {
  int adcVal = analogRead(PIN_LM35);
  float milliVolt = adcVal * (ADC_VREF_mV / ADC_RESOLUTION);
  temperature = milliVolt / 10.0;
  return true;
}

bool read_thermistor(float &temperature) {
  Vo = analogRead(ThermistorPin);

  if (Vo <= 0 || Vo >= 1023) {
    return false;
  }

  // This assumes: VCC--R1--(ADC)--NTC--GND
  R2 = R1 * (1023.0 / (float)Vo - 1.0);

  logR2 = log(R2);
  T = 1.0 / (c1 + c2*logR2 + c3*logR2*logR2*logR2);
  temperature = T - 273.15;
  return true;
}

void print_json_reading(float humidity, float dhtTemp, float lm35Temp, float thermistorTemp) {
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
}

void loop() {
  float humidity;
  float dhtTemp;
  float lm35Temp;
  float thermistorTemp;

  bool hasDht = read_dht(humidity, dhtTemp);
  bool hasLm35 = read_lm35(lm35Temp);
  bool hasThermistor = read_thermistor(thermistorTemp);

  if (hasDht && hasLm35 && hasThermistor) {
    print_json_reading(humidity, dhtTemp, lm35Temp, thermistorTemp);
  }

  delay(2000);
}
