from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# RoboForge Wokwi generator, v4
# --------------------------------
# This module deliberately avoids a single fixed rover template.
# It builds a circuit from a project profile: controller + detected sensors + detected actuators + power needs.
# The output is still conservative and Wokwi-friendly, but the project type is not forced into a rover.


@dataclass
class CircuitComponent:
    kind: str
    count: int = 1
    label: str = ""


@dataclass
class CircuitProfile:
    project_family: str
    controller: str
    components: list[CircuitComponent]
    power: str
    notes: list[str]


def _norm(text: str) -> str:
    text = text.lower()
    repl = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "ё": "е",
    }
    for a, b in repl.items():
        text = text.replace(a, b)
    return text


def _has(text: str, *words: str) -> bool:
    return any(w in text for w in words)


def _number_before(text: str, *words: str, default: int = 1, minimum: int = 1, maximum: int = 8) -> int:
    for word in words:
        patterns = [
            rf"(?<![a-z0-9])(\d+)\s*(?:x|mal)?\s*{re.escape(word)}",
            rf"{re.escape(word)}\s*(?<![a-z0-9])(\d+)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return max(minimum, min(maximum, int(m.group(1))))
    return default




def _leg_count(text: str) -> int:
    m = re.search(r"(\d+)\s*(?:beine|legs)", text)
    if m:
        return max(2, min(8, int(m.group(1))))
    if _has(text, "spinne", "spider"):
        return 8
    if _has(text, "hexapod", "sechsbeiner"):
        return 6
    if _has(text, "hund", "dog", "quadruped", "vierbeiner"):
        return 4
    return 4


def detect_circuit_profile(title: str, description: str, spec: str = "") -> CircuitProfile:
    raw = f"{title}\n{description}\n{spec}"
    text = _norm(raw)
    notes: list[str] = []

    # 1) Respect explicitly requested controller first. This is non-negotiable.
    if _has(text, "arduino mega", "mega 2560"):
        controller = "arduino_mega"
    elif _has(text, "arduino nano", "nano"):
        controller = "arduino_nano"
    elif _has(text, "arduino", "uno"):
        controller = "arduino_uno"
    elif _has(text, "raspberry pi pico", "rp2040", "pico"):
        controller = "pico"
    elif _has(text, "esp32", "wlan", "wifi", "wi-fi", "bluetooth", "kamera", "camera", "cam"):
        controller = "esp32"
    else:
        # A servo-heavy educational arm is often taught on Arduino; otherwise ESP32 is a useful local default.
        controller = "arduino_uno" if _has(text, "servo", "roboterarm", "robot arm", "arm", "greifer", "gripper") else "esp32"
        notes.append("Kein Controller eindeutig angegeben; RoboForge hat einen didaktischen Standard gewählt.")

    # 2) Determine project family before individual components.
    if _has(text, "spinne", "spider", "hexapod", "sechsbeiner", "hund", "dog", "quadruped", "vierbeiner", "beine", "legs", "legged", "laufroboter"):
        family = "legged_robot"
    elif _has(text, "drohne", "drone", "quadcopter", "quadrocopter", "propeller"):
        family = "drone_frame"
    elif _has(text, "roboterarm", "robot arm", "manipulator", "greifer", "gripper", "gelenk", "joint", "servo arm"):
        family = "robot_arm"
    elif _has(text, "fahrzeug", "auto", "rover", "car", "wheel", "wheeled", "raeder", "rad", "linie", "line follower", "follower"):
        family = "wheeled_robot"
    elif _has(text, "wetter", "weather", "sensorstation", "sensor station", "dashboard", "monitor", "datenlogger", "data logger", "dht", "bme280", "bmp280", "temperatur", "luftfeuchtigkeit"):
        family = "sensor_dashboard"
    elif _has(text, "screen", "bildschirm", "display", "touch", "tft", "oled", "lcd", "anzeige"):
        family = "display_station"
    elif _has(text, "led", "ampel", "traffic light", "button", "taste") and not _has(text, "motor", "servo"):
        family = "io_demo"
    else:
        family = "generic_robotics"

    components: list[CircuitComponent] = []

    def add(kind: str, count: int = 1, label: str = "") -> None:
        # One kind should appear only once in the profile. This prevents duplicate servo blocks
        # such as 12 leg servos + 6 generic servos after keyword detection.
        for c in components:
            if c.kind == kind:
                c.count = max(c.count, max(1, count))
                if label and label not in c.label:
                    c.label = (c.label + "; " + label).strip("; ")
                return
        components.append(CircuitComponent(kind=kind, count=max(1, count), label=label))

    # 3) Family defaults.
    if family == "robot_arm":
        servo_count = _number_before(text, "servo", "servos", default=4, maximum=6)
        if _has(text, "greifer", "gripper"):
            servo_count = max(servo_count, 4)
        add("servo", servo_count, "Arm/Greifer-Servos")
        if _has(text, "joystick", "analog stick"):
            add("joystick", 1, "Steuer-Joystick")
        elif _has(text, "potentiometer", "poti", "potis", "potentiometer"):
            add("potentiometer", min(4, _number_before(text, "poti", "potentiometer", default=2, maximum=4)), "Positions-Eingabe")
        else:
            add("potentiometer", 2, "Optionale manuelle Steuerung")
        power = "external_5v_servo_power"
    elif family == "legged_robot":
        legs = _leg_count(text)
        explicit_servos = _number_before(text, "servo", "servos", default=0, maximum=24)
        servo_count = explicit_servos if explicit_servos else legs * (3 if _has(text, "3dof", "3 dof", "knie", "knee") else 2)
        add("servo", max(legs * 2, servo_count), f"Bein-Servos für {legs} Beine")
        if _has(text, "mpu", "imu", "balance", "lage"):
            add("mpu6050", 1, "Lagesensor")
        power = "external_5v_servo_power"
    elif family == "drone_frame":
        add("terminal", 1, "Flight-controller/ESC-Anschlussblock")
        add("mpu6050", 1, "IMU-Platzhalter")
        power = "external_motor_battery"
    elif family == "display_station":
        add("oled", 1, "Anzeige")
        if _has(text, "button", "taste", "taster"):
            add("button", 2, "Bedientasten")
        power = "usb_or_5v"
    elif family == "wheeled_robot":
        if _has(text, "stepper", "schrittmotor", "a4988", "drv8825"):
            count = _number_before(text, "stepper", "schrittmotor", default=2, maximum=4)
            add("stepper_motor", count, "Antrieb")
            add("stepper_driver", count, "A4988/DRV8825")
        else:
            count = _number_before(text, "dc motor", "motor", "motoren", default=2, maximum=4)
            add("dc_motor", count, "Antrieb")
            add("motor_driver", 1, "L298N/TB6612")
        power = "external_motor_battery"
    elif family == "sensor_dashboard":
        power = "usb_or_5v"
    elif family == "io_demo":
        power = "usb_or_5v"
    else:
        power = "usb_or_5v"

    # 4) Explicit sensors / IO / actuators across all families.
    if _has(text, "hc-sr04", "hcsr04", "ultraschall", "ultrasonic", "distance", "abstand"):
        add("ultrasonic", 1, "Abstandssensor")
    elif family == "wheeled_robot" and _has(text, "sensor", "hindernis", "obstacle"):
        add("ultrasonic", 1, "Hinderniserkennung")

    if _has(text, "dht22", "dht11", "temperature", "temperatur", "humidity", "feuchte", "luftfeuchtigkeit"):
        add("dht22", 1, "Temperatur/Feuchte")
    if _has(text, "oled", "ssd1306", "display", "bildschirm"):
        add("oled", 1, "I2C-Anzeige")
    if _has(text, "mpu6050", "imu", "gyroscope", "gyroskop", "accelerometer", "beschleunigung"):
        add("mpu6050", 1, "IMU")
    if _has(text, "pir", "bewegungssensor", "motion sensor"):
        add("pir", 1, "PIR-Bewegungssensor")
    if _has(text, "ldr", "lichtsensor", "photoresistor", "fotowiderstand"):
        add("ldr", 1, "Lichtsensor")
    if _has(text, "buzzer", "summer", "piezo"):
        add("buzzer", 1, "Signalgeber")
    if _has(text, "relay", "relais"):
        add("relay", 1, "Schaltrelais")
    if _has(text, "neopixel", "ws2812", "rgb led"):
        add("neopixel", _number_before(text, "neopixel", "ws2812", default=1, maximum=8), "RGB-LED")
    elif _has(text, "led", "leds"):
        add("led", _number_before(text, "led", "leds", default=1, maximum=6), "Status-LED")
    if _has(text, "button", "taste", "taster", "pushbutton"):
        add("button", _number_before(text, "button", "taste", "taster", default=1, maximum=4), "Benutzereingabe")

    # Explicit actuators not already covered.
    if family != "robot_arm" and _has(text, "servo", "servos"):
        add("servo", _number_before(text, "servo", "servos", default=1, maximum=6), "Servo-Aktuator")
        if power == "usb_or_5v":
            power = "external_5v_servo_power"
    if family != "wheeled_robot" and _has(text, "stepper", "schrittmotor", "a4988", "drv8825"):
        count = _number_before(text, "stepper", "schrittmotor", default=1, maximum=4)
        add("stepper_motor", count, "Schrittmotor")
        add("stepper_driver", count, "A4988/DRV8825")
        power = "external_motor_battery"
    if family != "wheeled_robot" and _has(text, "dc motor", "gleichstrommotor", "l298n", "tb6612"):
        add("dc_motor", _number_before(text, "dc motor", "gleichstrommotor", default=1, maximum=4), "DC-Motor")
        add("motor_driver", 1, "Motortreiber")
        power = "external_motor_battery"

    if not components:
        add("terminal", 1, "Generische I/O-Anschlüsse")
        notes.append("Keine eindeutig unterstützten Wokwi-Komponenten erkannt; generische I/O-Schnittstelle erzeugt.")

    if controller.startswith("arduino") and _has(text, "esp32"):
        notes.append("Achtung: Text enthält Arduino und ESP32. Der explizit früher erkannte Controller wurde beibehalten.")

    return CircuitProfile(family, controller, components, power, notes)


CONTROLLER_PARTS = {
    "esp32": ("board-esp32-devkit-c-v4", "esp", {"vcc3": "3V3", "vcc5": "5V", "gnd": "GND.1"}),
    "arduino_uno": ("wokwi-arduino-uno", "uno", {"vcc3": "3.3V", "vcc5": "5V", "gnd": "GND.1"}),
    "arduino_nano": ("wokwi-arduino-nano", "nano", {"vcc3": "3V3", "vcc5": "5V", "gnd": "GND.1"}),
    "arduino_mega": ("wokwi-arduino-mega", "mega", {"vcc3": "3.3V", "vcc5": "5V", "gnd": "GND.1"}),
    "pico": ("wokwi-pi-pico", "pico", {"vcc3": "3V3", "vcc5": "VBUS", "gnd": "GND.1"}),
}

PIN_POOLS = {
    "esp32": ["23", "22", "21", "19", "18", "5", "17", "16", "4", "2", "15", "14", "27", "26", "25", "33", "32"],
    "arduino_uno": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "A0", "A1", "A2", "A3", "A4", "A5"],
    "arduino_nano": ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "A0", "A1", "A2", "A3", "A4", "A5"],
    "arduino_mega": ["22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"],
    "pico": ["GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8", "GP9", "GP10", "GP11", "GP12", "GP13", "GP14", "GP15"],
}


def _part(part_type: str, part_id: str, top: float, left: float, attrs: dict[str, Any] | None = None, rotate: int | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"type": part_type, "id": part_id, "top": top, "left": left, "attrs": attrs or {}}
    if rotate is not None:
        item["rotate"] = rotate
    return item


def _text(part_id: str, text: str, top: float, left: float) -> dict[str, Any]:
    return _part("wokwi-text", part_id, top, left, {"text": text})


def _wire(a: str, b: str, color: str = "green", route: list[str] | None = None) -> list[Any]:
    return [a, b, color, route or []]


def _diagram(parts: list[dict[str, Any]], connections: list[list[Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "author": "RoboForge Local",
        "editor": "wokwi",
        "parts": parts,
        "connections": connections,
        "dependencies": {},
    }


class PinAllocator:
    def __init__(self, controller: str):
        self.pins = PIN_POOLS.get(controller, PIN_POOLS["esp32"]).copy()
        self.index = 0

    def next(self) -> str:
        if self.index >= len(self.pins):
            # Wokwi still needs a syntactically valid pin name; repeat last fallback if project is too large.
            return self.pins[-1]
        pin = self.pins[self.index]
        self.index += 1
        return pin

    def take_i2c(self, controller: str) -> tuple[str, str]:
        if controller.startswith("arduino"):
            return ("A4", "A5")  # SDA, SCL on Uno/Nano; acceptable didactic default.
        if controller == "pico":
            return ("GP4", "GP5")
        return ("21", "22")


def _controller_pin(ctrl_id: str, pin: str) -> str:
    return f"{ctrl_id}:{pin}"


def _power_parts(profile: CircuitProfile) -> tuple[list[dict[str, Any]], dict[str, str]]:
    parts: list[dict[str, Any]] = []
    ids: dict[str, str] = {}
    if profile.power == "external_5v_servo_power":
        parts += [
            _text("lbl_power", "External servo power 5V", 25, 350),
            _part("wokwi-vcc", "logic_vcc", 75, 245, {"value": "5V"}),
            _part("wokwi-gnd", "logic_gnd", 365, 245),
            _part("wokwi-battery", "servo_bat", 80, 380, {"voltage": "5"}),
            _part("wokwi-gnd", "power_gnd", 365, 380),
        ]
        ids = {"logic_vcc": "logic_vcc:VCC", "logic_gnd": "logic_gnd:GND", "ext_vcc": "servo_bat:+", "ext_gnd": "servo_bat:-", "common_gnd": "power_gnd:GND"}
    elif profile.power == "external_motor_battery":
        parts += [
            _text("lbl_power", "Motor battery / external power", 25, 350),
            _part("wokwi-vcc", "logic_vcc", 75, 245, {"value": "5V"}),
            _part("wokwi-gnd", "logic_gnd", 365, 245),
            _part("wokwi-vcc", "motor_vcc", 75, 390, {"value": "BAT+"}),
            _part("wokwi-gnd", "motor_gnd", 365, 390),
            _part("wokwi-slide-switch", "power_sw", 98, 470, {"bounce": "0"}),
        ]
        ids = {"logic_vcc": "logic_vcc:VCC", "logic_gnd": "logic_gnd:GND", "ext_vcc": "power_sw:2", "ext_gnd": "motor_gnd:GND", "common_gnd": "motor_gnd:GND", "motor_vcc_raw": "motor_vcc:VCC", "switch_in": "power_sw:1"}
    else:
        parts += [
            _text("lbl_power", "USB / board power", 25, 350),
            _part("wokwi-vcc", "logic_vcc", 75, 245, {"value": "5V"}),
            _part("wokwi-gnd", "logic_gnd", 365, 245),
        ]
        ids = {"logic_vcc": "logic_vcc:VCC", "logic_gnd": "logic_gnd:GND", "ext_vcc": "logic_vcc:VCC", "ext_gnd": "logic_gnd:GND", "common_gnd": "logic_gnd:GND"}
    return parts, ids


def build_diagram(title: str, description: str, spec: str = "") -> dict[str, Any]:
    profile = detect_circuit_profile(title, description, spec)
    controller_type, ctrl_id, ctrl_pins = CONTROLLER_PARTS.get(profile.controller, CONTROLLER_PARTS["esp32"])
    pins = PinAllocator(profile.controller)

    parts: list[dict[str, Any]] = [
        _part(controller_type, ctrl_id, 125, 25),
        _text("lbl_controller", profile.controller.replace("_", " ").upper(), 80, 25),
    ]
    power_parts, power = _power_parts(profile)
    parts.extend(power_parts)
    connections: list[list[Any]] = []

    # Basic power references. Keep the controller and external loads tied to common ground.
    vcc_pin = ctrl_pins.get("vcc5", "5V")
    gnd_pin = ctrl_pins.get("gnd", "GND.1")
    connections.append(_wire(_controller_pin(ctrl_id, vcc_pin), power["logic_vcc"], "red", ["h165", "v-70"]))
    connections.append(_wire(_controller_pin(ctrl_id, gnd_pin), power["logic_gnd"], "black", ["h170", "v150"]))
    if "motor_vcc_raw" in power:
        connections.append(_wire(power["motor_vcc_raw"], power["switch_in"], "red", ["h70", "v20"]))
    if power.get("common_gnd") != power.get("logic_gnd"):
        connections.append(_wire(power["logic_gnd"], power["common_gnd"], "black", ["h140"]))

    # Place functional components on a grid to the right of the power rail.
    col_x = 620
    row_y = 80
    row_gap = 155
    item_index = 0

    def next_pos() -> tuple[float, float]:
        nonlocal item_index
        col = item_index // 4
        row = item_index % 4
        item_index += 1
        return row_y + row * row_gap, col_x + col * 250

    def add_label(text: str, y: float, x: float, suffix: str) -> None:
        parts.append(_text(f"lbl_{suffix}", text, y - 38, x))

    # Multi-part handling: when a driver pairs with motors, keep them aligned and readable.
    comp_map = {c.kind: c for c in profile.components}

    # Stepper drivers + steppers.
    if "stepper_motor" in comp_map:
        count = comp_map["stepper_motor"].count
        for i in range(count):
            y, x = next_pos()
            drv_id = f"stepdrv{i+1}"
            mot_id = f"stepper{i+1}"
            add_label(f"Stepper {i+1}", y, x, mot_id)
            parts.append(_part("wokwi-a4988", drv_id, y + 10, x, rotate=270))
            parts.append(_part("wokwi-stepper-motor", mot_id, y, x + 210, {"size": "17", "display": "angle"}))
            connections += [
                _wire(power["ext_vcc"], f"{drv_id}:VMOT", "red", ["h120"]),
                _wire(power["ext_gnd"], f"{drv_id}:GND", "black", ["h120"]),
                _wire(power["logic_vcc"], f"{drv_id}:VDD", "red", ["h120"]),
                _wire(power["logic_gnd"], f"{drv_id}:GND", "black", ["h120"]),
                _wire(f"{drv_id}:RESET", f"{drv_id}:SLEEP", "green"),
                _wire(_controller_pin(ctrl_id, pins.next()), f"{drv_id}:STEP", "green", ["h450"]),
                _wire(_controller_pin(ctrl_id, pins.next()), f"{drv_id}:DIR", "blue", ["h465"]),
                _wire(f"{drv_id}:2B", f"{mot_id}:A-", "green", ["h115"]),
                _wire(f"{drv_id}:2A", f"{mot_id}:A+", "green", ["h115"]),
                _wire(f"{drv_id}:1A", f"{mot_id}:B+", "blue", ["h115"]),
                _wire(f"{drv_id}:1B", f"{mot_id}:B-", "blue", ["h115"]),
            ]

    # DC motor driver + motors.
    if "dc_motor" in comp_map:
        y, x = next_pos()
        motor_count = comp_map["dc_motor"].count
        add_label("DC motor driver", y, x, "dc_driver")
        parts.append(_part("wokwi-l298n", "drv", y + 10, x))
        connections += [
            _wire(power["ext_vcc"], "drv:12V", "red", ["h120"]),
            _wire(power["ext_gnd"], "drv:GND", "black", ["h120"]),
            _wire(power["logic_vcc"], "drv:5V", "red", ["h120"]),
            _wire(power["logic_gnd"], "drv:GND", "black", ["h120"]),
        ]
        for pin_name in ["IN1", "IN2", "IN3", "IN4"]:
            connections.append(_wire(_controller_pin(ctrl_id, pins.next()), f"drv:{pin_name}", "blue" if pin_name.endswith(("2", "4")) else "green", ["h450"]))
        for i in range(motor_count):
            mot_id = f"dc{i+1}"
            parts.append(_part("wokwi-dc-motor", mot_id, y + i * 95, x + 250))
            if i == 0:
                connections += [_wire("drv:OUT1", f"{mot_id}:+", "red", ["h110"]), _wire("drv:OUT2", f"{mot_id}:-", "black", ["h110"])]
            elif i == 1:
                connections += [_wire("drv:OUT3", f"{mot_id}:+", "red", ["h110"]), _wire("drv:OUT4", f"{mot_id}:-", "black", ["h110"])]

    # Servos: robot arms get multiple separate servo blocks, not wheels.
    if "servo" in comp_map:
        labels = ["Base", "Shoulder", "Elbow", "Gripper", "Wrist", "Aux"]
        for i in range(comp_map["servo"].count):
            y, x = next_pos()
            sid = f"servo{i+1}"
            label = labels[i] if i < len(labels) else f"Servo {i+1}"
            add_label(label, y, x, sid)
            parts.append(_part("wokwi-servo", sid, y, x))
            connections += [
                _wire(power["ext_vcc"], f"{sid}:V+", "red", ["h120"]),
                _wire(power["ext_gnd"], f"{sid}:GND", "black", ["h120"]),
                _wire(_controller_pin(ctrl_id, pins.next()), f"{sid}:PWM", "orange", ["h450"]),
            ]

    # Remaining sensors and IO.
    for comp in profile.components:
        if comp.kind in {"stepper_motor", "stepper_driver", "dc_motor", "motor_driver", "servo"}:
            continue
        for i in range(comp.count):
            y, x = next_pos()
            suffix = f"{comp.kind}{i+1}"
            if comp.kind == "ultrasonic":
                add_label("HC-SR04", y, x, suffix)
                pid = f"ultra{i+1}"
                parts.append(_part("wokwi-hc-sr04", pid, y, x))
                connections += [
                    _wire(power["logic_vcc"], f"{pid}:VCC", "red", ["h120"]),
                    _wire(power["logic_gnd"], f"{pid}:GND", "black", ["h120"]),
                    _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:TRIG", "green", ["h450"]),
                    _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:ECHO", "blue", ["h465"]),
                ]
            elif comp.kind == "dht22":
                add_label("DHT22", y, x, suffix)
                pid = f"dht{i+1}"
                parts.append(_part("wokwi-dht22", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:SDA", "green")]
            elif comp.kind == "oled":
                add_label("OLED SSD1306", y, x, suffix)
                pid = f"oled{i+1}"
                sda, scl = pins.take_i2c(profile.controller)
                parts.append(_part("board-ssd1306", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, sda), f"{pid}:SDA", "green"), _wire(_controller_pin(ctrl_id, scl), f"{pid}:SCL", "blue")]
            elif comp.kind == "mpu6050":
                add_label("MPU6050 / I2C IMU", y, x, suffix)
                pid = f"imu{i+1}"
                sda, scl = pins.take_i2c(profile.controller)
                parts.append(_part("wokwi-mpu6050", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, sda), f"{pid}:SDA", "green"), _wire(_controller_pin(ctrl_id, scl), f"{pid}:SCL", "blue")]
            elif comp.kind == "pir":
                add_label("PIR", y, x, suffix)
                pid = f"pir{i+1}"
                parts.append(_part("wokwi-pir-motion-sensor", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:OUT", "green")]
            elif comp.kind == "ldr":
                add_label("LDR", y, x, suffix)
                pid = f"ldr{i+1}"
                parts.append(_part("wokwi-photoresistor-sensor", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:AO", "green")]
            elif comp.kind == "buzzer":
                add_label("Buzzer", y, x, suffix)
                pid = f"buzz{i+1}"
                parts.append(_part("wokwi-buzzer", pid, y, x))
                connections += [_wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:1", "green"), _wire(power["logic_gnd"], f"{pid}:2", "black")]
            elif comp.kind == "relay":
                add_label("Relay module", y, x, suffix)
                pid = f"relay{i+1}"
                parts.append(_part("wokwi-relay-module", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:IN", "green")]
            elif comp.kind == "neopixel":
                add_label("NeoPixel", y, x, suffix)
                pid = f"neo{i+1}"
                parts.append(_part("wokwi-neopixel", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:DIN", "green")]
            elif comp.kind == "led":
                add_label("LED", y, x, suffix)
                rid, lid = f"r{i+1}", f"led{i+1}"
                parts.append(_part("wokwi-resistor", rid, y + 5, x, {"value": "220"}))
                parts.append(_part("wokwi-led", lid, y + 5, x + 130, {"color": "red"}))
                connections += [_wire(_controller_pin(ctrl_id, pins.next()), f"{rid}:1", "green"), _wire(f"{rid}:2", f"{lid}:A", "green"), _wire(f"{lid}:C", power["logic_gnd"], "black")]
            elif comp.kind == "button":
                add_label("Button", y, x, suffix)
                pid = f"btn{i+1}"
                parts.append(_part("wokwi-pushbutton", pid, y, x))
                connections += [_wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:1.l", "blue"), _wire(f"{pid}:2.r", power["logic_gnd"], "black")]
            elif comp.kind == "potentiometer":
                add_label("Potentiometer", y, x, suffix)
                pid = f"pot{i+1}"
                parts.append(_part("wokwi-potentiometer", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:SIG", "green")]
            elif comp.kind == "joystick":
                add_label("Joystick", y, x, suffix)
                pid = f"joy{i+1}"
                parts.append(_part("wokwi-analog-joystick", pid, y, x))
                connections += [_wire(power["logic_vcc"], f"{pid}:VCC", "red"), _wire(power["logic_gnd"], f"{pid}:GND", "black"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:VERT", "green"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:HORZ", "blue"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:SEL", "orange")]
            else:
                add_label("Generic I/O", y, x, suffix)
                pid = f"term{i+1}"
                parts.append(_part("wokwi-terminal", pid, y, x))
                connections += [_wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:RX", "green"), _wire(_controller_pin(ctrl_id, pins.next()), f"{pid}:TX", "blue")]

    return _diagram(parts, connections)


def export_wokwi(project_dir: Path, title: str, description: str, spec: str = "") -> list[str]:
    wokwi_dir = project_dir / "wokwi"
    wokwi_dir.mkdir(parents=True, exist_ok=True)

    profile = detect_circuit_profile(title, description, spec)
    diagram = build_diagram(title, description, spec)

    (wokwi_dir / "diagram.json").write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")
    (wokwi_dir / "circuit_profile.json").write_text(
        json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    component_lines = "\n".join(
        f"- {c.kind}: {c.count} × {c.label or c.kind}" for c in profile.components
    )
    notes = "\n".join(f"- {n}" for n in profile.notes) or "- Keine zusätzlichen Hinweise."
    readme = f"""# Wokwi-Schaltplan

Dieses Verzeichnis enthält einen generierten Wokwi-Schaltplan für das Projekt.

## Erkannter Schaltungs-Profile
- Projektfamilie: `{profile.project_family}`
- Controller: `{profile.controller}`
- Stromversorgung: `{profile.power}`

## Erkannte Komponenten
{component_lines}

## Hinweise
{notes}

## Warum kein einzelnes Template?
RoboForge verwendet keinen festen Rover-Schaltplan als Standard. Der Generator erkennt Controller, Mechanik, Sensoren, Aktuatoren und Stromversorgung aus Projekttitel, Beschreibung und `project_spec.md`. Danach wird `diagram.json` aus einzelnen Bauteil-Blöcken zusammengesetzt. Ein Arduino-Roboterarm bleibt deshalb Arduino + Servos, ein Sensor-Dashboard bleibt Controller + Sensoren/Display, und ein Rover bekommt nur dann Motorblöcke, wenn das Projekt wirklich ein Fahrzeug/Rover ist.

## Verwendung
1. Auf der RoboForge-Webseite `diagram.json für Wokwi kopieren` öffnen.
2. JSON kopieren.
3. In Wokwi Web ein Projekt öffnen.
4. Den Inhalt der Datei `diagram.json` komplett ersetzen.

## Grenzen
Der Schaltplan ist eine didaktische Vorlage. Vor echter Hardware müssen Spannung, Strom, Pinout, gemeinsame Masse, Pegel und Datenblätter geprüft werden.
"""
    (wokwi_dir / "README.md").write_text(readme, encoding="utf-8")
    return ["wokwi/diagram.json", "wokwi/circuit_profile.json", "wokwi/README.md"]
