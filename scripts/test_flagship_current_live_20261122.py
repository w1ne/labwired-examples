"""Checks source-pinned current project readback and actual reciprocal media screenshot."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'examples/flagship-live-current-20261122.json'


class LiveCurrentReadback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DOC.read_text())

    def test_independent_current_saved_oracle_statuses(self):
        d = self.data
        self.assertEqual(d['schema'], 'labwired-flagship-current-rest-and-image-v1')
        for key, n in [('quadrotor', 4), ('esc_negative_control', 4),
                       ('pathfinder_original', 5), ('axiom_original', 3), ('axiom_candidate', 3)]:
            with self.subTest(key=key):
                item = d['current_projects'][key]
                self.assertEqual(item['http_status'], 200)
                self.assertEqual(item['content_hash'], item['verified_hash'])
                self.assertEqual(len(item['requirements']), n)
                self.assertEqual([x['status'] for x in item['requirements']], ['verified'] * n)
                self.assertTrue(any(x['fresh'] and x['status'] == 'model_verified'
                                    and x['content_hash'] == item['content_hash'] for x in item['sim_verify']))
                self.assertIn(item['project_id'], item['project_url'])

    def test_pathfinder_candidate_remains_rejected(self):
        x = self.data['current_projects']['pathfinder_candidate']
        self.assertIsNone(x['verified_hash'])
        self.assertEqual([r['status'] for r in x['requirements']], ['failed'] * 5)
        self.assertFalse(any(r['fresh'] and r['status'] == 'model_verified' for r in x['sim_verify']))
        self.assertIn('no swept-clearance', self.data['acceptance_limits']['pathfinder'])

    def test_revision_pinned_mechanical_identity_not_promoted_to_motion(self):
        d = self.data['current_projects']
        self.assertEqual(d['quadrotor']['mechanical']['slug'], 'DyJ405zg')
        self.assertEqual(d['quadrotor']['mechanical']['version'], 6)
        self.assertEqual(d['axiom_original']['mechanical']['slug'], '45f5VM8t')
        self.assertEqual(d['axiom_original']['mechanical']['version'], 1)
        self.assertEqual(d['axiom_original']['pcb_board_id'], 'pcb_172fd76a950f0bd9')
        self.assertEqual(d['pathfinder_candidate']['mechanical']['slug'], 'PuRrQzv1')
        self.assertIn('do not', self.data['acceptance_limits']['run_id'].lower())

    def test_real_browser_image_and_recipient_project_link(self):
        x = self.data['quadrotor_live_screenshot']
        raw = (ROOT / x['path']).read_bytes()
        self.assertEqual(x['bytes'], len(raw))
        self.assertGreater(len(raw), 10000)
        self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(x['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertTrue(x['media_readback_confirmed'])
        self.assertIn(x['live_project_media_id'], x['live_project_media_url'])
        self.assertIn(self.data['current_projects']['quadrotor']['project_id'], x['live_project_media_url'])
        self.assertIn('browser', x['scope'])


if __name__ == '__main__':
    unittest.main()
