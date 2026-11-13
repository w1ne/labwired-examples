import pcbnew as pcb, json, hashlib
from collections import Counter
from pathlib import Path
src=Path('/source/4in1.kicad_pcb')
out=Path('/work/output')
b=pcb.LoadBoard(str(src)); assert b, 'KiCad 10 source failed to parse'
nets=['/ESC1/AH','/ESC1/GHA','/ESC1/GLA',
      '/ESC2/BH','/ESC2/GHC','/ESC2/GLC',
      '/ESC3/AH','/ESC3/GHA','/ESC3/GLA',
      '/ESC4/BH','/ESC4/GHC','/ESC4/GLB']
counts=Counter(); removed=[]
for t in list(b.GetTracks()):
    if t.GetNetname() in nets:
        counts[t.GetNetname()]+=1
        assert not isinstance(t,pcb.PCB_VIA),'unexpected via in selected net'
        a=t.GetStart();z=t.GetEnd()
        removed.append(dict(net=t.GetNetname(),x0=pcb.ToMM(a.x),y0=pcb.ToMM(a.y),
                            x1=pcb.ToMM(z.x),y1=pcb.ToMM(z.y),layer=t.GetLayerName(),
                            width_mm=pcb.ToMM(t.GetWidth())))
        b.Remove(t)
assert set(counts)==set(nets),(counts,nets)
assert sum(counts.values())>=27,sum(counts.values())
assert pcb.SaveBoard(str(out/'esc-routing-before.kicad_pcb'),b)
assert pcb.ExportSpecctraDSN(b,str(out/'esc-routing-before.dsn'))
manifest={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
          'design':'OpenESC 4-in-1 six-layer real board; routing study on a copy',
          'selected_nets':nets,'removed_source_segments_count':len(removed),
          'removed_segments_by_net':dict(counts),'removed_segments':removed}
(out/'route-input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('INPUT READY',sum(counts.values()),'segments removed from',len(nets),'nets')
print('DSN', (out/'esc-routing-before.dsn').stat().st_size)
