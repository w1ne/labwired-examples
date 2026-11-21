#!/usr/bin/python3
"""Tie STM32 VDDA to VDD and add the specified local 100 nF decoupler."""
from pathlib import Path
import pcbnew as p,sys,json,shutil,subprocess,hashlib
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(src));oldnet='+3V3A';newnet=b.FindNet('+3V3');tracks=list(b.GetTracks());added=[]
mm=p.ToMM;P=lambda xy:p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
report={'reason':'STM32F411CE requires VDDA connected to VDD and a 100nF plus1uF decoupling pair. C8 retains1uF; C10 adds100nF.','source_url':'https://www.st.com/resource/en/datasheet/stm32f411ce.pdf','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pad_changes':[],'retagged_copper':[],'new_reference':'C10','new_component_value':'100n','new_component_function':'VDDA high-frequency decoupling','retained_bulk_capacitor':'C8 1u'}
for f in b.GetFootprints():
 for q in f.Pads():
  if q.GetNetname()==oldnet:report['pad_changes'].append({'reference':f.GetReference(),'pad':q.GetNumber(),'from':oldnet,'to':'+3V3'});q.SetNet(newnet)
assert {(q['reference'],q['pad']) for q in report['pad_changes']}=={('U1','9'),('C8','1'),('J33','1'),('J34','1')}
for t in tracks:
 if t.GetNetname()==oldnet:report['retagged_copper'].append(t.m_Uuid.AsString());t.SetNet(newnet)
assert all(z.GetNetname()!=oldnet for z in b.Zones())
assert not any(f.GetReference()=='C10' for f in b.GetFootprints())
lib=Path(sys.argv[sys.argv.index('--footprint-lib')+1]) if '--footprint-lib' in sys.argv else Path('/usr/share/kicad/footprints/Capacitor_SMD.pretty');name='C_0603_1608Metric';c=p.FootprintLoad(str(lib),name);assert c;c.SetReference('C10');c.SetValue('100n');c.SetPosition(P((42.9,56.0)));c.SetOrientationDegrees(180);c.Reference().SetVisible(False);c.Value().SetVisible(False);b.Add(c)
for q in c.Pads():q.SetNet(newnet if q.GetNumber()=='1' else b.FindNet('GND'))
c.SetField('Description','100 nF ceramic VDDA decoupler; paired with C8=1 uF per STM32F411CE datasheet power-supply scheme.');c.GetField('Description').SetVisible(False)
report['footprint_source']={'library':str(lib/(name+'.kicad_mod')),'sha256':hashlib.sha256((lib/(name+'.kicad_mod')).read_bytes()).hexdigest(),'footprint_id':c.GetFPIDAsString(),'position_mm':[42.9,56.0],'orientation_deg':c.GetOrientationDegrees(),'pads':[{'number':q.GetNumber(),'net':q.GetNetname(),'xy_mm':[mm(q.GetPosition().x),mm(q.GetPosition().y)]} for q in c.Pads()]}
def track(net,pts,layer=p.F_Cu):
 for a,z in zip(pts[:-1],pts[1:]):
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetStart(P(a));t.SetEnd(P(z));b.Add(t);added.append(t)
def via(net,xy):
 t=p.PCB_VIA(b);t.SetNet(b.FindNet(net));t.SetPosition(P(xy));t.SetWidth(p.FromMM(.5));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(t);added.append(t)
track('+3V3',[(43.675,56.0),(44.9907,55.1021)])
track('GND',[(42.125,56.0),(42.125,54.6997)])
track('+3V3',[(43.675,56.0),(43.6,56.075),(43.6,56.8)]);via('+3V3',(43.6,56.8))
track('+3V3',[(43.6,56.8),(41.8,56.8),(41.8,40.3303),(43.6678,40.3303)],p.B_Cu)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b);shutil.copy2(src.with_suffix('.kicad_pro'),out.with_suffix('.kicad_pro'))
report['added_copper']=[t.m_Uuid.AsString() for t in added];report['output_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();out.with_suffix('.vdda-delta.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if '--drc' in sys.argv:
 d=out.with_suffix('.drc.json');subprocess.run(['kicad-cli','pcb','drc','--format','json','--output',str(d),str(out)],capture_output=True,text=True,timeout=120);j=json.loads(d.read_text());print('DRC',len(j['violations']),len(j['unconnected_items']),flush=True)
 for v in j['violations']+j['unconnected_items']:print(v['type'],v['description'],[(i['description'],i['pos'],i['uuid']) for i in v['items']],flush=True)
