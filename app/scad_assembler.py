from __future__ import annotations

from app.model_profile import ModelProfile


HEADER = r'''// RoboForge Local - universelle komponentenbasierte OpenSCAD-Teilebibliothek
// Deutsche finale Version v7.1.
// Dieses Modell ist eine Lernvorlage, keine produktionsfertige CAD-Datei.
// Ziel: mehr echte mechanische Einzelteile statt einer dekorativen Szene.
// Reale Platinen-, Akku-, Motor-, Servo- und Schraubenmaße vor dem Druck prüfen.

$fn = 48;
preview_colors = false;
fit_clearance = 0.4;
m3_clearance = 3.2;
plate_thickness = 4;

module maybe_color(name) {
    if (preview_colors) {
        if (name == "plate") color([0.6,0.6,0.6]) children();
        else if (name == "tray") color([0.2,0.5,0.8]) children();
        else if (name == "bracket") color([0.8,0.5,0.2]) children();
        else if (name == "arm") color([0.7,0.7,0.2]) children();
        else if (name == "test") color([0.3,0.7,0.3]) children();
        else children();
    } else children();
}

module label2d(txt, size=5) {
    linear_extrude(height=0.6) text(txt, size=size, halign="center", valign="center");
}

module rounded_plate(l, w, h, r=6) {
    maybe_color("plate") linear_extrude(height=h) hull() {
        translate([r, r]) circle(r=r);
        translate([l-r, r]) circle(r=r);
        translate([r, w-r]) circle(r=r);
        translate([l-r, w-r]) circle(r=r);
    }
}

module m3_hole(x, y, h=10) {
    translate([x, y, -0.1]) cylinder(h=h, d=m3_clearance);
}

module slot(x, y, l, w, h=10) {
    translate([x, y, -0.1]) hull() {
        cylinder(h=h, d=w);
        translate([l,0,0]) cylinder(h=h, d=w);
    }
}

module mounting_grid(l, w, h, step=20) {
    for (x=[20:step:l-20]) for (y=[20:step:w-20]) m3_hole(x, y, h+0.2);
}

module tray_box(l=60, w=35, wall=3, h=8, label="TRAY") {
    maybe_color("tray") difference() {
        union() {
            cube([l + wall*2, w + wall*2, h]);
            translate([(l+wall*2)/2, -3, h]) label2d(label, 5);
        }
        translate([wall, wall, 2]) cube([l, w, h+0.1]);
        m3_hole(8, 8, h+1); m3_hole(l+wall*2-8, 8, h+1);
        m3_hole(8, w+wall*2-8, h+1); m3_hole(l+wall*2-8, w+wall*2-8, h+1);
    }
}

module base_plate(l=120, w=90, h=4) {
    difference() {
        rounded_plate(l, w, h);
        mounting_grid(l, w, h);
        slot(l/2-18, w/2, 36, 5, h+0.2);
        slot(12, w/2, 18, 4, h+0.2);
        slot(l-30, w/2, 18, 4, h+0.2);
    }
}

module robot_arm_base_plate(l=145, w=110, h=4) {
    difference() {
        rounded_plate(l, w, h, 7);
        mounting_grid(l, w, h, 18);
        translate([l-55, w/2-18, -0.1]) cylinder(h=h+0.2, d=42);
        for(a=[0:90:270]) translate([l-55 + cos(a)*30, w/2 + sin(a)*30, -0.1]) cylinder(h=h+0.2, d=m3_clearance);
        slot(18, 18, 35, 5, h+0.2);
        slot(18, w-18, 35, 5, h+0.2);
    }
}

module x_frame_plate(l=130, h=4) {
    maybe_color("plate") difference() {
        union() {
            translate([0, l/2-10, 0]) cube([l,20,h]);
            translate([l/2-10,0,0]) cube([20,l,h]);
            translate([l/2,l/2,0]) cylinder(h=h, d=36);
        }
        translate([l/2,l/2,-0.1]) cylinder(h=h+0.2, d=18);
        for(a=[45:90:315]) translate([l/2+cos(a)*45,l/2+sin(a)*45,-0.1]) cylinder(h=h+0.2,d=m3_clearance);
    }
}

module top_cover(l=110, w=75, h=3) {
    difference() {
        rounded_plate(l, w, h, 5);
        m3_hole(12, 12, h+0.2); m3_hole(l-12, 12, h+0.2);
        m3_hole(12, w-12, h+0.2); m3_hole(l-12, w-12, h+0.2);
        slot(l/2-22, w/2, 44, 8, h+0.2);
    }
}

module controller_tray(controller="GEN") {
    if (controller == "arduino_uno") tray_box(72, 54, 3, 9, "ARDUINO");
    else if (controller == "arduino_nano") tray_box(48, 20, 3, 8, "NANO");
    else if (controller == "arduino_mega") tray_box(102, 54, 3, 9, "MEGA");
    else if (controller == "raspberry_pi_pico") tray_box(55, 24, 3, 8, "PICO");
    else if (controller == "esp32" || controller == "esp32_cam") tray_box(58, 32, 3, 8, "ESP32");
    else tray_box(64, 38, 3, 8, "CTRL");
}

module motor_driver_tray() { tray_box(52, 36, 3, 8, "DRIVER"); }
module stepper_driver_tray() { tray_box(42, 24, 3, 8, "A4988"); }
module relay_module_tray() { tray_box(50, 35, 3, 8, "RELAY"); }

module battery_tray(l=72, w=42, h=12) {
    maybe_color("tray") difference() {
        union() { cube([l+6, w+6, h]); translate([(l+6)/2, -3, h]) label2d("AKKU",5); }
        translate([3, 3, 2]) cube([l, w, h+0.1]);
        slot(8, 0, 14, 5, h+0.2); slot(l-14, w+6, 14, 5, h+0.2);
    }
}

module battery_18650_holder() {
    maybe_color("tray") difference() {
        cube([84, 24, 14]);
        translate([9,12,5]) rotate([0,90,0]) cylinder(h=66, d=18.6);
        translate([8, -0.1, 5]) cube([12, 24.2, 7]);
        m3_hole(5,5,15); m3_hole(79,19,15);
    }
}

module battery_strap_plate() {
    maybe_color("plate") difference() {
        rounded_plate(80, 42, 4, 5);
        slot(8,10,64,5,5); slot(8,30,64,5,5);
        m3_hole(8,8,5); m3_hole(72,34,5);
    }
}

module motor_clamp() {
    maybe_color("bracket") difference() {
        cube([42, 22, 18]);
        translate([5, -0.1, 5]) cube([32, 22.2, 9]);
        m3_hole(7, 11, 19); m3_hole(35, 11, 19);
    }
}

module n20_motor_mount() {
    maybe_color("bracket") difference() {
        union() { cube([38,18,20]); translate([0,18,0]) cube([38,8,4]); }
        translate([8,-0.1,7]) cube([22,18.2,10]);
        translate([19,-0.1,12]) rotate([-90,0,0]) cylinder(h=18.4,d=12);
        m3_hole(6,22,5); m3_hole(32,22,5);
    }
}

module caster_mount() {
    maybe_color("bracket") difference() {
        rounded_plate(42,32,5,5);
        translate([21,16,-0.1]) cylinder(h=5.2,d=18);
        m3_hole(8,8,6); m3_hole(34,8,6); m3_hole(8,24,6); m3_hole(34,24,6);
    }
}

module sensor_bracket() {
    maybe_color("bracket") difference() {
        union() {
            cube([55, 8, 38]);
            translate([0, 0, 30]) cube([55, 20, 8]);
            translate([5, 8, 0]) cube([8, 12, 30]);
            translate([42, 8, 0]) cube([8, 12, 30]);
        }
        translate([14, -0.1, 33]) rotate([-90,0,0]) cylinder(h=22, d=16);
        translate([41, -0.1, 33]) rotate([-90,0,0]) cylinder(h=22, d=16);
        m3_hole(8, 4, 9); m3_hole(47, 4, 9);
    }
}

module hc_sr04_front_mount() {
    maybe_color("bracket") difference() {
        union() { cube([60, 6, 34]); translate([0,6,0]) cube([60,12,6]); }
        translate([17,-0.1,22]) rotate([-90,0,0]) cylinder(h=7,d=16.5);
        translate([43,-0.1,22]) rotate([-90,0,0]) cylinder(h=7,d=16.5);
        m3_hole(6,12,7); m3_hole(54,12,7);
    }
}

module small_sensor_clip() {
    maybe_color("bracket") difference() {
        cube([34,24,10]);
        translate([4,4,2]) cube([26,16,9]);
        m3_hole(5,5,11); m3_hole(29,19,11);
    }
}

module standoff_set() {
    for (x=[0,18,36,54]) translate([x,0,0]) difference() {
        cylinder(h=18, d=8);
        translate([0,0,-0.1]) cylinder(h=18.2, d=m3_clearance);
    }
}

module wheel_hub() {
    maybe_color("bracket") difference() {
        union() { cylinder(h=10, d=36); translate([0,0,10]) cylinder(h=3,d=20); }
        translate([0,0,-0.1]) cylinder(h=13.2, d=5.2);
        for(a=[0:60:300]) rotate([0,0,a]) translate([9,-2,-0.1]) cube([9,4,10.2]);
    }
}

module sg90_servo_bracket() {
    // 9g/SG90 style cradle. Dimensions are intentionally parametric placeholders.
    maybe_color("bracket") difference() {
        union() {
            cube([36, 18, 28]);
            translate([-6,0,0]) cube([48,18,4]);
            translate([0,-4,22]) cube([36,4,6]);
        }
        translate([3, 3, 5]) cube([30, 12, 25]);
        translate([18,-4.1,25]) rotate([-90,0,0]) cylinder(h=5,d=7);
        m3_hole(-1,4,5); m3_hole(37,14,5);
    }
}

module standard_servo_u_bracket() {
    // MG996R/MG995 class U bracket concept.
    maybe_color("bracket") difference() {
        union() {
            cube([52, 12, 38]);
            translate([0,36,0]) cube([52,12,38]);
            translate([0,12,0]) cube([52,24,5]);
        }
        translate([26,-0.1,25]) rotate([-90,0,0]) cylinder(h=48.2,d=8);
        translate([8,6,-0.1]) cylinder(h=5.2,d=m3_clearance);
        translate([44,42,-0.1]) cylinder(h=5.2,d=m3_clearance);
    }
}

module rotating_base_servo_mount() {
    maybe_color("arm") difference() {
        union() {
            cylinder(h=8, d=76);
            translate([-30,-20,8]) cube([60,40,8]);
            translate([-24,-12,16]) cube([48,24,14]);
        }
        translate([0,0,-0.1]) cylinder(h=30.2, d=8);
        for(a=[0:90:270]) rotate([0,0,a]) translate([28,0,-0.1]) cylinder(h=30.2, d=m3_clearance);
        translate([-18,-7,17]) cube([36,14,14.2]);
    }
}

module rotating_base() { rotating_base_servo_mount(); }

module pan_tilt_base() {
    maybe_color("arm") difference() {
        union() { rounded_plate(70,55,5,6); translate([18,12,5]) cube([34,31,24]); }
        translate([35,27.5,13]) rotate([0,90,0]) cylinder(h=40,d=8);
        m3_hole(8,8,6); m3_hole(62,47,6);
        translate([22,18,6]) cube([26,19,24]);
    }
}

module arm_link(l=105, w=18, h=6) {
    maybe_color("arm") difference() {
        hull() {
            translate([w/2,w/2,0]) cylinder(h=h, d=w);
            translate([l-w/2,w/2,0]) cylinder(h=h, d=w);
        }
        translate([w/2,w/2,-0.1]) cylinder(h=h+0.2, d=5.5);
        translate([l-w/2,w/2,-0.1]) cylinder(h=h+0.2, d=5.5);
        for(x=[35:25:l-35]) translate([x,w/2,-0.1]) cylinder(h=h+0.2, d=8);
    }
}
module arm_link_short() { arm_link(75,18,6); }
module arm_link_long() { arm_link(118,20,6); }

module leg_link_long() {
    // Oberes Beinsegment für Spinnen-, Hexapod- oder Hundroboter.
    // Eigenes Modul, damit Beinprofile nicht fälschlich Roboterarm-Links verwenden.
    maybe_color("arm") difference() {
        hull() {
            translate([11,11,0]) cylinder(h=6, d=22);
            translate([107,11,0]) cylinder(h=6, d=22);
        }
        translate([11,11,-0.1]) cylinder(h=6.2, d=5.6);
        translate([59,11,-0.1]) cylinder(h=6.2, d=5.6);
        translate([107,11,-0.1]) cylinder(h=6.2, d=5.6);
        // Materialfenster zur Gewichtsreduzierung.
        translate([28,5,-0.1]) cube([22,12,6.2]);
        translate([68,5,-0.1]) cube([22,12,6.2]);
    }
}

module leg_link_short() {
    // Unteres Beinsegment für modulare Laufroboter.
    maybe_color("arm") difference() {
        hull() {
            translate([10,10,0]) cylinder(h=6, d=20);
            translate([68,10,0]) cylinder(h=6, d=20);
        }
        translate([10,10,-0.1]) cylinder(h=6.2, d=5.6);
        translate([39,10,-0.1]) cylinder(h=6.2, d=5.6);
        translate([68,10,-0.1]) cylinder(h=6.2, d=5.6);
        translate([25,4,-0.1]) cube([28,12,6.2]);
    }
}

module elbow_joint_plate() {
    maybe_color("arm") difference() {
        rounded_plate(62,38,6,6);
        translate([19,19,-0.1]) cylinder(h=6.2,d=6);
        translate([43,19,-0.1]) cylinder(h=6.2,d=6);
        m3_hole(8,8,7); m3_hole(54,30,7);
    }
}

module gripper_palm() {
    maybe_color("arm") difference() {
        union() { cube([54,38,8]); translate([17,-14,0]) cube([20,14,8]); }
        translate([27,19,-0.1]) cylinder(h=8.2,d=8);
        m3_hole(8,8,9); m3_hole(46,8,9); m3_hole(8,30,9); m3_hole(46,30,9);
    }
}

module gripper_finger_pair() {
    maybe_color("arm") union() {
        difference() {
            translate([0,0,0]) cube([72,10,8]);
            translate([14,-0.1,-0.1]) cube([10,10.2,8.2]);
            translate([50,-0.1,-0.1]) cube([8,10.2,8.2]);
            m3_hole(8,5,9); m3_hole(64,5,9);
        }
        difference() {
            translate([0,28,0]) cube([72,10,8]);
            translate([14,27.9,-0.1]) cube([10,10.2,8.2]);
            translate([50,27.9,-0.1]) cube([8,10.2,8.2]);
            m3_hole(8,33,9); m3_hole(64,33,9);
        }
    }
}

module servo_horn_adapter() {
    maybe_color("arm") difference() {
        union() { cylinder(h=5,d=30); for(a=[0:90:270]) rotate([0,0,a]) translate([0,-4,0]) cube([38,8,5]); }
        translate([0,0,-0.1]) cylinder(h=5.2,d=5);
        for(a=[0:45:315]) rotate([0,0,a]) translate([11,0,-0.1]) cylinder(h=5.2,d=1.8);
    }
}

module servo_power_distribution_plate() {
    maybe_color("plate") difference() {
        rounded_plate(84,42,4,5);
        for(x=[14,28,42,56,70]) { slot(x, 12, 0.1, 3, 5); slot(x, 30, 0.1, 3, 5); }
        m3_hole(6,6,5); m3_hole(78,6,5); m3_hole(6,36,5); m3_hole(78,36,5);
    }
}

module camera_mount() {
    maybe_color("bracket") difference() {
        union() {
            cube([45, 10, 45]);
            translate([0, 0, 35]) cube([45, 28, 10]);
        }
        translate([22.5, -0.1, 40]) rotate([-90,0,0]) cylinder(h=30, d=18);
        m3_hole(8, 5, 12); m3_hole(37, 5, 12);
    }
}

module display_bezel() {
    maybe_color("bracket") difference() {
        cube([72, 34, 4]);
        translate([6, 5, -0.1]) cube([60, 24, 4.2]);
        m3_hole(4,4,5); m3_hole(68,4,5); m3_hole(4,30,5); m3_hole(68,30,5);
    }
}

module potentiometer_panel() {
    maybe_color("bracket") difference() {
        cube([80, 36, 4]);
        for(x=[18,40,62]) translate([x,18,-0.1]) cylinder(h=4.2, d=7.5);
        m3_hole(6,6,5); m3_hole(74,30,5);
    }
}

module joystick_panel() {
    maybe_color("bracket") difference() {
        cube([64, 54, 4]);
        translate([32,27,-0.1]) cylinder(h=4.2, d=28);
        m3_hole(7,7,5); m3_hole(57,7,5); m3_hole(7,47,5); m3_hole(57,47,5);
    }
}

module universal_l_bracket() {
    maybe_color("bracket") difference() {
        union() { cube([50,5,30]); cube([50,28,5]); }
        m3_hole(8,14,6); m3_hole(42,14,6);
        translate([12,-0.1,18]) rotate([-90,0,0]) cylinder(h=6,d=m3_clearance);
        translate([38,-0.1,18]) rotate([-90,0,0]) cylinder(h=6,d=m3_clearance);
    }
}

module universal_u_bracket() {
    maybe_color("bracket") difference() {
        union() { cube([52,6,28]); translate([0,32,0]) cube([52,6,28]); translate([0,6,0]) cube([52,26,5]); }
        translate([26,-0.1,17]) rotate([-90,0,0]) cylinder(h=38.2,d=6);
        m3_hole(8,18,6); m3_hole(44,18,6);
    }
}
module universal_bracket() { universal_u_bracket(); }

module cable_clip_set() {
    maybe_color("bracket") for(i=[0:3]) translate([i*18,0,0]) difference() {
        cube([12,16,8]);
        translate([6,8,-0.1]) cylinder(h=8.2,d=7);
        translate([6,16,-0.1]) cube([2,5,8.2], center=true);
    }
}

module buzzer_clip() {
    maybe_color("bracket") difference() { cube([28,28,8]); translate([14,14,-0.1]) cylinder(h=8.2,d=18); m3_hole(4,4,9); m3_hole(24,24,9); }
}

module led_strip_clip() {
    maybe_color("bracket") difference() { cube([70,12,6]); translate([5,3,2]) cube([60,6,5]); m3_hole(4,6,7); m3_hole(66,6,7); }
}

module screw_fit_test() {
    maybe_color("test") difference() {
        cube([70,18,4]);
        for(i=[0:4]) translate([10+i*12,9,-0.1]) cylinder(h=4.2,d=2.8+i*0.2);
    }
}

module sensor_box_bottom(l=115, w=85, h=28) {
    maybe_color("plate") difference() {
        cube([l, w, h]);
        translate([3,3,3]) cube([l-6, w-6, h+0.1]);
        translate([l-28, w-0.1, 10]) cube([18, 4, 8]);
        m3_hole(10,10,h+0.2); m3_hole(l-10,10,h+0.2); m3_hole(10,w-10,h+0.2); m3_hole(l-10,w-10,h+0.2);
    }
}
'''

HEADER += r'''

module legged_body_plate(l=150, w=110, h=4) {
    difference() {
        rounded_plate(l, w, h, 10);
        mounting_grid(l, w, h, 22);
        for (yy=[18, w-18]) for (xx=[22:28:l-22]) slot(xx-6, yy, 12, 4, h+0.2);
        slot(l/2-24, w/2, 48, 7, h+0.2);
    }
}

module foot_pad() {
    maybe_color("bracket") difference() {
        union() { rounded_plate(42, 26, 5, 6); translate([7,8,5]) cube([28,10,5]); }
        m3_hole(8,13,11); m3_hole(34,13,11);
        slot(13,13,16,4,11);
    }
}

module side_servo_rail() {
    maybe_color("bracket") difference() {
        cube([130, 18, 8]);
        for (xx=[15:25:115]) { m3_hole(xx, 9, 9); translate([xx-5,3,-0.1]) cube([10,12,8.2]); }
    }
}

module track_side_plate() {
    maybe_color("bracket") difference() {
        hull() { translate([18,18,0]) cylinder(h=5,d=36); translate([110,18,0]) cylinder(h=5,d=36); }
        translate([18,18,-0.1]) cylinder(h=5.2,d=18);
        translate([110,18,-0.1]) cylinder(h=5.2,d=18);
        for(xx=[42:20:88]) m3_hole(xx,18,6);
    }
}

module motor_pod() {
    maybe_color("bracket") difference() {
        union() { cube([42,30,10]); translate([21,15,10]) cylinder(h=12,d=24); }
        translate([21,15,-0.1]) cylinder(h=22.2,d=12);
        m3_hole(6,6,11); m3_hole(36,24,11);
    }
}

module prop_guard_segment() {
    maybe_color("bracket") difference() {
        linear_extrude(height=4) difference() { circle(d=72); circle(d=62); translate([-40,-40]) square([80,40]); }
        translate([0,0,-0.1]) cylinder(h=4.2,d=8);
    }
}

module display_stand() {
    maybe_color("bracket") difference() {
        union() { cube([14,58,8]); translate([0,44,8]) rotate([25,0,0]) cube([14,8,42]); }
        m3_hole(7,10,9); m3_hole(7,46,9);
    }
}

module weather_louver() {
    maybe_color("bracket") union() {
        difference() { cube([78,36,4]); translate([6,6,-0.1]) cube([66,24,4.2]); }
        for (yy=[7:7:28]) translate([8,yy,4]) rotate([20,0,0]) cube([62,3,5]);
    }
}

module gripper_finger() {
    maybe_color("arm") difference() {
        union() { cube([76,11,8]); translate([58,0,0]) cube([18,18,8]); }
        translate([14,-0.1,-0.1]) cube([10,11.2,8.2]);
        translate([46,-0.1,-0.1]) cube([8,11.2,8.2]);
        m3_hole(8,5.5,9); m3_hole(66,9,9);
    }
}

'''


def _module_call(module_name: str, profile: ModelProfile) -> tuple[str, int, int]:
    l = profile.dimensions.get("length", 120)
    w = profile.dimensions.get("width", 90)
    h = profile.dimensions.get("thickness", 4)
    controller = profile.controller
    calls = {
        "base_plate": (f"base_plate({l}, {w}, {h});", l, w),
        "robot_arm_base_plate": (f"robot_arm_base_plate({max(l,135)}, {max(w,100)}, {h});", max(l,135), max(w,100)),
        "x_frame_plate": ("x_frame_plate(130, 4);", 132, 132),
        "top_cover": (f"top_cover({max(l-20, 90)}, {max(w-20, 60)}, 3);", max(l-20, 90), max(w-20, 60)),
        "bottom_shell": (f"sensor_box_bottom({l}, {w}, 28);", l, w),
        "lid": (f"top_cover({l}, {w}, 3);", l, w),
        "controller_tray": (f"controller_tray(\"{controller}\");", 116 if controller == "arduino_mega" else 90, 68 if controller.startswith("arduino") else 50),
        "motor_driver_tray": ("motor_driver_tray();", 64, 48),
        "stepper_driver_tray": ("stepper_driver_tray();", 54, 36),
        "relay_module_tray": ("relay_module_tray();", 62, 47),
        "battery_tray": ("battery_tray(72, 42, 12);", 84, 54),
        "battery_18650_holder": ("battery_18650_holder();", 90, 30),
        "battery_strap_plate": ("battery_strap_plate();", 86, 48),
        "motor_clamp": ("motor_clamp();", 46, 26),
        "n20_motor_mount": ("n20_motor_mount();", 44, 32),
        "caster_mount": ("caster_mount();", 46, 36),
        "sensor_bracket": ("sensor_bracket();", 60, 45),
        "hc_sr04_front_mount": ("hc_sr04_front_mount();", 64, 24),
        "small_sensor_clip": ("small_sensor_clip();", 40, 30),
        "display_bezel": ("display_bezel();", 76, 38),
        "standoffs": ("standoff_set();", 66, 20),
        "wheel_hub": ("translate([18,18,0]) wheel_hub();", 42, 42),
        "sg90_servo_bracket": ("sg90_servo_bracket();", 54, 28),
        "standard_servo_u_bracket": ("standard_servo_u_bracket();", 58, 52),
        "servo_bracket": ("sg90_servo_bracket();", 54, 28),
        "rotating_base_servo_mount": ("rotating_base_servo_mount();", 82, 82),
        "rotating_base": ("rotating_base_servo_mount();", 82, 82),
        "pan_tilt_base": ("pan_tilt_base();", 76, 62),
        "arm_link": ("arm_link(105, 18, 6);", 112, 26),
        "arm_link_short": ("arm_link_short();", 82, 26),
        "arm_link_long": ("arm_link_long();", 124, 28),
        "elbow_joint_plate": ("elbow_joint_plate();", 68, 44),
        "gripper_palm": ("gripper_palm();", 60, 56),
        "gripper_finger_pair": ("gripper_finger_pair();", 78, 44),
        "servo_horn_adapter": ("translate([40,40,0]) servo_horn_adapter();", 82, 82),
        "servo_power_distribution_plate": ("servo_power_distribution_plate();", 90, 48),
        "camera_mount": ("camera_mount();", 50, 50),
        "potentiometer_panel": ("potentiometer_panel();", 86, 42),
        "joystick_panel": ("joystick_panel();", 70, 60),
        "universal_l_bracket": ("universal_l_bracket();", 56, 36),
        "universal_u_bracket": ("universal_u_bracket();", 58, 44),
        "universal_bracket": ("universal_u_bracket();", 58, 44),
        "cable_clip_set": ("cable_clip_set();", 74, 22),
        "buzzer_clip": ("buzzer_clip();", 32, 32),
        "led_strip_clip": ("led_strip_clip();", 76, 18),
        "screw_fit_test": ("screw_fit_test();", 76, 24),
        "legged_body_plate": (f"legged_body_plate({max(l,130)}, {max(w,95)}, {h});", max(l,130), max(w,95)),
        "leg_link_short": ("leg_link_short();", 82, 26),
        "leg_link_long": ("leg_link_long();", 124, 28),
        "foot_pad": ("foot_pad();", 48, 32),
        "side_servo_rail": ("side_servo_rail();", 136, 24),
        "track_side_plate": ("track_side_plate();", 134, 42),
        "motor_pod": ("motor_pod();", 50, 38),
        "prop_guard_segment": ("translate([36,36,0]) prop_guard_segment();", 78, 78),
        "display_stand": ("display_stand();", 26, 72),
        "weather_louver": ("weather_louver();", 84, 42),
        "gripper_finger": ("gripper_finger();", 84, 24),
    }
    return calls.get(module_name, ("universal_u_bracket();", 58, 44))


def assemble_scad(profile: ModelProfile) -> str:
    """
    Assemble a self-contained OpenSCAD print plate from a detected component list.
    The model is no longer one template per robot type: it is a printable catalog composition.
    """
    parts: list[str] = [HEADER]
    parts.append("// Print plate: Einzelteile liegen getrennt auf der XY-Ebene.\n")
    parts.append(f"// Platform: {profile.platform}\n// Controller: {profile.controller}\n")
    parts.append("// Generated modules: " + ", ".join(profile.modules) + "\n\n")

    x = 0
    y = 0
    row_h = 0
    max_row_w = 430
    spacing = 24

    for idx, module_name in enumerate(profile.modules):
        call, sx, sy = _module_call(module_name, profile)
        if x > 0 and x + sx > max_row_w:
            x = 0
            y += row_h + spacing
            row_h = 0
        safe_name = module_name.replace("_", " ")
        parts.append(f"// Part {idx+1}: {safe_name}\n")
        parts.append(f"translate([{x}, {y}, 0]) {call}\n\n")
        x += sx + spacing
        row_h = max(row_h, sy)

    parts.append("// Hinweise:\n")
    parts.append("// - Dies ist eine universelle Druckplatte aus einzelnen Teilen, keine vormontierte Szene.\n")
    parts.append("// - Die Teile sind bewusst modular: Halter, Schalen, Laschen, Links, Trays und Teststücke.\n")
    parts.append("// - Teile im Slicer bei Bedarf trennen, drehen und mit passenden Druckeinstellungen platzieren.\n")
    parts.append("// - Reale Servo-, Motor-, Akku-, Platinen- und Schraubenmaße vor dem Druck prüfen.\n")
    parts.append(f"// - Profilnotiz: {profile.notes}\n")
    return "".join(parts)
