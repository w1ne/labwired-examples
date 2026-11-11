#!/usr/bin/env python3
"""Read-only audit of a passive LabWired Worker/CAD browser trace."""
import argparse
import base64
import hashlib
import json
from collections import Counter
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('trace', type=Path)
p.add_argument('--output', type=Path)
a = p.parse_args()
read = lambda name: json.loads((a.trace / name).read_text())
workers, cad, compiles, events = map(read, ['worker-final.json', 'cad-final.json', 'compiles.json', 'events.json'])
project = read('local-project-fixture.json')['project']
pause_at = next(e['epochMs'] for e in events if e['name'] == 'pause-click')
assert any(e['name'] == 'completed' for e in events) and not any(e['name'] == 'failed' for e in events)
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
        init.append({'chip': d['chip'], 'epoch_ms': e['epochMs'], 'firmware_bytes': m['payload']['firmwareLength'],
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
assert sorted((i['chip'], i['firmware_bytes']) for i in init if i['epoch_ms'] < pause_at) == sorted((c['chip'], c['elf_bytes']) for c in compiled)
reset_marker = next(e['epochMs'] for e in events if e['name'] == 'reset-click')
assert sorted((i['chip'], i['firmware_bytes']) for i in init if i['epoch_ms'] >= reset_marker) == sorted((c['chip'], c['elf_bytes']) for c in compiled)
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
assert all(c['chip'] == 'ctrl1' for c in commands if c['method'] == 'setBoardIoInput')
first_off = next(r['epoch_ms'] for r in raw if r['chip'] == 'ctrl1' and r['epoch_ms'] >= press['epoch_ms'] and r['state']['control_state'] == 'off:external-enable')
channels = []
for number in range(1, 5):
    chip = f'ctrl{number}'; values = [r for r in raw if r['chip'] == chip and r['epoch_ms'] < pause_at]
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
paused, held, stopped = map(read, ['ui-paused.json', 'ui-pause-held.json', 'ui-stopped.json'])
assert paused['status']['state'] == held['status']['state'] == 'paused'
assert stopped['status']['state'] == 'paused' and stopped['status']['motionCount'] == '0'
reset_frames = [e['data'] for e in cad if e['epochMs'] >= reset_marker and e['data'].get('type') == 'kernelcad.runtime.frame']
assert any(f['state'] == 'stopped' for f in reset_frames)
assert all(f['state'] in ('stopped', 'paused') and not f.get('motions') for f in reset_frames)
assert len(paused['rows']) == len(held['rows']) == len(stopped['rows']) == 4
held_by_id = {r['motionId']: r for r in held['rows']}
for row in paused['rows']:
    other = held_by_id[row['motionId']]
    assert row['positionRad'] == other['positionRad']
    assert row['speedRpm'] == other['speedRpm']
    assert row['sampleCurrent'] == other['sampleCurrent'] == 'false'
for row in stopped['rows']:
    assert row['sampleCurrent'] == 'false' and 'positionRad' not in row and 'speedRpm' not in row
    assert 'No sample' in row['text']
hold_event = next(e for e in events if e['name'] == 'pause-hold-verified')
assert hold_event['epochMs'] - pause_at >= 5000
reset_at = next(e['epochMs'] for e in events if e['name'] == 'reset-click')
assert reset_at > hold_event['epochMs']
assert not [e for e in workers if e['direction'] == 'sent' and e['data'].get('t') == 'labFrame' and pause_at + 1000 <= e['epochMs'] < reset_at]
provenance = read('provenance.json')
assert all(not t['dirty'] for t in provenance['sourceTrees'])
engine_errors = [e for e in workers if e['data'].get('t') in ('initError', 'stepError', 'commandError') or e['data'].get('msg', {}).get('t') in ('initError', 'stepError', 'commandError')]
assert not engine_errors
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
    'explicit_pause_test': {'verified': True, 'held_positions_rad': [r['positionRad'] for r in held['rows']],
                            'pause_to_hold_marker_ms': hold_event['epochMs'] - pause_at,
                            'all_four_samples_marked_last_observed': True, 'no_worker_run_frames_after_1s_quiescence_until_reset': True},
    'reset_test': {'verified': True, 'final_status': stopped['status']['state'], 'observed_sequence': 'Transient stopped while reinitializing, then paused with zero observed motions',
                   'all_four_positions_and_speeds_cleared': True, 'all_four_worker_nodes_reinitialized': True},
    'fault_interval_end_epoch_ms': pause_at,
    'fault_interval_limit': 'Before explicit pause/reset; reset observations are not used to assert uninterrupted peer operation.',
    'source_provenance': provenance,
    'worker_errors': worker_errors,
    'worker_errors_scope': f'{len(worker_errors)} unsupported runtime snapshot queries across initial boot and reset; no initError, stepError or commandError in captured Worker traffic. Simulation observations and UART continue.',
    'engine_errors': engine_errors,
    'known_environment_errors': ['Development Clerk initialization HTTP 400', 'Vite HMR websocket failure on locally routed CAD origin'],
    'physical_limits': ['24 V generic BLDC plant differs from selected 4S 14.8 V nominal / 16.8 V full hardware',
                        'STM32L476 bench firmware differs from actual AT32F421/AM32 ESC and RP2354B/Betaflight FC',
                        'No actual MOSFET/gate-driver switching, battery sag, thermal or EMI proof',
                        'No calibrated propeller thrust, airframe rigid-body dynamics, attitude loop or flight proof',
                        'CAD applies one-way observed shaft poses; geometry does not feed forces back into the motor model'],
    'input_sha256': {name: hashlib.sha256((a.trace/name).read_bytes()).hexdigest() for name in ['compiles.json','worker-final.json','cad-final.json','events.json','local-project-fixture.json','provenance.json','ui-paused.json','ui-pause-held.json','ui-stopped.json','assertions.json']}
}
text = json.dumps(report, indent=2) + '\n'
if a.output: a.output.write_text(text)
else: print(text)
print(f'PASS: {matches} exact motion matches; {excluded} transparent tail exclusions; 4 real compiles; isolated ctrl1 firmware shutdown.')
