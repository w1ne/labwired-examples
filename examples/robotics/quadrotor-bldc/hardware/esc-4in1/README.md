# Four-channel ESC: real routed PCB, open-hardware derivative

This is a KiCad 10 source-level derivative of the OpenDrone OpenESC-30x30
project, under CERN-OHL-S-2.0 (the upstream hardware license).
Source: https://github.com/OpenDrone-hw/OpenESC-30x30
Commit: bf306934b5decc130ab1df6b653563ea16165e8e.
The shared KiCad library submodule is pinned at
fdf8319b3512925a7566532ae4b38a298cf54c24.

This is a *physical* six-layer motor-control PCB, not a rendering. Its
four AT32F421G8U7 controllers drive four NSG2065Q half-bridge drivers and
24 SP40N01GHNK MOSFETs. It has a 2S–8S battery input, four independent
three-phase motor connections, four DShot inputs, and common battery-current
sensing. The manufacturer documents AM32-compatible control firmware.

## Editable hardware

- 4in1.kicad_sch: complete top-level schematic with 49 additional 4.7 uF
  capacitors (originally only on the PCB), each wired to +BATT and GND.
- ESC.kicad_sch: complete repeated one-motor controller and gate driver.
- 4in1.kicad_pcb: routed 6-layer board, 222 uniquely numbered footprints,
  195 original routed nets plus 10 isolated NC pin identities (205 named nets);
  2,916 routing items, including 1,708 vias.
- 4in1.kicad_pro, 4in1.kicad_dru: original manufacturer PCB rule settings.
- Local footprints, 3D shapes and symbols plus pinned KiCad-Library submodule.
- board-only-caps.csv: mapping of the 49 originally duplicate designators
  to C501–C549. The total board has 52 × 4.7 uF bulk ceramic capacitors.
- fabrication-review: plotted six-layer Gerbers, drill, SVGs,
  schematic netlist, placement and BOM data for design review only.

## Changes from upstream

1. 49 formerly PCB-only bulk capacitors now have unique references C501–C549.
2. The root schematic contains their symbols, 98 power wires, and +BATT/GND
   connections. They are linked to the existing footprints by symbol UUID.
3. 154 existing manufacturer properties and 47 additional board-only
   manufacturer/MPN fields were synchronized to the schematic.
4. KiCad 10 libraries were configured to resolve legacy footprint and
   symbol aliases. The copied board outline footprint was synchronized.
5. A first KiCad-checked revision restored U6 pins 5/7 and U10 pins
   5/7/8, removing one overlapping GND track and two GND stitching vias.
6. The U9 revision restored U9 AT32F421 pins 23/24, rerouting GND
   on In1.Cu and +3V3 on In4.Cu with blind microvia/via-in-pad.
   See [the U9 engineering review](validation/u9-power-reroute-20261110.md).
7. This revision restores all three U7 AT32F421 missing NC pins 8/23/24,
   rerouting +3V3, GND and analog FBCOMMON on In4.Cu. The narrower +3V3
   routing, high-density blind microvias, and a 20-micrometer motor-phase
   via move require fab, current-density and thermal review. See
   [the U7 review](validation/u7-power-feedback-reroute-20261110.md).

## Current verification (review-only)

Original copper is fully routed: 0 unconnected items, and no currently
reported copper shorts under the supplied project rules. However,
native KiCad DRC reports **2 package-footprint library mismatches**
(U2/U5 AT32F421) and **6 missing physical MCU pads** in schematic
parity:
- AT32F421 U2/U5: pins 8, 23, 24 are still missing.
- AT32F421 U7: pins 8/23/24 restored with full power/feedback rerouting.
- AT32F421 U9: pins 23/24 restored with six-layer rerouting.
- NSG2065Q U6 pins 5/7 and U10 pins 5/7/8 restored.

The remaining 6 are unconnected MCU pins in the schematic but omitted
from their real physical footprints. Restoring all 16 pads at once
without rerouting produced 17 shorts, so that candidate was rejected.
Native KiCad 10 reports **no physical shorts, clearance failures or
unrouted items** in this revision. Manufacturing approval remains blocked
on 7 blind microvias (including solder pad microvias), power/current-feedback
trace cross-section and return-current review, the remaining MCU pads,
and inherited electrical ERC findings.

The complete schematic ERC has 352 inherited findings (same category counts
as the original design, including pin electrical types and library issues).
See validation/README.md and the saved KiCad reports.

**Do not order, manufacture, fly, or power this board based solely on these
files.** Pending: reroute NC pad obstacles and rerun DRC/parity, electrical
ERC review, bench bring-up, thermal-current and safe-motor tests.

## Assembly

The physical board contains 222 footprints. The assembly BOM identifies
213 populated SMT components across 22 sourcing groups. U3 is an integrated
board outline/connector footprint and eight pads are test points; they are
not component placements. Every populated component has an LCSC catalog
number recorded in the design BOM; current live stock is not confirmed.

The matching full drone system, factory motors, flight controller, propellers,
battery and cabling are specified separately in ../system-bom.csv and
../assembly-wiring.md. The earlier LabWired browser demo uses one
STM32L476 reduced-order BLDC model, **not this AM32 hardware design**.
