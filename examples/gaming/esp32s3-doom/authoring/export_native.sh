#!/usr/bin/env bash
# Recreate native manufacturing exports from the reviewed routed KiCad project.
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$package_dir"
bash authoring/verify_native.sh
mkdir -p manufacturing/gerbers mechanical/inputs validation/renders
kicad-cli sch export netlist --format kicadxml -o manufacturing/doom-carrier.net.xml electronics/doom-carrier.kicad_sch
kicad-cli sch export pdf -o manufacturing/doom-carrier-schematic.pdf electronics/doom-carrier.kicad_sch
kicad-cli pcb export gerbers -o manufacturing/gerbers/ -l F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts electronics/doom-carrier.kicad_pcb
kicad-cli pcb export drill --format excellon --generate-map --map-format pdf -o manufacturing/gerbers/ electronics/doom-carrier.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --side both -o manufacturing/positions.csv electronics/doom-carrier.kicad_pcb
kicad-cli pcb export step --force --board-only --user-origin 0x0mm -o mechanical/inputs/doom-carrier-board.step electronics/doom-carrier.kicad_pcb
kicad-cli pcb export pdf --scale 0 -o manufacturing/doom-carrier-layout.pdf -l F.Cu,B.Cu,F.Silkscreen,Edge.Cuts electronics/doom-carrier.kicad_pcb
kicad-cli pcb render --width 1600 --height 1200 --quality high --background opaque --perspective --rotate "325,0,25" -o validation/renders/doom-carrier-native-3d.png electronics/doom-carrier.kicad_pcb
pdftoppm -f 1 -singlefile -scale-to 2000 -png manufacturing/doom-carrier-schematic.pdf validation/renders/doom-schematic
pdftoppm -f 1 -singlefile -scale-to 1800 -png manufacturing/doom-carrier-layout.pdf validation/renders/doom-layout
# Re-evaluate/export mechanical/doom-desktop.kcad.ts if the native board changes.
