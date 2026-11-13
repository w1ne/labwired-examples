import pcbnew as pcb, json, hashlib
from pathlib import Path
from collections import Counter
root=Path('/work/output')
manifest=json.loads((root/'route-input-manifest.json').read_text())
board=pcb.LoadBoard(str(root/'esc-routing-before.kicad_pcb')); assert board
all_nets=manifest['selected_nets']
assert len(all_nets)==12
stages=[]
def save(stage):
    dst=root/f'esc-route-stage-{stage}.kicad_pcb'
    assert pcb.SaveBoard(str(dst),board)
    return {'step':stage, 'board':dst.name,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
            'segments':len([t for t in board.GetTracks() if not isinstance(t,pcb.PCB_VIA)]),
            'vias':len([t for t in board.GetTracks() if isinstance(t,pcb.PCB_VIA)])}
before=save(0);stages.append(before)
for i in range(4):
    selected=set(all_nets[i*3:(i+1)*3])
    count=0
    for seg in manifest['removed_segments']:
        if seg['net'] not in selected: continue
        tr=pcb.PCB_TRACK(board)
        tr.SetStart(pcb.VECTOR2I(pcb.FromMM(seg['x0']), pcb.FromMM(seg['y0'])))
        tr.SetEnd(pcb.VECTOR2I(pcb.FromMM(seg['x1']), pcb.FromMM(seg['y1'])))
        tr.SetWidth(pcb.FromMM(seg['width_mm']))
        tr.SetLayer(board.GetLayerID(seg['layer']))
        info=board.FindNet(seg['net'])
        assert info,seg['net']
        tr.SetNet(info)
        board.Add(tr)
        count+=1
    stage=save(i+1);stage['nets_added']=sorted(selected);stage['segments_added']=count;stages.append(stage)
expected=1198
assert stages[-1]['segments']==expected,(stages[-1],expected)
(root/'native-route-stages.json').write_text(json.dumps({'description':'Native KiCad 10 scripted route restoration using source-approved copper geometry; not an autorouter','stages':stages},indent=2)+'\n')
print(json.dumps(stages,indent=2))
