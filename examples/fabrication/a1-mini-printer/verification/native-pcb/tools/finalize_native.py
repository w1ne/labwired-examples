#!/usr/bin/python3
"""Finalize source metadata, project-local footprint, zone fill and independent DRC."""
import argparse,json,shutil,subprocess,hashlib
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--evidence',required=True);args=ap.parse_args()
src=Path(args.input).resolve();out=Path(args.output).resolve();ev=Path(args.evidence).resolve();assert src!=out;out.parent.mkdir(parents=True,exist_ok=True);ev.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(src));j=next(f for f in b.GetFootprints() if f.GetReference()=='J20')
fields={'MPN':'USB4216-03-A','Manufacturer':'GCT','Datasheet':'https://www.mouser.lt/datasheet/3/1507/1/usb4216.pdf','Description':'USB Type-C receptacle; GCT USB4216-03-A drawing rev A2, 2025-07-28; primary drawing land pattern and clearance model.'}
for k,v in fields.items():j.SetField(k,v);j.GetField(k).SetVisible(False)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b);shutil.copy2(src.with_suffix('.kicad_pro'),out.with_suffix('.kicad_pro'))
lib=out.parent/'LabWired_GCT.pretty';lib.mkdir(exist_ok=True);p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib),j)
(out.parent/'fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "LabWired_GCT")(type "KiCad")(uri "${KIPRJMOD}/LabWired_GCT.pretty")(options "")(descr "GCT USB4216-03-A rev A2 source-backed land pattern"))\n)\n')
for f in b.GetFootprints():
 for model in f.Models():
  if model.m_Filename.startswith('${KIPRJMOD}/'):assert (out.parent/model.m_Filename[len('${KIPRJMOD}/'):]).is_file(),model.m_Filename
command=['kicad-cli','pcb','drc','--format','json','--output',str(ev/'native-drc.json'),str(out)]
r=subprocess.run(command,capture_output=True,text=True,timeout=120);(ev/'native-drc.log').write_text(r.stdout+r.stderr)
d=json.loads((ev/'native-drc.json').read_text());report={'pcb':str(out),'pcb_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'rules_sha256':hashlib.sha256(out.with_suffix('.kicad_pro').read_bytes()).hexdigest(),'kicad_version':subprocess.check_output(['kicad-cli','version'],text=True).strip(),'command':command,'return_code':r.returncode,'schematic_parity_checked':False,'counts':{k:len(d[k]) for k in ['violations','unconnected_items','schematic_parity']},'j20_source_fields':fields}
(ev/'native-validation-command.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert not d['violations'] and not d['unconnected_items'],'Native PCB did not pass final DRC'
