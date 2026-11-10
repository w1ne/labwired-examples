# OpenESC U5 AT32F421 package NC-pad and analog/power rerouting

Date: 2026-11-10. Six-layer KiCad 10.0.8 native board. This is an
electrical geometry review, NOT an approved manufacturing design.

## Exact changes

- U5 physical QFN pads 8 (PA2), 23 (PA15), 24 (PB3) restored from the
  original pinned footprint. Each is on its own disconnected KiCad
  NC net, matching the schematic. It must not be solder-connected to
  +3V3, GND or ESC current feedback.
- Crossing GND and +3V3 B.Cu traces under the two U5 southern pins
  removed. U5 lower rail connection was rerouted over In4.Cu
  using two blind B.Cu–In4.Cu vias at (79.99,42.4101) mm GND
  inside C55 capacitor ground pad and (80.63,42.4101) mm +3V3
  inside C55 capacitor +3V3 pad, both 0.40 mm diameter, 0.20 mm drill.
  In4 routes connect these to existing GND and +3V3 through-vias
  at (79.67,39.32) and (80.7702,40.6299) mm, respectively.
- For U5 pin8, removed six conflicting or unused B.Cu trace segments
  in /ESC2/FBCOMMON current-sense feedback and +3V3. New feedback
  route uses 0.35 mm and 0.40 mm diameter blind B.Cu–In4.Cu
  microvias at (77.88,38.46) and (77.5,36.99) mm with a 0.20 mm
  In4 copper dogleg through (77.35,38.10) mm, avoiding the
  existing ESC2/MotorA phase via at (77.95,37.83) mm.
- Removed an unused 0.502 mm B.Cu feedback stub after the
  In4 transition was verified. No physical motor phase via
  placement was changed in this revision.

This is one of four independently controlled ESC motor channels.
It is NOT simulation of actual AM32 firmware or gate-driver switching.

## Native KiCad 10 comparison

| Physical check | Main before | This revision |
|---|---:|---:|
| Missing physical NC package pads | 6 | **3** |
| Footprint library mismatch | 2 | **1 (U2)** |
| Schematic parity mismatches | 6 | **3 (U2)** |
| Copper shorts | 0 | 0 |
| Clearance/hole failures | 0 | 0 |
| Unrouted items | 0 | 0 |
| Dangling tracks | 0 | 0 |
| Physical footprints | 222 | 222 |
| Physical track/via items | 2,916 | **2,915** |
| Via objects | 1,708 | **1,712** |
| Named net entries incl. isolated NC | 205 | **208** |
| Blind B.Cu–In4.Cu microvias | 7 | **11** |

The original 195 motor/power/feedback routed net names remain.
The parts list remains 213 populated SMDs and 222 physical footprints.
The separately generated blind-layer drill should list exactly
eleven holes in the 5-to-6 blind drill category.

## Manufacturing and verification restrictions

Four additional B.Cu/In4.Cu blind microvias appear in this revision,
including vias under a 0402 capacitor and under an MCU current-
feedback pin. Microvia annular margin, laminate sequence, plating,
via filling/capping, paste mask and solder wicking require an
explicitly qualified fabricator. The 0.35 mm via diameter / 0.20 mm
drill is a demanding process limit. Power rail current density,
analog input noise, return-plane integrity and ESC heat spreading
require bench verification and calculation before accepting this
routing as equivalent to the manufacturer's original design.

The source schematic **still has 352 inherited ERC findings**.
Three MCU pads on U2 remain omitted. The board is not ready for
fabrication, initial power application or flight testing.
The available Gerber ZIP is **REVIEW ONLY**.
