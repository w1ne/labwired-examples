"""Pinned four-channel firmware, wiring, and CAD binding integrity."""
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
Q = ROOT / "examples/robotics/quadrotor-bldc"

class FourChannelArtifactIntegrity(unittest.TestCase):
    def test_each_controller_owns_the_recorded_source_and_motor(self):
        manifest = json.loads((Q / "labwired/four-channel-project.json").read_text())
        diagram = json.loads((Q / manifest["diagram"]).read_text())
        parts = {p["id"]: p["type"] for p in diagram["parts"]}
        self.assertEqual(len(manifest["channels"]), 4)
        self.assertEqual(len(diagram["wires"]), 64)
        wires = {(w["from"]["part"], w["from"]["pin"], w["to"]["part"], w["to"]["pin"]) for w in diagram["wires"]}
        for number, channel in enumerate(manifest["channels"], 1):
            source = (Q / channel["source"]).read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(), channel["sha256"])
            self.assertIn(f"#define CHANNEL_ID {number}\n", source.decode())
            self.assertIn(f"#define DUTY_PERMILLE {channel['duty_per_mille']}\n", source.decode())
            self.assertEqual(parts[channel["controller"]], "nucleo-l476rg")
            self.assertEqual(parts[channel["motor"]], "bldc-motor")
            self.assertIn((channel["controller"], "PB0", channel["motor"], "ENABLE"), wires)
            self.assertIn((channel["controller"], "PB7", channel["fault_input"], "SIG"), wires)
        self.assertFalse(manifest["flight_dynamics"])
        self.assertFalse(manifest["physical_hardware_tested"])

    def test_motion_maps_four_distinct_rotor_groups(self):
        bindings = json.loads((Q / "cad/runtime-bindings.json").read_text())
        motions = bindings["motions"]
        self.assertEqual({m["component"] for m in motions}, {"rotor1", "rotor2", "rotor3", "rotor4"})
        self.assertEqual(len({m["joint"] for m in motions}), 4)
        self.assertEqual(len({p for m in motions for p in m["parts"]}), 8)
        for motion in motions:
            self.assertEqual(motion["axis"], [0, 0, 1])
            self.assertEqual(len(motion["parts"]), 2)
            self.assertIn(motion["direction"], (-1, 1))
            self.assertEqual(motion["origin"][2], 9.3)

if __name__ == "__main__":
    unittest.main()
