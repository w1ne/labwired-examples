#!/usr/bin/env python3
"""Compare KiCad's own schematic netlist export with native PCB pad records."""
import sys,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew
board_path,xml_path,out_path=map(Path,sys.argv[1:4])
b=pcbnew.LoadBoard(str(board_path));root=ET.parse(xml_path).getroot()
inventory_path=Path(sys.argv[4]) if len(sys.argv)>4 else xml_path.parent/'native-mechanical-pad-inventory.json'
inventory=json.loads(inventory_path.read_text()) if inventory_path.exists() else {'groups':[]}
mechanical_by_ref={g['ref']:g for g in inventory['groups']}
mechanical_pad_uuids=set();mechanical_physical=[];unnumbered_physical=[];electrical_physical_count=0
for group in inventory['groups']:
 assert group['ref'] in ['J10','J11','J12','J13','J22','J23'],('unapproved mechanical group',group['ref'])
 assert len(group['pads'])==2 and all(p['number']=='MP' and p['netCode']==0 and not p['net'] for p in group['pads'])
 for pad in group['pads']:
  assert pad['uuid'] not in mechanical_pad_uuids
  mechanical_pad_uuids.add(pad['uuid'])

expected={};mechanical=[];pad_count=0;native_refs=set()
for f in b.GetFootprints():
 assert f.GetReference() not in native_refs,('duplicate native reference',f.GetReference())
 native_refs.add(f.GetReference())
 pads={};n=0
 for p in f.Pads():
  pad_count+=1;n+=1;number=p.GetNumber()
  if not number:
   assert p.GetNetCode()==0,(f.GetReference(),'unnumbered connected pad')
   layers=[b.GetLayerName(layer)for layer in p.GetLayerSet().Seq()]
   classification='mechanical hole'if p.GetDrillSize().x or p.GetDrillSize().y else 'paste aperture'if set(layers)<={'F.Paste','B.Paste'}else 'unclassified'
   assert classification!='unclassified',('unknown unnumbered pad',f.GetReference(),p.m_Uuid.AsString(),layers)
   unnumbered_physical.append({'ref':f.GetReference(),'uuid':p.m_Uuid.AsString(),'position':[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],'size':[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)],'drill':[pcbnew.ToMM(p.GetDrillSize().x),pcbnew.ToMM(p.GetDrillSize().y)],'padAttribute':p.GetAttribute(),'layers':layers,'classification':classification,'netCode':0})
   continue
  if f.GetReference() in mechanical_by_ref and number=='MP':
   group=mechanical_by_ref[f.GetReference()]
   assert f.GetFPIDAsString()==group['footprint'],('mechanical footprint changed',f.GetReference())
   item=next((a for a in group['pads']if a['uuid']==p.m_Uuid.AsString()),None)
   assert item and p.GetNetCode()==0 and not p.GetNetname(),('mechanical pad changed',f.GetReference(),p.m_Uuid.AsString())
   assert item['position']==[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)]
   assert item['size']==[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)]
   assert item['drill']==[pcbnew.ToMM(p.GetDrillSize().x),pcbnew.ToMM(p.GetDrillSize().y)]
   mechanical_physical.append({'ref':f.GetReference(),**item});continue
  electrical_physical_count+=1
  net=p.GetNetname() or None
  assert number not in pads or pads[number]==net,(f.GetReference(),number,'conflicting duplicate pad')
  pads[number]=net
 if not pads:
  mechanical.append({'ref':f.GetReference(),'footprint':str(f.GetFPID().GetLibItemName()),'padCount':n});continue
 fields={a.GetName():a.GetText() for a in f.GetFields()}
 expected[f.GetReference()]={'value':f.GetValue(),'footprint':(str(f.GetFPID().GetLibNickname())+':' if str(f.GetFPID().GetLibNickname()) else '')+str(f.GetFPID().GetLibItemName()),'pads':pads,**{name:fields.get(name,'') for name in ['MPN','Manufacturer','Datasheet','Description']},'excludeFromBom':bool(f.GetAttributes() & 8)}
actual={}
for c in root.findall('./components/comp'):
 ref=c.get('ref');assert ref not in actual,('duplicate reference',ref)
 fields={a.get('name'):a.text or '' for a in c.findall('./fields/field')}
 fields.update({a.get('name'):a.get('value') or '' for a in c.findall('property')})
 fields['Datasheet']=c.findtext('datasheet') or fields.get('Datasheet','')
 fields['Description']=c.findtext('description') or fields.get('Description','')
 actual[ref]={'value':c.findtext('value'),'footprint':c.findtext('footprint'),'pads':{},**{name:fields.get(name,'') for name in ['MPN','Manufacturer','Datasheet','Description']},'excludeFromBom':any(a.get('name')=='exclude_from_bom'for a in c.findall('property'))}
net_members={};net_codes=set();seen_nodes=set()
for net in root.findall('./nets/net'):
 name=net.get('name');code=net.get('code');members=[]
 assert name not in net_members,('duplicate net name',name)
 assert code not in net_codes,('duplicate net code',code)
 net_codes.add(code)
 for node in net.findall('node'):
  ref,pad=node.get('ref'),node.get('pin')
  if ref.startswith('#'):continue
  assert (ref,pad) not in seen_nodes,('duplicate schematic terminal',ref,pad)
  seen_nodes.add((ref,pad));members.append(ref+'.'+pad)
  assert ref in actual,('unknown reference',ref)
  assert pad not in actual[ref]['pads'] or actual[ref]['pads'][pad]==name,(ref,pad,'conflicting schematic pin')
  actual[ref]['pads'][pad]=name
 net_members[name]=members
issues=[];explicit_unwired=[];connected=0
for ref in sorted(set(expected)|set(actual)):
 if ref not in expected or ref not in actual:
  issues.append({'ref':ref,'issue':'reference missing or added','inNative':ref in expected,'inSchematic':ref in actual});continue
 e,a=expected[ref],actual[ref]
 for field in ['value','footprint','MPN','Manufacturer','Datasheet','Description','excludeFromBom']:
  if e[field]!=a[field]:issues.append({'ref':ref,'field':field,'native':e[field],'schematic':a[field]})
 for pad in sorted(set(e['pads'])|set(a['pads'])):
  if pad not in e['pads'] or pad not in a['pads']:
   issues.append({'ref':ref,'pad':pad,'issue':'pad missing or added','inNative':pad in e['pads'],'inSchematic':pad in a['pads']});continue
  en,an=e['pads'][pad],a['pads'][pad]
  if en is None:
   if not an.startswith('unconnected-') or net_members[an]!=[ref+'.'+pad]:issues.append({'ref':ref,'pad':pad,'issue':'native unconnected pad was joined','schematicNet':an,'members':net_members.get(an)})
   else:explicit_unwired.append({'ref':ref,'pad':pad,'schematicNet':an})
  elif en!=an:issues.append({'ref':ref,'pad':pad,'nativeNet':en,'schematicNet':an})
  else:connected+=1
assert len(mechanical_physical)==len(mechanical_pad_uuids),('mechanical inventory missing native pads',len(mechanical_physical),len(mechanical_pad_uuids))
assert electrical_physical_count+len(mechanical_physical)+len(unnumbered_physical)==pad_count
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'schema':'labwired.native-schematic-parity.v1','ok':not issues,'nativePcbSha256':sha(board_path),'kicadNetlistSha256':sha(xml_path),'nativeFootprints':len(list(b.GetFootprints())),'nativePadInstances':pad_count,'electricalReferences':len(expected),'schematicReferences':len(actual),'uniqueElectricalPads':sum(len(e['pads'])for e in expected.values()),'connectedPadNamesMatched':connected,'nativeMetadataFieldsCompared':['MPN','Manufacturer','Datasheet','Description','excludeFromBom'],'electricalPhysicalPadInstances':electrical_physical_count,'mechanicalRetentionPadInstances':len(mechanical_physical),'unnumberedPhysicalPadInstances':len(unnumbered_physical),'unnumberedPasteApertures':sum(p['classification']=='paste aperture'for p in unnumbered_physical),'unnumberedMountingHoles':sum(p['classification']=='mechanical hole'for p in unnumbered_physical),'allPhysicalPadsReconciled':electrical_physical_count+len(mechanical_physical)+len(unnumbered_physical)==pad_count,'mechanicalRetentionPads':mechanical_physical,'unnumberedPhysicalPads':unnumbered_physical,'mechanicalInventorySha256':sha(inventory_path)if inventory_path.exists()else None,'explicitUnwiredPads':explicit_unwired,'excludedMechanical':mechanical,'issues':issues,'method':'Native pcbnew pad records compared against KiCad sch export netlist (kicadxml). All reference/value/footprint identities and numbered pad net names are compared. Each electrical native no-net pad must remain an isolated explicit no-connect. The twelve source-identified connector retention pads remain net 0 and are audited by physical UUID, position, size and drill outside the electrical pin inventory; all other numbered pads remain electrical. Unnumbered mounting holes and paste apertures are also inventoried and the counts reconcile to every physical pad.'}
out_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({**{k:v for k,v in report.items() if k not in ['explicitUnwiredPads','excludedMechanical','method','issues','mechanicalRetentionPads','unnumberedPhysicalPads']},'issueCount':len(issues),'issues':issues[:15]},indent=2))
sys.exit(0 if report['ok'] else 1)
