#!/usr/bin/python3
"""Audit the exact A1 native-board delta against the accepted 3-open baseline."""
import argparse,csv,hashlib,json
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('baseline');ap.add_argument('candidate');ap.add_argument('--evidence',required=True);ap.add_argument('--require-clean',action='store_true');args=ap.parse_args()
base=Path(args.baseline);dst=Path(args.candidate);ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(base)=='19e6b415ad41bd9c068ce39610e7412091724cf7323162625783c7bed13c0142','Wrong accepted baseline'
def snapshot(path):
 b=p.LoadBoard(str(path));out={};pads={}
 for f in b.GetFootprints():
  ps=[]
  for v in f.Pads():
   pos=v.GetPosition();size=v.GetSize();drill=v.GetDrillSize()
   rec={'uuid':v.m_Uuid.AsString(),'ref':f.GetReference(),'pad':v.GetNumber(),'net':v.GetNetname(),'xy_nm':[pos.x,pos.y],'size_nm':[size.x,size.y],'drill_nm':[drill.x,drill.y],'shape':int(v.GetShape()),'layers':v.GetLayerSet().FmtHex()}
   ps.append(rec);pads[rec['uuid']]=rec
  pos=f.GetPosition();out[f.GetReference()]={'uuid':f.m_Uuid.AsString(),'value':f.GetValue(),'footprint':f.GetFPIDAsString(),'xy_nm':[pos.x,pos.y],'orientation_deg':f.GetOrientationDegrees(),'pads':sorted(ps,key=lambda x:x['uuid']),'fields':{v.GetName():v.GetText() for v in f.GetFields()},'models':[m.m_Filename for m in f.Models()]}
 zones=[]
 for z in b.Zones():
  poly=z.Outline();lines=[]
  for i in range(poly.OutlineCount()):
   line=poly.COutline(i);lines.append([(line.CPoint(j).x,line.CPoint(j).y) for j in range(line.PointCount())])
  zones.append({'uuid':z.m_Uuid.AsString(),'net':z.GetNetname(),'layer':z.GetLayer(),'outlines':lines})
 return b,{'footprints':out,'pads':pads,'zones':sorted(zones,key=lambda x:x['uuid'])}
bs,a=snapshot(base);board,b=snapshot(dst);errors=[]
expected={}
for ref in ['U10','U11','U12','U13']:
 for pad in ['9','10','11']:expected[(ref,pad)]=('+3V3','GND')
for ref,pad,net in [('R126','2','FAN1_GATE'),('Q4','1','FAN1_GATE'),('R128','1','FAN1_GATE'),('R127','2','FAN2_GATE'),('Q5','1','FAN2_GATE'),('R129','1','FAN2_GATE')]:expected[(ref,pad)]=(net,net+'_Q')
expected.update({('U1','9'):('+3V3A','+3V3'),('C8','1'):('+3V3A','+3V3'),('J33','1'):('+3V3A','+3V3'),('J34','1'):('+3V3A','+3V3')})
expected.update({('D10','1'):('LED_PWR_A','GND'),('D10','2'):('GND','LED_PWR_A'),('D11','1'):('LED_FAULT_A','USER_AUX'),('D11','2'):('USER_AUX','LED_FAULT_A')})
if set(b['footprints'])!=set(a['footprints'])|{'C10'}:errors.append('Unexpected footprint inventory change')
new_pad_ids=set(b['pads'])-set(a['pads'])
if not set(a['pads']).issubset(b['pads']) or len(new_pad_ids)!=2 or any(b['pads'][u]['ref']!='C10' for u in new_pad_ids):errors.append('Unexpected pad UUID inventory change')
netdelta=[];geometry=[]
for uid,x in a['pads'].items():
 y=b['pads'].get(uid)
 if not y:continue
 pair=(x['ref'],x['pad'])
 if x['net']!=y['net']:
  d={'reference':x['ref'],'pad':x['pad'],'uuid':uid,'before':x['net'],'after':y['net']};netdelta.append(d)
  if expected.get(pair)!=(x['net'],y['net']):errors.append('Unexpected pad net change: '+str(d))
 if pair in expected and (x['net'],y['net'])!=expected[pair]:errors.append('Missing authorized pad net change '+str(pair))
 for key in ['ref','pad','size_nm','drill_nm','shape','layers']:
  if x[key]!=y[key]:errors.append('Unexpected pad '+key+' change '+str(pair))
 if x['xy_nm']!=y['xy_nm']:
  geometry.append({'reference':x['ref'],'pad':x['pad'] or 'NPTH','uuid':uid,'before_mm':[v/1e6 for v in x['xy_nm']],'after_mm':[v/1e6 for v in y['xy_nm']]})
  if x['ref'] in ['D10','D11']:
   other=next(z for z in a['pads'].values() if z['ref']==x['ref'] and z['pad']!=x['pad'])
   if y['xy_nm']!=other['xy_nm'] or y['net']!=other['net']:errors.append('LED copper endpoint changed '+str(pair))
  elif x['ref']=='J20' and x['pad'] in ['SH','']:
   yy=94.595 if x['pad']=='' else (93.970 if x['xy_nm'][1]<95e6 else 97.895)
   if y['xy_nm']!=[x['xy_nm'][0],round(yy*1e6)]:errors.append('J20 position mismatch '+str(pair))
  else:errors.append('Unexpected pad position '+str(pair))
for ref,x in a['footprints'].items():
 y=b['footprints'][ref]
 for key in ['uuid','xy_nm']:
  if x[key]!=y[key]:errors.append('Unexpected footprint '+key+' '+ref)
 expect_angle=(x['orientation_deg']+180)%360 if ref in ['D10','D11'] else x['orientation_deg']%360
 if abs(y['orientation_deg']%360-expect_angle)>1e-7:errors.append('Unexpected footprint angle '+ref)
 if ref=='J20':
  if y['value']!='USB4216-03-A' or y['footprint']!='LabWired_GCT:USB4216-03-A':errors.append('Wrong J20 source identity')
 else:
  for key in ['value','footprint','fields']:
   if x[key]!=y[key]:errors.append('Unexpected footprint '+key+' '+ref)
 if ref not in ['U10','U11','U12','U13','U20','J20'] and x['models']!=y['models']:errors.append('Unexpected model change '+ref)
if len(netdelta)!=26:errors.append('Expected 26 pad-net changes, got '+str(len(netdelta)))
cap=b['footprints'].get('C10')
if not cap or cap['value']!='100n' or not cap['footprint'].endswith('C_0603_1608Metric') or cap['xy_nm']!=[42900000,56000000]:errors.append('VDDA capacitor identity or placement mismatch')
if cap and {(v['pad'],v['net']) for v in cap['pads']}!={('1','+3V3'),('2','GND')}:errors.append('VDDA capacitor net mismatch')
if any(v['net']=='+3V3A' for v in b['pads'].values()) or any(t.GetNetname()=='+3V3A' for t in board.GetTracks()):errors.append('Floating analog rail was not retired')
if len(geometry)!=10:errors.append('Expected 10 pad-position changes, got '+str(len(geometry)))
if a['zones']!=b['zones']:errors.append('Zone outlines or nets changed')
pro=base.with_suffix('.kicad_pro');dp=dst.with_suffix('.kicad_pro')
if pro.read_bytes()!=dp.read_bytes():errors.append('Project rules changed')
mcu={'9':'+3V3','18':'X_STEP','39':'Y_STEP','41':'Z_STEP','46':'E_STEP','19':'X_DIR','40':'Y_DIR','45':'Z_DIR','21':'E_DIR','25':'DRV_EN','29':'END_X','2':'END_Y','3':'END_Z','14':'TH_HOT','11':'TH_BED','26':'HOTEND_CMD','27':'BED_CMD','28':'FAN1_CMD','42':'I2C_SCL','43':'I2C_SDA'}
for pad,net in mcu.items():
 rec=next(v for v in b['pads'].values() if v['ref']=='U1' and v['pad']==pad)
 if rec['net']!=net:errors.append('MCU contract mismatch at pad'+pad)
for ref in ['U10','U11','U12','U13']:
 for pad in ['12','14','15']:
  if next(v for v in b['pads'].values() if v['ref']==ref and v['pad']==pad)['net']!='+3V3':errors.append('Driver supply/reset/sleep mismatch')
tracks=[t for t in board.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA)]
if min(t.GetWidth() for t in tracks)<p.FromMM(.2):errors.append('Subminimum track width')
if min(t.GetDrill() for t in vias)<p.FromMM(.3):errors.append('Subminimum via drill')
if min(t.GetWidth(p.F_Cu) for t in vias)<p.FromMM(.5):errors.append('Subminimum via diameter')
if min((t.GetWidth(p.F_Cu)-t.GetDrill())/2 for t in vias)<p.FromMM(.1):errors.append('Subminimum via annulus')
drcpath=ev/'native-drc.json';drc=json.loads(drcpath.read_text()) if drcpath.exists() else None
if args.require_clean and (not drc or drc['violations'] or drc['unconnected_items'] or drc['schematic_parity']):errors.append('Final DRC is not clean')
baseline_drc_path=base.with_name(base.stem+'-drc.json')
baseline_drc=json.loads(baseline_drc_path.read_text()) if baseline_drc_path.exists() else None
ignored_equal=None if not baseline_drc or not drc else baseline_drc['ignored_checks']==drc['ignored_checks']
if ignored_equal is False:errors.append('DRC ignored-check selection changed')
def thermal_info(b,xy):
 matches=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND' and t.GetPosition()==p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6))]
 assert len(matches)==1
 v=matches[0]
 return {'xy_mm':list(xy),'diameter_mm':p.ToMM(v.GetWidth(p.F_Cu)),'drill_mm':p.ToMM(v.GetDrill()),'front_tented':v.IsTented(p.F_Cu),'back_tented':v.IsTented(p.B_Cu),'filled':v.GetPrimaryDrillFilledFlag(),'capped':v.GetPrimaryDrillCappedFlag()}
thermal_before=thermal_info(bs,(65.0777,20.5746));thermal_after=thermal_info(board,(61.7,21.0))
if {k:v for k,v in thermal_before.items() if k!='xy_mm'}!={k:v for k,v in thermal_after.items() if k!='xy_mm'}:errors.append('Thermal-via fabrication settings changed')
def edge_records(b):
 out=[]
 for t in b.GetDrawings():
  if t.GetLayer()!=p.Edge_Cuts:continue
  a=t.GetStart();z=t.GetEnd();out.append((t.m_Uuid.AsString(),int(t.GetShape()),a.x,a.y,z.x,z.y,t.GetWidth()))
 return sorted(out)
edge_equal=edge_records(bs)==edge_records(board)
if not edge_equal:errors.append('Board outline changed')
netlist=sorted([{'reference':v['ref'],'pad':v['pad'],'net':v['net'],'uuid':v['uuid']} for v in b['pads'].values()],key=lambda x:(x['reference'],x['pad'],x['uuid']))
netbytes=json.dumps(netlist,sort_keys=True,separators=(',',':')).encode();(ev/'native-pad-net-map.json').write_text(json.dumps(netlist,indent=2)+'\n')
report={'baseline_sha256':sha(base),'candidate_sha256':sha(dst),'rules_sha256':sha(pro),'rules_byte_identical':pro.read_bytes()==dp.read_bytes(),'zone_outlines_and_nets_identical':a['zones']==b['zones'],'footprint_count':len(b['footprints']),'pad_count':len(netlist),'track_count':len(tracks),'via_count':len(vias),'pad_net_map_sha256':hashlib.sha256(netbytes).hexdigest(),'schematic_parity_checked':False,'added_components':{'C10':cap},'authorized_pad_net_changes':sorted(netdelta,key=lambda x:(x['reference'],x['pad'])),'authorized_pad_position_changes':sorted(geometry,key=lambda x:(x['reference'],x['pad'],x['uuid'])),'mcu_contract':mcu,'drc_counts':None if not drc else {k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},'drc_ignored_checks_unchanged':ignored_equal,'ignored_checks':None if not drc else drc['ignored_checks'],'edge_cuts_identical':edge_equal,'u12_thermal_via':{'before':thermal_before,'after':thermal_after,'source':'Allegro A4988 datasheet p19 note C and p12 layout'},'errors':errors,'pass':not errors}
(ev/'native-source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['candidate_sha256','rules_byte_identical','zone_outlines_and_nets_identical','footprint_count','pad_count','track_count','via_count','drc_counts','errors','pass']},indent=2));assert not errors,errors
