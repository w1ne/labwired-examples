"""Regress fresh direct REST/oracle receipts without promoting them to hardware proof."""
import json
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'examples/flagship-direct-verify-20261122-1340z.json'


class FlagshipDirectVerify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(RECEIPT.read_text())

    def test_oracle_receipts_are_hash_bound_and_do_not_fabricate_run_ids(self):
        self.assertEqual(self.r['schema'], 'labwired-flagship-direct-live-verify-v1')
        for key, size in [('quadrotor', 4), ('single_esc_negative_control', 4), ('axiom_h1_candidate', 3), ('axiom_h1_original', 3)]:
            with self.subTest(key=key):
                item = self.r[key]
                self.assertEqual(item['http_status'], 200)
                self.assertTrue(item['verified'])
                self.assertEqual(item['proof'], 'oracle')
                self.assertEqual(item['oracle_source'], 'declared')
                self.assertEqual(len(item['verified_hash']), 64)
                self.assertEqual(len(item['requirements']), size)
                self.assertEqual([r['passed'] for r in item['requirements']], [True] * size)
                self.assertIsNone(item['run_id'])
                self.assertIn(item['project_id'], item['project_url'])
                self.assertTrue(item['started_utc'].startswith('2026-11-22T'))

    def test_older_failure_readback_remains_immutable_and_current_one_is_separate(self):
        previous = json.loads((ROOT / self.r['prior_receipts'][0]).read_text())
        self.assertEqual(previous['quadrotor']['current_verification'], 'failed')
        self.assertEqual(previous['quadrotor']['project_id'], self.r['quadrotor']['project_id'])
        self.assertEqual(previous['quadrotor']['content_hash'], self.r['quadrotor']['verified_hash'])
        self.assertEqual(self.r['fresh_readbacks']['quadrotor']['content_hash'], self.r['quadrotor']['verified_hash'])
        self.assertEqual(self.r['fresh_readbacks']['single_esc_negative_control']['verified_hash'], self.r['single_esc_negative_control']['verified_hash'])
        self.assertEqual(self.r['fresh_readbacks']['axiom_h1_candidate']['verified_hash'], self.r['axiom_h1_candidate']['verified_hash'])
        self.assertEqual(self.r['fresh_readbacks']['axiom_h1_original']['verified_hash'], self.r['axiom_h1_original']['verified_hash'])

    def test_mechanical_link_is_saved_but_not_joint_or_physical_proof(self):
        m = self.r['axiom_mechanical_link']
        self.assertEqual(m['project_id'], self.r['axiom_h1_candidate']['project_id'])
        self.assertEqual(m['after_content_hash'], self.r['axiom_h1_candidate']['verified_hash'])
        self.assertNotEqual(m['before_content_hash'], m['after_content_hash'])
        self.assertEqual(m['motion_bindings'], 20)
        self.assertTrue(m['static_integration_check']['ok'])
        self.assertEqual(m['static_integration_check']['issue_count'], 0)
        self.assertFalse(m['hosted_joint_transform_oracle_verified'])
        self.assertFalse(m['physical_joint_motion_verified'])
        self.assertFalse(self.r['pathfinder']['candidate_full_clearance_verified'])
        self.assertFalse(self.r['ui']['fix_deployed_and_ui_rechecked'])
        self.assertEqual(self.r['axiom_original_mechanical_link']['after_content_hash'], self.r['axiom_h1_original']['verified_hash'])
        self.assertEqual(self.r['axiom_original_mechanical_link']['motion_bindings'], 20)
        self.assertFalse(self.r['axiom_original_mechanical_link']['hosted_joint_transform_oracle_verified'])
        shot = self.r['ui']['failed_capture']
        raw = (ROOT / shot['image']).read_bytes()
        self.assertTrue(raw.startswith(b'\xff\xd8\xff'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), shot['sha256'])
        self.assertIn('editor error', shot['scope'])
        self.assertTrue(self.r['unverified'])


if __name__ == '__main__':
    unittest.main()
