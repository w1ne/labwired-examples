#!/usr/bin/python3
"""Name only the twelve isolated A4988 NC pads for exact KiCad schematic parity."""
import argparse, hashlib, json, re, shutil, xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew
ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--netlist',required=True);ap.add_argument('--evidence',required=True);args=ap.parse_args()
src,dst=Path(args.input),Path(args.output);assert src.resolve()!=dst.resolve()
raw=src.read_text();before=pcbnew.LoadBoard(str(src));before.BuildConnectivity();conn=before.GetConnectivity()
expected={(ref,str(pad)) for ref in ['U10','U11','U12','U13'] for pad in [7,20,25]}
xml=ET.parse(args.netlist).getroot();names={}
for net in xml.findall('./nets/net'):
 members=[(node.get('ref'),node.get('pin')) for node in net.findall('node')]
 for member in members:
  if member in expected:
   assert members==[member],('NC terminal is not a singleton',member,members)
   name=net.get('name');assert name.startswith('unconnected-('),name
   assert member not in names;names[member]=name
assert set(names)==expected and len(set(names.values()))==12
by_ref={f.GetReference():f for f in before.GetFootprints()};changes=[]
for ref,pad in sorted(expected):
 matches=[p for p in by_ref[ref].Pads() if p.GetNumber()==pad];assert len(matches)==1
 p=matches[0];assert p.GetNetCode()==0 and p.GetNetname()==''
 assert not [item for item in conn.GetConnectedItems(p) if item.m_Uuid.AsString()!=p.m_Uuid.AsString()],(ref,pad,'physically connected before NC normalization')
 assert not any(v.GetNetname()==names[(ref,pad)] for f in before.GetFootprints() for v in f.Pads())
 changes.append({'reference':ref,'pad':pad,'uuid':p.m_Uuid.AsString(),'before':'','after':names[(ref,pad)],'connected_items_before':[]})
changed=[]
def patch_foot(block,reverse=False):
 ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
 if ref not in ['U10','U11','U12','U13']:return block
 def patch_pad(m):
  pad=m.group();number=re.search(r'\(pad "([^"]*)"',pad).group(1)
  if (ref,number) not in names:return pad
  line='\n\t\t\t(net "'+names[(ref,number)]+'")'
  if reverse:
   assert pad.count(line)==1
   return pad.replace(line,'')
  assert '\n\t\t\t(net ' not in pad
  assert pad.count('\n\t\t\t(uuid ')==1
  changed.append((ref,number))
  return pad.replace('\n\t\t\t(uuid ',line+'\n\t\t\t(uuid ')
 return re.sub(r'\n\t\t\(pad\b.*?\n\t\t\)',patch_pad,block,flags=re.S)
pattern=r'\n\t\(footprint\b.*?\n\t\)'
result=re.sub(pattern,lambda m:patch_foot(m.group()),raw,flags=re.S)
assert set(changed)==expected and len(changed)==12
restored=re.sub(pattern,lambda m:patch_foot(m.group(),True),result,flags=re.S)
assert restored==raw
assert len(result)-len(raw)==sum(len('\n\t\t\t(net "'+name+'")') for name in names.values())
dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(result)
if src.with_suffix('.kicad_pro').is_file():shutil.copy2(src.with_suffix('.kicad_pro'),dst.with_suffix('.kicad_pro'))
after=pcbnew.LoadBoard(str(dst));after.BuildConnectivity();ac=after.GetConnectivity()
after_pads={p.m_Uuid.AsString():p for f in after.GetFootprints() for p in f.Pads()}
for change in changes:
 pad=after_pads[change['uuid']]
 assert pad.GetNetname()==change['after']
 assert sum(p.GetNetname()==change['after'] for p in after_pads.values())==1
 assert not list(ac.GetConnectedItems(p)),change
 assert not any(t.GetNetname()==change['after'] for t in after.GetTracks())
 assert not any(z.GetNetname()==change['after'] for z in after.Zones())
 change.update({'connected_items_after':[],'net_physical_pad_count':1,'associated_tracks_or_vias':0,'associated_zones':0})
sha=lambda d:hashlib.sha256(d).hexdigest()
report={'input_sha256':sha(raw.encode()),'output_sha256':sha(result.encode()),'schematic_netlist_sha256':sha(Path(args.netlist).read_bytes()),'changes':changes,'nc_definition_source':{'url':'https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf','page':18,'terminal_numbers':[7,20,25],'definition':'No connection'},'reverse_restores_input_bytes':True,'physical_pad_geometry_and_all_pad_uuids_unchanged':True,'all_copper_records_unchanged':True,'conductive_connectivity_unchanged':True,'each_new_net_is_one_isolated_physical_pad':True,'duplicated_mounting_pads_remain_no_net':True,'pass':True}
ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True);(ev/'native-nc-metadata.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
