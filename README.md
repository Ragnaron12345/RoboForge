# RoboForge

**Lokale Web-Anwendung für AI-unterstützte Robotik-Lernprojekte**

Robo Forge ist eine lokale Web-Anwendung, die Schülern und Studierenden hilft, aus einer ersten Robotik-Idee automatisch eine strukturierte Projektdokumentation zu erstellen.
Das System nutzt eine lokale Sprachmodell-Umgebung über Ollama und erzeugt daraus Projektdateien, Schaltplan-Grundlagen, Code-Skelett, OpenSCAD-Modelle und einen PDF-Bericht.

Der Fokus liegt nicht darauf, fertige Industrie-Hardware automatisch zu entwickeln. Robo Forge erstellt bewusst einen überprüfbaren Lern- und Projektentwurf, der anschließend manuell kontrolliert und verbessert werden muss.

---

## Idee des Projekts

Moderne Sprachmodelle können viel Text und Code erzeugen. In echten Projekten reicht ein Chatfenster aber oft nicht aus. Wichtig ist das Umfeld um das Modell:

* klare Projektstruktur
* vorbereitete Prompt-Templates
* lokale Dateien
* ein wiederholbarer Workflow
* Export von Dokumentation
* manuelle Kontrolle durch den Nutzer

Robo Forge setzt genau dort an. Die lokale KI wird nicht einfach als Chatbot benutzt, sondern als Teil eines strukturierten Workflows für Robotik-Projekte.

---

## Hauptfunktionen

Robo Forge kann aus einem kurzen Projekttitel und einer Beschreibung automatisch mehrere Dateien erzeugen:

* `project_spec.md` — technische Projektspezifikation
* `README.md` — Projektbeschreibung
* `components.md` — Komponentenliste als übersichtliche Karten
* `wiring.md` — Verdrahtungskonzept und Hinweise zur Schaltung
* `code.ino` — Arduino/C++ Lern-Skelett
* `wokwi/diagram.json` — Schaltplan für Wokwi Web
* `wokwi/circuit_profile.json` — Profil der gewählten Elektronik
* `model_profile.json` — Profil der 3D-Modell-Generierung
* `model.scad` — parametrische OpenSCAD-Druckteile
* `printable_parts.md` — Liste der druckbaren Teile
* `report.md` — zusammengefasster Markdown-Bericht
* `report.pdf` — fertiger PDF-Bericht

Alle Dateien werden lokal in einem Projektordner gespeichert und können direkt im Browser geöffnet und bearbeitet werden.

---

## Technischer Überblick

Der Workflow ist bewusst einfach gehalten:

```text
Nutzer
  ↓
FastAPI Web UI
  ↓
Projektordner wird erstellt
  ↓
Prompt-Templates werden ausgefüllt
  ↓
Lokales LLM über Ollama wird aufgerufen
  ↓
Projektdateien werden gespeichert
  ↓
Wokwi-Schaltplan, OpenSCAD-Modell und PDF-Bericht werden erzeugt
```

Wichtige Module:

* `app/main.py` — FastAPI-Routen, Projektverwaltung und Datei-Editor
* `app/llm_adapter.py` — Verbindung zur lokalen Ollama-API
* `app/generator.py` — Hauptpipeline zur Dateigenerierung
* `app/wokwi_exporter.py` — Erzeugung der Wokwi-Dateien
* `app/model_profile.py` — Auswahl und Prüfung des 3D-Modellprofils
* `app/scad_assembler.py` — Erstellung der OpenSCAD-Datei
* `app/report_exporter.py` — Erstellung von `report.md` und `report.pdf`
* `app/card_tools.py` — Umwandlung breiter Tabellen in lesbare Karten
* `app/text_cleanup.py` — Bereinigung unnötiger Markdown-Formatierung

---

## Lokale KI

Standardmäßig ist Robo Forge für folgendes Modell vorbereitet:

```text
qwen3-coder:30b
```

Das Modell läuft lokal über Ollama. Dadurch bleiben die Projektinformationen auf dem eigenen Computer und müssen nicht an einen externen Cloud-Dienst gesendet werden.

Die Modellkonfiguration kann über Umgebungsvariablen angepasst werden:

```bash
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3-coder:30b
```

---

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/Ragnaron12345/RoboForge
cd RoboForge
```

### 2. Virtuelle Umgebung erstellen

Windows PowerShell:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. Ollama-Modell vorbereiten

```bash
ollama pull qwen3-coder:30b
ollama run qwen3-coder:30b
```

### 5. Anwendung starten

```bash
uvicorn app.main:app --reload
```

Danach im Browser öffnen:

```text
http://127.0.0.1:8000
```

---

## Beispiel

Beispiel für einen Projekttitel:

```text
ESP32 Wetterstation mit OLED und DHT22
```

Beispiel für eine Beschreibung:

```text
Eine einfache Wetterstation für ein Lernprojekt. Das System soll mit einem ESP32, einem DHT22-Sensor und einem kleinen OLED-Display aufgebaut werden. Der DHT22 misst Temperatur und Luftfeuchtigkeit, während das OLED-Display die aktuellen Messwerte anzeigt. Für den Aufbau soll ein einfaches Gehäuse mit separater Display-Halterung bzw. einem kleinen Standfuß als OpenSCAD-Modell vorbereitet werden. 
```

Robo Forge erstellt daraus automatisch einen Projektordner mit Dokumentation, Code, Wokwi-Dateien, OpenSCAD-Modell und PDF-Bericht.

---

## Wokwi-Export

Robo Forge erzeugt eine Datei:

```text
wokwi/diagram.json
```

Diese Datei kann in Wokwi Web eingefügt werden. Dafür gibt es im Web-Interface eine eigene Seite zum Kopieren des JSON-Inhalts.

Der Wokwi-Export ist als Lern- und Simulationshilfe gedacht. Er ersetzt keine vollständige elektrische Prüfung.

---

## OpenSCAD-Generierung

Robo Forge erzeugt kein dekoratives 3D-Modell eines fertigen Roboters.
Stattdessen wird eine sogenannte Print Plate erstellt:

```text
model.scad
```

Diese Datei enthält mehrere getrennte, druckbare Teile, zum Beispiel:

* Grundplatte
* Halterungen
* Controller-Tray
* Batteriehalter
* Servo- oder Motorhalter
* Sensorhalter
* Abstandshalter
* optionale Räder oder Greiferteile

Die Teile sind parametrische Lernvorlagen und müssen vor dem echten 3D-Druck überprüft werden.

---

## Grenzen des Projekts

Robo Forge ist ein Lern- und Demonstrationsprojekt. Es ersetzt keine professionelle technische Prüfung.

Wichtig:

* `code.ino` ist ein Code-Skelett, keine finale Firmware.
* `wiring.md` und Wokwi sind Lernhilfen, keine zertifizierte Schaltung.
* `model.scad` ist eine parametrische 3D-Vorlage, kein fertiges Produktions-CAD.
* Alle Spannungen, Ströme, Pinouts, Maße und Bauteile müssen manuell geprüft werden.
* Vor realer Hardware-Nutzung sind Datenblätter und Sicherheitsregeln zu beachten.

---

## Warum lokal?

Die lokale Ausführung hat mehrere Vorteile:

* keine Cloud-Abhängigkeit
* keine API-Kosten pro Anfrage
* mehr Kontrolle über Daten
* gute Demonstrierbarkeit auf eigener Hardware
* geeignet für Lernumgebungen und Experimente

Das Ziel ist nicht nur eine stärkere KI, sondern ein besseres Arbeitsumfeld für die KI.

---

## Mögliche Weiterentwicklung

Mögliche nächste Schritte:

* mehr Wokwi-Schaltplanprofile
* bessere 3D-Modellprofile
* FreeCAD- oder CadQuery-Integration
* KiCad-Export
* automatische Plausibilitätsprüfung von Schaltungen
* Unterstützung mehrerer lokaler Modelle
* Vergleich zwischen lokalen und Cloud-Modellen
* einfachere Installation als Desktop-Anwendung

---

## Projektstatus

Robo Forge ist ein funktionierender MVP / Prototyp für eine Projektpräsentation.
Die Anwendung zeigt, wie lokale KI-Modelle durch ein passendes Umfeld gezielter für technische Lernprojekte eingesetzt werden können.

---

## Lizenz

Dieses Projekt ist als Lern- und Demonstrationsprojekt gedacht.
Eine passende Open-Source-Lizenz kann je nach Veröffentlichungsziel ergänzt werden.

---

## Kontakt

Weitere Informationen, Quellcode und Updates befinden sich im GitHub-Repository.

GitHub: `https://github.com/Ragnaron12345`
LinkedIn: `www.linkedin.com/in/maxim-johannson`
E-Mail: `johannsonmaxim@gmail.com`
