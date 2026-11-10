# U9 AT32F421 NC-pad and +3V3/GND rework (KiCad 10, review-only)

Restored U9 pins 23 (PA15) and 24 (PB3) with real QFN package pads
and isolated unconnected net identities. The existing B.Cu +3V3/GND traces
crossed their omitted pad positions, so those traces were rerouted.

## Electrical edits

- Ground: two new through vias at (71.28, 38.46) mm (C66 GND pad)
  and (71.85, 40.53) mm (U9 exposed thermal GND pad). Both are 0.45 mm
  outside / 0.30 mm drilled. 0.20 mm In1.Cu track joins them.
- +3V3: one 0.40 mm pad / 0.20 mm drill **blind microvia** at
  (70.64, 38.46) mm, layer pair B.Cu to In4.Cu, inside C66 +3V3 pad.
  0.20 mm In4.Cu track reaches the existing +3V3 via at
  (70.28, 41.44) mm.
- Removed the two crossing +3V3 and GND B.Cu traces under pads 23/24.
  Removed the now-disconnected old +3V3 stubs and trimmed the remaining
  diagonal to its existing power via.
- Physical footprints, placement and all original motor nets remain unchanged.

## Native KiCad 10 DRC

| Finding | Previous main PCB | This revision |
|---|---:|---:|
| Missing real package pads | 11 | 9 |
| Footprint mismatches | 4 | 3 |
| Schematic parity mismatches | 11 | 9 |
| Physical shorts / clearance failures | 0 | 0 |
| Unrouted copper connections | 0 | 0 |
| Dangling copper tracks | 0 | 0 |
| PCB footprints | 222 | 222 |
| Track/via objects | 2,919 | 2,920 |
| Vias | 1,700 | 1,703 |
| Net names incl. isolated NC | 200 | 202 |

The remaining three footprint mismatches and nine missing pads
are on U2, U5 and U7 (three pads per MCU). The schematic ERC
still retains 352 inherited issues.

## Manufacturing restrictions — Do NOT order

The reviewed PCB now requires a more complex fabrication process:

- Two through vias are located inside SMD pads (C66 GND capacitor pad
  and the U9 exposed thermal ground pad).
- One blind B.Cu–In4.Cu microvia is inside the C66 0402 +3V3 pad.
- The separate blind-via drill file is named
  fabrication-review/gerbers/4in1-in4-back.drl, and is included
  in the review-only Gerber ZIP.

A qualified fabricator must approve controlled 6-layer lamination,
laser blind drilling, aspect ratio, plating, filling, cap plating,
solder mask and paste apertures. Unfilled vias in 0402 pads can
wick solder and cause poor solder joints. Native KiCad DRC passing
does not verify these process requirements.

This is a physical-connectivity improvement, NOT an approved board.
Thermal, EMI, ground return, rail impedance, firmware and motor behavior
remain unverified on physical hardware.

## Negative controls

- Direct U9 pad restoration without rerouting: two unconnected nets.
- Through-via candidates around the capacitor banks shorted existing
  motor-control and power copper.
- Initial ground-via position intersected In2.Cu motor-control and
  In3.Cu +3V3 traces; moving it to (71.85, 40.53) removed these.
- An earlier naive U9 3V3 route crossed current-sense copper.
- The accepted microvia route has native KiCad DRC evidence but still
  needs a factory process qualification.
