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


    def test_next_day_live_recheck_uses_pinned_projects_without_upgrading_static_frames(self):
        latest = json.loads((ROOT / 'examples/flagship-hosted-recheck-20261122.json').read_text())
        by_slug = {r['slug']: r for r in self.receipt['screenshots']}
        self.assertEqual(latest['schema'], 'labwired-flagship-hosted-recheck-v1')
        self.assertEqual(latest['historical_screenshots_manifest'], str(MANIFEST.relative_to(ROOT)))
        self.assertIn('No fresh screenshot', latest['screenshots_note'])
        for name in ('quadrotor', 'pathfinder'):
            with self.subTest(name=name):
                item = latest[name]
                self.assertEqual(item['project_id'], by_slug[name]['project_id'])
                self.assertEqual(item['content_hash'], item['verified_hash'])
                self.assertTrue(item['verified'])
                self.assertEqual(item['proof'], 'oracle')
                self.assertEqual(item['board']['id'], by_slug[name]['artifact_readback']['pcb_id'])
                self.assertEqual(item['board']['rev'], by_slug[name]['artifact_readback']['pcb_rev'])
                self.assertEqual(item['cad'], by_slug[name]['artifact_readback']['cad_link'])
        self.assertEqual(set(latest['quadrotor']['requirements']), {'R1', 'R2', 'R3', 'R4'})
        self.assertTrue(latest['quadrotor']['run_id'].startswith('world-job:'))
        self.assertFalse(latest['quadrotor']['interrupted_run']['verified'])
        self.assertEqual(latest['single_esc_fault_control']['project_id'], self.receipt['fault_negative_control']['project_id'])
        self.assertIsNone(latest['single_esc_fault_control']['run_id'])
        self.assertEqual(latest['pathfinder']['requirements'], ['R1', 'R2', 'R3', 'R4', 'R5'])
        self.assertGreater(latest['pathfinder']['fit_geometry']['minimum_pad_center_width_mm'], latest['pathfinder']['fit_geometry']['airframe_coupler_inner_diameter_mm'])
        self.assertEqual(latest['pathfinder']['board']['fit'], 'REJECTED')
        self.assertEqual(latest['axiom']['original_project_id'], by_slug['axiom']['project_id'])
        self.assertNotEqual(latest['axiom']['original_content_hash'], latest['axiom']['original_verified_hash'])
        self.assertEqual(latest['axiom']['original_requirements'], ['stale'] * 3)
        self.assertEqual(latest['axiom']['candidate_requirements'], ['verified'] * 3)
        self.assertIn('NOT END-TO-END ACCEPTED', latest['overall'])


if __name__ == '__main__':
    unittest.main()
