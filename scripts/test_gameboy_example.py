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

    def test_native_preserve_preflight_binds_exact_source_and_generated_rules(self):
        prefix = 'pcb/native-preserve-preflight/'
        summary = read(prefix + 'local-preserve-drc-preflight.json')
        preparation = read(prefix + 'preparation-result.json')
        execution = read(prefix + 'drc-execution.json')
        report = read(prefix + 'drc.json')
        pcb_path = 'pcb/handheld-carrier.kicad_pcb'
        pcb_ref = 'sha256:' + digest(pcb_path)
        self.assertEqual(summary['pcb_ref'], pcb_ref)
        self.assertEqual(summary['pcb_bytes'], (GAME / pcb_path).stat().st_size)
        self.assertTrue(summary['passed'])
        self.assertFalse(summary['hosted_job_submitted'])
        self.assertFalse(summary['canonical_project_mutated'])
        self.assertEqual((preparation['mode'], preparation['status'], preparation['networkCalls']),
                         ('preserve', 'imported', 0))
        self.assertEqual(preparation['pcb_ref'], pcb_ref)
        for name, identity in preparation['files'].items():
            path = pcb_path if name == 'board.kicad_pcb' else prefix + name
            self.assertEqual(digest(path), identity['sha256'], name)
            self.assertEqual((GAME / path).stat().st_size, identity['bytes'], name)
        self.assertEqual(execution['inputSha256Before'], execution['inputSha256After'])
        self.assertTrue(execution['inputsUnchanged'])
        self.assertEqual(execution['inputSha256Before'], summary['input_sha256'])
        self.assertEqual(execution['exitCode'], 0)
        self.assertEqual(execution['kicadVersion'], report['kicad_version'])
        self.assertEqual(execution['drcReportSha256'], digest(prefix + 'drc.json'))
        self.assertEqual(summary['drc']['report_sha256'], digest(prefix + 'drc.json'))
        self.assertEqual(report['violations'], [])
        self.assertEqual(report['unconnected_items'], [])
        self.assertFalse(summary['drc']['schematic_parity_checked'])
        rule_artifact = read(prefix + 'rule-artifact.json')
        self.assertEqual(rule_artifact['pcb_ref'], pcb_ref)
        self.assertEqual(rule_artifact['pro'], (GAME / prefix / 'board.kicad_pro').read_text())
        self.assertEqual(rule_artifact['dru'], (GAME / prefix / 'board.kicad_dru').read_text())
        self.assertEqual(rule_artifact['applied_rules'], read(prefix + 'applied-rules.json'))
        self.assertEqual(summary['rules_ref'], 'sha256:' + digest(prefix + 'rule-artifact.json'))
        self.assertEqual(preparation['rules_ref'], summary['rules_ref'])
        wire_json = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(wire_json(rule_artifact['applied_rules'])).hexdigest(),
                         summary['rules_digest'])
        self.assertEqual('sha256:' + hashlib.sha256(wire_json(read(prefix + 'requested-rules.json'))).hexdigest(),
                         preparation['inputRulesRef'])
        saved = read('project-binding.json')
        self.assertEqual(saved['pcb']['local_preserve_preflight'], prefix + 'local-preserve-drc-preflight.json')
        self.assertEqual(read('manifest.json')['pcb']['preserve_preflight'], saved['pcb']['local_preserve_preflight'])

    def test_production_view_evidence_binds_current_artifacts_and_separates_scopes(self):
        manifest = read('manifest.json')
        prefix = 'firmware/production-view/'
        index = read(prefix + 'index.json')
        self.assertEqual(manifest['evidence']['browser_production'], prefix + 'index.json')
        self.assertEqual(index['project']['id'], manifest['project']['id'])
        self.assertEqual(index['project']['content_hash'], manifest['project']['content_hash'])
        self.assertEqual((index['project']['parts'], index['project']['wires']), (10, 24))
        self.assertEqual(index['firmware']['source_sha256'], digest(manifest['source']['path']))
        self.assertEqual(index['firmware']['source_bytes'], (GAME / manifest['source']['path']).stat().st_size)
        self.assertEqual(index['firmware']['artifact_ref'], manifest['firmware_ref'])
        self.assertEqual(index['firmware']['source_tree_ref'], manifest['source']['tree_ref'])
        self.assertEqual(index['mechanical']['source_sha256'], digest(manifest['mechanical']['path']))
        self.assertEqual(index['mechanical']['version'], manifest['mechanical']['revision'])
        self.assertEqual(index['mechanical']['meshProvenance'], manifest['mechanical']['mesh_provenance'])
        self.assertEqual(index['native_pcb']['source_sha256'], digest(manifest['pcb']['path']))
        owner = read(prefix + index['owner']['record'])
        self.assertEqual(digest(prefix + index['owner']['record']), index['owner']['record_sha256'])
        self.assertEqual(owner['owner_readback']['contentHash'], index['project']['content_hash'])
        self.assertEqual(owner['owner_readback']['firmwareRef'], index['firmware']['artifact_ref'])
        self.assertEqual(owner['owner_readback']['mechanical']['version'], index['mechanical']['version'])
        self.assertEqual((owner['owner_readback']['httpStatus'], owner['owner_readback']['is_owner'], owner['owner_readback']['role']), (200, True, 'owner'))
        self.assertFalse(owner['rendering_passed'])
        self.assertFalse(index['results']['owner_rendering_verified'])
        self.assertTrue(all(not context['created'] for context in owner['webgl_probe']['contexts']))
        self.assertEqual({surface['surface'] for surface in index['surfaces']}, {'desktop', 'mobile'})
        for surface in index['surfaces']:
            record = read(prefix + surface['record'])
            self.assertEqual(digest(prefix + surface['record']), surface['record_sha256'])
            self.assertEqual(record['anonymous_project_readback']['contentHash'], index['project']['content_hash'])
            self.assertEqual(record['anonymous_project_readback']['firmware']['artifact']['ref'], index['firmware']['artifact_ref'])
            self.assertFalse(record['anonymous_project_readback']['is_owner'])
            self.assertFalse(record['authentication']['local_auth_disabled'])
            self.assertFalse(record['authentication']['owner_storage_copied'])
            self.assertFalse(record['authentication']['authorization_header_supplied'])
            self.assertFalse(record['authentication']['owner_workflow_verified'])
            self.assertTrue(record['build']['documentUsesServedMain'])
            self.assertEqual(record['build']['documentModules'], record['build']['mainAssets'])
            self.assertEqual(record['build']['commit'], surface['served_commit'])
            self.assertEqual(record['cad']['ready_event']['data']['revision'], index['mechanical']['version'])
            self.assertTrue(all(record['cad']['ready_event']['data'][key] for key in ('geometryNonempty', 'cameraFitted', 'framePresented')))
            self.assertTrue(record['cad']['same_iframe_after_return'])
            self.assertTrue(record['cad']['same_iframe_after_reopen'])
            runtime = record['runtime']
            self.assertTrue(runtime['same_worker_object'])
            self.assertTrue(runtime['same_runtime_worker'])
            self.assertEqual(runtime['worker_asset'], surface['simulation_worker_asset'])
            gain = runtime['cad_visible_end']['cycles'] - runtime['cad_visible_start']['cycles']
            self.assertEqual(gain, surface['cycle_gain_while_cad_visible'])
            self.assertGreater(gain, 0)
            self.assertEqual(record['uncaught_exception_count'], 0)
            self.assertFalse(record['clean_console'])
            self.assertTrue(record['console_errors'])
            screenshot = surface['cad_screenshot']
            self.assertEqual(digest(prefix + screenshot['path']), screenshot['sha256'])
            self.assertEqual((GAME / prefix / screenshot['path']).stat().st_size, screenshot['bytes'])
            self.assertEqual(record['cad_screenshot']['sha256'], screenshot['sha256'])
            self.assertFalse(record['canonical_mutation'])
        self.assertFalse(index['results']['canonical_mutation'])
        self.assertFalse(index['results']['physical_hardware_tested'])

    def test_source_rom_and_cad_generators_reproduce_recorded_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = pathlib.Path(tmp) / 'gameboy'
            shutil.copytree(GAME, copied)
            mechanical = read('manifest.json')['mechanical']
            for script in ('firmware/build_rom.py', 'firmware/build_firmware.py',
                           'mechanical/generate_enclosure.py', mechanical['generator']):
                subprocess.run([sys.executable, str(copied / script)], check=True,
                               capture_output=True, text=True, timeout=10)
            for name in ('firmware/wire_runner.gb', 'firmware/wire_runner_rom.h',
                         'firmware/gameboy.c', 'mechanical/labwired-gameboy.kcad.ts',
                         mechanical['path'], mechanical['derived_interfaces']):
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
        mechanical = read('manifest.json')['mechanical']
        review = read(mechanical['fixed_mate_review'])
        derived = read(mechanical['derived_interfaces'])
        interfaces = read('design-interfaces.json')
        layout = read('pcb/carrier-layout.json')
        routing = read('pcb/routing-report.json')
        self.assertEqual(digest(ref['sourceFile']), ref['sourceSha256'])
        self.assertEqual(mechanical['path'], ref['sourceFile'])
        self.assertEqual(mechanical['sha256'], ref['sourceSha256'])
        self.assertEqual(derived['derived']['pcbSha256'], digest('pcb/handheld-carrier.kicad_pcb'))
        for path, expected in derived['sources'].items():
            self.assertEqual(digest(path), expected, path)
        self.assertEqual(review['evaluationEvidence']['source']['sha256'], ref['sourceSha256'])
        self.assertEqual(digest('design-interfaces.json'), ref['interfaceSha256'])
        self.assertEqual(routing['interface_sha256'], ref['interfaceSha256'])
        self.assertEqual(review['validator']['status'], 'solved')
        self.assertEqual((review['validator']['partCount'], review['validator']['jointCount']), (59, 58))
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
        self.assertEqual(binding['mechanical_revision'], read('manifest.json')['mechanical']['revision'])
        self.assertEqual(binding['mechanical_revision'], read('project-binding.json')['mechanical']['version'])
        self.assertEqual(binding['automatic_import'], 'design_only; see final-import-report.json')
        self.assertTrue((GAME / 'pcb/final-import-report.json').is_file())
        self.assertEqual(pcb_hash, read('kernelcad-reference.json')['pcbSha256'])
        self.assertEqual(pcb_hash, layout['pcb_sha256'])
        self.assertEqual(pcb_hash, read('pcb/routing-report.json')['pcb_sha256'])
        exported = read('pcb/export-validation.json')
        self.assertEqual(exported['input_sha256'], pcb_hash)
        self.assertEqual(exported['carrier_layout_sha256'], digest('pcb/carrier-layout.json'))
        self.assertEqual(exported['assembly_interfaces_sha256'], digest('pcb/assembly-interfaces.json'))
        self.assertEqual(exported['project_settings_sha256'], digest('pcb/handheld-carrier.kicad_pro'))
        self.assertEqual((exported['drc']['violations'], exported['drc']['unconnected_items']), (0, 0))
        self.assertFalse(exported['physical_fit_verified'])
        self.assertFalse(exported['manufacturing_signoff'])
        imported = read('pcb/final-import-report.json')
        self.assertEqual(imported['source']['sha256'], pcb_hash)
        self.assertEqual(imported['source']['bytes'], (GAME / 'pcb/handheld-carrier.kicad_pcb').stat().st_size)
        self.assertTrue(imported['result']['design_context_ok'])
        self.assertFalse(imported['result']['twin_buildable'])
        self.assertEqual(imported['result']['mode'], 'design_only')
        mappings = imported['result']['mapping']
        self.assertEqual({row['ref'] for row in mappings}, {row['ref'] for row in layout['components']})
        self.assertEqual({status: sum(row['status'] == status for row in mappings)
                          for status in ('mapped', 'dropped', 'ignored')},
                         {'mapped': 2, 'dropped': 9, 'ignored': 5})
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
        self.assertTrue(any('matches' in clause for clause in verify['oracle']['serial']))
        self.assertEqual(diagram['mechanical']['version'], read('kernelcad-reference.json')['revision'])
        self.assertEqual(diagram['mechanical']['meshProvenance'], read('kernelcad-reference.json')['meshProvenance'])
        self.assertFalse(binding['physical_tested'])
        controls = read('firmware/control-validation.json')
        vectors = read('firmware/control-vectors.json')
        self.assertEqual(controls['source_sha256'], digest('firmware/gameboy.c'))
        self.assertEqual(controls['rom_sha256'], digest('firmware/wire_runner.gb'))
        self.assertEqual(controls['firmware_ref'], diagram['firmware']['artifact']['ref'])
        self.assertEqual(vectors['firmware_ref'], controls['firmware_ref'])
        self.assertEqual(vectors['diagram'], {key: diagram[key] for key in ('version', 'board', 'parts', 'wires')})
        requests = {case['name']: case for case in vectors['cases']}
        self.assertEqual(set(requests), {'up', 'down', 'left', 'right', 'a', 'b', 'select', 'start'})
        self.assertEqual(verify['oracle'], requests['right']['oracle'])
        self.assertEqual(verify['stimuli'], requests['right']['stimuli'])
        saved = read('project-binding.json')
        self.assertTrue(saved['readback_verified'])
        self.assertEqual(saved['mechanical'], diagram['mechanical'])
        self.assertEqual(saved['stimuli'], verify['stimuli'])
        self.assertEqual(saved['source_sha256'], digest('firmware/gameboy.c'))
        self.assertEqual(saved['firmware_ref'], verify['firmware_ref'])
        self.assertEqual(saved['pcb']['native_source_sha256'], pcb_hash)
        self.assertEqual(saved['content_hash'], read('manifest.json')['project']['content_hash'])
        self.assertEqual({case['name'] for case in controls['cases']}, set(requests))
        self.assertFalse(controls['physical_hardware_tested'])
        for case in controls['cases']:
            self.assertEqual(case['status'], 'model_verified', case['name'])
            self.assertTrue(all(result['passed'] for result in case['oracle_results']), case['name'])
            expected = requests[case['name']]['stimuli']
            self.assertEqual(len(case['stimuli']), len(expected), case['name'])
            for actual, request in zip(case['stimuli'], expected):
                self.assertEqual((actual['component'], actual['channel'], actual['at_cycle'], actual['value'], actual['outcome']),
                                 (request['component'], request['channel'], request['after_cycles'], request['value'], 'applied'))


if __name__ == '__main__':
    unittest.main()
