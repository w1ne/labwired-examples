import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
Q = ROOT / "examples" / "robotics" / "quadrotor-bldc"


class QuadrotorExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diagram = json.loads((Q / "labwired" / "circuit.json").read_text())
        cls.evidence = json.loads((Q / "labwired" / "evidence.json").read_text())
        cls.source = (Q / "firmware" / "main.c").read_text()
        cls.cad = (Q / "cad" / "drone.kcad.ts").read_text()

    def test_known_catalog_types_and_board(self):
        self.assertEqual(self.diagram["board"], "stm32l476")
        self.assertEqual(
            {p["type"] for p in self.diagram["parts"]},
            {"nucleo-l476rg", "bldc-motor", "button-module"},
        )

    def test_motor_wiring_matches_firmware_registers(self):
        wired = {
            (w["from"]["part"], w["from"]["pin"], w["to"]["part"], w["to"]["pin"])
            for w in self.diagram["wires"]
        }
        expected = [
            ("PA8", "AH"), ("PB13", "AL"),
            ("PA9", "BH"), ("PB14", "BL"),
            ("PA10", "CH"), ("PB15", "CL"),
            ("PB0", "ENABLE"), ("PC0", "HALL_A"), ("PC1", "HALL_B"),
            ("PC2", "HALL_C"), ("PC3", "ENC_A"), ("PC4", "ENC_B"),
            ("PC5", "INDEX"),
        ]
        for pin, connector in expected:
            self.assertIn(("ctrl", pin, "rotor1", connector), wired)
        self.assertIn(("ctrl", "PB7", "fault", "SIG"), wired)
        for marker in ("BLDC READY", "TARGET REACHED", "FAULT DRIVER", "INVERTER OFF"):
            self.assertIn(marker, self.source)
        self.assertIn("TIM1_BDTR &= ~MOE", self.source)
        self.assertIn("GPIOB_ODR &= ~1u", self.source)

    def test_evidence_separates_cad_and_simulation(self):
        self.assertEqual(self.evidence["scope"]["electronic_motor_channels"], 1)
        self.assertEqual(self.evidence["scope"]["cad_propeller_joints"], 4)
        self.assertEqual(self.evidence["cad"]["revolute_joints"], 4)
        self.assertFalse(self.evidence["cad"]["aerodynamics_checked"])
        self.assertIn("return rig.model()", self.cad)
        self.assertIn("animationView(", self.cad)

    def test_shares_and_proprietary_claims(self):
        self.assertIn("app.labwired.com/?share=", self.evidence["project"]["labwired_url"])
        self.assertIn("app.kernelcad.com/p/", self.evidence["project"]["kernelcad_url"])
        self.assertIn("NOT ODrive firmware", self.source)
        self.assertIn("not ODrive firmware", self.evidence["scope"]["controller"])

    def test_media_artifacts_present(self):
        for name in ("media/circuit-lab.png", "media/quad-cad.png", "media/quadrotor-demo.mp4"):
            self.assertGreater((Q / name).stat().st_size, 10000)


INDUSTRIAL = ROOT / "examples" / "industrial" / "bldc-fault-verification"


class IndustrialDriveExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diagram = json.loads((INDUSTRIAL / "labwired" / "circuit.json").read_text())
        cls.evidence = json.loads((INDUSTRIAL / "labwired" / "evidence.json").read_text())

    def test_shared_compiled_source_and_distinct_inputs(self):
        source = (INDUSTRIAL / self.evidence["project"]["firmware_source"]).resolve()
        self.assertEqual(source, (Q / "firmware" / "main.c").resolve())
        self.assertTrue(source.is_file())
        self.assertEqual(self.diagram["board"], "stm32l476")
        self.assertEqual({p["id"] for p in self.diagram["parts"]},
                         {"ctrl", "rotor1", "fault", "overcurrent", "undervoltage"})
        wired = {(w["from"]["pin"], w["to"]["part"], w["to"]["pin"])
                 for w in self.diagram["wires"]}
        for pin, part in (("PB7", "fault"), ("PB6", "overcurrent"),
                          ("PC7", "undervoltage")):
            self.assertIn((pin, part, "SIG"), wired)
        self.assertEqual(len(self.diagram["wires"]), 22)

    def test_independent_oracles_and_proof_limits(self):
        cases = self.evidence["cases"]
        self.assertEqual(len(cases), 4)
        self.assertEqual(cases[0]["verdict"], "model_verified")
        self.assertGreater(cases[0]["observed"]["peak_abs_rpm"], 100)
        for case, part, marker in zip(cases[1:],
                                      ("fault", "overcurrent", "undervoltage"),
                                      ("FAULT DRIVER", "FAULT OVERCURRENT", "FAULT UNDERVOLTAGE")):
            self.assertEqual(case["verdict"], "model_verified")
            self.assertEqual(case["stimuli"][0]["component"], part)
            self.assertEqual(case["stimuli"][0]["outcome"], "applied")
            self.assertEqual(case["oracle"]["serial_contains"], [marker, "INVERTER OFF"])
            self.assertEqual(case["oracle"]["gpio"], {"pin": "PB0", "state": "low"})
        self.assertFalse(self.evidence["model"]["real_hardware_measured"])
        self.assertEqual(self.evidence["validation"]["errors"], 0)
        self.assertGreaterEqual(self.evidence["validation"]["warnings"], 1)
        self.assertTrue(self.evidence["project"]["studio_url"].startswith("https://app.labwired.com/?share="))
        self.assertGreater((INDUSTRIAL / "media" / "studio.png").stat().st_size, 10000)


if __name__ == "__main__":
    unittest.main()
