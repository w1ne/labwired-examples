"""Correct sourced native metadata with a complete copper/pad/outline parity guard."""
import pcbnew,json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parent
source=r/'history/before-native-identity/pathfinder-routed.kicad_pcb'
output=r/'pathfinder-routed.kicad_pcb'
layout=json.loads((r.parent/'placement-result.json').read_text())
parts={p['id']:p for p in layout['diagram']['parts']};components={c['ref']:c for c in layout['component_pin_map']}
def geometry(board):
 pads=[];footprints=[];copper=[];edges=[]
 for f in board.GetFootprints():
  footprints.append((f.GetReference(),f.GetFPIDAsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer()))
  for p in f.Pads():pads.append((f.GetReference(),p.GetNumber(),p.GetNetCode(),p.GetNetname(),tuple(p.GetPosition()),tuple(p.GetSize()),p.GetShape(pcbnew.F_Cu),p.GetAttribute(),p.GetOrientationDegrees(),tuple(p.GetDrillSize()),p.GetDrillShape(),tuple(p.GetOffset()),tuple(p.GetLayerSet().Seq())))
 for t in board.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA):copper.append(('via',t.GetNetCode(),t.GetNetname(),tuple(t.GetPosition()),t.GetWidth(pcbnew.F_Cu),t.GetDrillValue(),t.TopLayer(),t.BottomLayer(),t.IsLocked()))
  else:copper.append(('track',t.GetNetCode(),t.GetNetname(),t.GetLayer(),tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth(),t.IsLocked()))
 for e in board.GetDrawings():
  if isinstance(e,pcbnew.PCB_SHAPE):edges.append((e.GetLayer(),e.GetShape(),tuple(e.GetStart()),tuple(e.GetEnd()),tuple(e.GetCenter()),e.GetWidth()))
 return {'footprints':sorted(footprints),'pads':sorted(pads),'copper':sorted(copper),'board_graphics':sorted(edges),'net_table':sorted((n.GetNetCode(),n.GetNetname())for n in board.GetNetsByNetcode().values())}
b=pcbnew.LoadBoard(str(source));before=geometry(b);edits=[];pin_labels=0
for f in b.GetFootprints():
 c=components[f.GetReference()];part=parts[c['partId']]
 if f.GetValue()!=c['value']:edits.append({'ref':c['ref'],'field':'Value','from':f.GetValue(),'to':c['value']});f.SetValue(c['value'])
 fields={'LabWiredPartId':c['partId'],'LabWiredType':c['type'],'Description':c['type']+'; source part '+c['partId']}
 if c.get('mpn'):fields['MPN']=c['mpn']
 if c.get('manufacturer'):fields['Manufacturer']=c['manufacturer']
 if part.get('manufacturerPart'):fields['LabWiredManufacturerPart']=part['manufacturerPart']
 for name,value in fields.items():f.SetField(name,value);f.GetField(name).SetVisible(False)
 pin_by_pad={pad:pin for pin,pads in c['padOf'].items()for pad in pads}
 for p in f.Pads():
  if p.GetNumber()in pin_by_pad:p.SetPinFunction(pin_by_pad[p.GetNumber()]);pin_labels+=1
assert geometry(b)==before
pcbnew.SaveBoard(str(output),b)
after=geometry(pcbnew.LoadBoard(str(output)));assert after==before,'metadata correction changed geometry or electrical copper'
for ext in ['kicad_pro','kicad_dru']:(r/('pathfinder-routed.'+ext)).write_bytes((r/('rules.'+ext)).read_bytes())
receipt={'schema':'pathfinder.native-identity-correction.v1','source_pcb_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'corrected_pcb_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'geometry_electrical_snapshot_sha256':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'exact_geometry_and_electrical_parity':True,'compared':['all footprint references/library IDs/positions/rotations/layers','all pad names/netcodes/netnames/positions/sizes/shapes/drills/offsets/layers','all track/via netcodes/netnames/coordinates/widths/drills/layers/locks','all board edge/graphic shape coordinates','complete native net table'],'value_corrections':edits,'footprints':len(before['footprints']),'pads':len(before['pads']),'copper_items':len(before['copper']),'pin_function_labels_from_source_pad_map':pin_labels,'sourcing_fields':'Hidden MPN, Manufacturer, LabWired source ID/type/selected manufacturer-part fields; exact selected part records only. Passive values remain electrical values.','manufacturing_verified':False,'native_twin_parity_verified':False}
(r/'native-identity-correction.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
