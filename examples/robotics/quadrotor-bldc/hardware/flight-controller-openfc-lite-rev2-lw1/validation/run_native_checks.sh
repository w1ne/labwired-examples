#!/usr/bin/env bash
set -euo pipefail
revision_dir=$(cd "$(dirname "$0")/.." && pwd)
output_dir=${1:?Usage: run_native_checks.sh OUTPUT_DIRECTORY}
mkdir -p "$output_dir"
kicad_cli=${KICAD_CLI:-kicad-cli}
"$kicad_cli" version
"$kicad_cli" sch erc --format json -o "$output_dir/erc.json" "$revision_dir/hardware/OpenFC.kicad_sch"
"$kicad_cli" pcb drc --schematic-parity --format json -o "$output_dir/drc.json" "$revision_dir/hardware/OpenFC.kicad_pcb"
"$kicad_cli" sch export netlist --format kicadxml -o "$output_dir/schematic.net.xml" "$revision_dir/hardware/OpenFC.kicad_sch"
python3 - "$output_dir" <<'PY'
import collections,json,sys
from pathlib import Path
out=Path(sys.argv[1]);erc=json.loads((out/'erc.json').read_text());drc=json.loads((out/'drc.json').read_text());ev=[v for s in erc['sheets'] for v in s['violations']]
summary={'erc':dict(collections.Counter(v['severity'] for v in ev)),'drc':dict(collections.Counter(v['severity'] for v in drc['violations'])),'unconnected':len(drc['unconnected_items']),'parity':drc['schematic_parity']}
print(json.dumps(summary,indent=2))
assert all(v['severity']!='error' for v in ev)
assert all(v['severity']!='error' for v in drc['violations'])
assert not drc['unconnected_items']
assert len(drc['schematic_parity'])==1
assert drc['schematic_parity'][0]['description']=='No pad found for pin 8 in schematic'
assert drc['schematic_parity'][0]['items'][0]['description']=='Footprint Card1'
PY
