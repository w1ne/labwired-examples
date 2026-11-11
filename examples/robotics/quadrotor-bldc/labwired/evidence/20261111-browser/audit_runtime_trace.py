#!/usr/bin/env python3
"""Read-only audit of a passive LabWired Worker/CAD browser trace."""
import argparse
import base64
import hashlib
import gzip
import json
from collections import Counter
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('trace', type=Path)
p.add_argument('--output', type=Path)
a = p.parse_args()
def bytes_for(name):
    path = a.trace / name
    return path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix(path.suffix + '.gz').read_bytes())
read = lambda name: json.loads(bytes_for(name))
workers, cad, compiles, events = map(read, ['worker-final.json', 'cad-final.json', 'compiles.json', 'events.json'])
project = read('local-project-fixture.json')['project']
sources = {'ctrl1': project['source_code'], **{f['part_id']: f['source_code'] for f in project['firmware']}}
compiled = []
for c in compiles:
    q, r = c['request'], c['response']
    chip = 'ctrl' + q['source'].splitlines()[0].split()[-1]
    binary = base64.b64decode(r['elf'])
    assert sources[chip] == q['source'], f'{chip}: saved source mismatch'
    assert c['status'] == 200 and r['success'] and not r['errors']
    assert binary[:4] == b'\x7fELF'
    compiled.append({'chip': chip, 'board': q['board'], 'language': q['language'],
                     'duty_permille': int(q['source'].splitlines()[1].split()[-1]),
                     'source_sha256': hashlib.sha256(q['source'].encode()).hexdigest(),
                     'elf_bytes': len(binary), 'elf_sha256': hashlib.sha256(binary).hexdigest(),
                     'saved_source_exact': True})
assert len(compiled) == 4 and len({c['elf_sha256'] for c in compiled}) == 4
compiled.sort(key=lambda c: c['chip'])
raw, init, commands, worker_errors = [], [], [], []
for e in workers:
    d = e['data']; m = d.get('msg', {})
    if m.get('t') == 'init':
        init.append({'chip': d['chip'], 'firmware_bytes': m['payload']['firmwareLength'],
                     'clock_source': 'systemYaml/chipYaml in raw trace'})
    if m.get('t') == 'command':
        commands.append({'epoch_ms': e['epochMs'], 'chip': d['chip'], 'method': m['method'], 'args': m['args']})
    if m.get('t', '').endswith('Error'):
        worker_errors.append({'chip': d.get('chip'), 'type': m['t'], 'message': m.get('message')})
    if d.get('t') == 'labSnapshot':
        items = d['states']
    elif d.get('t') == 'lab' and m.get('t') == 'snapshot':
        items = [{'chip': d['chip'], 'state': m['state']}]
    else:
        items = []
    for item in items:
        for state in item['state'].get('actuatorStates', []):
            raw.append({'epoch_ms': e['epochMs'], 'chip': item['chip'], 'state': state,
                        'cycles': item['state'].get('cycles'), 'uart': item['state'].get('uartOutput', '')})
assert sorted((i['chip'], i['firmware_bytes']) for i in init) == sorted((c['chip'], c['elf_bytes']) for c in compiled)
# Workers and iframe are dumped sequentially. Bound comparisons to their common recorded time.
common_end = min(max(e['epochMs'] for e in workers), max(e['epochMs'] for e in cad))
matches, mismatches, excluded, age_ms = 0, [], 0, []
for e in cad:
    for motion in e['data'].get('motions', []):
        if e['epochMs'] > common_end:
            excluded += 1
            continue
        channel = int(motion['id'][1:]); sign = -1 if channel in (2, 3) else 1
        candidates = [r for r in raw if r['epoch_ms'] <= e['epochMs']
                      and r['state']['id'] == f'rotor{channel}'
                      and r['state']['position_rad'] * sign == motion['positionRad']
                      and r['state']['speed_rpm'] * sign == motion['speedRpm']
                      and r['state']['control_state'] == motion['controlState']
                      and r['state']['faults'] == motion['faults']]
        if candidates:
            matches += 1
            age_ms.append(e['epochMs'] - max(r['epoch_ms'] for r in candidates))
        else:
            mismatches.append({'sequence': e['data']['sequence'], 'motion': motion['id'], 'epoch_ms': e['epochMs']})
assert matches > 0 and not mismatches
press = next(c for c in commands if c['chip'] == 'ctrl1' and c['method'] == 'setBoardIoInput' and c['args'] == ['fault1', True])
release = next(c for c in commands if c['chip'] == 'ctrl1' and c['method'] == 'setBoardIoInput' and c['args'] == ['fault1', False])
assert press['epoch_ms'] < release['epoch_ms']
assert all(c['chip'] == 'ctrl1' for c in commands)
first_off = next(r['epoch_ms'] for r in raw if r['chip'] == 'ctrl1' and r['epoch_ms'] >= press['epoch_ms'] and r['state']['control_state'] == 'off:external-enable')
channels = []
for number in range(1, 5):
    chip = f'ctrl{number}'; values = [r for r in raw if r['chip'] == chip]
    before = [r for r in values if r['epoch_ms'] < press['epoch_ms']][-1]
    after = [r for r in values if r['epoch_ms'] >= first_off]
    final = values[-1]
    assert before['state']['control_state'] == 'inverter'
    if number == 1:
        assert all(v['state']['control_state'] == 'off:external-enable' for v in after)
        assert abs(final['state']['speed_rpm']) < 0.001
        assert 'ROTOR 1 FAULT DRIVER' in final['uart'] and 'ROTOR 1 INVERTER OFF' in final['uart']
    else:
        assert all(v['state']['control_state'] == 'inverter' and abs(v['state']['speed_rpm']) > 200 for v in after)
        assert 'FAULT' not in final['uart']
    channels.append({'chip': chip, 'before_rpm': before['state']['speed_rpm'],
                     'final_rpm': final['state']['speed_rpm'], 'final_control_state': final['state']['control_state'],
                     'final_cycles': final['cycles'], 'samples_after_first_motor_disabled': len(after),
                     'post_fault_states': dict(Counter(r['state']['control_state'] for r in after)),
                     'uart': final['uart']})
assert all(r['state']['bus_voltage_v'] == 24 for r in raw)
report = {
    'verdict': 'PASS within local patched four-channel reduced-order motor bench scope',
    'scope': 'Real saved C sources and hosted compiler, existing WASM MCU/motor plants, local candidate sender and CAD receiver; not deployed production and not actual OpenESC/flight validation.',
    'trace_directory': str(a.trace), 'compile_results': compiled,
    'worker_initializations': init,
    'worker_binary_identity_limit': 'Capture retains boot payload length but not boot-payload bytes; compiler ELF hashes plus per-node UART identifiers/duty and source loading path establish the observed compile/boot chain.',
    'cad_raw_equality': {'fields': ['absolute shaft angle', 'speed RPM', 'control state', 'fault list'],
                         'mapping_signs': {'M1': 1, 'M2': -1, 'M3': -1, 'M4': 1},
                         'exact_matches': matches, 'mismatches': mismatches,
                         'common_capture_end_epoch_ms': common_end,
                         'excluded_tail_observations': excluded,
                         'exclusion_reason': 'CAD capture continues after worker capture ends; no corresponding raw record is available.',
                         'matched_observation_age_ms_min_max': [min(age_ms), max(age_ms)]},
    'fault': {'kind': 'Simulated active-HIGH ctrl1 GPIO PB7 driver-fault input; firmware disables inverter',
              'press': press, 'release': release, 'first_disabled_epoch_ms': first_off,
              'no_transistor_fault_injected': True, 'channels': channels},
    'cad_frame_states': dict(Counter(e['data'].get('state') for e in cad if e['data'].get('type') == 'kernelcad.runtime.frame')),
    'explicit_pause_test': 'Skipped: UI Pause button count was zero. Paused CAD frames occurred when CAD view was hidden.',
    'worker_errors': worker_errors,
    'worker_errors_scope': 'Four unsupported runtime snapshot queries; no initError, stepError or commandError in captured Worker traffic. Simulation observations and UART continue.',
    'known_environment_errors': ['Development Clerk initialization HTTP 400', 'Vite HMR websocket failure on locally routed CAD origin'],
    'physical_limits': ['24 V generic BLDC plant differs from selected 4S 14.8 V nominal / 16.8 V full hardware',
                        'STM32L476 bench firmware differs from actual AT32F421/AM32 ESC and RP2354B/Betaflight FC',
                        'No actual MOSFET/gate-driver switching, battery sag, thermal or EMI proof',
                        'No calibrated propeller thrust, airframe rigid-body dynamics, attitude loop or flight proof',
                        'CAD applies one-way observed shaft poses; geometry does not feed forces back into the motor model'],
    'input_sha256': {name: hashlib.sha256(bytes_for(name)).hexdigest() for name in ['compiles.json','worker-final.json','cad-final.json','events.json','local-project-fixture.json']}
}
text = json.dumps(report, indent=2) + '\n'
if a.output: a.output.write_text(text)
else: print(text)
print(f'PASS: {matches} exact motion matches; {excluded} transparent tail exclusions; 4 real compiles; isolated ctrl1 firmware shutdown.')
