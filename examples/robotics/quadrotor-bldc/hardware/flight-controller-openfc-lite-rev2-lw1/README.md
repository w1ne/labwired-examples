# OpenFC-Lite revision 2-LW1 — review candidate

This is an editable, separately versioned repair of the pinned OpenFC-Lite
revision 2. It is **not a manufacturing release or a native firmware acceptance**.
The original submodule remains unchanged at
`def4ab29a5af430551aa15756b747e9ad6d4c480`.

The candidate passes the configured KiCad 10.0.8 physical DRC with **zero
errors and zero unconnected items**. One original physical omission remains:
Card1 DAT1 pad 8 has no PCB copper. Its parity warning is retained. ERC has
zero active errors after one exact, source-backed exclusion for the unused
LP5912 PG pin connected to ground. All design rules and ERC severities are
unchanged.

[Editable PCB](hardware/OpenFC.kicad_pcb) ·
[Editable schematic](hardware/OpenFC.kicad_sch) ·
[Seven-sheet review PDF](validation/schematic-rev2-lw1.pdf) ·
[Immutable source and result manifest](source-and-validation.json)

## Changes

| Item | Change and reason | Preserved contract |
| --- | --- | --- |
| U9 BMI270 | Disconnect ASDx/ASCx, physical pads 2/3, from GND in the schematic and PCB. Remove the single GND via that touched both pads and refill the zones. | The two existing copper pads remain; all other physical net assignments are unchanged. |
| U10 SN74LVC1G3157DTBR | Use the separately named TI DTB0006A Rev C land-pattern example, extracted from TI's mask and paste vectors. Reroute the six local connections and move C38 by 0.30 mm to accommodate that geometry. | Body pose, physical pin identities, source 3D model, existing net names, minimum clearance and via rules remain. |
| Original hole-clearance errors | Move J15, J28 and J54 by the recorded small offsets and update their same-net leads. | Pad shapes, contact identities and board outline remain. |
| Four omitted pads | Restore USB1 A8/B8 and LP5912 U7/U15 pad 2 from their existing footprint-library templates. Move one GND via by 0.1393 mm to clear USB1 A8. | The new pads are isolated NC contacts. No signal or supply is added. |
| Pin and part annotations | Correct U2 GPIO11 to bidirectional, U15 OUT to power output, U7 physical PG3/GND5 identity, Q1/Q2 manufacturer to ALLPOWER, and the U15 500 mA heading. Copy missing PCB MPN/manufacturer fields from the original schematic. | No passive component is retyped as a power source. Part numbers and existing connections remain. |
| ERC intent | Add seven PWR_FLAG symbols only at reviewed external entries or regulator/inductor/diode source paths. Add one exact PG-to-GND exclusion with its TI reference. | The importer ignores these annotations as electrical sources. The unpowered circuit still refuses the actual battery-input net. |
| Revision identity | Date all seven copied sheets 2026-11-12 and label them 2-LW1. | Upstream revision 2 remains available unchanged. |

The LP5912 NC restorations use the existing source/KiCad pattern: 0.375 ×
0.4 mm pads at x = ±0.8875 mm. TI's separate example uses different dimensions.
This repair does not claim that the source pattern is TI's land-pattern
example. U10's new footprint is explicitly a TI example extraction and is
recorded separately.

## Manufacturer evidence

Bosch's [BMI270 datasheet BST-BMI270-DS000-08](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf),
page 135, states for the auxiliary pins: **“Do not connect to GND.”**
The original board assigned both pads to GND and one GND via physically
contacted both. The final read-only KiCad shape test checks each restored
or corrected NC pad against all pads, tracks, vias and filled copper on its
copper layer. All six tested pads have zero contacts.

TI's [SN74LVC1G3157 datasheet SCES424O](https://www.ti.com/lit/ds/symlink/sn74lvc1g3157.pdf),
pages 54–55, provides the DTB0006A example mask and paste geometry used for
U10. The extraction retains the polygon contours, rounded corners, 0.1 mm
primitive stroke, separate paste apertures and 0.01 mm anchors. This provides
a nominal 0.10 mm copper gap against the existing 0.09 mm rule. The footprint
is not approximated by pad rectangles.

TI's [LP5912 datasheet SNVSA77D](https://www.ti.com/lit/ds/symlink/lp5912.pdf),
section 6, identifies PG as pad 3 and GND as pad 5. Section 8.3.6 permits an
unused PG pin to be grounded or left floating. The source connects both
pads to GND. The repaired symbol has the correct identity and open-collector
annotation. KiCad's generic rule still flags that explicitly permitted
connection against the GND PWR_FLAG. Only that marker's two pin UUIDs and
sheet paths are excluded; the reason and PDF hash are stored in the project
and [exclusion receipt](validation/documented-pg-erc-exclusion.json).

PDF hashes, source-library hashes and exact geometry changes are preserved
in the manifest and per-change receipts. These checks do not qualify solder
processes, current capacity, signal integrity, thermal behavior or production
yield.

## Observed checks

| KiCad 10.0.8 check | Pinned source | Revision 2-LW1 |
| --- | ---: | ---: |
| Physical DRC errors | 5: four hole-clearance, one copper-clearance | 0 |
| Physical DRC warnings | 11 | 5 |
| Unconnected PCB items | 0 | 0 |
| Schematic/PCB parity warnings | 17 | 1: Card1 DAT1 pad 8 omitted |
| Active ERC errors | 9: eight supply declarations, one input-driver declaration | 0 |
| ERC warnings | 182 | 178 |
| Exact documented ERC exclusions | 0 | 1: unused U7 PG3 grounded |

The five final physical warnings are four preserved source/library footprint
mismatches and the original non-mirrored `B = SIGNAL` annotation outside the
board. The 178 ERC warnings are retained; this repair does not reclassify
unknown pin roles or change the global pin-compatibility matrix to clear them.
The installed environment substitutes DejaVu for the unavailable Tokyo font.

The final board has **164 footprints and 583 pad objects**, up from 579 pad
objects. Its 19 zones were refilled with the original rules. All 445
schematic electrical endpoints remain. Only U9 pads 2/3 change their net
assignment. The six U10 pads each retain an actual same-net track contact.
See [native PCB proof](validation/final-pcb-connectivity-proof.json) and
[schematic endpoint proof](validation/schematic-connectivity-proof.json).

The actual app importer produces the same 160-part, 82-net graph before and
after the ERC flags and symbol annotations. Diagram, resolved nets, mapping,
compiler result and lowerer result are identical. The source-free import
still fails with `PWR_RAIL_UNDRIVEN` on `net@C22:1`, which contains the real
P1/J29 battery input and U6/U16 input rails. This proves that ERC annotations
cannot create an ideal battery or regulator supply. It does **not** prove a
powered native boot or qualify the RP2354B internal buck regulator.

## Remaining physical omission

Card1 DAT1 pad 8 is present in the schematic as an unused contact and in the
source footprint library, but absent from the native PCB. The exact 0.7 ×
1.6 mm library pad overlaps three existing power vias and approaches a USB
D− via and a GND via. A bounded same-net reroute was tested; it intersected
adjacent USB/DVDD/IOVDD escape routing. Those trial power and signal edits
were completely reverted. The accepted board retains the original omission
and its parity warning. No pad was shrunk and no rule or parity exclusion
was added to conceal it.

The rejected-candidate DRC reports remain in `validation/` as evidence of this
limit. They are **not** the final board reports. A broader connector/power/USB
escape redesign and its signal-integrity review remain required before
calling the copied board complete.

The existing populated KernelCAD revision 4 uses earlier board geometry.
Its fit receipt cannot qualify the moved components or changed copper in
2-LW1. This candidate also does not establish native sensor startup,
Betaflight arming, ESC operation, flight control or physical power-on.

## Model availability at review

The [model inventory](validation/model-resolution-inventory.json) records
107 enabled source model references. Eleven references resolve to ten cached
upstream files; each file matches its exact Git blob at the pinned upstream
commit. The environment lacks 17 standard KiCad STEP files used by 96 other
references. The 57 footprints without models are 53 solder contacts and four
testpoints. The committed hardware refers to the original pinned model
library through relative links; initialize that submodule to resolve them.

All source model paths, offsets and rotations remain unchanged. The native
inductor entries reference generic Murata/Changjiang package models. Their
presence does not establish manufacturer-specific dimensions. Root assembly
work must resolve and inspect the missing models and verify the newly moved
parts before claiming a populated FC fit.

## Reproduce

1. Initialize the original pinned source and its libraries:
   `git submodule update --init --recursive examples/robotics/quadrotor-bldc/hardware/flight-controller-openfc-lite`.
   The two relative library/model links in this copy refer to that source.
2. Use KiCad 10.0.8 with its standard symbol/footprint libraries and the project
   tables. Run `validation/run_native_checks.sh` with an output directory.
   The script does not edit or refill the board; it audits the committed fill.
3. Run the read-only `validation/verify_pcb.py` with KiCad's `pcbnew` Python
   environment, the pinned original board, the copied board, and an output
   receipt path. It compares pad identities, nets, geometry changes and direct
   NC copper contacts, and verifies the single allowed project-metadata delta.
4. To repeat app import checks, set `LABWIRED_APP_ROOT` to the reviewed app
   checkout listed in the manifest. Run `node --import tsx
   validation/audit_import.mjs INPUT.net OUTPUT.json` from that app checkout.
   Compare the recorded before-annotation and final netlists. The exact app
   source and generated metadata are required; an older released catalog
   cannot reproduce this onboarding result.
5. Run the repository's `python3 -m unittest discover -s scripts -p
   'test_*.py' -v` integrity suite. These tests verify archived source/evidence
   consistency; they do not substitute for KiCad or a physical test.

## Source and licence

The copied hardware derives from
[OpenDrone-hw/OpenFC-Lite](https://github.com/OpenDrone-hw/OpenFC-Lite/tree/def4ab29a5af430551aa15756b747e9ad6d4c480).
It remains under the upstream **CERN-OHL-S-2.0** licence, reproduced in
[LICENSE](LICENSE). The enclosing examples repository's general MIT notice
does not replace that hardware licence. This directory is a LabWired repair
candidate, not an upstream release or manufacturer endorsement. The editable
source, explicit changes and verification records accompany the copy.
