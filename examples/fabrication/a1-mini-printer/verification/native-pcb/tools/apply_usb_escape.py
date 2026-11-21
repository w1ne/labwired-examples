#!/usr/bin/env python3
from pathlib import Path
import pcbnew as p,sys,json,hashlib,shutil,subprocess
src=Path(sys.argv[1]);dst=Path(sys.argv[2]);dst.parent.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(src));old=list(b.GetTracks());mm=p.ToMM;P=lambda a:p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]));delta={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'removed':[],'changed':[],'added':[]}
def rec(t):
 return {'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'layer':t.GetLayerName(),'start':[mm(t.GetStart().x),mm(t.GetStart().y)],'end':[mm(t.GetEnd().x),mm(t.GetEnd().y)]}
def edge(net,aa,cc,layer=p.F_Cu):
 r=[t for t in old if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net and t.GetLayer()==layer and ((t.GetStart()==P(aa) and t.GetEnd()==P(cc)) or (t.GetStart()==P(cc) and t.GetEnd()==P(aa)))]
 assert len(r)==1,(net,aa,cc,layer,len(r));return r[0]
def rm(net,pts,layer=p.F_Cu):
 for aa,cc in zip(pts[:-1],pts[1:]):
  t=edge(net,aa,cc,layer);delta['removed'].append(rec(t));b.Remove(t)
def add(net,pts,layer=p.F_Cu):
 for aa,cc in zip(pts[:-1],pts[1:]):
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetStart(P(aa));t.SetEnd(P(cc));b.Add(t);delta['added'].append(rec(t))
def findvia(net,xy):
 v=[t for t in old if isinstance(t,p.PCB_VIA) and t.GetNetname()==net and t.GetPosition()==P(xy)];assert len(v)==1,(net,xy,len(v));return v[0]
template=findvia('USB_DM',(54.5989,53.2627))
def via(net,xy):
 v=p.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(P(xy));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetFrontTentingMode(template.GetFrontTentingMode());v.SetBackTentingMode(template.GetBackTentingMode());b.Add(v);delta['added'].append(rec(v))
def movevia(net,xy,new):
 v=findvia(net,xy);r=rec(v);v.SetPosition(P(new));r['new_position']=list(new);delta['changed'].append(r)
# Move USB DM's local via outward; retain the original lower diagonal.
rm('USB_DM',[(53.4375,53.25),(54.5862,53.25),(54.5989,53.2627)])
rm('USB_DM',[(54.5989,53.2627),(54.5989,55.2254),(56.1042,56.7307)],p.In1_Cu)
movevia('USB_DM',(54.5989,53.2627),(54.9,53.25))
add('USB_DM',[(53.4375,53.25),(54.9,53.25)])
add('USB_DM',[(54.9,53.25),(54.9,55.5265),(56.1042,56.7307)],p.In1_Cu)
# Give USER_AUX a short backside bypass and remove its congested old via.
rm('USER_AUX',[(53.4375,53.75),(53.5121,53.6754),(54.1133,53.6754),(54.2931,53.8552),(55.2997,53.8552),(55.3724,53.7825)])
rm('USER_AUX',[(55.3724,53.7825),(57.0692,55.4793),(57.0692,56.9047)],p.In1_Cu)
v=findvia('USER_AUX',(55.3724,53.7825));delta['removed'].append(rec(v));b.Remove(v)
via('USER_AUX',(54.2,53.802));via('USER_AUX',(56.8,56.708))
add('USER_AUX',[(53.4375,53.75),(54.2,53.802)])
add('USER_AUX',[(54.2,53.802),(55.523,55.125),(56.8,55.125),(56.8,56.708)],p.B_Cu)
add('USER_AUX',[(56.8,56.708),(57.0692,56.9047)],p.In1_Cu)
# The SWCLK backside track shifts left; its top via and lower path stay fixed.
rm('SWCLK',[(53.8086,50.0779),(53.8086,54.4351),(55.5723,56.1988)],p.B_Cu)
add('SWCLK',[(53.8086,50.0779),(53.5,50.3865),(53.5,54.1265),(55.5723,56.1988)],p.B_Cu)
# Spread the two lower neighboring fanouts while retaining their pad positions.
rm('END_X',[(53.4375,54.75),(54.05,54.75),(54.3,54.6),(55.3,54.6)])
rm('END_X',[(55.3,54.6),(67.7251,54.6)],p.In2_Cu)
movevia('END_X',(55.3,54.6),(55.95,54.55))
add('END_X',[(53.4375,54.75),(53.9,54.75),(54.02,54.845),(54.8,54.845),(55.095,54.55),(55.95,54.55)])
add('END_X',[(55.95,54.55),(56.0,54.6),(67.7251,54.6)],p.In2_Cu)
rm('FAN1_CMD',[(53.4375,55.25),(54.4515,55.25),(54.549,55.1525),(56.5795,55.1525),(58.166,56.739)])
add('FAN1_CMD',[(53.4375,55.25),(55.5,55.25),(55.5975,55.1525),(56.5795,55.1525),(58.166,56.739)])
# USB sense uses a legal via outside the fine-pitch pad row.
add('USB_VBUS_SENSE',[(53.4375,54.25),(53.6,54.25),(53.675,54.32),(53.96,54.32),(54.06,54.37),(54.7,54.37),(55.07,54.0),(55.5,54.0)])
via('USB_VBUS_SENSE',(55.5,54.0))
add('USB_VBUS_SENSE',[(55.5,54.0),(62,54.0),(62,72),(48,72),(48,68.85)],p.B_Cu)
via('USB_VBUS_SENSE',(48,68.85));via('USB_VBUS_SENSE',(43,68.85))
add('USB_VBUS_SENSE',[(48,68.85),(43,68.85)])
add('USB_VBUS_SENSE',[(43,68.85),(42,68.85),(40,70.85),(40,80),(38.7186,81.2814),(34.8936,81.2814)],p.B_Cu)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);shutil.copy2(src.with_suffix('.kicad_pro'),dst.with_suffix('.kicad_pro'));delta['output_sha256']=hashlib.sha256(dst.read_bytes()).hexdigest();dst.with_suffix('.delta.json').write_text(json.dumps(delta,indent=2))
drc=dst.with_suffix('.drc.json');subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',str(drc),str(dst)],capture_output=True,text=True,timeout=120)
d=json.loads(drc.read_text());print('DRC',len(d['violations']),len(d['unconnected_items']))
for v in d['violations']+d['unconnected_items']:print(v['type'],v['description'],[(i['description'],i['pos'],i['uuid']) for i in v['items']])

