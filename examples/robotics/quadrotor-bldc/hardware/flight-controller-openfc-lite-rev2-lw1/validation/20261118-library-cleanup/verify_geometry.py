#!/usr/bin/env python3
"""Read-only proof. Requires sexpdata 1.0.2. Optional argument: output JSON path."""
from pathlib import Path
import copy,gzip,hashlib,json,sexpdata as S,xml.etree.ElementTree as E,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
HW=ROOT/'hardware';OUT=Path(__file__).resolve().parent
def read_source(path):
 return path.read_text() if path.exists() else gzip.decompress(Path(str(path)+'.gz').read_bytes()).decode()
def source_digest(path):
 return hashlib.sha256(read_source(path).encode()).hexdigest()
def tag(n):return str(n[0]) if isinstance(n,list) and n else ''
def child(n,k):return next((x for x in n if tag(x)==k),None)
def val(n,k):return child(n,k)[1]
def prop(n,k):return next((x for x in n if tag(x)=='property' and x[1]==k),None)
def walk(n):
 if isinstance(n,list):
  yield n
  for x in n:yield from walk(x)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
aliases={
 '/PADS/U1RX':'/PADS/UART1_RX','/PADS/PU1TX':'/PADS/PIOUART1_TX','/PADS/PU1RX':'/PADS/PIOUART1_RX',
 'unconnected-(U9-SDx{slash}AH1{slash}Qvar1-Pad2)':'unconnected-(U9-ASDx-Pad2)',
 'unconnected-(U9-SCx{slash}AH2{slash}Qvar2-Pad3)':'unconnected-(U9-ASCx-Pad3)',
 'unconnected-(U9-OCS_Aux-Pad10)':'unconnected-(U9-OCSB-Pad10)',
 'unconnected-(U9-SDO_Aux-Pad11)':'unconnected-(U9-OSDO-Pad11)'}
a=S.loads(read_source(OUT/'before/OpenFC.kicad_pcb'));b=S.loads((HW/'OpenFC.kicad_pcb').read_text())
for n in walk(a):
 if tag(n) in ('net','net_name') and isinstance(n[1],str) and n[1] in aliases:n[1]=aliases[n[1]]
def inventory(root):
 pads={};tracks={};zones={};padids={};pinmeta={}
 for fp in (n for n in root if tag(n)=='footprint'):
  ref=prop(fp,'Reference')[2]
  for p in (x for x in fp if tag(x)=='pad'):
   ident=val(p,'uuid');padids[ident]=(ref,p[1])
   pads[ident]=[p[0],*copy.deepcopy(p[2:])]
   pads[ident]=[x for x in pads[ident] if tag(x) not in ('pinfunction','pintype','uuid')]
   pinmeta[ident]=[x for x in p if tag(x) in ('pinfunction','pintype')]
 for n in root:
  if tag(n) in ('segment','via','arc'):tracks[val(n,'uuid')]=[x for x in n if tag(x)!='uuid']
  if tag(n)=='zone':zones[val(n,'uuid')]=[x for x in n if tag(x)!='uuid']
 return pads,tracks,zones,padids,pinmeta
left,right=inventory(a),inventory(b);geometry={}
for name,x,y in zip(('pads','tracks_and_vias','zones'),left[:3],right[:3]):
 changed=[k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)]
 geometry[name]={'before_count':len(x),'after_count':len(y),'changed':changed}
 assert not changed,(name,changed[:5])
number_changes=[]
for id,(ref,old) in left[3].items():
 actual=right[3][id]
 expected=(ref,{'3':'4','4':'5','5':'3'}.get(old,old)) if ref=='U12' else (ref,old)
 assert actual==expected
 if actual!=(ref,old):number_changes.append({'ref':ref,'uuid':id,'old':old,'new':actual[1]})
def schematic_geometry(path):
 t=S.loads(read_source(path));lib={x[1]:x for x in child(t,'lib_symbols')[1:] if tag(x)=='symbol'}
 wires={val(x,'uuid'):x for x in t if tag(x) in ('wire','junction')}
 symbols={};pins={}
 for n in t:
  if tag(n)!='symbol' or not prop(n,'Reference'):continue
  ref=prop(n,'Reference')[2]
  if ref.startswith('#'):continue
  symbols[ref]=[child(n,'at'),child(n,'mirror'),child(n,'unit')]
  key=val(n,'lib_name') if child(n,'lib_name') else val(n,'lib_id')
  for p in walk(lib[key]):
   if tag(p)=='pin' and len(p)>2 and isinstance(p[1],S.Symbol):pins[(ref,val(p,'number'))]=child(p,'at')
 return wires,symbols,pins
schematic=[]
for p in HW.glob('*.kicad_sch'):
 original=OUT/'before'/p.name
 old,new=schematic_geometry(original),schematic_geometry(p)
 assert old[0]==new[0],('wire/junction edit',p.name)
 assert old[1]==new[1],('component moved',p.name)
 for (ref,pin),pos in old[2].items():
  mapped={'3':'4','4':'5','5':'3'}.get(pin,pin) if ref=='U12' else pin
  assert new[2][(ref,mapped)]==pos,(p.name,ref,pin)
 schematic.append({'file':p.name,'wires_and_junctions_preserved':len(old[0]),'placed_components_preserved':len(old[1]),'pin_positions_preserved':len(old[2])})
x=E.fromstring(gzip.decompress((OUT.parent/'schematic.net.xml.gz').read_bytes()))
y=E.fromstring(gzip.decompress((OUT/'schematic.net.xml.gz').read_bytes()))
def nets(root,inverse=False):
 return {tuple(sorted((n.attrib['ref'],({'4':'3','5':'4','3':'5'}.get(n.attrib['pin'],n.attrib['pin']) if inverse and n.attrib['ref']=='U12' else n.attrib['pin'])) for n in q.findall('node'))):q.attrib['name'] for q in root.findall('./nets/net')}
nx,ny=nets(x),nets(y,True);assert nx.keys()==ny.keys()
baseline_project_sha256='1ad2949fe79436a92685d25c8ddbddc3bda77cf13f8f03889318030023467b95'
assert digest(HW/'OpenFC.kicad_pro')==baseline_project_sha256,'ERC/DRC policy was changed'
receipt={
 'input_board_sha256':source_digest(OUT/'before/OpenFC.kicad_pcb'),
 'output_board_sha256':digest(HW/'OpenFC.kicad_pcb'),
 'physical_geometry_comparison':geometry,'pin_identity_changes':number_changes,
 'pin_metadata_updates':sum(left[4][k]!=right[4][k] for k in left[4]),
 'renamed_net_aliases':aliases,'schematic_geometry':schematic,
 'net_partition_proof':{'before':len(nx),'after':len(ny),'removed':0,'added':0,'pin_map_applied':{'U12.3':'U12.4','U12.4':'U12.5','U12.5':'U12.3'}},
 'project_rule_policy_unchanged':True,'project_sha256':digest(HW/'OpenFC.kicad_pro'),
 'scope':'All pad lands, drills, traces, vias, zone polygons, schematic wires, symbol positions and physical pin locations remain structurally identical. Only documented U12 pin numbering and net aliases are normalized for this comparison. Pin types/functions and symbol/library identity are separately corrected.'
}
if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'board_sha256':receipt['output_board_sha256'],'geometry':geometry,'net_partitions':len(nx),'pin_metadata':receipt['pin_metadata_updates'],'project_rule_policy_unchanged':True},indent=2))

