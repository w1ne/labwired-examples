"""Test that imported-board evidence never silently becomes whole-board proof."""
import copy
import importlib.util
import json
import pathlib
import io
from unittest.mock import patch
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

    def test_source_footprints_reconcile_with_import_classification(self):
        self.assertEqual(sum(b["source_topology"]["footprints"] for b in DATA["boards"]), 129)
        self.assertEqual(sum(b["source_topology"]["pads"] for b in DATA["boards"]), 575)
        self.assertEqual(sum(b["source_topology"]["pads_with_nets"] for b in DATA["boards"]), 510)
        self.assertEqual(sum(b["source_topology"]["pads_without_nets"] for b in DATA["boards"]), 65)
        for b in DATA["boards"]:
            self.assertEqual(b["source_topology"]["footprints"], sum(b["import_counts"].values()))
            self.assertEqual(b["model_coverage"]["net_completeness"], "not_measured")
            self.assertEqual(b["model_coverage"]["pin_completeness"], "not_measured")

    def test_source_reconciliation_rejects_missing_footprint_classification(self):
        altered = copy.deepcopy(DATA)
        altered["boards"][0]["import_counts"]["ignored"] -= 1
        self.assertIn("source footprints not reconciled", " ".join(mod.validate_manifest(altered)))

    def test_invented_import_net_pin_completeness_is_rejected(self):
        altered = copy.deepcopy(DATA)
        b = altered["boards"][0]
        b["model_coverage"]["net_completeness"] = "complete"
        b["model_coverage"]["pin_completeness"] = "complete"
        self.assertIn("complete connectivity requires reproducible imported pad/net comparison",
                      " ".join(mod.validate_manifest(altered)))

    def test_invalid_source_pad_counts_and_hash_are_rejected(self):
        altered = copy.deepcopy(DATA)
        topology = altered["boards"][0]["source_topology"]
        topology["pads_without_nets"] += 1
        self.assertIn("source connected/unconnected pad totals differ", " ".join(mod.validate_manifest(altered)))
        topology["pad_net_sha256"] = "not-a-hash"
        self.assertIn("invalid pinned source pad/net inventory", " ".join(mod.validate_manifest(altered)))

    def test_source_kicad_pad_parser_handles_nested_and_unconnected_pads(self):
        pcb = b'''(kicad_pcb (version 20260206)
            (footprint "Chip" (property "Reference" "U1")
              (property "Value" "quoted (not a pad)")
              (pad "1" smd rect (net "IO(A)"))
              (pad "2" smd rect)
              (pad "2" smd rect (net 0 ""))
            )
            (footprint "Header" (fp_text reference "J1")
              (pad "1" thru_hole circle (net 1 "IO(A)")))
          )'''
        topology = mod.source_topology(pcb)
        self.assertEqual(topology["footprints"], 2)
        self.assertEqual(topology["pads"], 4)
        self.assertEqual(topology["pads_with_nets"], 2)
        self.assertEqual(topology["pads_without_nets"], 2)
        self.assertEqual(topology["distinct_pad_nets"], 1)
        self.assertEqual(len(topology["pad_net_sha256"]), 64)
        modified = pcb.replace(b'IO(A)', b'IO(B)')
        self.assertNotEqual(mod.source_topology(modified)["pad_net_sha256"], topology["pad_net_sha256"])
        with self.assertRaises(ValueError):
            mod.source_topology(pcb[:-1])

    def test_pinned_source_check_detects_pin_net_changes_even_when_rehashed(self):
        # Simulate a pin reassignment in a new pinned blob. The new byte SHA
        # is valid, but the recorded topology from the prior design must fail.
        pcb = b'''(kicad_pcb (footprint "R" (property "Reference" "R1")
                    (pad "1" smd rect (net "VDD"))
                    (pad "2" smd rect (net "GND"))))'''
        modified = pcb.replace(b'VDD', b'VCC')
        example = copy.deepcopy(DATA["boards"][0])
        example["source"]["blob_sha"] = mod.git_blob_sha(modified)
        example["source"]["license_blob_sha"] = mod.git_blob_sha(b'MIT')
        example["source_topology"] = mod.source_topology(pcb)
        example["import_counts"] = {"mapped": 1, "dropped": 0, "ignored": 0}
        urls = {
            mod.raw_source_url(example["source"], example["source"]["path"]): modified,
            mod.raw_source_url(example["source"], example["source"]["license_path"]): b'MIT',
        }
        with patch.object(mod, "urlopen", side_effect=lambda url, timeout: io.BytesIO(urls[url])):
            errors, fetched = mod.verify_pinned_sources({"boards": [example]})
        self.assertEqual(fetched, 2)
        self.assertIn("pinned source pad/net topology differs", " ".join(errors))

    def test_pinned_license_text_must_match_declared_spdx(self):
        source = b'(kicad_pcb (footprint "R" (property "Reference" "R1") (pad "1" smd rect (net "VDD"))))'
        mit = (b"MIT License\n\nCopyright (c) HeyPCB\n\n"
               b"Permission is hereby granted, free of charge\n"
               b"THE SOFTWARE IS PROVIDED \"AS IS\"\n")
        cern = (b"CERN Open Hardware Licence Version 2 - Strongly Reciprocal\n"
                b"CERN-OHL-W and CERN-OHL-S may also be mentioned in this text.")
        self.assertEqual(mod.declared_license_spdx(mit), "MIT")
        self.assertEqual(mod.declared_license_spdx(cern), "CERN-OHL-S-2.0")
        self.assertIsNone(mod.declared_license_spdx(b"GPL-3.0\nMIT License\n"))
        self.assertIsNone(mod.declared_license_spdx(b"MIT License\nNo distribution permitted."))
        board = copy.deepcopy(DATA["boards"][0])
        board["source"]["blob_sha"] = mod.git_blob_sha(source)
        board["source"]["license_blob_sha"] = mod.git_blob_sha(cern)
        board["source"]["license_spdx"] = "MIT"
        board["source_topology"] = mod.source_topology(source)
        urls = {
            mod.raw_source_url(board["source"], board["source"]["path"]): source,
            mod.raw_source_url(board["source"], board["source"]["license_path"]): cern,
        }
        with patch.object(mod, "urlopen", side_effect=lambda url, timeout: io.BytesIO(urls[url])):
            errors, fetched = mod.verify_pinned_sources({"boards": [board]})
        self.assertEqual(fetched, 2)
        self.assertIn("pinned LICENSE text declares CERN-OHL-S-2.0, not manifest MIT",
                      " ".join(errors))

    def test_git_blob_hash(self):
        fixture = b"hello-kicad"
        import hashlib
        self.assertEqual(mod.git_blob_sha(fixture),
                         hashlib.sha1(b"blob 11\0hello-kicad").hexdigest())


if __name__ == "__main__":
    unittest.main()
