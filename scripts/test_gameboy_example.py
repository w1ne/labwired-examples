"""Bounded source/evidence integrity and real host-ROM behavior checks."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GAME = ROOT / 'examples' / 'gaming' / 'gameboy-handheld'


def read(name):
    return json.loads((GAME / name).read_text())


def digest(name):
    return hashlib.sha256((GAME / name).read_bytes()).hexdigest()


class GameBoyExample(unittest.TestCase):
    def test_manifest_binds_all_checked_in_artifacts(self):
        manifest = read('manifest.json')
        actual = {str(p.relative_to(GAME)) for p in GAME.rglob('*')
                  if p.is_file() and p.name != 'manifest.json'}
        self.assertEqual(actual, {item['path'] for item in manifest['files']})
        for item in manifest['files']:
            path = GAME / item['path']
            self.assertEqual(path.stat().st_size, item['bytes'], item['path'])
            self.assertEqual(digest(item['path']), item['sha256'], item['path'])
        self.assertFalse(manifest['proof']['physical_hardware_tested'])
        self.assertFalse(manifest['pcb']['automatic_twin_import'])

    def test_source_rom_and_cad_generators_reproduce_recorded_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = pathlib.Path(tmp) / 'gameboy'
            shutil.copytree(GAME, copied)
            for script in ('firmware/build_rom.py', 'firmware/build_firmware.py',
                           'mechanical/generate_enclosure.py'):
                subprocess.run([sys.executable, str(copied / script)], check=True,
                               capture_output=True, text=True, timeout=10)
            for name in ('firmware/wire_runner.gb', 'firmware/wire_runner_rom.h',
                         'firmware/gameboy.c', 'mechanical/labwired-gameboy.kcad.ts'):
                self.assertEqual((copied / name).read_bytes(), (GAME / name).read_bytes(), name)

    def test_original_rom_behavior_on_real_peanut_core(self):
        compiler = shutil.which('cc')
        self.assertIsNotNone(compiler, 'The bounded ROM behavior check requires a C compiler.')
        with tempfile.TemporaryDirectory() as tmp:
            binary = pathlib.Path(tmp) / 'host-verify'
            subprocess.run([compiler, '-std=c99', '-O2', str(GAME / 'firmware/host_verify.c'),
                            '-o', str(binary)], check=True, capture_output=True, text=True, timeout=30)
            ran = subprocess.run([str(binary)], check=True, capture_output=True,
                                 text=True, timeout=10)
            self.assertIn('all 8 controls; collision/score; pause; palette; 17424 scanlines.', ran.stdout)
        # This host test proves the cartridge behavior, not MCU timing or hardware.
        self.assertEqual(read('firmware/host-validation.json')['rom_sha256'], digest('firmware/wire_runner.gb'))

    def test_fixed_mates_and_shared_mounts_keep_the_same_source_identity(self):
        ref = read('kernelcad-reference.json')
        review = read('mechanical/independent-mates.json')
        interfaces = read('design-interfaces.json')
        layout = read('pcb/carrier-layout.json')
        routing = read('pcb/routing-report.json')
        self.assertEqual(digest(ref['sourceFile']), ref['sourceSha256'])
        self.assertEqual(review['evaluationEvidence']['source']['sha256'], ref['sourceSha256'])
        self.assertEqual(digest('design-interfaces.json'), ref['interfaceSha256'])
        self.assertEqual(routing['interface_sha256'], ref['interfaceSha256'])
        self.assertEqual(review['validator']['status'], 'solved')
        self.assertEqual((review['validator']['partCount'], review['validator']['jointCount']), (15, 14))
        self.assertEqual(review['interferenceSummary']['actionableCount'], 0)
        self.assertFalse(ref['physicalAssemblyVerified'])
        self.assertEqual(layout['mounts'], interfaces['pcb']['mounts'])
        actual = []
        for component in layout['components']:
            if component['ref'].startswith('H'):
                pad = component['pads'][0]
                self.assertEqual(pad['drill'], interfaces['pcb']['mountHoleDiameter'])
                actual.append((pad['x'] - interfaces['pcb']['width'] / 2,
                               interfaces['pcb']['center'][1] + interfaces['pcb']['height'] / 2 - pad['y']))
        self.assertCountEqual(actual, [tuple(m['at'][:2]) for m in interfaces['pcb']['mounts']])

    def test_pcb_binding_and_driven_mcu_evidence_remain_consistent(self):
        diagram = read('firmware/circuit.json')
        binding = read('pcb/simulation-binding.json')
        layout = read('pcb/carrier-layout.json')
        evidence = read('firmware/evidence.json')
        verify = read('firmware/verification.json')
        provenance = read('source-provenance.json')
        pcb_hash = digest('pcb/handheld-carrier.kicad_pcb')
        self.assertEqual(pcb_hash, binding['pcb_sha256'])
        self.assertEqual(pcb_hash, layout['pcb_sha256'])
        self.assertEqual(pcb_hash, read('pcb/routing-report.json')['pcb_sha256'])
        self.assertEqual(read('pcb/drc-routed.json')['violations'], [])
        self.assertEqual(read('pcb/drc-routed.json')['unconnected_items'], [])
        self.assertEqual({p['type'] for p in diagram['parts']}, {'stm32f411ceu6-blackpill', 'ili9341', 'button'})
        components = {c['ref']: c for c in layout['components']}
        wires = {(w['from']['part'], w['from']['pin'], w['to']['part'], w['to']['pin']) for w in diagram['wires']}
        for part, link in binding['bindings'].items():
            self.assertIn(link['pcb_ref'], components)
            if part.startswith('btn-'):
                self.assertIn(('mcu', link['pin1'], part, '1'), wires)
                self.assertIn(('mcu', link['pin2'], part, '2'), wires)
                self.assertEqual({pad['net'] for pad in components[link['pcb_ref']]['pads']}, {link['pin1'], link['pin2']})
        self.assertEqual(digest('firmware/gameboy.c'), provenance['firmware_source_sha256'])
        self.assertEqual(verify['firmware_ref'], diagram['firmware']['artifact']['ref'])
        self.assertEqual(verify['firmware_ref'], 'sha256:' + provenance['firmware_elf_sha256'])
        self.assertEqual(evidence['input_verification']['status'], 'model_verified')
        self.assertTrue(all(result['passed'] for result in evidence['input_verification']['oracle_results']))
        stimulus = evidence['input_verification']['stimuli'][0]
        requested = verify['stimuli'][0]
        self.assertEqual((stimulus['component'], stimulus['at_cycle'], stimulus['value'], stimulus['outcome']),
                         (requested['component'], requested['after_cycles'], requested['value'], 'applied'))
        self.assertEqual(verify['max_steps'], 50000000)
        self.assertIn('matches', verify['oracle']['serial'][1])
        self.assertEqual(diagram['mechanical']['version'], read('kernelcad-reference.json')['revision'])
        self.assertEqual(diagram['mechanical']['meshProvenance'], read('kernelcad-reference.json')['meshProvenance'])
        self.assertFalse(binding['physical_tested'])


if __name__ == '__main__':
    unittest.main()
