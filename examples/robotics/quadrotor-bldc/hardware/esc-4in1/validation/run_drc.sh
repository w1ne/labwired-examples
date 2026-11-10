#!/usr/bin/env bash
# Native KiCad 10 DRC review gate. This is not manufacturing approval.
set -euo pipefail
D="$(cd "$(dirname "$0")/.." && pwd)"
NAME="drc-native-rerun.txt"
if [ "$#" -gt 0 ]; then NAME="$1"; fi
docker run --rm --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e XDG_CACHE_HOME=/tmp/kicad-cache \
  -e XDG_CONFIG_HOME=/tmp/kicad-config \
  -v "$D":/work -w /work kicad/kicad:10.0 \
  kicad-cli pcb drc --refill-zones --schematic-parity \
  -o "/work/validation/$NAME" /work/4in1.kicad_pcb
python3 - "$D/validation/$NAME" <<'PY'
import collections,re,sys
s=open(sys.argv[1]).read()
c=collections.Counter(re.findall(r'^\[([^\]]+)\]',s,re.M))
print('KiCad native report:',dict(c))
expected={'lib_footprint_mismatch':2,'net_conflict':6}
if dict(c)!=expected:
    raise SystemExit('DRC result changed; review all new findings.')
print('No physical shorts, clearance errors or unrouted connections.')
print('NOT FABRICATION APPROVED: 6 missing MCU pads and inherited ERC.')
PY
