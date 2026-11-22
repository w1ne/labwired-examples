"""Add documented fixed copper before routing; do not alter circuit or footprints."""
import hashlib,json,pcbnew
from pathlib import Path
root=Path(__file__).resolve().parent
source=root.parent/'pathfinder-unrouted.kicad_pcb'
b=pcbnew.LoadBoard(str(source))
assert len(list(b.GetTracks()))==0
nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
def point(p): return pcbnew.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
def track(net, points,width,layer=pcbnew.F_Cu):
 for start,end in zip(points,points[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(nets[net]);t.SetStart(point(start));t.SetEnd(point(end));t.SetWidth(round(width*1e6));t.SetLayer(layer);t.SetLocked(True);b.Add(t)
def via(net,p,diameter,drill):
 v=pcbnew.PCB_VIA(b);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(nets[net]);v.SetPosition(point(p));v.SetWidth(round(diameter*1e6));v.SetDrill(round(drill*1e6));v.SetLocked(True);b.Add(v)
escapes=[{'ref':'R2','pin':'2','path':[(19.75,187.675),(18.25,186),(12,186)]},{'ref':'R6','pin':'2','path':[(31.75,187.675),(33,185.9),(37,185.9)]},{'ref':'R10','pin':'2','path':[(22.75,192.675),(22.75,191),(16.75,191),(12,191)]},{'ref':'Q1','pin':'2','path':[(38.2,236.6375),(40,236.6375)]}]
for e in escapes:
 p=next(p for f in b.GetFootprints() if f.GetReference()==e['ref'] for p in f.Pads() if p.GetNumber()==e['pin'])
 assert p.GetNetname()=='GND' and p.GetPosition()==point(e['path'][0]),e
 track('GND',e['path'],1.8);via('GND',e['path'][-1],2.5,1.9)
track('GND',[(16.75,192.675),(16.75,191)],1.8)
track('GND',[(12,186),(12,191)],1.8,pcbnew.B_Cu)
track('+',[(38.5,189.325),(38.5,192)],1.8)
via('+',(38.5,192),2.5,1.9)
branches=[('A1','20'),('J1','1'),('U2','1'),('U1','1'),('U1','7'),('J4','4')]
bus=[]
for ref,pin in branches:
 p=next(p for f in b.GetFootprints() if f.GetReference()==ref for p in f.Pads() if p.GetNumber()==pin)
 assert p.GetNetname()=='+3V3'
 xy=(p.GetPosition().x/1e6,p.GetPosition().y/1e6)
 track('+3V3',[(10.6,xy[1]),xy],.5);bus.append({'ref':ref,'pin':pin,'point':xy})
track('+3V3',[(10.6,e['point'][1]) for e in sorted(bus,key=lambda e:e['point'][1])],.5)
for f in b.GetFootprints():
 if f.GetReference().startswith('R') and f.GetReference()[1:].isdigit():
  ref=f.Reference();ref.SetLayer(pcbnew.B_SilkS);ref.SetMirrored(True);ref.SetTextAngle(pcbnew.EDA_ANGLE(0,pcbnew.DEGREES_T));ref.SetPosition(f.GetPosition())
output=root/'protected-source.kicad_pcb';pcbnew.SaveBoard(str(output),b)
assert pcbnew.ExportSpecctraDSN(b,str(root/'native.dsn'))
receipt={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'protectedSourceSha256':hashlib.sha256(output.read_bytes()).hexdigest(),'kicadVersion':pcbnew.Version(),'groundEscapes':escapes,'groundTrackWidthMm':1.8,'groundViaDiameterMm':2.5,'groundViaDrillMm':1.9,'logicBus':{'xMm':10.6,'widthMm':.5,'branches':bus},'lockedCopper':True,'references':'R1..R14 moved to B.SilkS at original component centres; no footprint, net or pad changed.'}
(root/'protected-copper.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
