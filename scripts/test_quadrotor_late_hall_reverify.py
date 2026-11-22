"""Pin the fresh hosted multi-controller and injected-fault results without overstating scope."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'examples/flagship-quadrotor-hall-reverify-20261122-2116z.json'


class QuadrotorLateHallReverify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(RECEIPT.read_text())

    def test_fresh_four_controller_run_is_hash_bound_and_observable(self):
        r = self.rec
        self.assertEqual(r['schema'], 'labwired-quadrotor-hall-reverify-v1')
        q = r['positive_control']
        self.assertEqual(q['run_id'], 'world-job:218a1aca-e78c-47aa-827b-bf3274592210')
        self.assertEqual(q['step_limit'], 2_000_000)
        self.assertEqual(q['content_hash'], q['verified_hash'])
        self.assertEqual(q['proof'], 'oracle')
        self.assertIn(q['project_id'], q['project_url'])
        self.assertEqual([x['id'] for x in q['requirements']], ['R1','R2','R3','R4'])
        for i, check in enumerate(q['requirements'], start=1):
            self.assertTrue(check['passed'])
            self.assertEqual(check['status'], 'verified')
            self.assertEqual(check['serial_contains'], f'ROTOR {i} HALL LOCKED')
        self.assertEqual(r['observed']['four_hall_oracles_passed'], 4)

    def test_single_esc_negative_control_does_not_claim_full_flight(self):
        r = self.rec
        n = r['fault_negative_control']
        self.assertIsNone(n['run_id'])
        self.assertEqual(n['content_hash'], n['verified_hash'])
        self.assertEqual(n['proof'], 'oracle')
        self.assertEqual([x['id'] for x in n['requirements']], ['R1','R2','R3','R4'])
        self.assertTrue(all(x['status'] == 'verified' and x['passed'] for x in n['requirements']))
        self.assertIn('FAULT DRIVER', n['requirements'][1]['serial_contains'])
        self.assertIn('INVERTER OFF', n['requirements'][2]['serial_contains'])
        self.assertEqual(n['requirements'][3]['gpio'], {'pin': 'PB0', 'state': 'low'})
        self.assertEqual(r['observed']['single_esc_fault_oracles_passed'], 4)
        self.assertFalse(r['observed']['six_dof_flight_verified'])
        self.assertFalse(r['observed']['physical_hardware_verified'])
        self.assertFalse(r['observed']['source_code_changed_in_this_check'])
        self.assertIn('NOT END-TO-END', r['overall'])
        self.assertTrue((ROOT / r['historical_evidence']).is_file())


if __name__ == '__main__':
    unittest.main()
