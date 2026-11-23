"""Source-pinned AXIOM public embed regression: static paint != LabWired motion."""
import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'examples/robotics/axiom-h1'
RECEIPT = BASE / 'mechanical/axiom-provenance-embed-recheck-20261123.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf8')).hexdigest()


class AxiomProvenanceRecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(RECEIPT.read_text())
        cls.historical = json.loads(gzip.decompress((BASE / 'mechanical/producer-refresh-20261122/mesh.json.gz').read_bytes()))

    def test_old_immutable_pin_and_current_attested_producer_have_same_source_and_geometry(self):
        r = self.r
        self.assertEqual(r['schema'], 'labwired-examples/axiom-provenance-embed-recheck/v1')
        self.assertEqual(r['historical_provenance'], self.historical['provenance'])
        self.assertEqual(digest(r['historical_provenance']), r['historical_provenance_digest_sha256'])
        self.assertEqual(digest(r['observed_current_provenance']), r['observed_current_provenance_digest_sha256'])
        self.assertNotEqual(r['historical_provenance_digest_sha256'], r['observed_current_provenance_digest_sha256'])
        old = r['historical_provenance']; new = r['observed_current_provenance']
        self.assertEqual(old['source'], new['source'])
        self.assertEqual(old['geometryHash'], new['geometryHash'])
        self.assertNotEqual(old['producer'], new['producer'])
        self.assertEqual(r['model']['saved_source_sha256'], old['source']['sha256'])
        self.assertEqual(r['model']['geometry_sha256'], old['geometryHash'])

    def test_both_browser_screenshots_are_real_pixels_and_scoped(self):
        r = self.r
        self.assertEqual({i['status'] for i in r['screenshots']}, {'rejected_old_pin', 'displayed_current_pin'})
        for image in r['screenshots']:
            with self.subTest(image=image['status']):
                data = (ROOT / image['path']).read_bytes()
                self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertEqual(len(data), image['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), image['sha256'])
        self.assertIn('provenance', r['viewer']['old_saved_pin']['observed_error'].lower())
        self.assertFalse(r['viewer']['old_saved_pin']['canvas_present'])
        self.assertTrue(r['viewer']['current_cdn_pin']['webgl2'])
        self.assertEqual(r['viewer']['current_cdn_pin']['canvas_pixels'], [1280, 820])
        self.assertEqual(r['viewer']['current_cdn_pin']['animation_artifact_http_status'], 404)
        self.assertFalse(r['scope']['live_saved_labwired_view_repaired'])
        self.assertFalse(r['scope']['servo_pwm_joint_motion_observed'])
        self.assertFalse(r['scope']['physical_hardware_verified'])
        self.assertTrue(r['scope']['browser_paint_observed_only_on_public_kernelcad_embed'])


if __name__ == '__main__':
    unittest.main()
