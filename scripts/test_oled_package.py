"""Cross-file checks for the OLED device release; no firmware or CAD mock."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'examples/displays/esp32c3-oled'


def read_json(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


class OledDevicePackage(unittest.TestCase):
    def test_complete_source_manifest(self):
        manifest = read_json('release-manifest.json')
        expected = {
            str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()
            and '.pio' not in p.parts and 'released' not in p.parts
            and 'rerun' not in p.parts
            and str(p.relative_to(ROOT)) not in ('release-manifest.json', 'SHA256SUMS')
        }
        rows = manifest['files']
        self.assertEqual({row['path'] for row in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        for row in rows:
            with self.subTest(path=row['path']):
                path = (ROOT / row['path']).resolve()
                self.assertIn(ROOT.resolve(), path.parents)
                self.assertEqual(path.stat().st_size, row['bytes'])
                self.assertEqual(digest(row['path']), row['sha256'])

    def test_copper_and_cad_bind_the_same_native_board(self):
        pcb_hash = digest('electronics/oled-carrier.kicad_pcb')
        pcb_ref = 'sha256:' + pcb_hash
        native = read_json('manufacturing/validation.json')
        self.assertEqual(native['source_files'][0]['sha256'], pcb_hash)
        self.assertEqual(native['drc']['unconnected_items'], 0)
        self.assertEqual(native['drc']['schematic_parity_issues'], 0)
        interface = read_json('cad/mechanical-interface.json')
        self.assertEqual(interface['carrier']['nativePcbRef'], pcb_ref)
        self.assertEqual(interface['carrier']['hardwareInterfaceSha256'], digest('hardware-interface.json'))
        model = read_json('labwired/mechanical.json')
        self.assertEqual(model['pcbBindings'][0]['pcbRef'], pcb_ref)
        self.assertEqual(read_json('labwired/circuit.json')['mechanical'], model)
        cad = read_json('cad/release.json')
        self.assertEqual(cad['sourceSha256'], digest('cad/' + cad['source']))
        self.assertEqual(cad['assetSha256'], digest('cad/' + cad['asset']))
        self.assertEqual(cad['assetSha256'], digest('manufacturing/oled-carrier-bare.step'))
        for output in cad['exports']:
            self.assertEqual(output['sha256'], digest('cad/' + output['path']))

    def test_native_connectivity_matches_the_functional_view_and_sketch(self):
        nets = {}
        for net in ET.parse(ROOT / 'manufacturing/oled-carrier.net.xml').getroot().findall('./nets/net'):
            nets[net.attrib['name']] = {(n.attrib['ref'], n.attrib['pin']) for n in net.findall('node')}
        expected = {
            '/SDA': {('J2', '3'), ('J1', '3'), ('R1', '2')},
            '/SCL': {('J2', '4'), ('J1', '4'), ('R2', '2')},
            '/3V3': {('J3', '5'), ('J1', '2')},
            '/GND': {('J3', '6'), ('J1', '1')},
        }
        for name, members in expected.items():
            self.assertTrue(members.issubset(nets[name]), (name, nets[name]))
        diagram = read_json('labwired/circuit.json')
        wires = {(w['from']['part'], w['from']['pin'], w['to']['part'], w['to']['pin']) for w in diagram['wires']}
        self.assertIn(('mcu', 'D2', 'oled', 'SDA'), wires)
        self.assertIn(('mcu', 'D3', 'oled', 'SCL'), wires)
        parts = {p['id']: p for p in diagram['parts']}
        self.assertEqual(parts['mcu']['manufacturerPart'], 'seeed-113991054')
        self.assertEqual(parts['oled']['manufacturerPart'], 'adafruit-326')
        self.assertEqual(parts['oled']['attrs']['module_i2c_address'], '0x3C')
        source = (ROOT / 'firmware/vendor/esp32c3-display-workshop.ino').read_text()
        self.assertIn('PIN_I2C_SDA = 4;', source)
        self.assertIn('PIN_I2C_SCL = 5;', source)
        self.assertIn('Wire.beginTransmission(0x3C)', source)
        self.assertEqual(read_json('firmware/source-provenance.json')['source']['sha256'], digest('firmware/vendor/esp32c3-display-workshop.ino'))

    def test_runtime_receipts_identify_bytes_and_real_frames(self):
        assets = {a['filename']: a for a in read_json('firmware/release-manifest.json')['assets']}
        wasm = read_json('verification/released-wasm-acceptance.json')
        self.assertTrue(wasm['passed'])
        for field, name in [
            ('firmwareSha256', 'demo-esp32c3-display-workshop.elf'),
            ('flashSha256', 'demo-esp32c3-display-workshop-flash.bin'),
            ('snapshotSha256', 'demo-esp32c3-oled-lab.lwrs'),
        ]:
            self.assertEqual(wasm[field], assets[name]['sha256'])
        raw = gzip.decompress((ROOT / 'verification/package-rom-boot-result.json.gz').read_bytes())
        observed = read_json('verification/package-rom-boot-observations.json')
        self.assertEqual(hashlib.sha256(raw).hexdigest(), observed['source_result_sha256'])
        cli = json.loads(raw)
        self.assertEqual(len(cli['assertions']), 5)
        self.assertTrue(all(a['passed'] for a in cli['assertions']))
        display = next(d for d in cli['inspect']['devices'] if d['id'] == 'oled')
        self.assertEqual(display['attachment']['address'], 0x3C)
        frame = next(a for a in display['artifacts'] if a['kind'] == 'framebuffer')
        self.assertEqual((frame['meta']['w'], frame['meta']['h']), (128, 64))
        self.assertTrue(frame['meta']['powered'])
        hashes = {f['sha256'] for f in frame['meta']['frames_seen'] if f['ink_bytes'] > 0}
        self.assertGreaterEqual(len(hashes), 2)
        self.assertEqual(hashes, {f['sha256'] for f in wasm['frames']})

    def test_combined_bom_has_every_electrical_and_mechanical_item(self):
        with (ROOT / 'bom.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        combined = {(r['assembly'], r['references']): (int(r['quantity']), r['part_number']) for r in rows}
        self.assertEqual(len(combined), len(rows))
        with (ROOT / 'electronics-bom.csv').open() as stream:
            for row in csv.DictReader(stream):
                self.assertEqual(combined['electronics', row['references']], (int(row['quantity']), row['manufacturer_part_number_or_sku']))
        with (ROOT / 'cad/mechanical-bom.csv').open() as stream:
            for row in csv.DictReader(stream):
                self.assertEqual(combined['enclosure', row['reference']], (int(row['quantity']), row['part_number']))

    def test_open_gates_cannot_be_reported_as_accepted(self):
        release = read_json('release-manifest.json')
        cad = read_json('cad/release.json')
        if cad['acceptance']['designLoop'] != 'pass' or cad['acceptance']['assemblyPath'] != 'pass':
            self.assertEqual(release['status'], 'engineering-candidate')
            self.assertEqual(cad['status'], 'assembly-candidate')
            self.assertTrue(release['open_acceptance_items'])
        if cad['acceptance']['physicalFit'] == 'not performed':
            self.assertFalse(release['physical_hardware_tested'])


if __name__ == '__main__':
    unittest.main()
