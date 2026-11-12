#!/usr/bin/env python3
"""Recompute conservative external clearance from source-bound hosted BREP facts."""
from pathlib import Path
import hashlib
import json
import math

cad = Path(__file__).resolve().parents[1]
evidence = cad / 'evidence'
step = json.loads((evidence / 'native-fc-step-inspection-20261112.json').read_text())
assembly = json.loads((evidence / 'native-fc-assembly-inventory-20261112.json').read_text())
esc = json.loads((evidence / 'populated-clearance-audit-20261112.json').read_text())
source = cad / 'drone.kcad.ts'
model = cad.parent / 'hardware/flight-controller-openfc-lite-rev2-lw1/mechanical-review/fc-populated.step'
assert hashlib.sha256(source.read_bytes()).hexdigest() == assembly['sourceSha256']
assert hashlib.sha256(model.read_bytes()).hexdigest() == step['sourceSha256']
solids = step['solids']
assert len(solids) == step['solidCount'] == 164
assert all(s['brepCheck'] == 'valid' for s in solids)
translation = [0, -12.75, 22]
fc = {
    'min': [min(s['bboxExact']['min'][i] for s in solids) + translation[i] for i in range(3)],
    'max': [max(s['bboxExact']['max'][i] for s in solids) + translation[i] for i in range(3)],
}
epsilon = step['precisionAllowanceMm']
external = [p for p in assembly['parts'] if not p['name'].startswith('fc-')
            and p['name'] not in ('esc-board', 'esc-population-native-mesh')]
external.append({'name': 'populated-esc-exact-step', 'bbox': esc['pcbBoundsAssemblyMm']})
pairs = []
for part in external:
    b = part['bbox']
    gaps = [max(fc['min'][i] - b['max'][i], b['min'][i] - fc['max'][i], 0) for i in range(3)]
    lower = max(math.hypot(*gaps) - epsilon, 0)
    assert lower > 0, f"No proven separating bound: {part['name']}"
    pairs.append({'part': part['name'], 'axisGapMm': gaps, 'separationLowerBoundMm': lower})
assert len(pairs) == 31
rings = []
for x in [-15.25, 15.25]:
    for y in [-15.25, 15.25]:
        distances = []
        for solid in solids:
            if solid['index'] == step['substrateIndex']:
                # Board bottom and ring top share z0 in the FC export frame.
                assert solid['bboxExact']['min'][2] == 0
                continue
            b = solid['bboxExact']
            dx = max(b['min'][0] - x, x - b['max'][0], 0)
            dy = max(b['min'][1] - y, y - b['max'][1], 0)
            dz = max(b['min'][2], -6.07 - b['max'][2], 0)
            # A solid lies inside its BREP box. A ring lies inside its outer
            # radius-3 cylinder. Positive separation of these supersets proves
            # separation of the original bodies, including the ring bore.
            lower = max(math.hypot(max(math.hypot(dx, dy) - 3, 0), dz) - epsilon, 0)
            assert lower > 0, f"Further exact check required: ring({x},{y}), solid {solid['index']}"
            distances.append({'solidIndex': solid['index'], 'lowerBoundMm': lower})
        rings.append({'centerNativeMm': [x, y], 'componentPairs': len(distances),
                      'minimum': min(distances, key=lambda row: row['lowerBoundMm']),
                      'substrateContact': 'coplanar z0; no positive-volume intersection'})
result = {'schema': 'labwired.native-fc-clearance.v1', 'sourceSha256': assembly['sourceSha256'],
          'fcStepSha256': step['sourceSha256'], 'translationMm': translation,
          'fcBoundsAssemblyMm': fc, 'precisionAllowanceMm': epsilon,
          'externalPairs': pairs, 'upperSupportRings': rings,
          'componentRingPairs': sum(r['componentPairs'] for r in rings),
          'geometryClearancePassed': True, 'physicalAcceptance': False,
          'limitations': ['All distances are conservative geometric lower bounds, not measured manufacturing tolerances.',
                          'Solder, cables/plugs, grommet compression, fastener retention and loads are not modeled.',
                          'L1/L2/L3 retain original package proxies; motor and propeller parts remain envelopes.',
                          'Full production design review remains false; mixed-mesh assembly-path planning is unsupported.']}
(evidence / 'native-fc-clearance-audit-20261112.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'externalPairs': len(pairs), 'minimumExternalBoundMm': min(p['separationLowerBoundMm'] for p in pairs),
                  'componentRingPairs': result['componentRingPairs'],
                  'minimumRingBoundMm': min(r['minimum']['lowerBoundMm'] for r in rings),
                  'geometryClearancePassed': True, 'physicalAcceptance': False}, indent=2))
