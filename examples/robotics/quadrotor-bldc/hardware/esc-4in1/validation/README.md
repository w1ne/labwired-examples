# Native electrical and layout review — 2026-11-11

Current source: KiCad 10.0.8 ERC 0 errors / 0 warnings; DRC 0 findings;
0 unconnected pads and 0 schematic parity findings. These are source/rule
checks, not powered-hardware acceptance.

## Evidence

- 222 footprints, 1,067 pad objects, 213 SMT placements.
- 210 physical net memberships preserved exactly from the prior schematic.
- 2,914 tracks/vias, 1,716 vias, 15 blind In4.Cu/B.Cu microvias.
- `drc-final.txt`, `erc-final.txt`: current native reports.
- `20261111/board-inventory.json`: native counts and outline bounds.
- `20261111/netlist-equivalence.json`: unchanged physical connectivity.
- `20261111/symbol-type-changes.json`: 119 corrected electrical pin types.
- `20261111/power-source-declarations.json`: 31 source flags and reasons.
- `20261111/labwired-import-coverage.json`: actual hosted import response.
- `20261111/historical-*`: superseded Nov 10 reports and review notes.

No ERC or DRC severity was disabled. Native reports preserve the inherited
ignored categories. The drawing's connection grid is 25 mil (0.635 mm).

## Electrical source review

Pin types use the pinned manufacturer datasheets in `KiCad-Library/datasheet`:
`AT32F421.pdf`, `NSG2065Q.pdf` Table 7-1, `LMR54406.pdf` Table 5-1,
`TLV76733DRVR.pdf` Table 5-1 and `INA186A3IDCKR.pdf` pin functions.
Frozen source libraries preserve symbol drawings and pin numbers. Custom
footprints are frozen from the actual PCB; geometry and pad nets are preserved.

Power flags identify known sources across connectors, the buck inductor,
analog RC filters, the NSG2065Q internal bootstrap diodes and MOSFET bridge
switch nodes. They do not prove bootstrap charge, switching deadtime, correct
voltage, startup, sag, inrush or fault protection. All physical ref/pin net
memberships are unchanged.

## Simulation gap

The generic importer accepts 222 components and 210 nets with zero dropped
pin endpoints. It maps 176 passive parts and retains 46 inert parts: 37
unsupported functional items plus 9 connector/test-point items. It reports
`design_only`, `twin_buildable: false`. Unsupported MOSFETs currently appear
under `bjt` and the U14 inductor under `ic`; raw evidence preserves these
classification limitations. No substitute MCU was added to obtain a pass.

The separate four-channel STM32L476/24 V six-step motor demo does not run
this AT32F421/4S AM32 circuit. Thermal, current-density, EMC, battery,
MOSFET transient, propeller load and physical flight evidence remain absent.
The manufacturer must approve the 15 blind microvias and via-in-pad process.

Run `bash run_native_checks.sh` to regenerate both native reports.
