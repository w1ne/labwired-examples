#!/usr/bin/env python3
"""Extract purchased ST shield mechanics from the verified factory Gerbers.

Requires gerbonara 1.6.3. This creates mechanical references, not routed PCBs.
The PCB stack thickness is transcribed from each archive's fabrication drawing.
"""
import argparse
import hashlib
import json
import math
import warnings
from collections import Counter, defaultdict
from pathlib import Path

from gerbonara import ExcellonFile, GerberFile
from gerbonara.cam import FileSettings
from gerbonara.graphic_objects import Flash, Line
from gerbonara.utils import Inch, MM


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(directory, kind):
    unit = MM if kind == 'iom' else Inch
    fab_path = next(directory.glob('*_10FAB.GBR'))
    top_path = next(directory.glob('*_01TOP.GBR'))
    drill_path = next(directory.glob('*.drl'))
    fab = GerberFile.open(fab_path)
    # The eight 1 mm fabrication-outline strokes have no frame/text ambiguity.
    lines = [o for o in fab.objects if isinstance(o, Line)
             and abs(MM(getattr(o.aperture, 'diameter', 0), o.aperture.unit) - 1) < .001]
    if len(lines) != 8:
        raise ValueError(f'Expected eight factory outline lines, found {len(lines)}')
    edges = [[(round(MM(o.x1, o.unit), 6), round(MM(o.y1, o.unit), 6)),
              (round(MM(o.x2, o.unit), 6), round(MM(o.y2, o.unit), 6))] for o in lines]
    adjacency = defaultdict(list)
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    if any(len(v) != 2 for v in adjacency.values()):
        raise ValueError('Factory outline is not a single closed degree-two loop')
    first = min(adjacency)
    points, previous, current = [first], None, first
    while True:
        choices = sorted(p for p in adjacency[current] if p != previous)
        following = choices[0]
        if following == first:
            break
        points.append(following)
        previous, current = current, following
        if len(points) > 8:
            raise ValueError('Factory outline traversal did not close')
    if len(points) != 8:
        raise ValueError('Factory outline did not include every segment')
    # Both paired TOP Gerbers explicitly declare 2.5 coordinates. The Excellon
    # files omit that field; use the paired source declaration, then cross-check
    # every plated hole against a TOP pad/via flash at the same location.
    settings = FileSettings(number_format=(2, 5), unit=unit, zeros='leading')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', SyntaxWarning)
        drill = ExcellonFile.open(drill_path, settings=settings)
    holes = [{'xMm': round(MM(o.x, o.unit), 6),
              'yMm': round(MM(o.y, o.unit), 6),
              'diameterMm': round(MM(o.tool.diameter, o.tool.unit), 6)} for o in drill.objects]
    flashes = [(MM(o.x, o.unit), MM(o.y, o.unit))
               for o in GerberFile.open(top_path).objects if isinstance(o, Flash)]
    unmatched = []
    for h in holes:
        if abs(h['diameterMm'] - 1.1176) < .000001:  # factory non-plated locator row
            continue
        distance = min(math.hypot(h['xMm'] - x, h['yMm'] - y) for x, y in flashes)
        if distance > .0006:
            unmatched.append({**h, 'nearestFlashMm': distance})
    if unmatched:
        raise ValueError(f'{len(unmatched)} plated drill centres do not match TOP: {unmatched[:8]}')
    extent = {'min': [min(p[i] for p in points) for i in range(2)],
              'max': [max(p[i] for p in points) for i in range(2)]}
    counts = Counter(h['diameterMm'] for h in holes)
    area = abs(sum(points[i][0]*points[(i+1)%8][1]-points[(i+1)%8][0]*points[i][1] for i in range(8)))/2
    return {
        'schema': 'labwired.factory-gerber-mechanical-reference.v1',
        'board': 'STEVAL-IOM001V1' if kind == 'iom' else 'STEVAL-IOD003V1',
        'scope': 'Factory outline and all drill centres; purchased-board mechanical reference only. No reconstructed electrical layout or as-built component model is asserted.',
        'sources': [{'file': p.name, 'sha256': sha(p), 'byteLength': p.stat().st_size} for p in [fab_path, top_path, drill_path]],
        'outlineStrokeWidthMm': 1,
        'outline': points,
        'boundsMm': extent,
        'coordinateFormat': '2.5, from paired TOP Gerber; metric IOM and inch IOD',
        'coordinateVerification': {'platedDrillsCompared': len(holes)-counts[1.1176], 'unmatched': 0, 'toleranceMm': .0006},
        'fullStackThicknessMm': 1.67,
        'thicknessSource': 'Factory FAB drawing design cross section: 1.6 mm FR-4 + 0.035 mm copper on each side. Drawing gives the stack as a reference dimension.',
        'drillCounts': {str(k): v for k,v in sorted(counts.items())},
        'holes': holes,
        'calculatedBoardVolumeMm3': (area-sum(math.pi*(h['diameterMm']/2)**2 for h in holes))*1.67,
    }


def source(data):
    points = data['outline']
    cross = [points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points))]
    # holes() uses the outer face's area centroid, not its bounding-box centre.
    # The outer loop remains the reference after earlier holes are cut.
    centre = [sum((points[i][axis]+points[(i+1)%len(points)][axis])*cross[i] for i in range(len(points)))/(3*sum(cross)) for axis in range(2)]
    size = [b-a for a,b in zip(data['boundsMm']['min'], data['boundsMm']['max'])]
    groups = defaultdict(list)
    for h in data['holes']:
        groups[h['diameterMm']].append({'u': round(h['xMm']-centre[0],6), 'v': round(h['yMm']-centre[1],6)})
    code = [f'// {data["board"]}: factory-Gerber mechanical reference, millimetres.',
            '// Full fabrication source/provenance is in the adjacent geometry JSON.',
            '// This is not a manufacturer-supplied populated 3D model or a routed PCB.',
            f'let board = extrudePolygon({json.dumps(data["outline"], separators=(",",":"))}, 1.67);']
    for diameter, positions in sorted(groups.items()):
        code.append(f'board = board.holes("top", {{diameter:{diameter},depth:"through",positions:{json.dumps(positions,separators=(",",":"))}}});')
    code.extend([f'require("factory-outline-and-thickness", bbox(board).within({{x:[{size[0]-.001},{size[0]+.001}],y:[{size[1]-.001},{size[1]+.001}],z:[1.669,1.671]}}));', 'return board;'])
    return '\n'.join(code)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_directory', type=Path, help='Contains extracted iom/ and iod/ factory Gerbers')
    parser.add_argument('output_directory', type=Path)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    for kind in ['iom', 'iod']:
        data = extract(args.source_directory/kind, kind)
        (args.output_directory/f'{kind}-factory-geometry.json').write_text(json.dumps(data,indent=2)+'\n')
        (args.output_directory/f'{kind}-factory-board.kcad.ts').write_text(source(data))
        print(data['board'],len(data['holes']),'holes',data['boundsMm'],'calculated volume',data['calculatedBoardVolumeMm3'])


if __name__ == '__main__':
    main()
