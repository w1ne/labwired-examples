#!/usr/bin/python3
"""Run native KiCad DRC with schematic parity and record exact input hashes."""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('pcb');ap.add_argument('--evidence',required=True);args=ap.parse_args()
pcb=Path(args.pcb).resolve();ev=Path(args.evidence).resolve();ev.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={p.suffix:sha(p) for p in [pcb,pcb.with_suffix('.kicad_pro'),pcb.with_suffix('.kicad_sch')]}
cmd=['kicad-cli','pcb','drc','--schematic-parity','--format','json','--output',str(ev/'native-drc.json'),str(pcb)]
t0=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
(ev/'native-drc.log').write_text(r.stdout+r.stderr)
d=json.loads((ev/'native-drc.json').read_text())
after={p.suffix:sha(p) for p in [pcb,pcb.with_suffix('.kicad_pro'),pcb.with_suffix('.kicad_sch')]}
report={'pcb':str(pcb),'pcb_sha256':inputs['.kicad_pcb'],'rules_sha256':inputs['.kicad_pro'],'schematic_sha256':inputs['.kicad_sch'],'kicad_version':subprocess.check_output(['kicad-cli','version'],text=True).strip(),'command':cmd,'return_code':r.returncode,'elapsed_seconds':round(time.monotonic()-t0,3),'schematic_parity_checked':True,'counts':{k:len(d[k]) for k in ['violations','unconnected_items','schematic_parity']},'input_files_unchanged':inputs==after,'input_hashes_after':after}
(ev/'native-validation-command.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert inputs==after,'KiCad modified a native source input'
