/*
  Projekt: Hund-Roboter
  Zweck: Grundgerüst für einen beweglichen, lichtstarken Haustier-ähnlichen Roboter auf Basis von Arduino Mega.
  Warnung: Bitte prüfe den Pinout und die Hardware vor dem Upload!
  Hardwareanforderungen:
    - 2 DC-Motoren mit Treiber (z. B. L298N)
    - 8 LEDs (z. B. als Beleuchtung)
    - OLED-Display (SSD1306, I²C)
    - PIR-Bewegungssensor
    - Taster für manuelle Steuerung
    - Kamera (OV7670) - TODO: Implementierung fehlt
    - WLAN-Modul (ESP32) - TODO: Implementierung fehlt

  Funktionen:
    - Bewegung (vorwärts, rückwärts, links/rechts)
    - Lichteffekte (LEDs)
    - OLED-Display als „Gesicht“
    - Eingabeverarbeitung (Taster, Sensor)
*/

#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>

// Pin-Definitionen
#define MOTOR_LEFT_A     2
#define MOTOR_LEFT_B     3
#define MOTOR_RIGHT_A    4
#define MOTOR_RIGHT_B    5
#define LED_PIN          6
#define PIR_PIN          7
#define BUTTON_PIN       8

// OLED Display
#define SCREEN_WIDTH     128
#define SCREEN_HEIGHT    64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Globale Variablen
bool motorRunning = false;
bool ledState = false;
int buttonState = 0;
int lastButtonState = 0;

void setup() {
  Serial.begin(9600);
  setupHardware();
  printStatus();
}

void loop() {
  readInputs();
  updateMotors();
  updateDisplay();
  delay(100);
}

void setupHardware() {
  // Motorpins als Ausgang
  pinMode(MOTOR_LEFT_A, OUTPUT);
  pinMode(MOTOR_LEFT_B, OUTPUT);
  pinMode(MOTOR_RIGHT_A, OUTPUT);
  pinMode(MOTOR_RIGHT_B, OUTPUT);

  // LED und Taster
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);

  // OLED Display initialisieren
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("OLED-Display konnte nicht initialisiert werden"));
    for (;;); // Fehler, Programm stoppt
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Hund-Roboter");
  display.display();
}

void readInputs() {
  // Taster-Eingabe
  buttonState = digitalRead(BUTTON_PIN);
  if (buttonState != lastButtonState) {
    if (buttonState == HIGH) {
      motorRunning = !motorRunning; // Toggle Motor
    }
  }
  lastButtonState = buttonState;

  // PIR-Sensor
  if (digitalRead(PIR_PIN) == HIGH) {
    ledState = true;
    digitalWrite(LED_PIN, HIGH);
  } else {
    ledState = false;
    digitalWrite(LED_PIN, LOW);
  }
}

void updateMotors() {
  if (motorRunning) {
    // Vorwärts fahren
    digitalWrite(MOTOR_LEFT_A, HIGH);
    digitalWrite(MOTOR_LEFT_B, LOW);
    digitalWrite(MOTOR_RIGHT_A, HIGH);
    digitalWrite(MOTOR_RIGHT_B, LOW);
  } else {
    stopMotors();
  }
}

void stopMotors() {
  digitalWrite(MOTOR_LEFT_A, LOW);
  digitalWrite(MOTOR_LEFT_B, LOW);
  digitalWrite(MOTOR_RIGHT_A, LOW);
  digitalWrite(MOTOR_RIGHT_B, LOW);
}

void updateDisplay() {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Hund-Roboter");
  display.print("Motor: ");
  display.println(motorRunning ? "AN" : "AUS");
  display.print("LED: ");
  display.println(ledState ? "AN" : "AUS");
  display.print("PIR: ");
  display.println(digitalRead(PIR_PIN) == HIGH ? "Bewegung" : "Still");
  display.display();
}

void printStatus() {
  Serial.println("Hund-Roboter gestartet");
  Serial.println("Motor: " + String(motorRunning ? "AN" : "AUS"));
  Serial.println("LED: " + String(ledState ? "AN" : "AUS"));
}

// TODO: Kamera-Implementierung (OV7670)
// TODO: WLAN-Implementierung (ESP32)

---
> Hinweis: Dieser Inhalt wurde lokal mit RoboForge Local erzeugt. Er ist eine Lern- und Entwurfsvorlage und muss vor realer Hardware, Druck oder Abgabe geprüft werden.
