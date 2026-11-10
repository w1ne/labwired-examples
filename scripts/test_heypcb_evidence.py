"""Test that imported-board evidence never silently becomes whole-board proof."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/heypcb_evidence.py"
spec = importlib.util.spec_from_file_location("heypcb_evidence", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
DATA = json.loads(mod.MANIFEST.read_text())


class HeyPcbAcceptance(unittest.TestCase):
    def test_pinned_sources_and_records(self):
        self.assertEqual(mod.validate_manifest(DATA), [])
        self.assertEqual(len(DATA["boards"]), 7)
        self.assertEqual(sum(x["import_counts"]["mapped"] for x in DATA["boards"]), 92)
        self.assertEqual(sum(x["import_counts"]["dropped"] for x in DATA["boards"]), 17)
        self.assertTrue(all(x["stages"]["whole_board_verified"] == "blocked" for x in DATA["boards"]))
        self.assertEqual(DATA["subcircuit_bench"]["negative"]["run_status"], "fail")

    def test_fabricated_full_board_pass_rejected(self):
        altered = copy.deepcopy(DATA)
        b = altered["boards"][0]
        b["stages"]["whole_board_verified"] = "passed"
        b["whole_board"]["verdict"] = "PASS"
        b["whole_board"]["run_status"] = "pass"
        self.assertIn("whole-board PASS without required model and oracle evidence",
                      " ".join(mod.validate_manifest(altered)))

    def test_unsupported_board_cannot_start(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][1]["whole_board"]["run_status"] = "pass"
        self.assertIn("UNSUPPORTED board cannot claim simulation", " ".join(mod.validate_manifest(altered)))

    def test_fake_complete_part_map_fails(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][2]["stages"]["mapped"] = "passed"
        self.assertIn("cannot report complete model map", " ".join(mod.validate_manifest(altered)))

    def test_sources_must_be_sha_pinned_and_licensed(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][3]["source"]["commit"] = "main"
        altered["boards"][3]["source"]["license_spdx"] = "UNKNOWN"
        errors = " ".join(mod.validate_manifest(altered))
        self.assertIn("missing pinned commit", errors)
        self.assertIn("missing scoped source license", errors)

    def test_negative_control_is_required(self):
        altered = copy.deepcopy(DATA)
        altered["subcircuit_bench"]["negative"]["run_status"] = "pass"
        self.assertIn("requires a passing positive and failing negative control",
                      " ".join(mod.validate_manifest(altered)))

    def test_partial_board_can_have_scoped_analog_proof(self):
        altered = copy.deepcopy(DATA)
        board = altered["boards"][1]
        self.assertEqual(board["stages"]["mapped"], "partial")
        board["stages"]["analog_simulated"] = "passed"
        board["analog_proof"] = {
            "scope": "subcircuit",
            "input": "ideal 5 V source across a divider",
            "output": "captured ADC voltage with measured tolerance",
            "negative_control": "swap divider resistor values and fail the oracle",
        }
        self.assertEqual(mod.validate_manifest(altered), [])

    def test_digital_firmware_oracle_does_not_require_analog(self):
        altered = copy.deepcopy(DATA)
        board = altered["boards"][0]
        board["stages"]["firmware_verified"] = "passed"
        board["whole_board"]["firmware_oracle"] = "UART marker on a modeled MCU"
        board["whole_board"]["firmware_negative_control"] = "remove UART bridge and fail assertion"
        self.assertEqual(mod.validate_manifest(altered), [])

    def test_unscoped_analog_result_rejected(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][1]["stages"]["analog_simulated"] = "passed"
        self.assertIn("analog PASS without scoped input/output and negative control",
                      " ".join(mod.validate_manifest(altered)))

    def test_firmware_requires_negative_control(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][0]["stages"]["firmware_verified"] = "passed"
        altered["boards"][0]["whole_board"]["firmware_oracle"] = "UART marker"
        self.assertIn("firmware PASS without input/oracle and negative control",
                      " ".join(mod.validate_manifest(altered)))

    def test_partial_whole_board_status_is_rejected(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][0]["stages"]["whole_board_verified"] = "partial"
        self.assertIn("whole-board verdict must be passed, blocked or not_verified",
                      " ".join(mod.validate_manifest(altered)))

    def test_model_gap_inventory_reports_unmodeled_active_parts(self):
        summary = mod.model_gap_report(DATA)
        self.assertEqual(summary["model_gap_references"], 18)
        self.assertEqual(summary["dropped_references"], 17)
        self.assertEqual(summary["mapped_without_behavior_references"], 1)
        self.assertEqual(summary["full_boards_verified"], 0)
        boost = next(b for b in DATA["boards"] if b["id"] == "power-kit/boost-1s")
        self.assertEqual(next(g for g in boost["model_coverage"]["model_gaps"] if g["ref"] == "U1")["import_resolution"], "mapped_without_behavior")
        self.assertTrue(any(x["part"].startswith("MT3608") for x in summary["models"]))

    def test_dropped_count_and_unmodeled_reference_inventory_must_match(self):
        altered = copy.deepcopy(DATA)
        b = altered["boards"][1]
        b["model_coverage"]["model_gaps"] = [x for x in b["model_coverage"]["model_gaps"] if x["ref"] != "D1"]
        errors = " ".join(mod.validate_manifest(altered))
        self.assertIn("model-gap references differ from unmodeled refs", errors)
        self.assertIn("model-gap dropped references differ from import count", errors)

    def test_mapped_active_does_not_count_as_dropped(self):
        altered = copy.deepcopy(DATA)
        b = altered["boards"][1]
        b["model_coverage"]["model_gaps"][1]["import_resolution"] = "dropped"
        self.assertIn("model-gap dropped references differ from import count", " ".join(mod.validate_manifest(altered)))

    def test_model_gap_identity_and_resolution_are_required(self):
        altered = copy.deepcopy(DATA)
        b = altered["boards"][0]
        b["model_coverage"]["model_gaps"][0]["part"] = ""
        b["model_coverage"]["model_gaps"][1]["import_resolution"] = "simulated"
        errors = " ".join(mod.validate_manifest(altered))
        self.assertIn("model-gap part identity required", errors)
        self.assertIn("invalid model-gap import resolution", errors)

    def test_git_blob_hash(self):
        fixture = b"hello-kicad"
        import hashlib
        self.assertEqual(mod.git_blob_sha(fixture),
                         hashlib.sha1(b"blob 11\0hello-kicad").hexdigest())


if __name__ == "__main__":
    unittest.main()
