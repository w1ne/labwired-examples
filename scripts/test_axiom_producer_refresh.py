"""Bind the post-deployment AXIOM producer refresh to the accepted geometry."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
MECHANICAL = ROOT / "examples/robotics/axiom-h1/mechanical"
CURRENT = MECHANICAL / "producer-refresh-20261122"
PRIOR = MECHANICAL / "artifact-refresh-20261122"


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class AxiomProducerRefresh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = read(CURRENT / "qualification.json")
        cls.prior = read(PRIOR / "mesh.json.gz")
        cls.current = read(CURRENT / "mesh.json.gz")
        cls.model = read(CURRENT / "model.json")

    def test_every_current_input_and_verifier_is_bound(self):
        for name, expected in self.receipt["files"].items():
            data = (CURRENT / name).read_bytes()
            self.assertEqual(sha(data), expected["sha256"], name)
            self.assertEqual(len(data), expected["bytes"], name)
        script = (CURRENT / self.receipt["script"]).resolve()
        self.assertEqual(script, ROOT / "scripts/check-axiom-producer-refresh.mjs")
        self.assertEqual(sha(script.read_bytes()), self.receipt["scriptSha256"])
        self.assertEqual(sha((PRIOR / "mesh.json.gz").read_bytes()), self.receipt["previous"]["archiveSha256"])
        self.assertEqual(sha(gzip.decompress((CURRENT / "mesh.json.gz").read_bytes())), self.receipt["current"]["rawSha256"])

    def test_portable_verifier_replays_the_recorded_qualification(self):
        completed = subprocess.run(
            ["node", str(ROOT / "scripts/check-axiom-producer-refresh.mjs")],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=20,
        )
        replayed = json.loads(completed.stdout)
        recorded = dict(self.receipt)
        self.assertIsInstance(replayed.pop("observedAt"), str)
        self.assertIsInstance(recorded.pop("observedAt"), str)
        self.assertEqual(replayed, recorded)

    def test_all_geometry_and_bindings_remain_exact(self):
        old = {key: value for key, value in self.prior.items() if key != "provenance"}
        new = {key: value for key, value in self.current.items() if key != "provenance"}
        self.assertEqual(new, old)
        self.assertEqual(len(new["features"]), 27)
        prior_model = read(PRIOR / "model.json")
        self.assertEqual({**self.model, "meshProvenance": prior_model["meshProvenance"]}, prior_model)
        self.assertEqual(len(self.model["electronics"]["motions"]), 20)
        self.assertEqual(self.receipt["comparison"]["modelChangedFields"], ["meshProvenance"])
        for key in ["source", "assetsSha256", "geometryHash"]:
            self.assertEqual(self.current["provenance"][key], self.prior["provenance"][key])

    def test_actual_producer_and_stored_cdn_identity(self):
        producer = self.current["provenance"]["producer"]
        self.assertEqual(producer["serverCommit"], "fd52f2c20b801c8a7ab875ebeb6b844a928baf97")
        self.assertEqual(producer["runtimeSourceHash"], "f00d5beda7bb1f5befa8f001329013b0c2b1e6b9ae85019837415deee2d89977")
        encoded = json.dumps(self.current["provenance"], sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(sha(encoded), self.model["meshProvenance"])
        for name in ["stored-fetch.json", "cdn-fetch.json"]:
            response = read(CURRENT / name)
            self.assertEqual(response["status"], 200)
            self.assertEqual(response["sha256"], self.receipt["current"]["rawSha256"])
            self.assertEqual(response["bytes"], 3107233)
            self.assertIn("provenance=" + self.model["meshProvenance"], response["url"])
        source = (MECHANICAL / "axiom-compact-frame.kcad.ts").read_bytes()
        self.assertEqual(sha(source), self.current["provenance"]["source"]["sha256"])

    def test_existing_acceptance_boundaries_remain_explicit(self):
        q = self.receipt
        self.assertTrue(q["passed"])
        self.assertTrue(q["acceptance"]["original59DiscretePosesRetained"])
        self.assertTrue(q["acceptance"]["original20BindingTransformReceiptRetained"])
        self.assertIn("timeout retained", q["acceptance"]["additionalDenseSweep"])
        self.assertEqual(q["acceptance"]["physicalAcceptance"], "failed; unchanged")
        self.assertFalse(q["acceptance"]["savedProjectCasPerformed"])
        self.assertFalse(q["acceptance"]["viewerPainted"])
        self.assertFalse(q["actions"]["sourceResavePerformed"])
        self.assertFalse(q["actions"]["modelEvaluationPerformed"])
        self.assertFalse(q["actions"]["meshGenerationRequested"])


if __name__ == "__main__":
    unittest.main()
