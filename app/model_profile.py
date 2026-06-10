from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from collections import Counter


@dataclass
class PartSpec:
    name: str
    quantity: int = 1
    role: str = ""
    check: str = "Maße am realen Bauteil prüfen."


@dataclass
class ModelProfile:
    platform: str
    controller: str
    modules: list[str]
    wheel_count: int
    has_camera: bool
    has_battery: bool
    has_motor_driver: bool
    dimensions: dict[str, int]
    notes: str
    parts: list[PartSpec] = field(default_factory=list)
    sanity_warnings: list[str] = field(default_factory=list)


def _has_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


def _count_word(text: str, patterns: list[str]) -> int | None:
    for p in patterns:
        m = re.search(p, text)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    return None


def _controller_from_text(t: str) -> str:
    if _has_any(t, ["arduino mega", "mega 2560", "arduino-mega"]):
        return "arduino_mega"
    if _has_any(t, ["arduino nano", "nano"]):
        return "arduino_nano"
    if _has_any(t, ["arduino", "uno", "atmega"]):
        return "arduino_uno"
    if _has_any(t, ["raspberry pi pico", "pico", "rp2040"]):
        return "raspberry_pi_pico"
    if _has_any(t, ["esp32-cam", "esp32 cam"]):
        return "esp32_cam"
    if _has_any(t, ["esp32", "wlan", "wifi", "wi-fi"]):
        return "esp32"
    if _has_any(t, ["micro:bit", "microbit"]):
        return "microbit"
    if _has_any(t, ["stm32", "nucleo"]):
        return "stm32_generic"
    return "generic_controller"


def _parts_to_modules(parts: list[PartSpec]) -> list[str]:
    modules: list[str] = []
    for part in parts:
        q = max(1, min(48, int(part.quantity)))
        modules.extend([part.name] * q)
    return modules


def _merge_parts(parts: list[PartSpec]) -> list[PartSpec]:
    merged: dict[str, PartSpec] = {}
    order: list[str] = []
    for p in parts:
        name = str(p.name).strip()
        if not name:
            continue
        q = max(1, min(48, int(p.quantity or 1)))
        if name not in merged:
            merged[name] = PartSpec(name=name, quantity=q, role=p.role, check=p.check)
            order.append(name)
        else:
            merged[name].quantity += q
            if p.role and p.role not in merged[name].role:
                merged[name].role = (merged[name].role + "; " + p.role).strip("; ")
    return [merged[n] for n in order]


def _p(name: str, q: int, role: str, check: str = "Maße, Bohrungen und Druckausrichtung prüfen.") -> PartSpec:
    return PartSpec(name=name, quantity=q, role=role, check=check)


def _wheel_count(t: str) -> int:
    explicit = _count_word(t, [r"(\d+)\s*(?:räder|raeder|wheels|wheel)", r"(\d+)\s*rad", r"(\d+)\s*wd"])
    if explicit in {2, 3, 4, 6, 8}:
        return explicit
    if _has_any(t, ["two wheel", "2 wheel", "zweirad", "2-rad", "differential", "differentialantrieb"]):
        return 2
    if _has_any(t, ["six wheel", "6 wheel", "sechsrad", "6-rad"]):
        return 6
    if _has_any(t, ["tracked", "kette", "ketten", "tank"]):
        return 0
    return 4


def _leg_count(t: str) -> int:
    explicit = _count_word(t, [r"(\d+)\s*(?:beine|legs|legged)"])
    if explicit in {2, 4, 6, 8}:
        return explicit
    if _has_any(t, ["spider", "spinne", "arachnid"]):
        return 8
    if _has_any(t, ["hexapod", "sechsbeiner"]):
        return 6
    if _has_any(t, ["dog", "hund", "quadruped", "vierbeiner", "katze", "cat"]):
        return 4
    if _has_any(t, ["biped", "humanoid", "zweibeiner"]):
        return 2
    return 4


def _arm_servo_count(t: str) -> int:
    explicit = _count_word(t, [r"(\d+)\s*(?:dof|achsen|axis|servos|servo)"])
    if explicit and 2 <= explicit <= 8:
        return explicit
    if _has_any(t, ["6 dof", "6dof", "6 achsen", "six axis"]):
        return 6
    if _has_any(t, ["gripper", "greifer", "klaue"]):
        return 4
    return 3


def _keyword_profile(text: str) -> ModelProfile:
    t = text.lower()
    controller = _controller_from_text(t)
    warnings: list[str] = []

    arm_terms = ["roboterarm", "robot arm", "robot-arm", "arm", "greifer", "gripper", "manipulator", "gelenk", "kinematik", "klaue", "klauen"]
    rover_terms = ["rover", "fahrzeug", "auto", "car", "wagen", "fahrroboter", "fahrender", "rad", "räder", "raeder", "wheeled", "drive train", "differentialantrieb", "l298", "l298n", "tb6612", "dc motor", "gleichstrommotor", "n20", "getriebemotor", "stepper", "schrittmotor", "a4988", "drv8825", "motor driver", "motortreiber"]
    sensor_box_terms = ["wetterstation", "weather", "sensorstation", "sensor station", "dashboard", "monitoring", "monitor", "dht", "bme280", "bmp280", "datenlogger", "messstation", "umwelt", "temperatur", "luftfeuchtigkeit"]
    turret_terms = ["pan tilt", "pan-tilt", "kamerakopf", "camera turret", "servo kamera", "schwenk", "neig"]
    legged_terms = ["spider", "spinne", "hexapod", "sechsbeiner", "dog", "hund", "quadruped", "vierbeiner", "biped", "humanoid", "laufroboter", "walking robot", "bein", "beine", "legged"]
    display_terms = ["screen", "bildschirm", "display", "touch", "tft", "oled", "lcd", "anzeige"]
    drone_terms = ["drohne", "drone", "quadcopter", "quadrocopter", "propeller"]

    is_arm = _has_any(t, arm_terms) and not _has_any(t, ["fahrzeug", "rover", "räder", "raeder", "car"])
    is_turret = _has_any(t, turret_terms)
    is_sensor_box = (_has_any(t, sensor_box_terms) or (_has_any(t, ["sensor", "sensoren", "messung"]) and _has_any(t, ["oled", "display", "lcd", "screen", "bildschirm"]))) and not is_arm
    is_legged = _has_any(t, legged_terms)
    is_rover = _has_any(t, rover_terms) and not is_arm and not is_legged
    is_drone = _has_any(t, drone_terms)
    is_display = _has_any(t, display_terms) and not is_sensor_box and not is_arm

    parts: list[PartSpec] = []
    dims = {"length": 130, "width": 95, "thickness": 4}
    platform = "generic_chassis"
    wheel_count = 0

    # Important: generic words "robot/Roboter" alone never choose rover.
    if is_legged:
        legs = _leg_count(t)
        platform = "legged_robot"
        dims = {"length": 150 if legs >= 6 else 135, "width": 115 if legs >= 6 else 95, "thickness": 4}
        explicit_servos = _count_word(t, [r"(\d+)\s*(?:servos|servo)"])
        servo_per_leg = max(2, min(3, round(explicit_servos / legs))) if explicit_servos else (3 if _has_any(t, ["3dof", "3 dof", "three dof", "knie", "knee"]) else 2)
        parts += [
            _p("legged_body_plate", 1, f"Zentrale Körperplatte für {legs} Beine."),
            _p("top_cover", 1, "Deckplatte für Elektronik und Kabel."),
            _p("controller_tray", 1, "Halter für den gewählten Controller."),
            _p("battery_tray", 1, "Akkuhalter mit Gurtöffnungen."),
            _p("servo_power_distribution_plate", 1, "Verteilerplatte für externe Servoversorgung."),
            _p("standard_servo_u_bracket", max(legs * servo_per_leg, 4), "Servo-U-Halter für Hüfte/Schulter/Knie."),
            _p("leg_link_long", legs, "Obere Beinsegmente."),
            _p("leg_link_short", legs, "Untere Beinsegmente."),
            _p("foot_pad", legs, "Druckbare Füße für jedes Bein."),
            _p("standoffs", 2, "Abstandshalter-Sets."),
            _p("screw_fit_test", 1, "Teststück für Schraubenpassung."),
        ]
        if legs >= 6:
            parts.append(_p("side_servo_rail", 2, "Seitliche Servoschienen für viele Beine."))
    elif is_turret:
        platform = "pan_tilt_mount"
        dims = {"length": 120, "width": 90, "thickness": 4}
        parts += [
            _p("base_plate", 1, "Grundplatte für Pan-Tilt-Aufbau."),
            _p("pan_tilt_base", 1, "Basisteil für Schwenk-/Neigeeinheit."),
            _p("standard_servo_u_bracket", 1, "Halter für Pan-Servo."),
            _p("sg90_servo_bracket", 1, "Halter für Tilt-Servo."),
            _p("camera_mount", 1, "Kamerahalter."),
            _p("controller_tray", 1, "Controllerhalter."),
            _p("battery_tray", 1, "Akkuhalter."),
            _p("standoffs", 1, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]
    elif is_arm:
        servo_count = _arm_servo_count(t)
        platform = "robot_arm_base"
        dims = {"length": 150, "width": 115, "thickness": 4}
        parts += [
            _p("robot_arm_base_plate", 1, "Grundplatte für Roboterarm."),
            _p("rotating_base_servo_mount", 1, "Drehbasis mit Servoaufnahme."),
            _p("standard_servo_u_bracket", max(2, servo_count - 1), "U-Halter für Hauptservos."),
            _p("sg90_servo_bracket", 1, "Kleiner Halter für Greifer/Handgelenk."),
            _p("servo_horn_adapter", servo_count, "Adapter für Servohörner und Gelenke."),
            _p("arm_link_long", max(2, servo_count - 1), "Lange Armsegmente."),
            _p("arm_link_short", 1, "Kurzes Arm-/Handgelenksegment."),
            _p("elbow_joint_plate", 2, "Gelenkplatten für Schulter/Ellenbogen."),
            _p("gripper_palm", 1, "Greiferbasis."),
            _p("gripper_finger", 2, "Zwei Greiferfinger, nicht einer."),
            _p("controller_tray", 1, "Controllerhalter."),
            _p("servo_power_distribution_plate", 1, "Externe Servoversorgung."),
            _p("battery_tray", 1, "Akkuhalter."),
            _p("standoffs", 2, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]
        parts.append(_p("joystick_panel" if _has_any(t, ["joystick", "steuerknüppel"]) else "potentiometer_panel", 1, "Bedienpanel für manuelle Steuerung."))
    elif is_sensor_box:
        platform = "sensor_box"
        dims = {"length": 120, "width": 90, "thickness": 4}
        parts += [
            _p("bottom_shell", 1, "Gehäuseunterteil."),
            _p("lid", 1, "Deckel."),
            _p("controller_tray", 1, "Controllerhalter im Gehäuse."),
            _p("battery_tray", 1, "Akkuhalter."),
            _p("display_bezel", 1 if _has_any(t, ["oled", "display", "lcd", "screen", "bildschirm"]) else 0, "Displayrahmen."),
            _p("small_sensor_clip", 2 if _has_any(t, ["dht", "bme", "bmp", "temperatur", "luftfeuchtigkeit"]) else 1, "Sensorclips."),
            _p("weather_louver", 1 if _has_any(t, ["wetter", "weather", "umwelt", "temperatur", "luftfeuchtigkeit"]) else 0, "Einfache Wetterschutz-Lamellen."),
            _p("cable_clip_set", 1, "Kabelclips."),
            _p("standoffs", 1, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]
    elif is_rover:
        platform = "wheeled_rover"
        dims = {"length": 155, "width": 100, "thickness": 4}
        wheel_count = _wheel_count(t)
        drive_mounts = max(2, wheel_count if wheel_count in {2, 4, 6} else 2)
        if wheel_count == 0:
            parts += [_p("track_side_plate", 2, "Seitenteile für Ketten-/Tankkonzept.")]
        else:
            parts += [
                _p("wheel_hub", wheel_count, f"Radnaben: automatisch {wheel_count} Stück statt zufällig 1."),
                _p("n20_motor_mount", min(drive_mounts, 6), "Motorhalter passend zur Radanzahl."),
            ]
        parts += [
            _p("base_plate", 1, "Chassis-Grundplatte."),
            _p("top_cover", 1, "Deckplatte."),
            _p("controller_tray", 1, "Controllerhalter."),
            _p("motor_driver_tray", 1, "Motortreiberhalter."),
            _p("battery_tray", 1, "Akkuhalter."),
            _p("caster_mount", 1 if wheel_count == 2 else 0, "Caster-Halter für Zweirad-Differentialantrieb."),
            _p("sensor_bracket", 1, "Front-Sensorhalter."),
            _p("cable_clip_set", 1, "Kabelclips."),
            _p("standoffs", 2, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]
    elif is_drone:
        platform = "drone_frame"
        dims = {"length": 140, "width": 140, "thickness": 4}
        parts += [
            _p("x_frame_plate", 1, "X-Rahmenplatte für Drohnenkonzept."),
            _p("motor_pod", 4, "Vier Motorpods, nicht einer."),
            _p("prop_guard_segment", 4, "Vier einfache Propeller-Schutzsegmente."),
            _p("controller_tray", 1, "Controllerhalter."),
            _p("battery_strap_plate", 1, "Akku-Gurtplatte."),
            _p("standoffs", 1, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]
    elif is_display:
        platform = "display_station"
        dims = {"length": 120, "width": 85, "thickness": 4}
        parts += [
            _p("base_plate", 1, "Basisplatte."),
            _p("display_bezel", 1, "Displayrahmen."),
            _p("display_stand", 2, "Zwei Standfüße für Display/Panel."),
            _p("controller_tray", 1, "Controllerhalter."),
            _p("battery_tray", 1, "Akkuhalter."),
            _p("cable_clip_set", 1, "Kabelclips."),
            _p("standoffs", 1, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]
    else:
        platform = "generic_chassis"
        dims = {"length": 125, "width": 90, "thickness": 4}
        parts += [
            _p("base_plate", 1, "Universelle Montageplatte."),
            _p("top_cover", 1, "Optionale Deck-/Trägerplatte."),
            _p("controller_tray", 1, "Controllerhalter."),
            _p("battery_tray", 1, "Akkuhalter."),
            _p("universal_l_bracket", 2, "Zwei L-Winkel."),
            _p("universal_u_bracket", 2, "Zwei U-Winkel."),
            _p("sensor_bracket", 1, "Universeller Sensorhalter."),
            _p("cable_clip_set", 1, "Kabelclips."),
            _p("standoffs", 2, "Abstandshalter."),
            _p("screw_fit_test", 1, "Schraubentest."),
        ]

    # Additive component-specific holders. Quantity is normalized later.
    if _has_any(t, ["hc-sr04", "hcsr04", "ultraschall", "ultrasonic", "abstand"]):
        parts.append(_p("hc_sr04_front_mount", 1, "HC-SR04 Frontmount."))
    if _has_any(t, ["oled", "ssd1306", "display", "lcd", "screen", "bildschirm"]):
        parts.append(_p("display_bezel", 1, "Displayrahmen."))
    if _has_any(t, ["dht", "bme280", "bmp280", "temperatur", "luftfeuchtigkeit"]):
        parts.append(_p("small_sensor_clip", 1, "Sensorclip."))
    if _has_any(t, ["kamera", "camera", "esp32-cam", "cam"]):
        parts.append(_p("camera_mount", 1, "Kamerahalter."))
    if _has_any(t, ["relay", "relais"]):
        parts.append(_p("relay_module_tray", 1, "Relaismodulhalter."))
    if _has_any(t, ["buzzer", "summer"]):
        parts.append(_p("buzzer_clip", 1, "Buzzerclip."))
    if _has_any(t, ["neopixel", "rgb", "led strip", "led-streifen"]) or re.search(r"\bled\b", t):
        parts.append(_p("led_strip_clip", 1, "LED-/NeoPixel-Clip."))
    if _has_any(t, ["joystick", "steuerknüppel"]):
        parts.append(_p("joystick_panel", 1, "Joystick-Panel."))
    if _has_any(t, ["potentiometer", "poti", "drehregler"]):
        parts.append(_p("potentiometer_panel", 1, "Poti-Panel."))
    if _has_any(t, ["l298", "l298n", "tb6612", "motortreiber", "motor driver"]):
        parts.append(_p("motor_driver_tray", 1, "Motortreiberhalter."))
    if _has_any(t, ["a4988", "drv8825", "stepper", "schrittmotor"]):
        parts.append(_p("stepper_driver_tray", 1, "Stepperdriver-Halter."))
    if _has_any(t, ["18650"]):
        parts.append(_p("battery_18650_holder", 1, "18650-Halter."))
    if _has_any(t, ["sg90", "9g"]):
        parts.append(_p("sg90_servo_bracket", 1, "SG90-Halter."))
    if _has_any(t, ["mg996", "mg995", "standard servo", "standard-servo"]):
        parts.append(_p("standard_servo_u_bracket", 1, "Standardservo-Halter."))

    parts = [p for p in parts if p.quantity > 0]
    parts = _merge_parts(parts)
    profile = ModelProfile(
        platform=platform,
        controller=controller,
        modules=_parts_to_modules(parts),
        wheel_count=wheel_count,
        has_camera=_has_any(t, ["kamera", "camera", "cam", "esp32-cam"]),
        has_battery=True,
        has_motor_driver=is_rover or _has_any(t, ["l298", "tb6612", "a4988", "drv8825", "motortreiber", "motor driver"]),
        dimensions=dims,
        notes="Parametrische Lernvorlage aus einer erweiterten Teilebibliothek. Stückzahlen werden geprüft, damit z. B. ein Radroboter nicht nur ein Rad bekommt.",
        parts=parts,
        sanity_warnings=warnings,
    )
    return normalize_model_profile(profile, t)


ALLOWED_PLATFORMS = {"wheeled_rover", "sensor_box", "robot_arm_base", "pan_tilt_mount", "generic_chassis", "legged_robot", "drone_frame", "display_station"}
ALLOWED_MODULES = {
    "base_plate", "top_cover", "bottom_shell", "lid", "controller_tray", "motor_driver_tray", "stepper_driver_tray",
    "battery_tray", "battery_18650_holder", "battery_strap_plate", "motor_clamp", "n20_motor_mount", "caster_mount",
    "sensor_bracket", "hc_sr04_front_mount", "small_sensor_clip", "display_bezel", "standoffs", "wheel_hub",
    "servo_bracket", "sg90_servo_bracket", "standard_servo_u_bracket", "rotating_base", "rotating_base_servo_mount",
    "robot_arm_base_plate", "arm_link", "arm_link_short", "arm_link_long", "elbow_joint_plate", "gripper_jaw_pair",
    "gripper_palm", "gripper_finger_pair", "gripper_finger", "servo_horn_adapter", "camera_mount", "potentiometer_panel",
    "joystick_panel", "universal_bracket", "universal_l_bracket", "universal_u_bracket", "servo_power_distribution_plate",
    "relay_module_tray", "buzzer_clip", "led_strip_clip", "cable_clip_set", "screw_fit_test", "pan_tilt_base",
    "x_frame_plate", "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad", "side_servo_rail", "track_side_plate",
    "motor_pod", "prop_guard_segment", "display_stand", "weather_louver",
}




BLOCKED_BY_PLATFORM = {
    "wheeled_rover": {
        "gripper_finger", "gripper_finger_pair", "gripper_palm", "arm_link", "arm_link_short", "arm_link_long",
        "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad", "side_servo_rail",
        "x_frame_plate", "motor_pod", "prop_guard_segment", "weather_louver", "display_stand",
    },
    "robot_arm_base": {
        "wheel_hub", "caster_mount", "n20_motor_mount", "motor_clamp", "track_side_plate", "motor_driver_tray",
        "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad", "side_servo_rail",
        "x_frame_plate", "motor_pod", "prop_guard_segment", "weather_louver", "bottom_shell", "lid",
    },
    "legged_robot": {
        "wheel_hub", "caster_mount", "n20_motor_mount", "motor_clamp", "track_side_plate", "motor_driver_tray",
        "robot_arm_base_plate", "rotating_base_servo_mount", "rotating_base", "gripper_palm", "gripper_finger", "gripper_finger_pair", "gripper_jaw_pair",
        "x_frame_plate", "motor_pod", "prop_guard_segment", "weather_louver", "display_stand", "bottom_shell", "lid",
    },
    "sensor_box": {
        "wheel_hub", "caster_mount", "n20_motor_mount", "motor_clamp", "track_side_plate", "motor_driver_tray",
        "standard_servo_u_bracket", "sg90_servo_bracket", "servo_horn_adapter", "arm_link", "arm_link_short", "arm_link_long",
        "robot_arm_base_plate", "rotating_base_servo_mount", "gripper_palm", "gripper_finger", "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad",
        "x_frame_plate", "motor_pod", "prop_guard_segment",
    },
    "display_station": {
        "wheel_hub", "caster_mount", "n20_motor_mount", "motor_clamp", "track_side_plate", "motor_driver_tray",
        "standard_servo_u_bracket", "sg90_servo_bracket", "servo_horn_adapter", "arm_link", "arm_link_short", "arm_link_long",
        "robot_arm_base_plate", "rotating_base_servo_mount", "gripper_palm", "gripper_finger", "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad",
        "x_frame_plate", "motor_pod", "prop_guard_segment", "weather_louver",
    },
    "drone_frame": {
        "wheel_hub", "caster_mount", "n20_motor_mount", "motor_clamp", "track_side_plate", "motor_driver_tray",
        "standard_servo_u_bracket", "sg90_servo_bracket", "servo_horn_adapter", "arm_link", "arm_link_short", "arm_link_long",
        "robot_arm_base_plate", "rotating_base_servo_mount", "gripper_palm", "gripper_finger", "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad",
        "bottom_shell", "lid", "display_stand", "weather_louver",
    },
    "generic_chassis": {
        "wheel_hub", "caster_mount", "n20_motor_mount", "motor_clamp", "track_side_plate", "motor_driver_tray",
        "standard_servo_u_bracket", "sg90_servo_bracket", "servo_horn_adapter", "arm_link", "arm_link_short", "arm_link_long",
        "robot_arm_base_plate", "rotating_base_servo_mount", "gripper_palm", "gripper_finger", "legged_body_plate", "leg_link_short", "leg_link_long", "foot_pad",
        "x_frame_plate", "motor_pod", "prop_guard_segment", "weather_louver", "display_stand",
    },
}

def _apply_platform_filter(parts: list[PartSpec], platform: str, warnings: list[str]) -> list[PartSpec]:
    blocked = BLOCKED_BY_PLATFORM.get(platform, set())
    kept: list[PartSpec] = []
    removed: list[str] = []
    for part in parts:
        if part.name in blocked:
            removed.append(part.name)
            continue
        kept.append(part)
    if removed:
        unique = sorted(set(removed))
        warnings.append("Unpassende Druckteile entfernt: " + ", ".join(unique) + ".")
    return kept

def _upsert(parts: list[PartSpec], name: str, min_q: int, role: str, warnings: list[str]) -> None:
    for p in parts:
        if p.name == name:
            if p.quantity < min_q:
                warnings.append(f"{name}: Stückzahl von {p.quantity} auf {min_q} erhöht.")
                p.quantity = min_q
            return
    parts.append(_p(name, min_q, role))
    warnings.append(f"{name}: fehlendes Pflichtteil ergänzt ({min_q}x).")




SINGLETON_MAX_PARTS = {
    "base_plate", "top_cover", "bottom_shell", "lid", "controller_tray", "battery_tray", "battery_18650_holder",
    "battery_strap_plate", "motor_driver_tray", "stepper_driver_tray", "caster_mount", "sensor_bracket", "hc_sr04_front_mount",
    "display_bezel", "weather_louver", "camera_mount", "robot_arm_base_plate", "rotating_base_servo_mount",
    "gripper_palm", "servo_power_distribution_plate", "potentiometer_panel", "joystick_panel", "pan_tilt_base",
    "x_frame_plate", "legged_body_plate", "track_side_plate", "relay_module_tray", "buzzer_clip", "led_strip_clip",
}

def _cap_singletons(parts: list[PartSpec], warnings: list[str]) -> list[PartSpec]:
    for part in parts:
        if part.name in SINGLETON_MAX_PARTS and part.quantity > 1:
            warnings.append(f"{part.name}: doppelte Einträge auf 1 reduziert.")
            part.quantity = 1
    return parts

def normalize_model_profile(profile: ModelProfile, raw_text: str = "") -> ModelProfile:
    warnings = list(profile.sanity_warnings or [])
    parts = [p for p in (profile.parts or []) if p.name in ALLOWED_MODULES and p.quantity > 0]
    if not parts and profile.modules:
        counts = Counter(m for m in profile.modules if m in ALLOWED_MODULES)
        parts = [_p(name, q, "Aus Modul-Liste übernommen.") for name, q in counts.items()]

    if profile.platform == "wheeled_rover":
        wc = profile.wheel_count or _wheel_count(raw_text) or 4
        wc = wc if wc in {2, 3, 4, 6, 8} else 4
        profile.wheel_count = wc
        _upsert(parts, "base_plate", 1, "Chassis-Grundplatte.", warnings)
        _upsert(parts, "controller_tray", 1, "Controllerhalter.", warnings)
        _upsert(parts, "battery_tray", 1, "Akkuhalter.", warnings)
        _upsert(parts, "motor_driver_tray", 1, "Motortreiberhalter.", warnings)
        if wc > 0:
            _upsert(parts, "wheel_hub", wc, "Radnaben passend zur Radanzahl.", warnings)
            _upsert(parts, "n20_motor_mount", 2 if wc <= 3 else min(wc, 6), "Motorhalter passend zur Radanzahl.", warnings)
        if wc == 2:
            _upsert(parts, "caster_mount", 1, "Caster für Zweirad-Rover.", warnings)
        _upsert(parts, "standoffs", 2, "Abstandshalter.", warnings)
    elif profile.platform == "robot_arm_base":
        _upsert(parts, "robot_arm_base_plate", 1, "Grundplatte.", warnings)
        _upsert(parts, "rotating_base_servo_mount", 1, "Drehbasis.", warnings)
        _upsert(parts, "standard_servo_u_bracket", 3, "Servo-U-Halter.", warnings)
        _upsert(parts, "servo_horn_adapter", 3, "Servohorn-Adapter.", warnings)
        _upsert(parts, "arm_link_long", 2, "Armsegmente.", warnings)
        _upsert(parts, "elbow_joint_plate", 2, "Gelenkplatten.", warnings)
        _upsert(parts, "gripper_palm", 1, "Greiferbasis.", warnings)
        _upsert(parts, "gripper_finger", 2, "Zwei Greiferfinger.", warnings)
        _upsert(parts, "servo_power_distribution_plate", 1, "Servostromplatte.", warnings)
        _upsert(parts, "controller_tray", 1, "Controllerhalter.", warnings)
    elif profile.platform == "legged_robot":
        legs = _leg_count(raw_text)
        explicit_servos = _count_word(raw_text, [r"(\d+)\s*(?:servos|servo)"])
        servo_per_leg = max(2, min(3, round(explicit_servos / legs))) if explicit_servos else (3 if _has_any(raw_text, ["3dof", "3 dof", "knie", "knee"]) else 2)
        _upsert(parts, "legged_body_plate", 1, "Körperplatte.", warnings)
        _upsert(parts, "controller_tray", 1, "Controllerhalter.", warnings)
        _upsert(parts, "battery_tray", 1, "Akkuhalter.", warnings)
        _upsert(parts, "servo_power_distribution_plate", 1, "Servostromplatte.", warnings)
        _upsert(parts, "standard_servo_u_bracket", max(legs * servo_per_leg, 4), "Servo-U-Halter pro Beingelenk.", warnings)
        _upsert(parts, "leg_link_long", legs, "Obere Beinsegmente.", warnings)
        _upsert(parts, "leg_link_short", legs, "Untere Beinsegmente.", warnings)
        _upsert(parts, "foot_pad", legs, "Ein Fuß pro Bein.", warnings)
        _upsert(parts, "standoffs", 2, "Abstandshalter.", warnings)
    elif profile.platform == "sensor_box":
        _upsert(parts, "bottom_shell", 1, "Gehäuseunterteil.", warnings)
        _upsert(parts, "lid", 1, "Deckel.", warnings)
        _upsert(parts, "controller_tray", 1, "Controllerhalter.", warnings)
        _upsert(parts, "standoffs", 1, "Abstandshalter.", warnings)
    else:
        _upsert(parts, "base_plate", 1, "Montageplatte.", warnings)
        _upsert(parts, "controller_tray", 1, "Controllerhalter.", warnings)
        _upsert(parts, "standoffs", 1, "Abstandshalter.", warnings)

    parts = _apply_platform_filter(parts, profile.platform, warnings)
    parts = _merge_parts(parts)
    parts = _cap_singletons(parts, warnings)
    profile.parts = parts
    profile.modules = _parts_to_modules(parts)
    profile.sanity_warnings = warnings
    return profile


def build_model_profile(title: str, description: str, spec: str = "", llm_json: str = "") -> ModelProfile:
    raw = f"{title}\n{description}\n{spec}"
    fallback = _keyword_profile(raw)
    if not llm_json.strip():
        return fallback
    try:
        match = re.search(r"\{.*\}", llm_json, re.DOTALL)
        data = json.loads(match.group(0) if match else llm_json)
        requested_platform = str(data.get("platform") or "")
        platform = requested_platform if requested_platform in ALLOWED_PLATFORMS else fallback.platform

        # LLM may suggest additional parts, but cannot remove sanity-required parts.
        llm_parts: list[PartSpec] = []
        raw_parts = data.get("parts") if isinstance(data.get("parts"), list) else []
        for item in raw_parts:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            if name in ALLOWED_MODULES:
                llm_parts.append(_p(name, int(item.get("quantity") or 1), str(item.get("role") or "Von LLM vorgeschlagen."), str(item.get("check") or "Maße prüfen.")))
        raw_modules = data.get("modules") if isinstance(data.get("modules"), list) else []
        for m in raw_modules:
            if str(m) in ALLOWED_MODULES:
                llm_parts.append(_p(str(m), 1, "Von LLM-Modulliste vorgeschlagen."))

        controller_from_llm = str(data.get("controller") or fallback.controller)
        controller = fallback.controller if fallback.controller != "generic_controller" else controller_from_llm
        if fallback.controller.startswith("arduino") and "esp32" in controller_from_llm.lower():
            controller = fallback.controller
        if "arduino" in raw.lower() and not controller.startswith("arduino"):
            controller = fallback.controller

        dims = data.get("dimensions") if isinstance(data.get("dimensions"), dict) else fallback.dimensions
        length = int(dims.get("length", fallback.dimensions["length"]))
        width = int(dims.get("width", fallback.dimensions["width"]))
        thickness = int(dims.get("thickness", fallback.dimensions["thickness"]))
        length = max(70, min(260, length)); width = max(50, min(200, width)); thickness = max(3, min(8, thickness))

        # If text clearly says arm/legged/sensor, do not let weak LLM force rover.
        if fallback.platform in {"robot_arm_base", "pan_tilt_mount", "sensor_box", "legged_robot", "display_station"} and platform == "wheeled_rover":
            platform = fallback.platform

        profile = ModelProfile(
            platform=platform,
            controller=controller,
            modules=[],
            wheel_count=int(data.get("wheel_count") or fallback.wheel_count or 0),
            has_camera=bool(data.get("has_camera", fallback.has_camera)),
            has_battery=bool(data.get("has_battery", fallback.has_battery)),
            has_motor_driver=bool(data.get("has_motor_driver", fallback.has_motor_driver)),
            dimensions={"length": length, "width": width, "thickness": thickness},
            notes=str(data.get("notes") or fallback.notes),
            parts=_merge_parts(llm_parts + fallback.parts),
            sanity_warnings=list(fallback.sanity_warnings),
        )
        return normalize_model_profile(profile, raw.lower())
    except Exception:
        return fallback


def profile_to_json(profile: ModelProfile) -> str:
    return json.dumps(asdict(profile), ensure_ascii=False, indent=2)


def printable_parts_markdown(profile: ModelProfile) -> str:
    lines = [
        "# Druckteileliste",
        "",
        f"Plattform: {profile.platform}",
        f"Controller: {profile.controller}",
        "",
        "## Automatisch geprüfte Stückzahlen",
        "",
    ]
    for p in profile.parts:
        lines += [f"### {p.quantity}x {p.name}", f"Zweck: {p.role or 'Druckbares Modul.'}", f"Prüfen: {p.check}", ""]
    if profile.sanity_warnings:
        lines += ["## Sanity-Check", ""]
        lines += [f"- {w}" for w in profile.sanity_warnings]
        lines.append("")
    lines += [
        "## Wichtig",
        "Diese Liste ist eine Lern- und Entwurfsvorlage. Vor dem Druck müssen echte Komponenten, Schrauben, Servoabmessungen, Kabelwege und Wandstärken geprüft werden.",
    ]
    return "\n".join(lines).strip() + "\n"
