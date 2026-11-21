from pathlib import Path
import pcbnew as p,shutil,json,subprocess,sys
src=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();D=out.parent;D.mkdir(exist_ok=True,parents=True)
b=p.LoadBoard(str(src));old=list(b.GetTracks());m=p.ToMM;P=lambda a:p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]));added=[];removed=[]
def tr(net,pts,layer=p.F_Cu):
 for a,c in zip(pts[:-1],pts[1:]):
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetStart(P(a));t.SetEnd(P(c));b.Add(t);added.append(t)
def via(net,xy):
 v=p.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(P(xy));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(v);added.append(v)
for t in old:
 net=t.GetNetname();a=t.GetStart();c=t.GetEnd();x1,y1,x2,y2=map(m,[a.x,a.y,c.x,c.y]);isvia=isinstance(t,p.PCB_VIA)
 if net=='+3V3' and isvia and abs(x1-45.1)<1e-6 and abs(y1-50.7)<1e-6:b.Remove(t);removed.append(t);continue
 if net=='E_STEP' and not isvia and t.GetLayer()==p.F_Cu:
  aa=[x1,y1];cc=[x2,y2];change=False
  for z in [aa,cc]:
   if any(abs(z[0]-x)<1e-6 for x in [88.1063,88.2252]):z[0]-=.02;change=True
  if change:t.SetStart(P(aa));t.SetEnd(P(cc))
tr('END_Z',[(45,52.4),(44.91,52.31),(43.4,52.31),(43.4,54.5),(44.2,55.3),(44.2,75.1),(87,75.1),(87,67),(96,67)],p.B_Cu)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b);shutil.copyfile(src.with_suffix('.kicad_pro'),out.with_suffix('.kicad_pro'))
subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',str(D/'board-drc.json'),str(out)],capture_output=True,text=True,timeout=120)
j=json.loads((D/'board-drc.json').read_text());print('DRC',len(j['violations']),len(j['unconnected_items']))
for v in j['violations']+j['unconnected_items']:print(v['type'],v['description'],[(x['description'],x['pos'],x['uuid']) for x in v['items']])
