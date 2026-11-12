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

    def test_native_drc_and_single_unresolved_physical_omission(self):
        report = read_json(VAL / 'final-drc.json')
        self.assertEqual(collections.Counter(v['severity'] for v in report['violations']), {'warning': 5})
        self.assertEqual(report['unconnected_items'], [])
        self.assertEqual(len(report['schematic_parity']), 1)
        item = report['schematic_parity'][0]
        self.assertEqual(item['description'], 'No pad found for pin 8 in schematic')
        self.assertEqual(item['items'][0]['description'], 'Footprint Card1')

    def test_erc_warning_retention_and_exact_pg_exclusion(self):
        report = read_json(VAL / 'final-erc.json')
        entries = [v for sheet in report['sheets'] for v in sheet['violations']]
        self.assertEqual(collections.Counter(v['severity'] for v in entries), {'warning': 178})
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
        self.assertEqual(proof['corrected_sha256'], hashlib.sha256((REV / 'hardware/OpenFC.kicad_pcb').read_bytes()).hexdigest())
        self.assertEqual((proof['original_pad_objects'], proof['corrected_pad_objects']), (579, 583))
        self.assertEqual(set(proof['isolated_nc_pads']), {'U9.2', 'U9.3', 'USB1.A8', 'USB1.B8', 'U7.2', 'U15.2'})
        self.assertTrue(all(not value['copper_contacts'] for value in proof['isolated_nc_pads'].values()))
        self.assertTrue(all(proof['u10_same_net_track_contacts'].values()))
        self.assertTrue(proof['u10_body_pose_preserved'])
        self.assertTrue(proof['physical_rules_and_erc_severities_identical'])

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
