# Wokwi-Schaltplan

Dieses Verzeichnis enthält einen generierten Wokwi-Schaltplan für das Projekt.

## Erkannter Schaltungs-Profile
- Projektfamilie: `legged_robot`
- Controller: `arduino_mega`
- Stromversorgung: `external_5v_servo_power`

## Erkannte Komponenten
- servo: 8 × Bein-Servos für 4 Beine; Servo-Aktuator
- mpu6050: 1 × Lagesensor; IMU
- dht22: 1 × Temperatur/Feuchte
- oled: 1 × I2C-Anzeige
- pir: 1 × PIR-Bewegungssensor
- ldr: 1 × Lichtsensor
- led: 1 × Status-LED
- button: 1 × Benutzereingabe

## Hinweise
- Keine zusätzlichen Hinweise.

## Warum kein einzelnes Template?
RoboForge verwendet keinen festen Rover-Schaltplan als Standard. Der Generator erkennt Controller, Mechanik, Sensoren, Aktuatoren und Stromversorgung aus Projekttitel, Beschreibung und `project_spec.md`. Danach wird `diagram.json` aus einzelnen Bauteil-Blöcken zusammengesetzt. Ein Arduino-Roboterarm bleibt deshalb Arduino + Servos, ein Sensor-Dashboard bleibt Controller + Sensoren/Display, und ein Rover bekommt nur dann Motorblöcke, wenn das Projekt wirklich ein Fahrzeug/Rover ist.

## Verwendung
1. Auf der RoboForge-Webseite `diagram.json für Wokwi kopieren` öffnen.
2. JSON kopieren.
3. In Wokwi Web ein Projekt öffnen.
4. Den Inhalt der Datei `diagram.json` komplett ersetzen.

## Grenzen
Der Schaltplan ist eine didaktische Vorlage. Vor echter Hardware müssen Spannung, Strom, Pinout, gemeinsame Masse, Pegel und Datenblätter geprüft werden.
