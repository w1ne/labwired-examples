#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
cd "$(dirname "$0")/../.."
pcb=electronics/input-board/input-board.kicad_pcb
sch=electronics/input-board/input-board.kicad_sch
kicad-cli sch erc --format json --exit-code-violations --output evidence/input-erc.json "$sch"
kicad-cli pcb drc --schematic-parity --format json --exit-code-violations --output evidence/input-drc.json "$pcb"
kicad-cli sch export netlist --format kicadxml --output manufacturing/input-board/input-board.net "$sch"
kicad-cli sch export pdf --output manufacturing/input-board/input-board.pdf "$sch"
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,Edge.Cuts --output manufacturing/input-board/gerbers/ "$pcb"
kicad-cli pcb export drill --format excellon --output manufacturing/input-board/gerbers/ "$pcb"
kicad-cli pcb export step --subst-models --force --output cad/input-board-populated.step "$pcb"
kicad-cli pcb export step --board-only --force --output cad/input-board-substrate.step "$pcb"
kicad-cli pcb render --width 1400 --height 1100 --side top --rotate 325,0,35 --background opaque --quality high --output cad/input-board-iso.png "$pcb"
