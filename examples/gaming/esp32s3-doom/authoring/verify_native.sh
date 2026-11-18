#!/usr/bin/env bash
# Run in an installed KiCad 10 environment. The accepted source is not changed.
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-$package_dir/validation/recheck}"
mkdir -p "$output_dir"
case "$(kicad-cli version)" in 10.*) ;; *) printf '%s\n' 'KiCad 10 is required.' >&2; exit 2 ;; esac
kicad-cli sch erc --format json --severity-all --exit-code-violations \
  -o "$output_dir/erc.json" "$package_dir/electronics/doom-carrier.kicad_sch"
kicad-cli pcb drc --format json --severity-all --schematic-parity --refill-zones \
  --exit-code-violations -o "$output_dir/drc.json" "$package_dir/electronics/doom-carrier.kicad_pcb"
