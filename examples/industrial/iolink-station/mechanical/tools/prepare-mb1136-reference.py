#!/usr/bin/env python3
"""Extract ST's real milling profile from a KiCad 10 import of MB1136.PcbDoc.

This is a mechanical reference for a purchased board, not fabrication data.
The original import's Edge.Cuts is only the Altium bounding rectangle. Factory
milling is on Mechanical 1. Preserve the original separately. No component
geometry is invented by this conversion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('imported_board', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--receipt', type=Path, required=True)
args = parser.parse_args()
b = pcbnew.LoadBoard(str(args.imported_board))
removed = []
converted = []
repairs = []
source_drawings = list(b.GetDrawings())  # Keep SWIG handles alive through SaveBoard.
for drawing in source_drawings:
    if drawing.GetLayer() == pcbnew.Edge_Cuts:
        removed.append(drawing.m_Uuid.AsString())
        b.Remove(drawing)
        continue
    if b.GetLayerName(drawing.GetLayer()) != 'Mechanical 1' or not isinstance(drawing, pcbnew.PCB_SHAPE):
        continue
    start, end = drawing.GetStart(), drawing.GetEnd()
    original = {
        'uuid': drawing.m_Uuid.AsString(),
        'kind': drawing.GetShapeStr(),
        'startMm': [pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)],
        'endMm': [pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)],
    }
    if drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT and start == end:
        repairs.append({'kind': 'drop-zero-length-milling-marker', **original})
        b.Remove(drawing)
        continue
    # ST's bottom right horizontal line extends 0.030 mm past its intended
    # intersection with the 45-degree tab edge. Trim that duplicate overrun.
    if drawing.GetShape() == pcbnew.SHAPE_T_SEGMENT and original['startMm'] == [161.9711, 144.5036] and original['endMm'] == [181.5011, 144.5036]:
        drawing.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(162.0011), start.y))
        repairs.append({'kind': 'trim-overlapping-line-to-factory-intersection', 'trimMm': 0.03, **original, 'resultStartMm': [162.0011, 144.5036]})
    drawing.SetLayer(pcbnew.Edge_Cuts)
    converted.append(original)

if len(removed) != 4 or len(converted) != 29 or len(repairs) != 2:
    raise SystemExit(f'Unexpected factory layer topology: {len(removed)} rectangle edges, {len(converted)} mill edges, {len(repairs)} repairs')

origin = [113.5011, 64.0036]
mounting = []
connectors = []
footprint_counts = {}
for f in b.GetFootprints():
    footprint_counts[b.GetLayerName(f.GetLayer())] = footprint_counts.get(b.GetLayerName(f.GetLayer()), 0) + 1
    pads = []
    for p in f.Pads():
        pos = [pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)]
        record = {'number': p.GetNumber(), 'factoryMm': pos, 'localMm': [round(pos[0]-origin[0], 6), round(pos[1]-origin[1], 6)], 'drillMm': [pcbnew.ToMM(p.GetDrillSize().x), pcbnew.ToMM(p.GetDrillSize().y)]}
        pads.append(record)
        if p.GetDrillSize().x > pcbnew.FromMM(2): mounting.append(record)
    if f.GetReference().startswith('CN') or f.GetReference() in ['B1', 'B2']:
        connectors.append({'reference': f.GetReference(), 'value': f.GetValue(), 'rotationDegrees': f.GetOrientationDegrees(), 'pads': pads})

args.output.parent.mkdir(parents=True, exist_ok=True)
pcbnew.SaveBoard(str(args.output), b)
receipt = {
    'schema': 'labwired.purchased-board-mechanical-reference.v1',
    'sourceArchiveSha256': '66e2aa6a1ca58e787ea1717c0736a1853777f93a20a95e4d2e0273dc234eb52d',
    'sourceMember': 'MB1136C/Altium_Designer/MB1136.PcbDoc',
    'importedBoardSha256': hashlib.sha256(args.imported_board.read_bytes()).hexdigest(),
    'outputBoardSha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
    'kicadVersion': pcbnew.GetBuildVersion(),
    'scope': 'Common MB1136 factory mechanical reference; purchased NUCLEO-L476RG as-built variant and component heights remain separately qualified.',
    'originalEdgeCuts': 'Removed four-edge Altium bounding rectangle; not the factory milled profile.',
    'factoryMillingLayer': 'Mechanical 1',
    'removedRectangleUuids': removed,
    'millingEdges': converted,
    'topologyRepairs': repairs,
    'milledProfileExtentsMm': {'min': [113.5011,64.0036], 'max': [183.5011,146.5036], 'width': 70, 'height': 82.5},
    'localOriginFactoryMm': origin,
    'sourceBoardThicknessMm': pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()),
    'embeddedComponentModelCount': sum(len(f.Models()) for f in b.GetFootprints()),
    'footprintCountBySide': footprint_counts,
    'mountingHoles': mounting,
    'connectors': connectors,
}
args.receipt.parent.mkdir(parents=True, exist_ok=True)
args.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'output': str(args.output), 'receipt': str(args.receipt), 'millingEdges': len(converted), 'mountingHoles': len(mounting), 'thicknessMm': receipt['sourceBoardThicknessMm'], 'sha256': receipt['outputBoardSha256']}))
