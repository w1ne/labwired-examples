#!/usr/bin/env python3
"""Restore fan series gate resistors and LED polarity in the A1 native PCB.
Changes only the authorized six fan gate pad nets, four LED pad nets and two
LED rotations. Existing copper endpoints retain their nets after LED rotation.
New fan traces remain0.20mm; new vias are0.60/0.30mm with existing tenting modes.
"""
from pathlib import Path
import argparse,json,hashlib,shutil,subprocess
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--drc',action='store_true');a=ap.parse_args()
src=Path(a.input).resolve();dst=Path(a.output).resolve();assert src!=dst
source_sha=hashlib.sha256(src.read_bytes()).hexdigest();b=p.LoadBoard(str(src));fps={f.GetReference():f for f in b.GetFootprints()};tracks=list(b.GetTracks());mm=p.ToMM
P=lambda xy:p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
report={'reason':'Restore the declared100ohm series gate resistors and source-backed LED cathode/anode convention.','source':str(src),'source_sha256':source_sha,'pad_changes':[],'removed_tracks':[],'retagged_tracks':[],'added_tracks':[],'added_vias':[],'footprint_rotations':[],'sources':['https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf','https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/master/LED_SMD.pretty/LED_0603_1608Metric.kicad_mod']}
def pads(ref):return {v.GetNumber():v for v in fps[ref].Pads() if v.GetNumber()}
def change(ref,num,old,new):
 q=pads(ref)[num];assert q.GetNetname()==old,(ref,num,q.GetNetname(),old);q.SetNet(b.FindNet(new));report['pad_changes'].append({'ref':ref,'pad':num,'from':old,'to':new})
def track_record(t):
 return {'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'layer':t.GetLayerName(),'start_mm':[mm(t.GetStart().x),mm(t.GetStart().y)],'end_mm':[mm(t.GetEnd().x),mm(t.GetEnd().y)],'width_mm':mm(t.GetWidth())}
def edge(net,a,c):
 found=[t for t in tracks if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net and t.GetLayer()==p.F_Cu and ((t.GetStart()==P(a) and t.GetEnd()==P(c)) or (t.GetStart()==P(c) and t.GetEnd()==P(a)))]
 assert len(found)==1,(net,a,c,len(found));return found[0]
def remove(net,a,c):
 t=edge(net,a,c);report['removed_tracks'].append(track_record(t));b.Remove(t)
def retag(old,new,a,c):
 t=edge(old,a,c);r=track_record(t);t.SetNet(b.FindNet(new));r['new_net']=new;report['retagged_tracks'].append(r)
def add(net,pts,layer=p.F_Cu):
 for a,c in zip(pts[:-1],pts[1:]):
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetStart(P(a));t.SetEnd(P(c));b.Add(t);report['added_tracks'].append(track_record(t))
template=next(v for v in tracks if isinstance(v,p.PCB_VIA) and v.GetNetname()=='FAN2_GATE')
def via(net,xy):
 v=p.PCB_VIA(b);v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetPosition(P(xy));v.SetNet(b.FindNet(net));v.SetFrontTentingMode(template.GetFrontTentingMode());v.SetBackTentingMode(template.GetBackTentingMode());b.Add(v);report['added_vias'].append({'net':net,'xy_mm':list(xy),'diameter_mm':.6,'drill_mm':.3,'tenting':'copied from existing FAN2_GATE through via'})
for n,r,q,pd in [(1,'R126','Q4','R128'),(2,'R127','Q5','R129')]:
 old=f'FAN{n}_GATE';new=old+'_Q';assert b.FindNet(new) is None or b.FindNet(new).GetNetCode()<0
 b.Add(p.NETINFO_ITEM(b,new))
 assert fps[q].GetValue()=='AO3400A'
 qp=pads(q);assert qp['1'].GetNetname()==old and qp['2'].GetNetname()=='GND' and qp['3'].GetNetname()==f'FAN{n}_SW'
 for ref,num in [(r,'2'),(q,'1'),(pd,'1')]:change(ref,num,old,new)
 assert pads(r)['1'].GetNetname()==old
 dx=(n-1)*8
 # Remove the copper short across the100ohm resistor and old pull-down branch.
 remove(old,(43.825+dx,80.5),(42.175+dx,80.5))
 remove(old,(42.175+dx,80.5),(42.175+dx,83.5))
 retag(old,new,(43.825+dx,80.5),(45.5125+dx,80.5))
 retag(old,new,(45.5125+dx,80.5),(46.0625+dx,81.05))
 add(new,[(43.825+dx,80.5),(43.825+dx,81.3),(42.175+dx,82.95),(42.175+dx,83.5)])
 via(old,(42.175+dx,79.25));add(old,[(42.175+dx,79.25),(42.175+dx,80.5)])
# FAN1 long feed now terminates on R126.1 through a short backside jog.
remove('FAN1_GATE',(46.0625,81.05),(50.875,76.2375))
add('FAN1_GATE',[(50.875,76.2375),(47.1125,80.0)])
via('FAN1_GATE',(47.1125,80.0))
add('FAN1_GATE',[(47.1125,80.0),(46.3625,79.25),(42.175,79.25)],p.B_Cu)
# Reuse the existing FAN2 feed via; disconnect its direct copper path to Q5.G.
remove('FAN2_GATE',(55.3374,80.9911),(54.1214,80.9911))
remove('FAN2_GATE',(54.1214,80.9911),(54.0625,81.05))
add('FAN2_GATE',[(55.3374,80.9911),(53.5963,79.25),(50.175,79.25)],p.B_Cu)
# LED footprints use pad1=K and pad2=A. Swapping nets plus180-degree rotation
# preserves each absolute copper endpoint while correcting the package polarity.
for ref,old1,old2 in [('D10','LED_PWR_A','GND'),('D11','LED_FAULT_A','USER_AUX')]:
 f=fps[ref];qs=pads(ref);assert f.GetFPIDAsString().endswith('LED_0603_1608Metric')
 before=sorted((v.GetPosition().x,v.GetPosition().y,v.GetNetname()) for v in qs.values())
 change(ref,'1',old1,old2);change(ref,'2',old2,old1)
 angle=f.GetOrientationDegrees();f.SetOrientationDegrees(angle+180)
 after=sorted((v.GetPosition().x,v.GetPosition().y,v.GetNetname()) for v in qs.values())
 assert before==after,(ref,before,after)
 report['footprint_rotations'].append({'ref':ref,'before_deg':angle,'after_deg':f.GetOrientationDegrees(),'absolute_copper_net_positions_unchanged':True})
assert len(report['pad_changes'])==10
assert pads('U30')['8'].GetNetname()=='FAN1_GATE' and pads('U30')['11'].GetNetname()=='FAN2_GATE'
p.ZONE_FILLER(b).Fill(b.Zones());dst.parent.mkdir(parents=True,exist_ok=True);p.SaveBoard(str(dst),b);shutil.copy2(src.with_suffix('.kicad_pro'),dst.with_suffix('.kicad_pro'))
assert hashlib.sha256(src.read_bytes()).hexdigest()==source_sha,'Input changed during patch'
report['output']=str(dst);report['output_sha256']=hashlib.sha256(dst.read_bytes()).hexdigest()
dst.with_suffix('.fan-led-delta.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if a.drc:
 path=dst.with_suffix('.drc.json');subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',str(path),str(dst)],capture_output=True,text=True,timeout=90,check=True);j=json.loads(path.read_text());print('DRC',len(j['violations']),len(j['unconnected_items']))
 for v in j['violations']:print(v['description'],[(i['description'],i['pos'],i['uuid']) for i in v['items']])

