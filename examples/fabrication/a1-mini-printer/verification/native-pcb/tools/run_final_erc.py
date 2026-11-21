#!/usr/bin/python3
"""Record native schematic ERC without changing project rules or exclusions."""
import argparse,collections,hashlib,json,subprocess,time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('schematic');ap.add_argument('--evidence',required=True);args=ap.parse_args()
sch=Path(args.schematic).resolve();ev=Path(args.evidence).resolve();ev.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[sch,sch.with_suffix('.kicad_pcb'),sch.with_suffix('.kicad_pro')];before={p.suffix:sha(p) for p in files}
command=['kicad-cli','sch','erc','--format','json','--output',str(ev/'native-erc.json'),str(sch)]
t0=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,timeout=120);(ev/'native-erc.log').write_text(r.stdout+r.stderr)
x=json.loads((ev/'native-erc.json').read_text());findings=[v for sheet in x['sheets'] for v in sheet['violations']];after={p.suffix:sha(p) for p in files}
report={'command':command,'return_code':r.returncode,'elapsed_seconds':round(time.monotonic()-t0,3),'pcb_sha256':before['.kicad_pcb'],'schematic_sha256':before['.kicad_sch'],'rules_sha256':before['.kicad_pro'],'kicad_version':x['kicad_version'],'counts_by_severity':dict(collections.Counter(v['severity'] for v in findings)),'counts_by_type':dict(collections.Counter(v['type'] for v in findings)),'ignored_checks':x['ignored_checks'],'input_files_unchanged':before==after,'warnings':findings,'errors':sum(v['severity']=='error' for v in findings)}
(ev/'native-erc-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['warnings','ignored_checks']},indent=2));assert before==after,'ERC changed native source';assert not report['errors'],'Native ERC has error-severity findings'
