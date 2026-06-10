# Projekt Spezifikation: Hund-Roboter

## Ziel
Das Projekt zielt darauf ab, einen einfachen, funktionsfähigen Roboter zu entwickeln, der als Hund modelliert ist. Der Roboter soll grundlegende Bewegungen, Lichteffekte, eine Kamera und eine Anzeige aufweisen, um die Funktionalität eines Haustiers im robotischen Kontext zu simulieren.

## Robotertyp
Der Roboter ist ein beweglicher, interaktiver Haustier-ähnlicher Roboter. Er ist auf einer einfachen Plattform aufgebaut, die Bewegung und Lichtsteuerung ermöglicht. Die Gestaltung ist an einen Hund angelehnt, wobei die Hauptfunktionen auf die Interaktion mit dem Benutzer ausgerichtet sind.

## Hauptfunktionen
- Bewegung (z. B. Vorwärts, Rückwärts, Drehung)
- Lichteffekte (LEDs)
- Kamera (z. B. zur Erkennung von Bewegungen oder zur Aufnahme von Bildern)
- OLED-Display als „Gesicht“ des Roboters
- Steuerung über Arduino Mega

## Vermutete Architektur
- Zentrale Steuerung durch Arduino Mega
- Hardware-Module für Bewegung, Licht, Kamera und Display sind über I²C oder SPI angeschlossen
- Softwaremodul zur Steuerung der Module und zur Verarbeitung von Eingaben
- Eingabemöglichkeiten über Tasten, Sensoren oder Fernbedienung

## Controller
- Arduino Mega (ATmega2560)
- Verwendung von Libraries zur Steuerung von LEDs, Kamera, Display und Motoren

## Energieversorgung
- Stromversorgung über Akkus (z. B. 12 V LiPo oder AA-Batterien)
- Stromversorgung für verschiedene Module über Spannungsregler (z. B. 5 V und 3.3 V)
- Akku-Ladefunktion oder Austauschmöglichkeit

## Sensorik
- Bewegungssensor (z. B. PIR)
- Kamera (z. B. OV7670 oder ähnlich)
- Taster oder Knöpfe zur manuellen Steuerung
- Eventuell Temperatur- oder Lichtsensor zur Umgebungswahrnehmung

## Aktoren
- Motoren zur Bewegung (z. B. zwei DC-Motoren mit Treiber)
- LEDs zur Beleuchtung
- OLED-Display (z. B. 128x64 Pixel, I²C-Anschluss)
- Eventuell Servos zur Bewegung von Gliedmaßen

## Risiken
- Kompatibilitätsprobleme bei der Ansteuerung von Sensoren und Aktoren
- Stromverbrauch kann die Akkulaufzeit beeinträchtigen
- Softwarefehler bei der Kommunikation zwischen Modulen
- Hardwaredefekte durch falsche Verkabelung oder Überlastung
- Unzureichende Leistung der Kamera oder des Displays

## MVP-Grenzen
- Die Bewegung ist auf einfache Vorwärts-/Rückwärts-Bewegungen begrenzt
- Die Kamera wird nur für grundlegende Funktionen genutzt (keine fortschrittliche Bildverarbeitung)
- Die Lichteffekte sind auf statische LEDs begrenzt
- Das OLED-Display zeigt nur einfache Grafiken oder Texte an
- Die Steuerung ist nicht vollständig autonom, sondern erfordert manuelle Eingriffe

---  
*Dieses Dokument beschreibt die geplanten Funktionen und technischen Annahmen des Projekts. Es dient als Grundlage für die Projektplanung und Präsentation.*


---
> Hinweis: Dieser Inhalt wurde lokal mit RoboForge Local erzeugt. Er ist eine Lern- und Entwurfsvorlage und muss vor realer Hardware, Druck oder Abgabe geprüft werden.
