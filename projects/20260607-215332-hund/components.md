# Komponenten

## Controller
### Arduino Mega (ATmega2560)
Zweck: Zentrale Steuerung des Roboters mit ausreichend I/O-Pins für diverse Module.
Warum passend: Die Mega bietet mehr Pins als kleinere Controller wie Uno, was für die Ansteuerung von LEDs, Motoren, Kamera und Display erforderlich ist.
Zu prüfen: Kompatibilität der verwendeten Libraries mit der Mega-Plattform.
Hinweis: Für die Kommunikation mit Sensoren und Aktoren über I²C/SPI muss die korrekte Pinbelegung berücksichtigt werden.

## Energieversorgung
### LiPo-Akku (12 V)
Zweck: Stromversorgung des gesamten Roboters.
Warum passend: Hohe Energiekapazität und geringes Gewicht für tragbare Anwendungen.
Zu prüfen: Passende Spannungsregler (z. B. 5 V und 3.3 V) zur Versorgung der Module.
Hinweis: Akku-Ladefunktion oder Austauschmöglichkeit sollte im Design berücksichtigt werden.

## Sensorik/Kamera
### Kamera (OV7670 oder ähnlich)
Zweck: Erkennung von Bewegungen und Aufnahme von Bildern.
Warum passend: Geringe Kosten, einfache Ansteuerung über I²C, geeignet für grundlegende Bildverarbeitung.
Zu prüfen: Kompatibilität mit Arduino Mega und benötigte Speicherkapazität.
Hinweis: Die Kamera wird nur für grundlegende Funktionen genutzt, keine fortschrittliche Bildverarbeitung.

## Motoren/Aktoren
### DC-Motoren (zwei)
Zweck: Bewegung des Roboters.
Warum passend: Einfache Ansteuerung über Treiber (z. B. L298N), geeignet für einfache Bewegung.
Zu prüfen: Passende Treiber für die benötigte Stromstärke.
Hinweis: Die Bewegung ist auf Vorwärts-/Rückwärts-Bewegungen begrenzt.

## Motoren/Aktoren
### LEDs (zahlreiche)
Zweck: Lichteffekte zur Visualisierung des Roboters.
Warum passend: Einfache Ansteuerung über digitale Pins, viele Farben und Effekte möglich.
Zu prüfen: Stromaufnahme und Passung zur Spannungsversorgung.
Hinweis: LEDs sind statisch, keine dynamischen Effekte wie PWM oder Farbwechsel.

## Motoren/Aktoren
### OLED-Display (128x64 Pixel, I²C)
Zweck: Anzeige als „Gesicht“ des Roboters.
Warum passend: Kleine Größe, hohe Auflösung, einfache Ansteuerung über I²C.
Zu prüfen: Kompatibilität mit Arduino Mega und verwendete Bibliothek.
Hinweis: Anzeige ist auf einfache Grafiken und Texte begrenzt.

## Gehäuse/Befestigung
### Roboter-Gehäuse (3D-gedruckt oder aus Holz)
Zweck: Struktur und Form des Hundes.
Warum passend: Einfache Gestaltung, Anpassung an die benötigten Module.
Zu prüfen: Passform der Module im Gehäuse, Stabilität und Schutz.
Hinweis: Das Gehäuse sollte leicht zu reparieren und zu erweitern sein.

## Zusatzteile
### Taster/Knöpfe
Zweck: Manuelle Steuerung des Roboters.
Warum passend: Einfache und zuverlässige Eingabemöglichkeit.
Zu prüfen: Anzahl und Position der Taster im Gehäuse.
Hinweis: Taster können zur Steuerung von Funktionen wie Licht, Bewegung oder Display genutzt werden.

## Zusatzteile
### PIR-Bewegungssensor
Zweck: Erkennung von Bewegungen in der Umgebung.
Warum passend: Einfache Ansteuerung, geringe Kosten, gut für grundlegende Interaktion.
Zu prüfen: Sensorposition und Reichweite im Gehäuse.
Hinweis: Sensor wird zur Aktivierung oder Steuerung des Roboters genutzt.

## Zusatzteile
### Spannungsregler (5 V und 3.3 V)
Zweck: Versorgung der Module mit passender Spannung.
Warum passend: Ermöglicht gleichzeitige Nutzung verschiedener Module mit unterschiedlichen Spannungen.
Zu prüfen: Leistungsfähigkeit des Reglers für die benötigte Stromstärke.
Hinweis: Regler sollten über Wärmeableitung verfügen, um Überlastung zu vermeiden.

---
> Hinweis: Dieser Inhalt wurde lokal mit RoboForge Local erzeugt. Er ist eine Lern- und Entwurfsvorlage und muss vor realer Hardware, Druck oder Abgabe geprüft werden.
