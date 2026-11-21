from pathlib import Path
import pcbnew as p,shutil,json,subprocess,sys
root=Path(__file__).parent;src=Path(sys.argv[1]) if len(sys.argv)>1 else root/'manual_finish/board.kicad_pcb';out=Path(sys.argv[2]) if len(sys.argv)>2 else root/'i2c_escape/board.kicad_pcb';out.parent.mkdir(exist_ok=True,parents=True)
b=p.LoadBoard(str(src));old=list(b.GetTracks());m=p.ToMM;P=lambda a:p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]));added=[];removed=[];changed=[]
def tr(net,pts,layer=p.F_Cu):
 for a,c in zip(pts[:-1],pts[1:]):
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetStart(P(a));t.SetEnd(P(c));b.Add(t);added.append(t)
def via(net,xy):
 v=p.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(P(xy));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(v);added.append(v)
for t in old:
 net=t.GetNetname();a=t.GetStart();c=t.GetEnd();x1,y1,x2,y2=map(m,[a.x,a.y,c.x,c.y]);isvia=isinstance(t,p.PCB_VIA);remove=False
 if net=='I2C_SDA' and not isvia and t.GetLayer()==p.F_Cu and min(x1,x2)>=48.88329 and max(x1,x2)<51 and max(y1,y2)>=49.19:remove=True
 if net=='BOOT0' and not isvia:
  if t.GetLayer()==p.F_Cu and min(x1,x2)>=48.59169 and max(y1,y2)<50.563:remove=True
  if t.GetLayer()==p.B_Cu:remove=True
 if net=='Z_DIR':
  if isvia and abs(x1-48.85)<1e-6 and abs(y1-49.7)<1e-6:t.SetPosition(P((48.59,49.63)));changed.append({'uuid':t.m_Uuid.AsString(),'via_from':[x1,y1],'to':[48.59,49.63]})
  if not isvia and t.GetLayer()==p.F_Cu and max(y1,y2)>49 and max(x1,x2)<50:remove=True
  if not isvia and t.GetLayer()==p.In2_Cu:
   if abs(x1-48.85)<1e-6 and abs(x2-48.85)<1e-6 and min(y1,y2)>49:remove=True
   elif a==P((48.85,49.5979)):t.SetStart(P((48.59,49.63)));changed.append({'uuid':t.m_Uuid.AsString(),'start_from':[x1,y1],'to':[48.59,49.63]})
   elif c==P((48.85,49.5979)):t.SetEnd(P((48.59,49.63)));changed.append({'uuid':t.m_Uuid.AsString(),'end_from':[x2,y2],'to':[48.59,49.63]})
 if remove:b.Remove(t);removed.append(t.m_Uuid.AsString())
tr('Z_DIR',[(48.75,50.5625),(48.75,49.9),(48.65,49.8),(48.59,49.63)])
tr('BOOT0',[(49.25,50.5625),(49.25,50.05),(49.24,50.04),(49.24,49.5),(48.5917,48.8102)])
tr('BOOT0',[(48.5917,48.8102),(47.8,48.8102),(47.8,56.8),(48.4,57.4),(48.4,59.5),(47.8,60.1),(47.8,65.7778),(47.9706,65.9484)],p.B_Cu)
tr('I2C_SDA',[(49.75,50.5625),(49.75,50.05),(49.65,49.95),(49.65,49.1904),(48.8833,48.2506)])
tr('I2C_SCL',[(50.25,50.5625),(50.25,49.3),(50.05,49.1),(50.0,48.95),(50.0,48.15),(49.2,47.55)]);via('I2C_SCL',(49.2,47.55))
tr('I2C_SCL',[(49.2,47.55),(49.2,39.4),(34.5,39.4),(34.5,73.0513)],p.B_Cu)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b);shutil.copyfile(src.with_suffix('.kicad_pro'),out.with_suffix('.kicad_pro'))
(out.parent/'i2c-escape-delta.json').write_text(json.dumps({'removed':removed,'changed':changed,'added':[t.m_Uuid.AsString() for t in added]},indent=2))
subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',str(out.with_suffix('.drc.json')),str(out)],capture_output=True,text=True,timeout=120)
j=json.loads(out.with_suffix('.drc.json').read_text());print('DRC',len(j['violations']),len(j['unconnected_items']))
for v in j['violations']+j['unconnected_items']:print(v['type'],v['description'],[(x['description'],x['pos'],x['uuid']) for x in v['items']])
