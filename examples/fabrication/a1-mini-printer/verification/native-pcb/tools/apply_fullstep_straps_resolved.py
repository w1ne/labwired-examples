from pathlib import Path
import pcbnew as p,sys,json,shutil,subprocess
src=Path(sys.argv[1]);dest=Path(sys.argv[2]);dest.parent.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(src));tracks=list(b.GetTracks());mm=p.ToMM;P=lambda xy:p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]));report={'reason':'Match saved A1 full-step firmware: MS1/MS2/MS3=GND; retain VDD/RESET/SLEEP=3V3.','pad_changes':[],'retagged_tracks':[],'removed_tracks':[]};added=[]
def add(net,pts):
 for a,c in zip(pts[:-1],pts[1:]):
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.2));t.SetStart(P(a));t.SetEnd(P(c));b.Add(t);added.append(t)
for f in b.GetFootprints():
 if f.GetReference() not in ['U10','U11','U12','U13']:continue
 cx=mm(f.GetPosition().x);cy=mm(f.GetPosition().y);row=cy+2.3625;pads={v.GetNumber():v for v in f.Pads() if v.GetNumber()}
 for num in ['9','10','11']:
  assert pads[num].GetNetname()=='+3V3';pads[num].SetNet(b.FindNet('GND'));report['pad_changes'].append({'reference':f.GetReference(),'pad':num,'from':'+3V3','to':'GND'})
 for num in ['12','14','15']:assert pads[num].GetNetname()=='+3V3'
 count=0
 for t in tracks:
  if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu or t.GetNetname()!='+3V3':continue
  a=t.GetStart();c=t.GetEnd();x1,y1,x2,y2=map(mm,[a.x,a.y,c.x,c.y])
  if abs(y1-row)<1e-6 and abs(y2-row)<1e-6 and min(x1,x2)>=cx-1.000001 and max(x1,x2)<=cx+.500001:
   if max(x1,x2)>cx+.01:b.Remove(t);report['removed_tracks'].append(t.m_Uuid.AsString())
   else:t.SetNet(b.FindNet('GND'));report['retagged_tracks'].append(t.m_Uuid.AsString())
   count+=1
 assert count==3,(f.GetReference(),count)
 add('GND',[(cx,row),(cx,cy+1.5)])
# U12 was fed through old MS1. Move that supply leg to RESET pad12.
remove_pairs=[((60.7,23.3625),(60.7,23.8655)),((60.7,23.8655),(58.8683,25.6972))]
for aa,cc in remove_pairs:
 found=[]
 for t in tracks:
  if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu or t.GetNetname()!='+3V3':continue
  if (t.GetStart()==P(aa) and t.GetEnd()==P(cc)) or (t.GetEnd()==P(aa) and t.GetStart()==P(cc)):found.append(t)
 assert len(found)==1,(aa,cc,len(found));b.Remove(found[0]);report['removed_tracks'].append(found[0].m_Uuid.AsString())
add('+3V3',[(62.2,23.3625),(62.2,24.0),(60.5028,25.6972),(58.8683,25.6972)])

# Preserve 0.20 mm track/clearance rules while separating the three U10 fanouts.
def remove_edge(net,a,c):
 found=[t for t in tracks if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu and t.GetNetname()==net and ((t.GetStart()==P(a) and t.GetEnd()==P(c)) or (t.GetStart()==P(c) and t.GetEnd()==P(a)))]
 assert len(found)==1,(net,a,c,len(found))
 b.Remove(found[0]);report['removed_tracks'].append(found[0].m_Uuid.AsString())
def replace_polyline(net,old,new):
 for a,c in zip(old[:-1],old[1:]):remove_edge(net,a,c)
 add(net,new)
replace_polyline('+3V3',[(15.5,23.3625),(15.5,23.8246),(14.4759,24.8487),(14.0263,24.8487)],[(15.5,23.3625),(15.5,23.975),(14.6263,24.8487),(14.0263,24.8487)])
replace_polyline('X_ROSC',[(16.0,23.3625),(16.0,23.895),(14.4446,25.4504),(14.2754,25.4504)],[(16.0,23.3625),(16.0,24.075),(14.6246,25.4504),(14.2754,25.4504)])
replace_polyline('+3V3',[(16.5,23.3625),(16.5,24.0945),(14.5104,26.0841),(13.6732,26.0841)],[(16.5,23.3625),(16.5,24.2),(14.6159,26.0841),(13.6732,26.0841)])
# Move the U12 ROSC diagonal outward so RESET reaches the original supply feed.
replace_polyline('Z_ROSC',[(62.7,23.3625),(62.7,23.8818),(59.4407,27.1411)],[(62.7,23.3625),(62.7,24.15),(59.7089,27.1411),(59.4407,27.1411)])

p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dest),b);shutil.copyfile(src.with_suffix('.kicad_pro'),dest.with_suffix('.kicad_pro'))
(dest.parent/'fullstep-straps-delta.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if '--drc' in sys.argv:
 d=dest.with_suffix('.drc.json');r=subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',str(d),str(dest)],capture_output=True,text=True,timeout=90);j=json.loads(d.read_text());print('DRC',len(j['violations']),len(j['unconnected_items']))
 for a in j['violations']:print(a['description'],[(i['description'],i['pos'],i['uuid']) for i in a['items']])
