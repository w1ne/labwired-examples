"""Integrity gates for the pinned AXIOM CAD and firmware transform evidence."""
import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "robotics" / "axiom-h1"
MECHANICAL = EXAMPLE / "mechanical"


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AxiomCadEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = read_json(MECHANICAL / "compact-frame-review.json")
        cls.evaluation = read_json(MECHANICAL / "compact-frame-evaluation.json")
        cls.model = read_json(MECHANICAL / "compact-frame-model.json")
        cls.receipt = read_json(MECHANICAL / "joint-transform-evidence.json")
        cls.project = read_json(EXAMPLE / "current-project.input.json")

    def test_exact_source_and_saved_revision_match_all_receipts(self):
        digest = sha256(MECHANICAL / "axiom-compact-frame.kcad.ts")
        self.assertEqual(digest, self.review["cadSourceSha256"])
        self.assertEqual(digest, self.receipt["cadSourceSha256"])
        self.assertEqual(digest, self.evaluation["evaluationEvidence"]["source"]["sha256"])
        self.assertTrue(self.review["sourceReadbackMatched"])
        for key in ("slug", "version", "meshProvenance"):
            self.assertEqual(self.model[key], self.receipt["model"][key])
            self.assertEqual(self.model[key], self.review["savedProject"][key])
        self.assertEqual(self.review["original"]["slug"], "QC9kIRT9")
        self.assertEqual(self.review["original"]["version"], 1)

    def test_firmware_evidence_chain_and_all_joint_ranges(self):
        self.assertEqual(sha256(EXAMPLE / "actuator-runtime-evidence.json"),
                         self.receipt["actuatorEvidenceSha256"])
        source = self.project["source"]
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),
                         self.receipt["firmwareSourceSha256"])
        def values(name):
            return [int(v) for v in re.search(
                name + r"\[NUM_JOINTS\]=\{([^}]+)\}", source)[1].split(",")]
        names = re.findall(r'"([^"]+)"', re.search(
            r"joint_name\[NUM_JOINTS\] = \{([\s\S]*?)\};", source)[1])
        source_ranges = [{"name": name, "min": lo, "max": hi}
                         for name, lo, hi in zip(names, values("jmin"), values("jmax"))]
        self.assertEqual(source_ranges, self.receipt["sourceLimitsDeg"])
        self.assertEqual(len(names), 20)

    def test_unique_component_and_part_ownership(self):
        electronics = self.model["electronics"]
        self.assertEqual(electronics,
                         read_json(MECHANICAL / "source-derived-electronics.json"))
        self.assertEqual(electronics["version"], 2)
        motions = electronics["motions"]
        self.assertEqual({m["component"] for m in motions},
                         {"servo" + str(i) for i in range(20)})
        parts = [part for motion in motions for part in motion["parts"]]
        self.assertEqual(len(parts), 23)
        self.assertEqual(len(parts), len(set(parts)))
        by_id = {motion["id"]: motion for motion in motions}
        for motion in motions:
            visited = set()
            cursor = motion
            while "parent" in cursor:
                self.assertNotIn(cursor["id"], visited)
                visited.add(cursor["id"])
                cursor = by_id[cursor["parent"]]

    def test_actual_runtime_transform_and_estop_evidence(self):
        receipt = self.receipt
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["bindingCount"], 20)
        self.assertEqual(len(receipt["samples"]), 46)
        self.assertLess(receipt["maximumMatrixMarkerErrorMm"], 1e-8)
        self.assertIn("left_gripper", receipt["changedParts"])
        self.assertIn("head_visor", receipt["changedParts"])
        disabled = [s for s in receipt["samples"]
                    if s["phase"].startswith("estop") and s["allDisabled"]]
        self.assertGreaterEqual(len(disabled), 2)
        for sample in disabled:
            self.assertEqual(sample["acceptedMotions"], 20)
            self.assertTrue(all(c["controlState"] == "servo-source-disabled"
                                for c in sample["commands"]))
            self.assertEqual(sample["transforms"], disabled[0]["transforms"])

    def test_collision_coverage_and_physical_failures_remain_distinct(self):
        self.assertTrue(self.evaluation["ok"])
        mechanism = self.evaluation["mechanismSummary"]
        self.assertEqual(mechanism["failures"], [])
        self.assertIn("59 poses across 20 joints", mechanism["statement"])
        physical = self.review["physicalAcceptance"]
        self.assertEqual(physical["status"], "failed")
        self.assertEqual(physical["rangeMismatch"]["status"], "failed")
        for limits in physical["rangeMismatch"]["sourceRangesDeg"].values():
            self.assertGreater(limits[1] - limits[0],
                               physical["rangeMismatch"]["manufacturerNormalTravelDeg"])
        hold = physical["loadHold"]
        self.assertEqual(hold["status"], "unverified")
        self.assertEqual(hold["motionLoad"]["samples"], 0)
        self.assertEqual(hold["motionLoad"]["joints"], [])
        self.assertEqual(hold["staticHold"]["posesSampled"], 0)
        self.assertEqual(hold["staticHold"]["joints"], [])

    def test_original_and_revised_renderer_images_are_present(self):
        for prefix in ("original", "compact"):
            for view in ("front", "right", "iso"):
                data = (EXAMPLE / "media" / f"{prefix}-frame-{view}.png").read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertGreater(len(data), 10000)


if __name__ == "__main__":
    unittest.main()
