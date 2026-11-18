#!/usr/bin/python3
"""Remove only disconnected track stubs named by the preceding KiCad DRC."""
from pathlib import Path
import hashlib, json, sys
import pcbnew as k
root=Path(__file__).resolve().parents[1]
path=root/'electronics/doom-carrier.kicad_pcb'
raw=path.read_bytes()
if len(sys.argv)!=2 or hashlib.sha256(raw).hexdigest()!=sys.argv[1]:
    raise SystemExit('Pass the exact SHA-256 of the board used by the DRC report.')
drc=json.loads((root/'validation/drc.json').read_text())
if drc['unconnected_items'] or drc['schematic_parity'] or any(v['type']!='track_dangling' for v in drc['violations']):
    raise SystemExit('Unexpected findings require review.')
board=k.LoadBoard(str(path)); tracks={t.m_Uuid.AsString():t for t in board.GetTracks()}
removed=[]
for finding in drc['violations']:
    if len(finding['items'])!=1: raise SystemExit('Ambiguous track finding.')
    item=finding['items'][0];track=tracks[item['uuid']]
    if isinstance(track,k.PCB_VIA): raise SystemExit('Expected a track, not a via.')
    removed.append({'uuid':item['uuid'],'net':track.GetNetname(),'layer':track.GetLayerName(),'length_mm':k.ToMM(track.GetLength())})
    board.Remove(track)
(root/'validation/drc-after-via-cleanup.json').write_text(json.dumps(drc,indent=2)+'\n')
board.BuildConnectivity();k.SaveBoard(str(path),board)
(root/'validation/track-cleanup.json').write_text(json.dumps({'input_sha256':sys.argv[1],'removed_drc_named_stubs':removed,'output_before_refill_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n')
print('Removed',len(removed),'DRC-named disconnected stubs.')
