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


    def test_new_runtime_readback_preserves_failed_live_status_and_fit_scope(self):
        fresh = json.loads((ROOT / 'examples/flagship-runtime-readback-20261122.json').read_text())
        self.assertEqual(fresh['schema'], 'labwired-flagship-runtime-readback-v1')
        old = json.loads((ROOT / fresh['historical_evidence']).read_text())
        quad = fresh['quadrotor']
        self.assertEqual(quad['project_id'], old['quadrotor']['project_id'])
        self.assertEqual(quad['content_hash'], old['quadrotor']['content_hash'])
        self.assertIsNone(quad['verified_hash'])
        self.assertEqual(set(quad['requirements'].values()), {'failed'})
        self.assertEqual(quad['interrupted_attempt']['reason'], 'config_error')
        self.assertTrue(quad['interrupted_attempt']['run_id'].startswith('world-job:'))
        self.assertEqual(quad['interrupted_attempt']['controller_serial_count'], 0)
        self.assertFalse(quad['interrupted_attempt']['behavioral_failure_observed'])
        self.assertFalse(quad['flight_6dof_live_verified'])
        self.assertFalse(quad['physical_flight_verified'])
        neg = fresh['single_esc_negative_control']
        self.assertEqual(neg['project_id'], old['single_esc_fault_control']['project_id'])
        self.assertEqual(neg['verified_hash'], neg['content_hash'])
        self.assertEqual(neg['requirement_statuses'], ['verified'] * 4)
        orig = fresh['pathfinder']['original']
        cand = fresh['pathfinder']['source_bound_candidate']
        self.assertEqual(orig['project_id'], old['pathfinder']['project_id'])
        self.assertGreater(orig['board']['outline_mm'][0], orig['coupler_inner_diameter_mm'])
        self.assertEqual(orig['pcb_cad_fit'], 'rejected')
        self.assertEqual(cand['current_verification'], 'failed')
        self.assertEqual(cand['requirements_failed'], 5)
        self.assertTrue(cand['pcb']['kicad_drc']['passed'])
        self.assertFalse(cand['pcb']['kicad_drc']['schematic_parity_checked'])
        self.assertFalse(cand['pcb']['manufacturing_verified'])
        pcb_x, pcb_z = cand['pcb']['outline_mm']
        cad_x, cad_y, cad_z = cand['cad']['bbox_extents_mm']
        self.assertEqual((pcb_x, pcb_z), (cad_x, cad_z))
        self.assertLess(cad_y, pcb_x)
        self.assertTrue(cand['cad']['bbox_size_matches_pcb'])
        self.assertFalse(cand['cad']['full_clearance_or_collision_verified'])
        self.assertFalse(cand['pcb_fit_server_receipt_observed'])
        self.assertFalse(cand['promoted_to_original'])
        axi = fresh['axiom']
        self.assertEqual(axi['original']['project_id'], old['axiom']['original_project_id'])
        self.assertEqual(axi['original']['requirements_stale'], 3)
        self.assertEqual(axi['candidate']['requirements_verified'], 3)
        self.assertEqual(axi['candidate']['content_hash'], axi['candidate']['verified_hash'])
        self.assertFalse(axi['cad_joint_coupling_hosted_verified'])
        self.assertFalse(axi['physical_servo_verified'])
        self.assertIsNone(fresh['screenshots']['fresh_capture_date'])
        self.assertIn('NOT END-TO-END ACCEPTED', fresh['overall'])


if __name__ == '__main__':
    unittest.main()
