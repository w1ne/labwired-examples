"""Pinned artifact and browser screenshot are static evidence, not servo-motion proof."""
import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'examples/robotics/axiom-h1'
RECEIPT = BASE / 'mechanical/axiom-restored-producer-proof-20261123.json'


class AxiomRestoredProducer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(RECEIPT.read_text())

    def test_pinned_artifact_matches_archived_producer(self):
        r = self.r
        archive = ROOT / r['storage']['archive_path']
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), r['storage']['archive_sha256'])
        raw = gzip.decompress(archive.read_bytes())
        self.assertEqual(len(raw), r['storage']['body_bytes'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), r['storage']['body_sha256'])
        artifact = json.loads(raw)
        self.assertEqual(artifact['revision'], r['kernelcad_model']['revision'])
        self.assertEqual(artifact['provenance']['source']['sha256'], '5c392121b7cccfd8dc41fb0226ac68e3f344b06bf954ccb35db74e0fd9ac4496')
        from test_axiom_provenance_recheck import digest
        self.assertEqual(digest(artifact['provenance']), r['kernelcad_model']['producer_digest'])
        self.assertIn(r['kernelcad_model']['producer_digest'], r['storage']['immutable_url'])
        self.assertEqual(r['storage']['public_http_status'], 200)

    def test_static_screenshot_is_immutable_and_not_motion_proof(self):
        r = self.r
        b = (ROOT / r['static_embed']['screenshot']['path']).read_bytes()
        self.assertTrue(b.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(len(b), r['static_embed']['screenshot']['bytes'])
        self.assertEqual(hashlib.sha256(b).hexdigest(), r['static_embed']['screenshot']['sha256'])
        self.assertIn(r['kernelcad_model']['producer_digest'], r['static_embed']['url'])
        self.assertTrue(r['static_embed']['no_servo_or_joint_animation_tested'])
        self.assertTrue(r['acceptance']['static_public_embed_painted'])
        for gate in ('saved_LabWired_browser_mechanics_painted', 'PWM_to_CAD_motion_verified',
                     'physical_actuation_verified', 'populated_Pathfinder_PCB_fit_verified',
                     'six_axis_quadrotor_flight_verified'):
            self.assertFalse(r['acceptance'][gate], gate)


if __name__ == '__main__':
    unittest.main()
