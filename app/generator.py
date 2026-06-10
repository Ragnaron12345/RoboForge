from __future__ import annotations

from pathlib import Path

from app.card_tools import ensure_card_format
from app.llm_adapter import generate_text
from app.model_profile import build_model_profile, profile_to_json, printable_parts_markdown
from app.scad_assembler import assemble_scad
from app.text_cleanup import cleanup_markdown, strip_code_fence
from app.wokwi_exporter import export_wokwi

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

GENERATION_MODES = [
    ("overview.md", "README.md"),
    ("components.md", "components.md"),
    ("wiring.md", "wiring.md"),
    ("code.md", "code.ino"),
]


def load_prompt_template(template_name: str) -> str:
    return (PROMPTS_DIR / template_name).read_text(encoding="utf-8")


def build_prompt(template_text: str, title: str, description: str, spec: str = "") -> str:
    return (
        template_text.replace("{{ title }}", title.strip())
        .replace("{{ description }}", description.strip())
        .replace("{{ project_spec }}", spec.strip())
    )


def de_notice() -> str:
    return (
        "\n\n---\n"
        "> Hinweis: Dieser Inhalt wurde lokal mit RoboForge Local erzeugt. "
        "Er ist eine Lern- und Entwurfsvorlage und muss vor realer Hardware, Druck oder Abgabe geprüft werden.\n"
    )


def _fallback_spec(title: str, description: str) -> str:
    return f"""# Projektspezifikation

## Projektidee
{title}

## Kurzbeschreibung
{description or 'Keine zusätzliche Beschreibung angegeben.'}

## Ziel des MVP
Ein didaktischer Robotik-Entwurf mit Dokumentation, Bauteilübersicht, Verdrahtung, Code-Skelett, Wokwi-Schaltplan und 3D-Druckvorlage.

## Grenzen
Die erzeugten Inhalte ersetzen keine technische Prüfung. Pinout, Stromversorgung, Datenblätter, mechanische Abmessungen und Sicherheit müssen manuell kontrolliert werden.
"""


def generate_project_files(project_dir: Path, title: str, description: str) -> tuple[list[str], list[str]]:
    generated: list[str] = []
    warnings: list[str] = []

    spec_prompt = build_prompt(load_prompt_template("project_spec.md"), title, description)
    spec = generate_text(spec_prompt, fallback=_fallback_spec(title, description))
    if spec.startswith("Fehler:") or spec.startswith("Ollama"):
        warnings.append(spec)
        spec = _fallback_spec(title, description)
    spec = cleanup_markdown(spec)
    (project_dir / "project_spec.md").write_text(spec + de_notice(), encoding="utf-8")
    generated.append("project_spec.md")

    for template_name, output_name in GENERATION_MODES:
        prompt = build_prompt(load_prompt_template(template_name), title, description, spec)
        fallback = _fallback_for_output(output_name, title, description, spec)
        result = generate_text(prompt, fallback=fallback)
        if result.startswith("Fehler:"):
            warnings.append(f"{output_name}: {result}")
            result = fallback
        if output_name == "code.ino":
            cleaned = strip_code_fence(result)
        else:
            cleaned = cleanup_markdown(result)
        if output_name in {"components.md", "wiring.md"}:
            cleaned = ensure_card_format(cleaned)
        (project_dir / output_name).write_text(cleaned.strip() + de_notice(), encoding="utf-8")
        generated.append(output_name)

    model_files = generate_model_files(project_dir, title, description, spec)
    generated.extend(model_files)

    try:
        generated.extend(export_wokwi(project_dir, title, description, spec))
    except Exception as error:
        warnings.append(f"Wokwi-Dateien konnten nicht erstellt werden: {error}")

    return generated, warnings


def generate_model_files(project_dir: Path, title: str, description: str, spec: str = "") -> list[str]:
    prompt = build_prompt(load_prompt_template("model.md"), title, description, spec)
    llm_json = generate_text(prompt, fallback="")
    profile = build_model_profile(title, description, spec, llm_json)
    (project_dir / "model_profile.json").write_text(profile_to_json(profile), encoding="utf-8")
    (project_dir / "printable_parts.md").write_text(printable_parts_markdown(profile), encoding="utf-8")
    (project_dir / "model.scad").write_text(assemble_scad(profile), encoding="utf-8")
    return ["model_profile.json", "printable_parts.md", "model.scad"]


def _fallback_for_output(output_name: str, title: str, description: str, spec: str) -> str:
    if output_name == "README.md":
        return f"""# {title}

## Ziel
Dieses Projekt ist eine lokale Lernvorlage für einen Robotik-Entwurf.

## Was der Roboter tun soll
{description or 'Die genaue Funktion soll im Unterricht oder bei der Demo konkretisiert werden.'}

## Projektstruktur
- project_spec.md: technische Einordnung
- components.md: Bauteile als Karten
- wiring.md: Anschlusslogik und Wokwi-Hinweise
- code.ino: Arduino/ESP32-Code-Skelett
- model.scad: 3D-Druckvorlage
- wokwi/diagram.json: Schaltplan für Wokwi Web
- report.md und report.pdf: Abschlussbericht

## MVP-Grenze
Das Ergebnis ist kein finales Ingenieurprodukt. Alle elektrischen und mechanischen Details müssen geprüft werden.
"""
    if output_name == "components.md":
        return """# Komponenten

## Controller
### ESP32 DevKit
Zweck: Hauptcontroller für Motoren, Sensorik und WLAN-Funktion.
Warum passend: ESP32 passt gut zu lokalen Robotik-Demos mit WLAN.
Zu prüfen: Pinout, Stromversorgung, Board-Variante.

## Antrieb
### DC-Motoren mit Motortreiber
Zweck: Bewegung des Rovers.
Warum passend: Ein L298N- oder TB6612-Treiber trennt Motorstrom und Logik.
Zu prüfen: Motorstrom, Treibergrenzen, gemeinsame Masse.

## Sensorik
### HC-SR04 oder Kamera-Modul
Zweck: einfache Wahrnehmung der Umgebung.
Zu prüfen: Spannung, Pegel, Bibliotheken, mechanische Befestigung.

## Energie
### Externer Akku
Zweck: Versorgung von Motoren und Elektronik.
Zu prüfen: Spannung, Strom, Sicherung, Polung.
"""
    if output_name == "wiring.md":
        return """# Verdrahtung

## Grundprinzip
ESP32, Motortreiber, Sensorik und externer Akku müssen eine gemeinsame Masse haben. Motoren werden nicht direkt am ESP32 betrieben.

## Anschlusskarten
### ESP32 zu Motortreiber
Signal: GPIO-Pins für IN1, IN2, IN3, IN4.
Kommentar: Pins vor der realen Verdrahtung am konkreten ESP32-Board prüfen.

### Akku zu Motortreiber
Signal: Motorversorgung an VM/12V und GND.
Kommentar: Spannung und Strom müssen zum Motortreiber passen.

### Sensor zu ESP32
Signal: VCC, GND, TRIG, ECHO oder I2C/SPI je nach Sensor.
Kommentar: Pegelwandlung prüfen, falls 5V-Sensorik verwendet wird.

## Wokwi
Der visuelle Schaltplan liegt in wokwi/diagram.json und kann in Wokwi Web eingefügt werden.
"""
    if output_name == "code.ino":
        return """/*
RoboForge Local - Code-Skelett
Dieses Programm ist keine fertige Firmware. Pinout, Bibliotheken und Hardware müssen geprüft werden.
*/

const int MOTOR_LEFT_A = 26;
const int MOTOR_LEFT_B = 27;
const int MOTOR_RIGHT_A = 14;
const int MOTOR_RIGHT_B = 12;

void setupHardware() {
  pinMode(MOTOR_LEFT_A, OUTPUT);
  pinMode(MOTOR_LEFT_B, OUTPUT);
  pinMode(MOTOR_RIGHT_A, OUTPUT);
  pinMode(MOTOR_RIGHT_B, OUTPUT);
}

void stopMotors() {
  digitalWrite(MOTOR_LEFT_A, LOW);
  digitalWrite(MOTOR_LEFT_B, LOW);
  digitalWrite(MOTOR_RIGHT_A, LOW);
  digitalWrite(MOTOR_RIGHT_B, LOW);
}

void readInputs() {
  // TODO: Sensoren oder WLAN-Befehle einlesen.
}

void updateMotors() {
  // TODO: Motorgeschwindigkeit und Richtung nach realem Treiber anpassen.
}

void printStatus() {
  Serial.println("RoboForge demo skeleton running");
}

void setup() {
  Serial.begin(115200);
  setupHardware();
  stopMotors();
}

void loop() {
  readInputs();
  updateMotors();
  printStatus();
  delay(500);
}
"""
    return spec
