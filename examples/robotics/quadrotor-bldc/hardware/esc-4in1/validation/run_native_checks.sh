#!/usr/bin/env bash
# Native checks of this source, not a manufacturing approval.
set -euo pipefail
D="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e XDG_CONFIG_HOME=/tmp/kicad-config -e XDG_CACHE_HOME=/tmp/kicad-cache -v "$D":/work -w /work kicad/kicad:10.0 sh -eu -c '
 mkdir -p /tmp/kicad-config/kicad/10.0
 cp /usr/share/kicad/template/sym-lib-table /usr/share/kicad/template/fp-lib-table /tmp/kicad-config/kicad/10.0/
 kicad-cli version
 kicad-cli sch erc -o /work/validation/erc-native-rerun.txt /work/4in1.kicad_sch
 kicad-cli pcb drc --refill-zones --schematic-parity -o /work/validation/drc-native-rerun.txt /work/4in1.kicad_pcb'
python3 - "$D/validation" <<'PY'
from pathlib import Path
import re,sys,json,hashlib,shutil,datetime
p=Path(sys.argv[1]);erc=(p/'erc-native-rerun.txt').read_text();drc=(p/'drc-native-rerun.txt').read_text()
assert not re.findall(r'^\[([^\]]+)\]',erc,re.M),erc
assert not re.findall(r'^\[([^\]]+)\]',drc,re.M),drc
assert 'ERC messages: 0  Errors 0  Warnings 0' in erc
assert 'Found 0 DRC violations' in drc and 'Found 0 unconnected pads' in drc and 'Found 0 Footprint errors' in drc
root=p.parent
for name in ['erc','drc']:
 shutil.copy2(p/(name+'-native-rerun.txt'),p/(name+'-final.txt'))
 shutil.copy2(p/(name+'-native-rerun.txt'),p/'20261111'/(name+'-final.txt'))
paths=[root/x for x in ['4in1.kicad_pcb','4in1.kicad_pro','4in1.kicad_dru','4in1.kicad_sch','ESC.kicad_sch','sym-lib-table','fp-lib-table']]
paths+=sorted((root/'reviewed-symbols').glob('*.kicad_sym'))+sorted((root/'reviewed-footprints.pretty').glob('*.kicad_mod'))
evidence={'tool':'KiCad 10.0.8 native CLI','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'erc_errors':0,'erc_warnings':0,'drc_findings':0,'unconnected':0,'parity_findings':0,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},'limits':['Inherited ignored rule categories remain listed in native reports.','No transient, thermal, current-density, AM32 or flight proof.']}
(p/'20261111/native-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('PASS: native ERC 0/0, DRC 0, unconnected 0, parity 0. No transient, thermal or flight proof.')
PY
