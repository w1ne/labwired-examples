#!/usr/bin/env python3
"""Behavior checks for external mass inputs; all populated values are synthetic."""
import copy
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CALCULATOR = HERE / "calculate-mass-stability.py"

class MassInputValidation(unittest.TestCase):
    def fixture(self, measured=False):
        data = json.loads((HERE / "mass-inputs.template.json").read_text())
        for entry in data["entries"]:
            entry.update(mass_g=1., com_mm=[0., 0., 350.], measured=measured,
                         source="Synthetic parser test; not a physical measurement.")
        return data

    def run_case(self, data, *, optimized=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs, output = root / "inputs.json", root / "review.json"
            inputs.write_text(json.dumps(data))
            command = [sys.executable]
            if optimized:
                command.append("-O")
            command += [str(CALCULATOR), "--measurements", str(inputs), "--output", str(output)]
            result = subprocess.run(command, text=True, capture_output=True)
            report = json.loads(output.read_text()) if output.exists() else None
            return result, report

    def reject(self, data, *, optimized=False):
        result, report = self.run_case(data, optimized=optimized)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ValueError:", result.stderr)
        self.assertIsNone(report)

    def test_estimates_remain_unmeasured(self):
        result, report = self.run_case(self.fixture(False))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["physical_assembly"]["mass_g"], 69.)
        self.assertEqual(report["physical_assembly"]["com_mm"], [0., 0., 350.])
        self.assertEqual(report["physical_assembly"]["status"], "input estimates")
        self.assertFalse(report["flight_acceptance"]["mass_and_CG_measured"])
        self.assertFalse(report["flight_acceptance"]["accepted"])

    def test_declared_measurements_do_not_grant_flight_acceptance(self):
        result, report = self.run_case(self.fixture(True))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report["flight_acceptance"]["mass_and_CG_measured"])
        self.assertFalse(report["flight_acceptance"]["accepted"])
        self.assertIn("not independently verified",
                      report["physical_assembly"]["measurement_status_basis"])

    def test_one_estimated_entry_keeps_complete_budget_unmeasured(self):
        data = self.fixture(True)
        data["entries"][0]["measured"] = False
        result, report = self.run_case(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(report["flight_acceptance"]["mass_and_CG_measured"])

    def test_string_false_cannot_be_measurement_evidence(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                data = self.fixture()
                for entry in data["entries"]:
                    entry["measured"] = "false"
                self.reject(data, optimized=optimized)

    def test_missing_or_numeric_measurement_flags_are_rejected(self):
        for value in (None, 0, 1):
            with self.subTest(value=value):
                data = self.fixture()
                data["entries"][0]["measured"] = value
                self.reject(data)

    def test_boolean_mass_is_rejected(self):
        data = self.fixture()
        data["entries"][0]["mass_g"] = True
        self.reject(data)

    def test_boolean_centroid_is_rejected(self):
        data = self.fixture()
        data["entries"][0]["com_mm"][0] = False
        self.reject(data)

    def test_nonfinite_or_negative_mass_is_rejected(self):
        for value in (float("nan"), float("inf"), -1.):
            with self.subTest(value=value):
                data = self.fixture()
                data["entries"][0]["mass_g"] = value
                self.reject(data)

    def test_empty_or_nontext_provenance_is_rejected(self):
        for value in (" ", True, {"citation": "synthetic"}):
            with self.subTest(value=value):
                data = self.fixture()
                data["entries"][0]["source"] = value
                self.reject(data)

    def test_duplicate_or_missing_budget_entry_is_rejected(self):
        data = self.fixture()
        data["entries"][0] = copy.deepcopy(data["entries"][1])
        self.reject(data)
        data = self.fixture()
        data["entries"].pop()
        self.reject(data)

    def test_wrong_geometry_identity_is_rejected(self):
        data = self.fixture()
        data["source_sha256"] = "0" * 64
        self.reject(data)

    def test_changed_actual_cad_is_rejected_with_optimization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("calculate-mass-stability.py", "mass-geometry-components.json",
                         "pathfinder-extended.kcad.ts"):
                shutil.copyfile(HERE / name, root / name)
            source = root / "pathfinder-extended.kcad.ts"
            source.write_text(source.read_text() + "\\n// Synthetic source-identity mismatch.\\n")
            output = root / "review.json"
            result = subprocess.run([sys.executable, "-O",
                                     str(root / "calculate-mass-stability.py"),
                                     "--output", str(output)],
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ValueError: Actual CAD source hash differs", result.stderr)
            self.assertFalse(output.exists())

    def test_zero_total_mass_is_rejected(self):
        data = self.fixture()
        for entry in data["entries"]:
            entry["mass_g"] = 0.
        self.reject(data)

if __name__ == "__main__":
    unittest.main()
