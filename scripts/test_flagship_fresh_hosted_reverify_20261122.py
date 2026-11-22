"""Immutable current hosted evidence, with clear firmware/fit/physical scope separation."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / 'examples/flagship-fresh-hosted-reverify-20261122.json'
PRIOR = ROOT / 'examples/flagship-live-current-20261122.json'


class FreshFlagshipReverify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FRESH.read_text())
        cls.prior = json.loads(PRIOR.read_text())

    def test_recheck_preserves_project_and_exact_content_hash(self):
        data = self.data
        self.assertEqual(data['schema'], 'labwired-flagship-fresh-hosted-verification-v1')
        for field in ('quadrotor', 'single_esc_fault_negative_control',
                      'pathfinder_source_bound_candidate', 'axiom_original'):
            with self.subTest(field=field):
                r = data[field]
                self.assertEqual(r['verified_hash'], r['content_hash'])
                self.assertEqual(len(r['content_hash']), 64)
                self.assertIn(r['project_id'], r['project_url'])
        mapping = {'quadrotor':'quadrotor','single_esc_fault_negative_control':'esc_negative_control',
                   'pathfinder_source_bound_candidate':'pathfinder_candidate','axiom_original':'axiom_original'}
        for current, historical in mapping.items():
            a, b = data[current], self.prior['current_projects'][historical]
            self.assertEqual(a['project_id'], b['project_id'])
            self.assertEqual(a['content_hash'], b['content_hash'])

    def test_new_quadrotor_run_has_four_named_oracles_not_flight_proof(self):
        q = self.data['quadrotor']
        self.assertRegex(q['run_id'], r'^world-job:[0-9a-f-]{36}$')
        self.assertEqual(q['proof'], 'oracle')
        self.assertEqual(q['oracle_source'], 'declared')
        self.assertEqual(q['max_steps'], 2000000)
        self.assertEqual(set(q['requirements']), {'R1','R2','R3','R4'})
        for i in range(1,5):
            self.assertEqual(q['requirements'][f'R{i}']['node'], f'ctrl{i}')
            self.assertTrue(q['requirements'][f'R{i}']['passed'])
            self.assertEqual(q['requirements'][f'R{i}']['marker'], f'ROTOR {i} HALL LOCKED')
        self.assertFalse(q['six_axis_flight_hosted_verified'])
        self.assertFalse(q['physical_flight_verified'])

    def test_negative_control_is_independent_single_esc_only(self):
        n = self.data['single_esc_fault_negative_control']
        self.assertNotEqual(n['project_id'], self.data['quadrotor']['project_id'])
        self.assertEqual(n['passed_count'], 4)
        self.assertEqual(n['requirements']['R4'], 'PB0 low')
        self.assertIsNone(n['run_id'])
        self.assertFalse(n['four_motor_flight_failsafe_verified'])
        self.assertFalse(n['physical_failsafe_verified'])

    def test_pathfinder_synthetic_firmware_pass_does_not_promote_fit(self):
        p = self.data['pathfinder_source_bound_candidate']
        self.assertEqual(p['passed_count'], 5)
        self.assertEqual(p['max_steps'], 20000000)
        self.assertEqual(p['proof'], 'oracle')
        self.assertEqual(p['pcb_id'], 'pcb_af828a3152e61e08')
        self.assertEqual(p['pcb_rev'], 0)
        self.assertEqual(p['pcb_cad_fit'], 'not_hosted_verified')
        self.assertFalse(p['physical_flight_verified'])
        self.assertIsNone(p['run_id'])

    def test_axiom_status_is_readback_not_new_motion_run(self):
        a = self.data['axiom_original']
        self.assertEqual(a['requirements_verified'], 3)
        self.assertIn('no fresh verify job', a['proof_scope'].lower())
        self.assertFalse(a['servo_to_joint_hosted_verified'])
        self.assertFalse(a['physical_robot_verified'])

    def test_screenshots_exact_bytes_do_not_claim_simulation(self):
        s = self.data['screenshots']
        self.assertEqual({x['view'] for x in s}, {'circuit','pcb'})
        for item in s:
            with self.subTest(view=item['view']):
                b = (ROOT / item['path']).read_bytes()
                self.assertTrue(b.startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertEqual(len(b), item['bytes'])
                self.assertEqual(hashlib.sha256(b).hexdigest(), item['sha256'])
                self.assertIn('not', item['scope'])
        self.assertIn('NOT END-TO-END ACCEPTED', self.data['overall'])

    def test_readmes_link_to_this_receipt(self):
        for name in ('examples/aerospace/pathfinder-rocket/README.md',
                     'examples/aerospace/pathfinder-rocket/candidate/README.md',
                     'examples/robotics/quadrotor-bldc/README.md',
                     'examples/robotics/axiom-h1/README.md'):
            with self.subTest(name=name):
                self.assertIn('flagship-fresh-hosted-reverify-20261122.json', (ROOT/name).read_text())


if __name__ == '__main__':
    unittest.main()
