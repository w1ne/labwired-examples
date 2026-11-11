# OpenESC quadrotor electrical and PCB source

The current KiCad 10 source passes native ERC, DRC and schematic-to-PCB parity.
This physical AT32F421/AM32 ESC remains separate from LabWired's runnable
STM32L476 reduced-order motor demonstration.

## Source and hardware

Derivative of [OpenDrone OpenESC-30x30](https://github.com/OpenDrone-hw/OpenESC-30x30),
commit `bf306934b5decc130ab1df6b653563ea16165e8e`, under CERN-OHL-S-2.0.
The manufacturer library is pinned at `fdf8319b3512925a7566532ae4b38a298cf54c24`.
Four AT32F421G8U7 MCUs drive four NSG2065Q gate drivers and 24 SP40N01GHNK
MOSFETs. The selected drone uses 4S LiPo: 14.8 V nominal, 16.8 V fully charged.
The PCB regulator rails are +10V and +3V3. A 24 V STM32 motor plant is not
the electrical equivalent of this hardware.

## Native results — 2026-11-11

| Check | Result |
|---|---:|
| Physical footprints | 222 |
| Physical pad objects | 1,067 |
| Populated SMT placements | 213 |
| Exact schematic nets | 210 |
| Track and via objects | 2,914 |
| Vias, including blind microvias | 1,716 |
| Blind In4.Cu to B.Cu microvias | 15 |
| KiCad 10.0.8 ERC errors / warnings | 0 / 0 |
| DRC findings / unconnected / schematic parity | 0 / 0 / 0 |

All 210 physical net memberships match the prior schematic exactly. No rule
severity was disabled. The reports list inherited ignored rule categories.

## Repairs

All 16 originally omitted physical MCU/driver pads are now present. The last
three U2 pads (8/23/24) are isolated from former overlapping copper through
four new blind microvias and In4.Cu routing. The prior 1,064-pad source still
omitted these three pads; the corrected source has 1,067 pads.

Local frozen source libraries provide 119 datasheet-backed pin-type corrections.
Capacitors and connectors no longer pretend to be input pins or power sources.
Thirty-one explicit power declarations represent the battery feed, buck output
after its inductor, filtered analog rails, internal bootstrap diodes and switched
phase references. They describe source paths; they do not validate voltage,
startup, bootstrap refresh or protection behavior. Two custom footprints are
frozen from their exact PCB shapes. The existing drawing uses a 25 mil connection
grid, and phase labels now match their hierarchical port names.

## Files and reproduction

- `4in1.kicad_sch`, `ESC.kicad_sch`: complete five-sheet electrical source.
- `4in1.kicad_pcb`, `.kicad_pro`, `.kicad_dru`: native routed board and rules.
- `reviewed-symbols/`, `reviewed-footprints.pretty/`: local source libraries.
- `reviewed-models/`: official KiCad package models, pinned hashes and license.
- [Native review](validation/README.md), [ERC](validation/erc-final.txt),
  [DRC](validation/drc-final.txt), [netlist comparison](validation/20261111/netlist-equivalence.json).
- [Hosted import coverage](validation/20261111/labwired-import-coverage.json).
- `fabrication-review/esc-board-populated.step` and `.glb`: actual populated board.

Run `bash validation/run_native_checks.sh`. It uses `kicad/kicad:10.0` and fails
if ERC, DRC or parity report a finding. Review exports are not an order.

## Remaining limits

The generic LabWired import preserves all 222 components and 210 nets with zero
dropped pin endpoints. It maps 176 passive parts and keeps 46 inert parts.
The actual MCU, driver, MOSFET, regulator and current-amplifier models remain
unsupported: `design_only`, `twin_buildable: false`. The actual AM32 power stage,
battery sag, MOSFET switching, thermal behavior and aircraft flight are untested.

The factory must review the six-layer process, 15 blind microvias, via-in-pad,
trace current density and analog return paths. First-article electrical and
thermal validation remains outstanding. Do not order or power this review-only
board based solely on ERC/DRC.
