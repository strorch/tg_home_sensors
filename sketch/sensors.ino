#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11

#define ADC_VREF_mV    5000.0
#define ADC_RESOLUTION 1023.0

#define PIN_LM35 A0
const int ThermistorPin = A1;

float R1 = 10000.0;
int Vo;
float logR2, R2, T, Tc;

float c1 = 1.009249522e-03;
float c2 = 2.378405444e-04;
float c3 = 2.019202697e-07;

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void print_dht() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.print("DHT: read fail  ");
    return;
  }

  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print("%  DHT Temp: ");
  Serial.print(temperature);
  Serial.print("C  ");
}

void print_adc() {
  int adcVal = analogRead(PIN_LM35);
  float milliVolt = adcVal * (ADC_VREF_mV / ADC_RESOLUTION);
  float tempC = milliVolt / 10.0;

  Serial.print("LM35: ");
  Serial.print(tempC);
  Serial.print("C  ");
}

void print_thermistor() {
  Vo = analogRead(ThermistorPin);

  if (Vo <= 0) { Serial.print("Therm: ADC=0"); return; }
  if (Vo >= 1023) { Serial.print("Therm: ADC=1023"); return; }

  // This assumes: VCC--R1--(ADC)--NTC--GND
  R2 = R1 * (1023.0 / (float)Vo - 1.0);

  logR2 = log(R2);
  T = 1.0 / (c1 + c2*logR2 + c3*logR2*logR2*logR2);
  Tc = T - 273.15;

  Serial.print("Therm: ");
  Serial.print(Tc);
  Serial.print("C");
}

void loop() {
  print_dht();
  print_adc();
  print_thermistor();
  Serial.println();
  delay(2000);
}

