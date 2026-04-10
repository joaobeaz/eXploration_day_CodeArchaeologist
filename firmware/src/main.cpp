#include <Arduino.h>
#include <ArduinoJson.h>



// Built-in LED pin on ESP32-DevKit
#define LED_PIN 2

void setup() {
    // Initialize the LED pin as an output
    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    // Turn LED on
    digitalWrite(LED_PIN, HIGH);
    delay(1000);  // Wait 1 second
    
    // Turn LED off
    digitalWrite(LED_PIN, LOW);
    delay(1000);  // Wait 1 second
}
