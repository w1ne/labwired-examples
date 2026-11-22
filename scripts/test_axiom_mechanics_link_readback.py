"""Integrity and conservative scope of the later AXIOM browser readback."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'examples/flagship-axiom-mechanics-recheck-20261122.json'


class AxiomMechanicsLinkReadback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFEST.read_text())

    def test_both_saved_project_screenshots_are_real_and_content_pinned(self):
        rec = self.data
        self.assertEqual(rec['schema'], 'labwired-axiom-live-mechanics-link-readback-v1')
        captures = rec['captures']
        self.assertEqual({x['id'] for x in captures}, {'original', 'candidate'})
        self.assertEqual({x['project_id'] for x in captures}, {
            'e6b30d45ba55e64aa450a2aa292edd4b',
            'dab8622b41adbf3b9e2175909146b207',
        })
        for x in captures:
            with self.subTest(project=x['id']):
                raw = (ROOT / x['image']).read_bytes()
                self.assertTrue(raw.startswith(b'\x89PNG\r\n\x1a\n'))
                w, h = struct.unpack('>II', raw[16:24])
                self.assertGreaterEqual(w, 1280)
                self.assertGreaterEqual(h, 720)
                self.assertEqual(x['bytes'], len(raw))
                self.assertEqual(x['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertIn(x['project_id'], x['project_url'])
                self.assertTrue(x['linked_model_title_visible'])
                self.assertEqual(x['browser_3d_renderer'], 'unavailable')
                self.assertFalse(x['servo_to_cad_motion_observed'])
                self.assertEqual(x['observed_model_title'], 'AXIOM H1 — staggered kinematic frame')

    def test_link_is_not_misrepresented_as_verified_motion(self):
        rec = self.data
        self.assertTrue(rec['model_link_visible_but_motion_unverified'])
        self.assertFalse(rec['physical_hardware_verified'])
        self.assertEqual(rec['new_live_run_ids'], [])
        self.assertIn('not its slug/revision', rec['cad_reference_basis'])
        self.assertIn('No pulse-to-CAD motion', rec['limitations'][2])
        self.assertTrue((ROOT / rec['historical_readback']).exists())
        readme = (ROOT / 'examples/robotics/axiom-h1/README.md').read_text()
        self.assertIn('flagship-axiom-mechanics-recheck-20261122.json', readme)
        self.assertIn('3D view is unavailable', readme)
        self.assertIn('not accepted live motion', readme)


if __name__ == '__main__':
    unittest.main()
