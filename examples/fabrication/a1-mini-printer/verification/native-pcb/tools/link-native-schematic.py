#!/usr/bin/env python3
"""Attach the validated native schematic UUIDs without changing native geometry."""
from pathlib import Path
import sys,re,json,hashlib,shutil,subprocess,collections,difflib,xml.etree.ElementTree as ET
import pcbnew as p
source,sch,xml,destination=map(Path,sys.argv[1:5]);destination.parent.mkdir(parents=True,exist_ok=True)
text=source.read_text();sch_text=sch.read_text();root=ET.parse(xml).getroot()
uid=r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
root_uuid=re.search(r'^\s*\(uuid "('+uid+r')"\)',sch_text,re.M).group(1)
uuid_map=json.loads((destination.parent/'schematic-uuid-map.json').read_text())
assert uuid_map['sourceSha256']==hashlib.sha256(sch.read_bytes()).hexdigest()
assert uuid_map['rootUuid']==root_uuid
links={}
for c in root.findall('./components/comp'):
 ref=c.get('ref');assert ref not in links,('duplicate reference',ref)
 ids=re.findall(uid,c.findtext('tstamps') or '')
 record=uuid_map['references'][ref]
 assert set(ids)=={u['uuid'] for u in record['instances']},(ref,'schematic and netlist instance mismatch')
 assert record['unit1Uuid'] in ids
 links[ref]=record['path']
b=p.LoadBoard(str(source));changes=[]
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref not in links:
  assert not any(a.GetNumber() for a in f.Pads()),('unmatched electrical footprint',ref)
  continue
 old=f.GetPath().AsString();assert not old or old==links[ref],(ref,'existing path conflicts',old)
 path=p.KIID_PATH()
 for item in links[ref].split('/')[1:]:path.append(p.KIID(item))
 f.SetPath(path);assert f.GetPath().AsString()==links[ref]
 changes.append({'ref':ref,'before':old,'after':links[ref]})
assert len(changes)==len(links)
p.SaveBoard(str(destination),b)
strip_paths=lambda s:re.sub(r'^[ \t]*\(path "[^"\n]*"\)\n','',s,flags=re.M)
serialized=destination.read_text();restored_defaults=[]
if strip_paths(text)!=strip_paths(serialized):
 raw=serialized.splitlines(keepends=True)
 kept=[i for i,line in enumerate(raw) if not re.match(r'^[ \t]*\(path "[^"\n]*"\)\n',line)]
 before=strip_paths(text).splitlines(keepends=True);after=[raw[i] for i in kept];remove=set()
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag=='equal':continue
  assert tag=='insert' and all(line.strip()=='(thickness 0.15)' for line in after[k:l]),('Unexpected serializer delta',tag,after[k:l])
  remove.update(kept[x] for x in range(k,l));restored_defaults.extend([line.strip() for line in after[k:l]])
 destination.write_text(''.join(line for i,line in enumerate(raw) if i not in remove))
same=strip_paths(text)==strip_paths(destination.read_text())
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
report={'schema':'labwired.schematic-uuid-linkage.v1','ok':same,'nativePcbSha256':sha(source),'linkedPcbSha256':sha(destination),'schematicSha256':sha(sch),'kicadNetlistSha256':sha(xml),'rootSchematicUuid':root_uuid,'linkedReferences':len(changes),'restoredImplicitFontDefaults':restored_defaults,'changes':changes,'onlyDelta':'Schematic UUID path records. Removing those records makes every other byte identical to the accepted native PCB.','allOtherBytesIdentical':same,'geometryUnchanged':same,'copperUnchanged':same,'padsAndNetsUnchanged':same,'rulesAndZonesUnchanged':same}
(destination.parent/'native-schematic-linkage.json').write_text(json.dumps(report,indent=2)+'\n')
assert same,'Serialization changed other source bytes; inspect before acceptance'
for suffix in ['.kicad_pro']:
 shutil.copy2(source.with_suffix(suffix),destination.with_suffix(suffix))
for name in ['fp-lib-table','LabWired_GCT.pretty','models']:
 original=source.parent/name
 if original.is_dir():shutil.copytree(original,destination.parent/name,dirs_exist_ok=True)
 elif original.is_file():shutil.copy2(original,destination.parent/name)
if sch.resolve()!=destination.with_suffix('.kicad_sch').resolve():shutil.copy2(sch,destination.with_suffix('.kicad_sch'))
if '--skip-drc' in sys.argv[5:]:
 print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2));raise SystemExit(0)
result=subprocess.run(['kicad-cli','pcb','drc','--format','json','--schematic-parity','--output','native-linked.drc.json',destination.name],cwd=destination.parent,capture_output=True,text=True,timeout=120)
if result.returncode:print(result.stdout,result.stderr);raise SystemExit(result.returncode)
d=json.loads((destination.parent/'native-linked.drc.json').read_text());counts={k:len(v) for k,v in d.items() if isinstance(v,list)}
print(json.dumps({'metadataOnly':same,'linkedReferences':len(changes),'sourceSha256':sha(source),'linkedSha256':sha(destination),'drc':counts},indent=2))
for k,v in d.items():
 if isinstance(v,list) and v:
  print(k,collections.Counter(x.get('type','')for x in v));print(json.dumps(v[:12],indent=2))
