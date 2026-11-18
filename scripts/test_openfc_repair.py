"""Integrity of the separately versioned FC repair and its actual KiCad evidence.

These source/receipt checks do not rerun KiCad or establish physical readiness.
"""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / 'examples/robotics/quadrotor-bldc/hardware/flight-controller-openfc-lite-rev2-lw1'
VAL = REV / 'validation'
CLEANUP = VAL / '20261118-library-cleanup'


def read_json(path):
    return json.loads(path.read_text())


class OpenFCRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read_json(REV / 'source-and-validation.json')

    def test_exact_delivered_hardware_and_receipt_hashes(self):
        for field in ('hardware_files_sha256', 'validation_files_sha256'):
            for name, expected in self.manifest[field].items():
                self.assertEqual(hashlib.sha256((REV / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(hashlib.sha256((REV / 'LICENSE').read_bytes()).hexdigest(), self.manifest['source']['licence_sha256'])
        for name, target in self.manifest['external_dependencies'].items():
            self.assertTrue((REV / name).is_symlink())
            self.assertEqual(str((REV / name).readlink()), target)

    def test_original_gitlink_and_release_boundaries_remain(self):
        row = subprocess.check_output(['git', 'ls-tree', 'HEAD', self.manifest['source']['original_gitlink']], cwd=ROOT, text=True)
        self.assertIn('160000 commit ' + self.manifest['source']['commit'], row)
        self.assertEqual(self.manifest['source']['licence'], 'CERN-OHL-S-2.0')
        for field in ('accepted_for_manufacture', 'native_firmware_accepted', 'mechanical_fit_requalified'):
            self.assertIs(self.manifest[field], False)

    def test_native_drc_and_schematic_parity_are_clean(self):
        report = read_json(CLEANUP / 'drc.json')
        self.assertEqual(report['violations'], [])
        self.assertEqual(report['unconnected_items'], [])
        self.assertEqual(report['schematic_parity'], [])

    def test_card1_dat1_restoration_record(self):
        record = read_json(VAL / 'card1-dat1-pad-restoration.json')
        self.assertEqual(record['output_sha256'], read_json(CLEANUP / 'pcb-repair.json')['input_board_sha256'])
        self.assertFalse(record['rules_changed'])
        self.assertFalse(record['restored_pad']['shrunk_or_modified'])
        comparison = record['connectivity_comparison']
        self.assertEqual(comparison['existing_pads_with_changed_net'], 0)
        self.assertEqual(comparison['existing_pads_with_changed_geometry'], 0)
        self.assertEqual(comparison['footprints_moved_or_changed'], 0)
        self.assertEqual([(p['ref'], p['pin']) for p in comparison['added_pads']], [('Card1', '8')])
        self.assertEqual(record['drc_after']['errors'], 0)
        self.assertEqual(record['drc_after']['schematic_parity'], [])

    def test_current_erc_clean_and_exact_pg_exclusion_retained(self):
        report = read_json(VAL / 'final-erc.json')
        entries = [v for sheet in report['sheets'] for v in sheet['violations']]
        self.assertEqual(collections.Counter(v['severity'] for v in entries), {'warning': 178})
        current = read_json(CLEANUP / 'erc.json')
        self.assertEqual([v for sheet in current['sheets'] for v in sheet['violations']], [])
        before = read_json(VAL / 'final-erc-before-exclusion.json')
        errors = [v for sheet in before['sheets'] for v in sheet['violations'] if v['severity'] == 'error']
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['items'][0]['description'], 'Symbol U7 Pin 3 [PG, Open collector, Line]')
        project = read_json(REV / 'hardware/OpenFC.kicad_pro')
        exclusions = project['erc']['erc_exclusions']
        self.assertEqual(len(exclusions), 1)
        receipt = read_json(VAL / 'documented-pg-erc-exclusion.json')
        self.assertEqual(exclusions, [[receipt['exact_marker'], receipt['comment']]])
        self.assertTrue(receipt['physical_rules_and_erc_severities_unchanged'])
        self.assertIn('section8.3.6', receipt['comment'])

    def test_only_two_actual_schematic_endpoints_change(self):
        def endpoints(filename):
            xml = ET.fromstring(gzip.decompress((VAL / filename).read_bytes()))
            return {(p.get('ref'), p.get('pin')): n.get('name') for n in xml.findall('nets/net') for p in n.findall('node') if not p.get('ref').startswith('#')}
        old = endpoints('baseline.net.xml.gz')
        new = endpoints('schematic.net.xml.gz')
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual(len(new), 445)
        changed = {key for key in old if old[key] != new[key]}
        self.assertEqual(changed, {('U9', '2'), ('U9', '3')})
        self.assertTrue(all(old[key] == 'GND' and new[key].startswith('unconnected-') for key in changed))

    def test_native_shape_receipt_matches_board_and_has_no_nc_contacts(self):
        proof = read_json(VAL / 'final-pcb-connectivity-proof.json')
        self.assertEqual(proof['corrected_sha256'], read_json(CLEANUP / 'pcb-repair.json')['input_board_sha256'])
        self.assertEqual((proof['original_pad_objects'], proof['corrected_pad_objects']), (579, 584))
        self.assertEqual(set(proof['isolated_nc_pads']), {'U9.2', 'U9.3', 'USB1.A8', 'USB1.B8', 'U7.2', 'U15.2', 'Card1.8'})
        self.assertTrue(all(not value['copper_contacts'] for value in proof['isolated_nc_pads'].values()))
        self.assertTrue(all(proof['u10_same_net_track_contacts'].values()))
        self.assertTrue(proof['u10_body_pose_preserved'])
        self.assertTrue(proof['physical_rules_and_erc_severities_identical'])

    def test_native_cleanup_chain_and_export_identity(self):
        proof = read_json(CLEANUP / 'pcb-repair.json')
        board_hash = hashlib.sha256((REV / 'hardware/OpenFC.kicad_pcb').read_bytes()).hexdigest()
        datum_dir = REV.parents[1] / 'cad/evidence/model-datum-correction-20261118'
        datum = read_json(datum_dir / 'source-transform-proof.json')
        board_datum = next(item for item in datum['files'] if item['file'] == 'hardware/flight-controller-openfc-lite-rev2-lw1/hardware/OpenFC.kicad_pcb')
        self.assertEqual(proof['output_board_sha256'], board_datum['beforeSha256'])
        self.assertTrue(board_datum['onlyModelTransformTokensChanged'])
        self.assertEqual(board_datum['afterSha256'], board_hash)
        current_drc = read_json(datum_dir / 'fc-drc.json')
        for key in ('violations', 'unconnected_items', 'schematic_parity'):
            self.assertEqual(current_drc[key], [], key)
        self.assertTrue(proof['project_rule_policy_unchanged'])
        self.assertEqual(proof['project_sha256'], hashlib.sha256((REV / 'hardware/OpenFC.kicad_pro').read_bytes()).hexdigest())
        for item in proof['physical_geometry_comparison'].values():
            self.assertEqual(item['before_count'], item['after_count'])
            self.assertEqual(item['changed'], [])
        self.assertEqual(proof['net_partition_proof']['before'], 113)
        self.assertEqual(proof['net_partition_proof']['after'], 113)
        models = read_json(REV / 'mechanical-review/model-resolution-review.json')
        self.assertEqual(models['board_sha256'], board_datum['beforeSha256'])
        self.assertEqual(models['resolved_enabled_entries'], 107)
        # The newer export receipt owns the current bytes. The earlier model
        # inventory remains an honest record of its original source/export.
        exports = read_json(datum_dir / 'native-exports.json')
        current_exports = [item for item in exports if item['sourceBoard'] == board_datum['file']]
        self.assertEqual(len(current_exports), 3)
        self.assertEqual({Path(item['artifact']).name for item in current_exports}, set(models['exports']))
        for asset in current_exports:
            path = REV.parents[1] / asset['artifact']
            self.assertEqual(asset['sourceBoardSha256'], board_hash)
            self.assertEqual(asset['exit'], 0)
            self.assertEqual(asset['bytes'], path.stat().st_size)
            self.assertEqual(asset['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        bodies = next(item for item in read_json(datum_dir / 'native-solid-comparison.json')['boards'] if item['board'] == 'fc')
        self.assertEqual(bodies['beforeStepSha256'], models['exports']['fc-populated.step']['sha256'])
        self.assertEqual(bodies['afterStepSha256'], hashlib.sha256((REV / 'mechanical-review/fc-populated.step').read_bytes()).hexdigest())
        self.assertEqual((bodies['solidCount'], bodies['validCount']), (164, 164))
        self.assertEqual(len(bodies['samePoseIndices']) + len(bodies['changedSolids']), 164)

    def test_erc_annotations_are_not_simulated_sources(self):
        before = json.loads(gzip.decompress((VAL / 'before-erc-intent-audit.json.gz').read_bytes()))
        after = json.loads(gzip.decompress((VAL / 'final-import-audit.json.gz').read_bytes()))
        for key in ('diagram', 'nets', 'mapping', 'compiled', 'lower'):
            self.assertEqual(before[key], after[key], key)
        self.assertEqual(len(after['diagram']['parts']), 160)
        self.assertEqual(len(after['nets']), 82)
        self.assertFalse(after['compiled']['ok'])
        errors = [v for v in after['compiled']['diagnostics'] if v['severity'] == 'error']
        self.assertEqual([v['code'] for v in errors], ['PWR_RAIL_UNDRIVEN'])
        self.assertEqual(errors[0]['subjects'], ['net@C22:1'])
        net = next(n for n in after['nets'] if n['name'] == 'net@C22:1')
        self.assertIn({'part': 'P1', 'pin': '1'}, net['members'])
        self.assertIn({'part': 'U6', 'pin': 'VIN'}, net['members'])


if __name__ == '__main__':
    unittest.main()
