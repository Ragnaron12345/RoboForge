# Wiring.md – Hund-Roboter

## Projektübersicht

Das Projekt „Hund“ ist ein interaktiver Roboter, der auf einem Arduino Mega basiert. Er simuliert ein Haustier mit Bewegung, Lichteffekten, Kamera und einem OLED-Display als „Gesicht“. Die Hardware ist modular aufgebaut, wobei alle Module über I²C oder SPI an den Controller angeschlossen sind. Die Steuerung erfolgt über ein Arduino Mega (ATmega2560), das alle Module steuert und Eingaben verarbeitet.

---

## Hardware-Komponenten und Anschlüsse

### 1. Arduino Mega (ATmega2560)

- Controller: Arduino Mega (ATmega2560)
- Versorgung: 12V Akku über Spannungsregler (z. B. LM7805 für 5V, LM317 für 3.3V)
- Anschlüsse:
  - I²C: SDA (Pin 20), SCL (Pin 21)
  - SPI: MISO (Pin 50), MOSI (Pin 51), SCK (Pin 52), SS (Pin 53)
  - PWM-Pins für Motoren und LEDs
  - Serielle Schnittstellen (UART) für Debugging

---

### 2. OLED-Display (128x64 Pixel, I²C)

- Typ: SSD1306 (I²C-Anschluss)
- Versorgung: 3.3V (über Spannungsregler)
- Anschlüsse:
  - VCC → 3.3V
  - GND → gemeinsame Masse
  - SDA → Pin 20 (I²C)
  - SCL → Pin 21 (I²C)

---

### 3. Kamera (OV7670)

- Typ: OV7670 (I²C- und Parallel-Schnittstelle)
- Versorgung: 3.3V (über Spannungsregler)
- Anschlüsse:
  - VCC → 3.3V
  - GND → gemeinsame Masse
  - SDA → Pin 20 (I²C)
  - SCL → Pin 21 (I²C)
  - PCLK, HREF, VSYNC, D0–D7 → an digitale Pins (z. B. 2–9)
  - XCLK → an Pin 10 (über Taktgenerator)

---

### 4. Bewegungsmodule (Motoren)

- Motoren: 2 DC-Motoren
- Treiber: L298N oder TB6612FNG
- Versorgung:
  - Logikstrom: 5V (von Arduino)
  - Motorstrom: 12V Akku (extern)
- Anschlüsse:
  - Motor A → OUT1, OUT2 (Treiber)
  - Motor B → OUT3, OUT4 (Treiber)
  - Enable → PWM-Pin (z. B. 9, 10)
  - IN1–IN4 → digitale Pins (z. B. 2, 3, 4, 5)
  - GND → gemeinsame Masse (zwischen Logik und Motorstrom)

---

### 5. LEDs (Lichteffekte)

- Typ: WS2812B oder einfache LEDs
- Versorgung: 5V (über Spannungsregler)
- Anschlüsse:
  - Daten → Pin 6 (z. B. für WS2812B)
  - VCC → 5V
  - GND → gemeinsame Masse

---

### 6. Sensoren

#### a) Bewegungssensor (PIR)

- Typ: HC-SR501
- Versorgung: 5V
- Anschlüsse:
  - VCC → 5V
  - GND → gemeinsame Masse
  - OUT → digitaler Pin (z. B. 7)

#### b) Taster

- Typ: mechanische Taster
- Anschlüsse:
  - Taster 1 → digitaler Pin (z. B. 8)
  - Taster 2 → digitaler Pin (z. B. 11)
  - GND → gemeinsame Masse

---

### 7. Spannungsversorgung

- Hauptstromversorgung: 12V LiPo-Akku
- Spannungsregler:
  - LM7805 → 5V für Logik (Arduino, Sensoren, LEDs)
  - LM317 → 3.3V für OLED, Kamera
- Gemeinsame Masse: Alle Module (Motor, Logik, Sensoren, Display) teilen eine gemeinsame GND-Leitung

---

## Wokwi-Schaltplan

Ein Wokwi-Schaltplan wird als `wokwi/diagram.json` erzeugt, um die elektrische Verkabelung visuell darzustellen. Die Module sind wie folgt in Wokwi konfiguriert:

- Arduino Mega (ATmega2560)
- OLED Display (SSD1306)
- Kamera (OV7670)
- L298N Motor-Treiber
- WS2812B LEDs
- PIR-Sensor
- Taster
- Spannungsregler (LM7805, LM317)

---

## Wichtige Hinweise

- Gemeinsame Masse: Alle Module (Motor, Logik, Sensoren, Display) müssen über eine gemeinsame GND-Leitung verbunden sein.
- Motorstrom: Der Motorstrom wird über eine externe 12V-Versorgung geliefert, die vom Arduino getrennt ist. Die GND-Leitungen müssen dennoch miteinander verbunden sein.
- Pegelprüfung: Die Logikmodule (z. B. Arduino) arbeiten mit 5V, Sensoren (z. B. Kamera) benötigen 3.3V. Es ist wichtig, Spannungsregler und Pegelwandler zu verwenden.
- Datenblätter: Für alle Module sollten die Datenblätter herangezogen werden, um die korrekten Spannungen, Stromwerte und Pinbelegungen zu überprüfen.

---

## Zusammenfassung

Die Hardware des Hund-Roboters ist modular aufgebaut und über I²C und SPI an den Arduino Mega angeschlossen. Die Stromversorgung ist getrennt in Logik- und Motorstrom aufgeteilt, wobei eine gemeinsame Masse für alle Module verwendet wird. Die Module sind in Wokwi als `wokwi/diagram.json` dargestellt und dienen als Grundlage für die Projektplanung und Simulation.

--- 

*Dieses Wiring-Dokument dient als didaktische Anleitung zur elektrischen Verkabelung und soll als Grundlage für die Entwicklung eines funktionsfähigen Roboters dienen.*

---
> Hinweis: Dieser Inhalt wurde lokal mit RoboForge Local erzeugt. Er ist eine Lern- und Entwurfsvorlage und muss vor realer Hardware, Druck oder Abgabe geprüft werden.
