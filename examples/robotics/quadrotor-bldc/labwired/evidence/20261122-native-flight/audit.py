#!/usr/bin/env python3
"""Verify archived bytes and independently recompute body/fault readback checks.

This script never runs firmware or simulates motion.
"""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

def audit_bundle():
    manifest = json.loads((ROOT / 'artifacts.json').read_text())
    for name, expected in manifest['files'].items():
        data = (ROOT / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
        if name.endswith('.gz'):
            assert hashlib.sha256(gzip.decompress(data)).hexdigest() == expected['uncompressedSha256'], name
    acceptance = json.loads((ROOT / 'acceptance.json').read_text())
    for node, source in acceptance['sourceFiles'].items():
        data = (ROOT / source['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == source['sha256'], node
    assert acceptance['diagramSha256'] == hashlib.sha256(json.dumps(
        json.loads((ROOT / 'candidate-project.json').read_text())['diagram'],
        sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    project = json.loads((ROOT / 'candidate-project.json').read_text())
    project_sources = {'ctrl1': project['source_code']}
    project_sources.update({item['part_id']: item['source_code'] for item in project['firmware']})
    for node, source in acceptance['sourceFiles'].items():
        assert hashlib.sha256(project_sources[node].encode()).hexdigest() == source['sha256'], node
    expected_assets = {}
    for name in ['candidate-wasm.mjs', 'candidate-wasm.wasm', 'ctrl1.elf', 'ctrl2.elf', 'ctrl3.elf', 'ctrl4.elf', 'fc.elf']:
        folder = 'firmware' if name.endswith('.elf') else 'runtime'
        packed = name != 'candidate-wasm.mjs'
        data = (ROOT / folder / (name + '.gz' if packed else name)).read_bytes()
        if packed:
            data = gzip.decompress(data)
        expected_assets[name] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    for compiled in json.loads((ROOT / 'compiles.json').read_text()):
        assert compiled['firmware_ref'] == 'sha256:' + expected_assets[compiled['id'] + '.elf']['sha256']
    passes = negatives = 0
    with tempfile.TemporaryDirectory(prefix='quadrotor-readback-') as temporary:
        work = Path(temporary)
        for scenario in acceptance['scenarios']:
            tag = scenario['tag']
            result = work / (tag + '-result.json')
            result.write_bytes(gzip.decompress((ROOT / scenario['result']).read_bytes()))
            (work / (tag + '.ndjson')).write_bytes(gzip.decompress((ROOT / scenario['trace']).read_bytes()))
            run = subprocess.run([sys.executable, str(ROOT / 'capture/analyze-flight.py'), str(result)], capture_output=True, text=True)
            recomputed = json.loads((work / (tag + '-oracle.json')).read_text())
            expected = scenario['expectedPass']
            assert recomputed['passed'] == expected, (tag, recomputed['checks'])
            assert run.returncode == (0 if expected else 1), (tag, run.stderr)
            recorded = json.loads((ROOT / scenario['oracle']).read_text())
            for key in ['hover', 'recovery', 'maximumAltitudeM', 'finalAltitudeM']:
                assert recomputed['measurements'][key] == recorded['measurements'][key], (tag, key)
            if expected:
                captured = json.loads(result.read_text())
                assert {asset['name']: {'size': asset['size'], 'sha256': asset['sha256']}
                        for asset in captured['assets']} == expected_assets, tag
                passes += 1
                assert recomputed['checks'] == recorded['checks'], tag
            else:
                negatives += 1
        original = [json.loads(line) for line in (work / 'fault-inverter_fault.ndjson').read_text().splitlines()]
        observed = [json.loads(line) for line in (work / 'fault-inverter-gates.ndjson').read_text().splitlines()]
        for rows in (original, observed):
            for row in rows:
                row.pop('wallSeconds', None)
                row.pop('gateRegisters', None)
        assert original == observed, 'Read-only gate observations changed the captured plant trace'
        nominal = [json.loads(line) for line in (work / 'nominal-damping.ndjson').read_text().splitlines()]
        portable = [json.loads(line) for line in gzip.decompress((ROOT / 'reproduction/portable-nominal.ndjson.gz').read_bytes()).decode().splitlines()]
        for rows in (nominal, portable):
            for row in rows:
                row.pop('wallSeconds', None)
                row.pop('gateRegisters', None)
        assert nominal == portable, 'Portable driver did not reproduce the nominal trace'
    return {'artifactFiles': len(manifest['files']), 'passingScenarios': passes,
            'preservedNegativeScenarios': negatives, 'inverterObserverEquivalent': True, 'portableReplayEquivalent': True}

if __name__ == '__main__':
    print(json.dumps(audit_bundle(), indent=2))
