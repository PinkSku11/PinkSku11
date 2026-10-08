// futurometer — an ESP32 fetches the readout's /api/state and shows the lead in nanoseconds
// on a TM1637 6-digit (or 4-digit) 7-segment module; swap the display driver for Nixie tubes.
//
// UNTESTED ON HARDWARE: written as a starting point.  Libraries: ArduinoJson, TM1637Display.
// Wiring: TM1637 CLK -> GPIO 22, DIO -> GPIO 21, VCC 3.3 V, GND.

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TM1637Display.h>

const char* WIFI_SSID = "lodge-wifi";
const char* WIFI_PASS = "********";
const char* STATE_URL = "http://192.168.1.50:8080/api/state";   // the Pi running `greylock serve`
const unsigned long REFRESH_MS = 60UL * 1000UL;

TM1637Display display(22, 21);

void setup() {
  Serial.begin(115200);
  display.setBrightness(5);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(250); Serial.print("."); }
  Serial.println("\nwifi ok");
}

void loop() {
  HTTPClient http;
  http.begin(STATE_URL);
  int code = http.GET();
  if (code == 200) {
    // the state JSON is large (daily series); filter to the summary only
    StaticJsonDocument<256> filter;
    filter["summary"]["lead_total_ns"] = true;
    filter["summary"]["sigma_from_prediction"] = true;
    DynamicJsonDocument doc(2048);
    DeserializationError err = deserializeJson(doc, http.getStream(), DeserializationOption::Filter(filter));
    if (!err && doc["summary"]["lead_total_ns"].is<float>()) {
      long lead = lround(doc["summary"]["lead_total_ns"].as<float>());
      Serial.printf("lead %ld ns (%.1f sigma from prediction)\n", lead, doc["summary"]["sigma_from_prediction"].as<float>());
      display.showNumberDec(lead % 10000, false);   // 4 digits; a 6-digit module shows lead % 1000000
    } else {
      Serial.println("no summary yet (calibrating?)");
      display.showNumberDec(0);
    }
  } else {
    Serial.printf("http %d\n", code);
  }
  http.end();
  delay(REFRESH_MS);
}
