"""Check captured screenshot bytes and scope claims; not a motion or physical acceptance test."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'examples/flagship-live-snapshots-20261121.json'


class FlagshipLiveSnapshots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads(MANIFEST.read_text())

    def test_three_real_image_files_match_pinned_sha_and_size(self):
        self.assertEqual(self.receipt['schema'], 'labwired-live-static-snapshot-inventory-v1')
        images = self.receipt['screenshots']
        self.assertEqual({r['slug'] for r in images}, {'quadrotor', 'axiom', 'pathfinder'})
        for rec in images:
            with self.subTest(rec=rec['slug']):
                image_path = ROOT / rec['dst']
                self.assertTrue(image_path.is_file())
                data = image_path.read_bytes()
                self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertEqual(len(data), rec['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), rec['screenshot_sha256'])
                self.assertIn(rec['project_id'], rec['project_url'])
                self.assertEqual(len(rec['hash']), 64)
                self.assertIn('not', self.receipt['verification_scope'].lower())

    def test_browser_artifact_links_are_not_claimed_as_motion_or_fit_proof(self):
        by_slug = {r['slug']: r for r in self.receipt['screenshots']}
        for slug in ('quadrotor', 'axiom', 'pathfinder'):
            rec = by_slug[slug]
            with self.subTest(rec=slug):
                self.assertIn('No', rec['limitations'])
                self.assertIn('pcb_id', rec['artifact_readback'])
                self.assertIn('pcb_rev', rec['artifact_readback'])
                self.assertIn('cad_link', rec['artifact_readback'])
        self.assertEqual(by_slug['pathfinder']['artifact_readback']['fit_result'], 'REJECTED')
        self.assertFalse(by_slug['axiom']['artifact_readback']['cad_pinned'])
        self.assertIsNone(by_slug['axiom']['run_id'])
        self.assertIsNone(by_slug['pathfinder']['run_id'])
        self.assertTrue(by_slug['quadrotor']['run_id'].startswith('world-job:'))
        self.assertIn('Single modeled ESC', self.receipt['fault_negative_control']['scope'])


if __name__ == '__main__':
    unittest.main()
