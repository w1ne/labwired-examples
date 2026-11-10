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

    def test_git_blob_hash(self):
        fixture = b"hello-kicad"
        import hashlib
        self.assertEqual(mod.git_blob_sha(fixture),
                         hashlib.sha1(b"blob 11\0hello-kicad").hexdigest())


if __name__ == "__main__":
    unittest.main()
