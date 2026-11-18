# OpenFC-Lite revision 2-LW1 — review candidate

This is an editable, separately versioned repair of the pinned OpenFC-Lite
revision 2. It is **not a manufacturing release or a native firmware acceptance**.
The original submodule remains unchanged at
`def4ab29a5af430551aa15756b747e9ad6d4c480`.

The candidate passes the configured KiCad 10.0.8 physical DRC with **zero
errors or warnings, zero unconnected items and zero schematic/PCB parity differences**.
The original omission of Card1 DAT1 pad 8 is repaired with the exact library
pad. ERC has
zero active errors or warnings after one exact, source-backed exclusion for the unused
LP5912 PG pin connected to ground. All design rules and ERC severities are
unchanged.

[Editable PCB](hardware/OpenFC.kicad_pcb) ·
[Editable schematic](hardware/OpenFC.kicad_sch) ·
[Current seven-sheet review PDF](validation/20261118-library-cleanup/schematic.pdf) ·
[Immutable source and result manifest](source-and-validation.json)

## Changes

| Item | Change and reason | Preserved contract |
| --- | --- | --- |
| U9 BMI270 | Disconnect ASDx/ASCx, physical pads 2/3, from GND in the schematic and PCB. Remove the single GND via that touched both pads and refill the zones. | The two existing copper pads remain; all other physical net assignments are unchanged. |
| U10 SN74LVC1G3157DTBR | Use the separately named TI DTB0006A Rev C land-pattern example, extracted from TI's mask and paste vectors. Reroute the six local connections and move C38 by 0.30 mm to accommodate that geometry. | Body pose, physical pin identities, source 3D model, existing net names, minimum clearance and via rules remain. |
| Original hole-clearance errors | Move J15, J28 and J54 by the recorded small offsets and update their same-net leads. | Pad shapes, contact identities and board outline remain. |
| Card1 DAT1 pad 8 | Restore the exact 0.7 × 1.6 mm TF-PUSH library pad as an isolated NC contact. Move five through vias (two +1.1V into L1 pad 1, the D− via inside R10 pad 1, two GND vias), remove the +3.3V via under C19 and join U2.64/C19.1 to U2.60 with a 0.10 mm track inside the U2 pad ring. | No footprint moved; every other pad keeps its net and geometry; all nets remain connected. See [restoration record](validation/card1-dat1-pad-restoration.json). |
| Four omitted pads | Restore USB1 A8/B8 and LP5912 U7/U15 pad 2 from their existing footprint-library templates. Move one GND via by 0.1393 mm to clear USB1 A8. | The new pads are isolated NC contacts. No signal or supply is added. |
| Pin and part annotations | Correct U2 GPIO11 to bidirectional, U15 OUT to power output, U7 physical PG3/GND5 identity, Q1/Q2 manufacturer to ALLPOWER, and the U15 500 mA heading. Copy missing PCB MPN/manufacturer fields from the original schematic. | No passive component is retyped as a power source. Part numbers and existing connections remain. |
| ERC intent | Add seven PWR_FLAG symbols only at reviewed external entries or regulator/inductor/diode source paths. Add one exact PG-to-GND exclusion with its TI reference. | The importer ignores these annotations as electrical sources. The unpowered circuit still refuses the actual battery-input net. |
| Revision identity | Date all seven copied sheets 2026-11-12 and label them 2-LW1. | Upstream revision 2 remains available unchanged. |

The LP5912 NC restorations use the existing source/KiCad pattern: 0.375 ×
0.4 mm pads at x = ±0.8875 mm. TI's separate example uses different dimensions.
This repair does not claim that the source pattern is TI's land-pattern
example. U10's new footprint is explicitly a TI example extraction and is
recorded separately.

## Native library cleanup — 2026-11-18

The follow-up cleanup resolves the remaining 178 ERC warnings and five DRC
warnings at their native source. It preserves every routed land, drill,
track, via and filled-zone polygon from the DAT1-restored board. The
[change receipt](validation/20261118-library-cleanup/receipt.json) classifies
the original warnings and links the selected package identity.

- Define active pin directions from the RP2350, BMI270, LMR51635, LP5912,
  SN74LVC1G3157, COS8051 and TLV7031 manufacturer tables. Use passive roles
  for physical connector contacts, inductors, diodes, crystals and switches.
  Synchronize the project library and schematic caches.
- Give the existing BMI270 its own correct symbol identity. The populated
  device remains BMI270; it no longer inherits the unrelated LSM6 symbol name.
- Normalize U12 TLV7031 numbering to functional table 4-1 and the separately
  linked TI DPW0005A drawing: OUT1, VCC2, VEE3, IN−4, IN+5. Both schematic
  and footprint retain their physical terminal positions and connections.
  TI also appends DPW0005B in its current datasheet. This is documented
  A-drawing identity consistency, not evidence of a repaired physical short.
- Preserve the actual J52/J54 custom solder lands under distinct project
  footprint names. Synchronize the Card1 and USB1 definitions with the
  existing placed lands and drills. Keep U12 under its named A drawing.
- Remove one dangling no-connect marker, unify redundant net aliases and
  move the outside-board “B = SIGNAL” note from B.Cu to Cmts.User.
- Declare the filtered VREG_AVDD supply after the existing 30 Ω R12 with
  one PWR_FLAG. This is ERC intent, not a physical voltage source.

No rule severity, minimum clearance, design-rule exclusion or pin-compatibility
matrix changed. The exact pre-existing U7 PG exception remains. The project
file is byte-identical to its input. The read-only
[structural proof](validation/20261118-library-cleanup/pcb-repair.json)
checks 584 pad objects, 1,753 tracks/vias, 19 zones and 113 net partitions.
All compare equal after the documented aliases and U12 identifier map.

## Manufacturer evidence

Bosch's [BMI270 datasheet BST-BMI270-DS000-08](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf),
page 135, states for the auxiliary pins: **“Do not connect to GND.”**
The original board assigned both pads to GND and one GND via physically
contacted both. The final read-only KiCad shape test checks each restored
or corrected NC pad against all pads, tracks, vias and filled copper on its
copper layer. All seven tested pads, including restored Card1 DAT1, have zero contacts.

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

| KiCad 10.0.8 check | Pinned upstream | Initial 2-LW1 | Current cleanup |
| --- | ---: | ---: | ---: |
| Physical DRC errors | 5 | 0 | 0 |
| Physical DRC warnings | 11 | 5 | 0 |
| Unconnected PCB items | 0 | 0 | 0 |
| Schematic/PCB parity warnings | 17 | 0 | 0 |
| Active ERC errors | 9 | 0 | 0 |
| ERC warnings | 182 | 178 | 0 |
| Exact documented ERC exclusions | 0 | 1 | 1 |

Current [ERC](validation/20261118-library-cleanup/erc.json) and
[DRC/parity](validation/20261118-library-cleanup/drc.json) receipts apply to
PCB SHA-256 5c458e5101e154ade50d4f46838bfef8431463d00d7e8059d6d342e8b68a4dc9.
The older receipts remain unchanged and bind to the preceding native hashes.
The installed environment substitutes DejaVu for the unavailable Tokyo font.

The board has **164 footprints and 584 pad objects**, up from the upstream
579 pad objects. The preceding physical repair changed the auxiliary BMI270
connections and local routing; this follow-up library cleanup changes no
physical connectivity or placement. Its explicit U12 numbering map is
applied when comparing the 113 net partitions. The six U10 pads retain the
same-net track contacts established by the earlier
[native proof](validation/final-pcb-connectivity-proof.json).

The archived initial-repair app importer check produced the same 160-part, 82-net graph before and
after the ERC flags and symbol annotations. Diagram, resolved nets, mapping,
compiler result and lowerer result are identical. The source-free import
still fails with `PWR_RAIL_UNDRIVEN` on `net@C22:1`, which contains the real
P1/J29 battery input and U6/U16 input rails. This proves that ERC annotations
cannot create an ideal battery or regulator supply. It does **not** prove a
powered native boot or qualify the RP2354B internal buck regulator.

## Card1 DAT1 pad 8 restoration

Card1 DAT1 pad 8 was present in the schematic as an unused contact and in the
source footprint library, but absent from the native PCB. The Card1 contact
row occupies a 1.6 mm wide column on B.Cu with 0.4 mm gaps, too narrow for a
0.35 mm via under the 0.09 mm rule, so every through via inside the pad
outline had to leave the column:

- the two +1.1V plane vias moved into L1 pad 1 on the existing In3.Cu +1.1V
  track; U2.65, C20.1 and L1.1 stay joined by the unchanged F.Cu tracks;
- the +3.3V via under C19.1 has no legal site reachable on F.Cu. It was
  removed and U2.64/C19.1 now join U2.60 (with C41/R12) through a 0.10 mm
  F.Cu track inside the U2 pad ring. The C19 decoupling loop is longer;
- the USB D− via moved 0.12 mm inside R10 pad 1; one GND via moved 0.13 mm
  inside C20 pad 2 and one GND stitch via 0.06 mm for hole clearance.

Every coordinate is in the
[restoration record](validation/card1-dat1-pad-restoration.json), with the
before and after DRC reports. No rule, layer or footprint changed. No
signal-integrity or power-integrity review of the reroute was performed.

The native STEP and component mesh have now been regenerated from the current
board. The [export manifest](mechanical-review/export-result.json) binds each
actual command and output to the exact native board hash. The existing
KernelCAD revision 4 used earlier geometry and does not qualify this revision.
Native sensor startup, Betaflight arming, ESC operation, flight control and
physical power-on remain unqualified.

## Model availability

All 107 enabled source model entries resolve to their pinned assets. The
17 standard KiCad STEP files are preserved under reviewed-models; custom
models remain in the original source submodule. The
[current model review](mechanical-review/model-resolution-review.json)
records every model hash, native offset, rotation and scale. The earlier
[model inventory](validation/model-resolution-inventory.json) remains a
historical record of the initially incomplete export environment.

The 57 model-free footprints are 53 solder contacts and four testpoints.
The inductor models remain nominal Murata/Changjiang package proxies, not
manufacturer-specific models. The new component mesh has 47,778 facets.
No assigned body, source pose or model scale was changed to improve fit.
A native identity binding is not a populated assembly fit result.

## Reproduce

1. Initialize the original pinned source and its libraries:
   `git submodule update --init --recursive examples/robotics/quadrotor-bldc/hardware/flight-controller-openfc-lite`.
   The two relative library/model links in this copy refer to that source.
2. Use KiCad 10.0.8 with its standard symbol/footprint libraries and the project
   tables. Run `validation/run_native_checks.sh` with an output directory.
   The script does not edit or refill the board; it audits the committed fill.
3. Run the read-only validation/20261118-library-cleanup/verify_geometry.py
   with Python and sexpdata 1.0.2. Its compressed baseline files reproduce
   the exact structural comparison without a KiCad mutation. An optional
   output-path argument writes a fresh JSON receipt. The older
   validation/verify_pcb.py describes the initial physical repair; its
   historical output is linked by the new proof's input board hash.
4. To repeat app import checks, set `LABWIRED_APP_ROOT` to the reviewed app
   checkout listed in the manifest. Run `node --import tsx
   validation/audit_import.mjs INPUT.net OUTPUT.json` from that app checkout.
   Compare the recorded before-annotation and final netlists. The exact app
   source and generated metadata are required; an older released catalog
   cannot reproduce this onboarding result.
5. To regenerate native mechanical inputs, use KiCad 10.0.8 and its pcbnew
   Python module to run mechanical-review/export_native.py. The script fails
   if an assigned model asset or local transform differs from the review.
6. Run the repository's `python3 -m unittest discover -s scripts -p
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
