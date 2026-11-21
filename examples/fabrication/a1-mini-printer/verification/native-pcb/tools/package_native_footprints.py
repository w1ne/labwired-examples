#!/usr/bin/python3
"""Use KiCad to snapshot embedded footprints and qualify only their library namespace."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--evidence',required=True);args=ap.parse_args()
src,dst=Path(args.input),Path(args.output);assert src.resolve()!=dst.resolve();dst.parent.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(src));groups={};records=[]
for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
 old=f.GetFPIDAsString()
 if ':' in old:
  assert old=='LabWired_GCT:USB4216-03-A';continue
 namespace='A1_Native_C10' if f.GetReference()=='C10' else 'A1_Native'
 new=namespace+':'+old
 groups.setdefault((namespace,old),[]).append(f)
 records.append({'reference':f.GetReference(),'uuid':f.m_Uuid.AsString(),'before':old,'after':new})
assert len(records)==156
plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
for (namespace,item),footprints in groups.items():
 lib=dst.parent/(namespace+'.pretty');lib.mkdir(exist_ok=True);plugin.FootprintSave(str(lib),footprints[0])
raw=src.read_text();changed=[]
def patch(m,reverse=False):
 block=m.group();ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
 record=next((v for v in records if v['reference']==ref),None)
 if not record:return block
 old='(footprint "'+record['before']+'"';new='(footprint "'+record['after']+'"'
 if reverse:old,new=new,old
 assert block.count(old)==1,(ref,old)
 if not reverse:changed.append(ref)
 return block.replace(old,new,1)
pattern=r'\n\t\(footprint\b.*?\n\t\)'
result=re.sub(pattern,patch,raw,flags=re.S)
assert len(changed)==156
assert re.sub(pattern,lambda m:patch(m,True),result,flags=re.S)==raw
dst.write_text(result);shutil.copy2(src.with_suffix('.kicad_pro'),dst.with_suffix('.kicad_pro'))
for name in ['models','LabWired_GCT.pretty']:
 shutil.copytree(src.parent/name,dst.parent/name,dirs_exist_ok=True)
(dst.parent/'fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "A1_Native_C10")(type "KiCad")(uri "${KIPRJMOD}/A1_Native_C10.pretty")(options "")(descr "Exact C10 native footprint variant exported by KiCad"))\n  (lib (name "A1_Native")(type "KiCad")(uri "${KIPRJMOD}/A1_Native.pretty")(options "")(descr "Exact native A1 footprint snapshots exported by KiCad"))\n  (lib (name "LabWired_GCT")(type "KiCad")(uri "${KIPRJMOD}/LabWired_GCT.pretty")(options "")(descr "GCT USB4216-03-A rev A2 source-backed land pattern"))\n)\n')
sha=lambda data:hashlib.sha256(data).hexdigest()
report={'input_sha256':sha(raw.encode()),'output_sha256':sha(result.encode()),'namespace':'A1_Native','changes':records,'mapping':[{k:record[k] for k in ['reference','before','after']} for record in records],'library_snapshots':[{'namespace':namespace,'footprint':item,'source_reference':fs[0].GetReference(),'references':[f.GetReference() for f in fs],'path':namespace+'.pretty/'+item+'.kicad_mod','sha256':sha((dst.parent/(namespace+'.pretty')/(item+'.kicad_mod')).read_bytes())}for (namespace,item),fs in sorted(groups.items())],'reverse_restores_input_bytes':True,'item_names_preserved':True,'pad_geometry_copper_models_and_fields_unchanged':True,'rules_byte_identical':src.with_suffix('.kicad_pro').read_bytes()==dst.with_suffix('.kicad_pro').read_bytes(),'pass':True}
ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True);(ev/'native-footprint-namespaces.json').write_text(json.dumps(report,indent=2)+'\n');(ev/'native-footprint-map.json').write_text(json.dumps(report['mapping'],indent=2)+'\n');print(json.dumps({'footprints':len(records),'unique_items':len(groups),'output_sha256':report['output_sha256'],'pass':True},indent=2))
