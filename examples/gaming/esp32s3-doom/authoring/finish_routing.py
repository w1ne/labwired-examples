#!/usr/bin/python3
"""Finish a native router result without changing pad identity or placement.

Remove only the unused vias named by the independent KiCad DRC receipt.
Add connected GND pours on both copper layers, respecting native rule areas.
Run KiCad DRC with schematic parity after this script.
"""
from pathlib import Path
import hashlib, json
import pcbnew as k

root = Path(__file__).resolve().parents[1]
board_path = root/'electronics/doom-carrier.kicad_pcb'
raw = board_path.read_bytes()
receipt = json.loads((root/'validation/native-drc-initial.json').read_text())
expected = receipt['pcb_ref'].split(':',1)[1]
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit('Input is not the exact independently checked router output.')
board = k.LoadBoard(str(board_path))

def identity(b):
    return sorted((f.GetReference(), f.GetFPIDAsString(),
        f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees(),
        tuple(sorted((p.GetNumber(), p.GetNetname(), p.GetPosition().x,
          p.GetPosition().y, p.GetDrillSize().x, p.GetDrillSize().y) for p in f.Pads())))
        for f in b.GetFootprints())

before = identity(board)
findings = receipt['drc']['review']['findings']
if any(f['rule'] != 'via_dangling' for f in findings):
    raise SystemExit('Unexpected DRC findings require review.')
tracks = {t.m_Uuid.AsString():t for t in board.GetTracks()}
removed = []
for finding in findings:
    anchor = finding['anchors'][0]
    via = tracks[anchor['uuid']]
    if not isinstance(via,k.PCB_VIA) or via.GetNetname() != anchor['net']:
        raise SystemExit('DRC identity no longer matches the named via.')
    board.Remove(via)
    removed.append({'uuid':anchor['uuid'],'net':anchor['net'],
                    'x':anchor['x'],'y':anchor['y']})

gnd = board.FindNet('/GND')
for layer,name in [(k.F_Cu,'Front connected ground'),(k.B_Cu,'Back connected ground')]:
    zone = k.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(gnd)
    zone.SetZoneName(name)
    zone.SetLocalClearance(k.FromMM(.2))
    zone.SetThermalReliefGap(k.FromMM(.3))
    zone.SetThermalReliefSpokeWidth(k.FromMM(.35))
    zone.SetPadConnection(k.ZONE_CONNECTION_THERMAL)
    zone.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
    outline = zone.Outline()
    outline.NewOutline()
    for x,y in [(.5,.5),(79.5,.5),(79.5,99.5),(.5,99.5)]:
        outline.Append(round(x*1e6),round(y*1e6))
    board.Add(zone)

# The dense connector escape blocks the default diagonal J3.26 thermal. Rotate
# only this GND pad's spokes; the required two-spoke rule stays unchanged.
header = next(f for f in board.GetFootprints() if f.GetReference() == 'J3')
next(p for p in header.Pads() if p.GetNumber() == '26').SetThermalSpokeAngle(k.EDA_ANGLE(0,k.DEGREES_T))

assert identity(board) == before
original = k.LoadBoard(str(root/'electronics/doom-carrier-unrouted.kicad_pcb'))
assert identity(original) == before, 'Routing changed a footprint or pad.'
board.BuildConnectivity()
k.SaveBoard(str(board_path),board)
(root/'validation/routing-cleanup.json').write_text(json.dumps({
    'input_sha256':expected, 'removed_drc_named_unused_vias':removed,
    'ground_pours':['F.Cu','B.Cu'], 'unconnected_copper_islands':'removed',
    'thermal_spoke_angle_degrees':{'J3.26':0},
    'footprints_unchanged':len(before), 'pad_identity_and_geometry_preserved':True,
    'output_before_zone_refill_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),
    'acceptance':'Independent KiCad DRC with zone refill and schematic parity is required.'
},indent=2)+'\n')
print('Removed',len(removed),'unused vias; retained',len(before),'exact footprints.')
