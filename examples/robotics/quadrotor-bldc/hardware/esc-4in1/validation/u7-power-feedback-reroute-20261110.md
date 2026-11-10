# OpenESC U7 physical pad and multi-layer routing rework — engineering review

Date: 2026-11-10. Source: full six-layer KiCad 10 board in this folder.

**Result:** U7 AT32F421 physical pads 8 (PA2), 23 (PA15), 24 (PB3)
restored, each isolated on its own schematic-correct NC net. No copper
physical DRC failures or unrouted items under the native KiCad project
rules. The remaining six missing physical package pads are on U2 and U5.

## Exact circuit-level edits

U7 resides on B.Cu. The following motor-control and supply circuits
crossed the previously omitted pad positions:

- **+3V3 supply**: replaced the crossing B.Cu route with two 0.40 mm
  diameter / 0.20 mm drill B.Cu–In4.Cu blind microvias at
  (70.71,48.1198) and (70.4,51.05) mm, one within C61 0402 +3V3
  solder pad. Connected these on In4.Cu by 0.2 mm trace.
  Removed the original +3V3 through via at (70.735714,48.352517).
  Replaced the previous **0.8 mm wide In2.Cu +3V3 spur** with a
  **0.3 mm wide In4.Cu trace** from the new lower microvia to the
  existing +3V3 power via at (75.15,50.344861) mm.
  An explicit current-carrying/power-integrity review is required:
  native DRC does not qualify a reduced-width supply trace.
- **GND return**: added two B.Cu–In4.Cu blind microvias at
  (71.35,48.1198) in the C61 ground pad and (71.92,50.20) mm in
  U7 thermal ground pad. A 0.2 mm In4.Cu segment connects the pair.
  The prior B.Cu ground track passing under NC pin24 was removed.
- **Analog current feedback (ESC3/FBCOMMON)**: restored U7 pin8 and
  removed the four conflicting B.Cu feedback segments. Added a
  0.35 mm diameter / 0.20 mm drill B.Cu–In4.Cu microvia
  at (73.67,52.05) mm, and a 0.40 mm diameter / 0.20 mm drill
  B.Cu–In4.Cu microvia at (73.9,53.509117) mm; connected them
  with a 0.2 mm In4.Cu trace, retaining endpoint connectivity.
  The 0.35 mm microvia has a very narrow annular ring and
  requires special manufacturer qualification.
- **Motor phase A return**: moved the existing ESC3/MotorA through
  via from (73.30,52.72) to (73.32,52.72) mm, a **20-micrometer**
  shift required to clear the U7 pad8. Native DRC checks continuity,
  but the phase current path and local copper remain subject to
  high-current/thermal inspection.

Every restored NC pad remains electrically isolated from GND,
power and motor phase signals.

## Native DRC and net/pad/footprint audit

| Measurement | Prior published PCB | This candidate |
|---|---:|---:|
| Physical missing NC pads | 9 | **6** |
| Footprint-library mismatches | 3 | **2** |
| Schematic parity findings | 9 | **6** |
| Physical DRC shorting/clearance violations | 0 | **0** |
| Unconnected items | 0 | **0** |
| PCB physical footprints | 222 | 222 |
| Track and via items | 2,920 | 2,916 |
| Via objects | 1,703 | 1,708 |
| Original routed nets | 195 | 195 |
| Isolated NC net entries | 7 | 10 |
| Blind B.Cu–In4.Cu microvias | 1 | **7** |

All seven blind microvias are identifiable in the native KiCad board.
Native KiCad 10 full DRC + parity on the **full project**, with pinned
local libraries, shows exactly two footprint-library mismatches (U2/U5)
and six absent-pad parity findings. All other physical DRC categories
are zero.

Original schematic ERC remains at **352 inherited findings**. Four-motor
AM32 firmware, physical gate-driver current, thermal and drone flight
have not been tested. A DRC-clean board is not an approved product.

## Manufacturing qualification REQUIRED

This revised board contains seven B.Cu–In4.Cu blind microvias,
including via-in-pad in 0402 SMD capacitors, current-feedback pin
footprints and thermal pads. **Do not use ordinary six-layer PCB
fabrication without a manufacturer-confirmed build profile.**
Specifically approve the blind via layer-pair, sequential lamination,
drill tooling, minimum annular ring, laser-drill aspect ratio,
via filling/cap plating, solder mask/paste, x-ray inspection,
current density, EMI, return current and PCBA assembly process.
The native Excellon blind-drill file must be checked against all
seven microvia sites.

The fabricated board should not be populated or powered until
these gates and the remaining 6 NC pads and 352 inherited ERC
issues are resolved. All Gerbers and drill exports retain the
REVIEW-ONLY designation.

## Rejected route candidates

- Direct restoration of the U7 upper NC pads produced clearance
  failures against +3V3 and adjacent via.
- An unmodified supply through via collided with GND pads of the
  4.7 uF bulk capacitor bank.
- Through-via replacements below capacitors produced new drill
  clearance conflicts.
- A feedback B.Cu dogleg collided with ESC3/MotorA copper;
  a direct blind via was 0.0049 mm below clearance to ESC3/FBA,
  corrected with a 30-micrometer lateral adjustment.
- The phase A via required a small, independently DRC-tested
  physical position adjustment to clear U7 NC pad8.
