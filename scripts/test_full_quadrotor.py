"""Source identity, wiring and command-failsafe checks for the five-MCU twin.

These tests do not claim that five-firmware physics execution was validated.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "examples/robotics/quadrotor-bldc"


class FullQuadrotorCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diagram = json.loads((QUAD / "labwired/five-controller-flight-circuit.json").read_text())
        cls.manifest = json.loads((QUAD / "labwired/five-controller-flight-project.json").read_text())
        cls.fc_source = (QUAD / "firmware/flight/fc.c").read_text()

    def test_exactly_five_source_bound_firmware_instances(self):
        channels = self.manifest["channels"]
        self.assertEqual({c["controller"] for c in channels}, {"fc", "ctrl1", "ctrl2", "ctrl3", "ctrl4"})
        self.assertEqual(len(channels), 5)
        for c in channels:
            source = (QUAD / c["source"]).read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(), c["source_sha256"])
            self.assertEqual(len(source), c["source_bytes"])
            self.assertEqual(c["board"], "stm32l476")

    def test_four_motors_full_wiring_and_imu(self):
        parts = {p["id"]: p for p in self.diagram["parts"]}
        self.assertEqual(len(parts), 17)
        self.assertEqual(len(self.diagram["wires"]), 81)
        self.assertEqual(parts["fc"]["type"], "nucleo-l476rg")
        self.assertEqual(parts["imu"]["type"], "bmi270")
        self.assertEqual(parts["kill"]["type"], "button-module")
        self.assertEqual(parts["fc"]["attrs"]["internal_pullups"], ["PB6", "PB7"])
        edges = {(w["from"]["part"], w["from"]["pin"], w["to"]["part"], w["to"]["pin"])
                 for w in self.diagram["wires"]}
        for index in range(1, 5):
            ctrl, rotor, fault = f"ctrl{index}", f"rotor{index}", f"fault{index}"
            self.assertEqual(parts[ctrl]["type"], "nucleo-l476rg")
            self.assertEqual(parts[rotor]["type"], "bldc-motor")
            self.assertEqual(parts[fault]["type"], "button-module")
            self.assertIn(("fc", f"PC{index+7}", ctrl, "PA0"), edges)
            self.assertIn((ctrl, "PB0", "fc", f"PC{index-1}"), edges)
            self.assertIn((ctrl, "PB7", fault, "SIG"), edges)
            for mcu_pin, motor_pin in (("PA8", "AH"), ("PB13", "AL"),
                                       ("PA9", "BH"), ("PB14", "BL"),
                                       ("PA10", "CH"), ("PB15", "CL"),
                                       ("PB0", "ENABLE"), ("PC0", "HALL_A"),
                                       ("PC1", "HALL_B"), ("PC2", "HALL_C")):
                self.assertIn((ctrl, mcu_pin, rotor, motor_pin), edges)
        for a, b in (("PB6", "SCL"), ("PB7", "SDA")):
            self.assertIn(("fc", a, "imu", b), edges)
        self.assertIn(("fc", "PC4", "kill", "SIG"), edges)

    def test_failsafe_paths_are_latched_before_logging(self):
        self.assertIn('"FC OPERATOR KILL - ALL ESC DISARM', self.fc_source)
        self.assertIn('"FC IMU LOST - ALL ESC DISARM', self.fc_source)
        self.assertIn('"FC ESC NOT READY - ALL ESC DISARM', self.fc_source)
        self.assertIn('"FC FAULT DETECTED - ALL ESC DISARM', self.fc_source)
        latch = self.fc_source.split('static void latch_disarm(', 1)[1].split('static uint8_t clamp_width', 1)[0]
        self.assertLess(latch.index('GPIOC_ODR &= ~COMMAND_MASK;'), latch.index('text(reason);'))
        self.assertIn('command_high_mask(phase, widths)', self.fc_source)
        self.assertIn('FC ESTIMATED GROUND CONTACT', self.fc_source)
        self.assertNotIn('SAFE LANDING VERIFIED', self.fc_source)

    @unittest.skipUnless(shutil.which("cc"), "host C compiler unavailable")
    def test_pwm_zero_command_clears_all_four_pins(self):
        # Includes the actual target implementation. Rename its main so the
        # pure command bitmask can be tested without MCU register access.
        harness = r'''
#define main flight_controller_entry
#include "fc.c"
#undef main
#include <assert.h>
int main(void) {
    const uint8_t widths[4] = {18, 40, 72, 0};
    const uint8_t disabled[4] = {0, 0, 0, 0};
    assert(command_high_mask(0, widths) == ((1u<<8)|(1u<<9)|(1u<<10)));
    assert(command_high_mask(17, widths) == ((1u<<8)|(1u<<9)|(1u<<10)));
    assert(command_high_mask(18, widths) == ((1u<<9)|(1u<<10)));
    assert(command_high_mask(40, widths) == (1u<<10));
    assert(command_high_mask(72, widths) == 0);
    assert(command_high_mask(40, disabled) == 0);
    assert(command_high_mask(0, disabled) == 0);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source = directory / "pwm_test.c"
            binary = directory / "pwm_test"
            source.write_text(harness)
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
                            "-I", str(QUAD / "firmware/flight"), str(source), "-o", str(binary)],
                           check=True, capture_output=True, text=True)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
