#!/usr/bin/python3
"""Reproduce the accepted native A1 board from the fixed routing exchange input.

Each patch uses KiCad's native board model. The acceptance gate is a new KiCad
DRC run and a pad/footprint/rules audit. New object UUIDs can differ between
runs; geometry, electrical contract and DRC acceptance must agree.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
ap=argparse.ArgumentParser();ap.add_argument('--routing-base',required=True);ap.add_argument('--baseline',required=True);ap.add_argument('--models-dir',required=True);ap.add_argument('--output-dir',required=True);args=ap.parse_args()
scripts=Path(__file__).resolve().parent;dest=Path(args.output_dir).resolve();work=dest/'intermediate';source=dest/'source';evidence=dest/'evidence'
for d in [work,source,evidence]:d.mkdir(parents=True,exist_ok=True)
models=source/'models';models.mkdir(exist_ok=True)
for f in Path(args.models_dir).glob('*.step'):shutil.copy2(f,models/f.name)
commands=[]
def run(script,*argv):
 cmd=[sys.executable,str(scripts/script),*[str(a) for a in argv]];commands.append(cmd)
 with (evidence/(script.removesuffix('.py')+'.log')).open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
first=work/'01-end-z-and-e-step.kicad_pcb';usb=work/'02-usb-escape.kicad_pcb';i2c=work/'03-i2c-escape.kicad_pcb';vdda=work/'04-vdda.kicad_pcb';straps=work/'05-fullstep.kicad_pcb';topology=work/'06-fan-led.kicad_pcb';mechanical=work/'07-mechanical.kicad_pcb';native=source/'a1-printcore.kicad_pcb'
run('close_end_z_and_e_step.py',args.routing_base,first)
run('apply_usb_escape.py',first,usb)
run('apply_i2c_escape.py',usb,i2c)
run('apply_vdda_supply.py',i2c,vdda,'--footprint-lib',Path(args.routing_base).resolve().parent/'Capacitor_SMD.pretty')
run('apply_fullstep_straps_resolved.py',vdda,straps)
run('apply_fan_led_topology.py',straps,topology)
run('apply_mechanical_patch.py',topology,mechanical,'--models-dir',models,'--model-prefix','${KIPRJMOD}/models')
shutil.copy2(topology.with_suffix('.kicad_pro'),mechanical.with_suffix('.kicad_pro'))
run('finalize_native.py',mechanical,native,'--evidence',evidence)
run('audit_native.py',args.baseline,native,'--evidence',evidence,'--require-clean')
report={'routing_input_sha256':hashlib.sha256(Path(args.routing_base).read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(Path(args.baseline).read_bytes()).hexdigest(),'final_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'commands':commands,'pass':True}
(evidence/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'native':str(native),'sha256':report['final_sha256'],'pass':True},indent=2))
