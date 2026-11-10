# OpenESC manufacturing review — outstanding deviations

Source board: OpenDrone OpenESC-30x30 commit
bf306934b5decc130ab1df6b653563ea16165e8e.
Tool: KiCad 10.0.8 native CLI, project-specific constraints,
local/pinned symbol and footprint libraries.

## Board physical DRC

- 222 unique physical component reference numbers.
- 0 unconnected copper items.
- 195 copper nets and 2,922 track/via items.
- 6 footprint library mismatches (U2, U5, U6, U7, U9, U10).
- 16 schematic-to-board parity mismatches because package pads
  are absent from specific IC footprints.
- No copper short or clearance violation was reported on the
  board as checked with its original missing pads.

The candidate with all missing package pads restored shows
17 shorting items, 7 clearance conflicts and 3 hole-clearance
conflicts. It was not promoted. Nearby copper must be rerouted,
not tied to an NC pad or bypassed with a false DRC exclusion.

Pin-level NC omissions:
- U2 AT32F421: 8 (PA2), 23 (PA15), 24 (PB3)
- U5 AT32F421: 8 (PA2), 23 (PA15), 24 (PB3)
- U7 AT32F421: 8 (PA2), 23 (PA15), 24 (PB3)
- U9 AT32F421: 23 (PA15), 24 (PB3)
- U6 NSG2065Q: 5 (NC), 7 (NC)
- U10 NSG2065Q: 5 (NC), 7 (NC), 8 (NC)

The missing pins are explicitly unconnected in the exported
schematic netlist. This does NOT permit connecting them to nearby
+3V3, GND or current-sense copper. Those copper traces overlap
actual package pads in the rejected geometry candidate.

## Schematic ERC

Baseline source schematic: 352 findings.
After adding 49 correctly wired bulk capacitors: 352 findings,
same breakdown:
- 240 pin-to-pin warnings/errors
- 45 library-symbol issues
- 26 endpoints off grid
- 24 inputs not driven
- 6 missing library-footprint links
- 5 symbol-definition mismatch
- 3 power pins not driven
- 3 multiple net names

Many findings reflect original vendor symbol electrical types and
missing library aliases. These are not silently ignored or asserted safe.
Manufacturer datasheets and electrical engineering review must
resolve all high-severity ERC issues.

## BOM/placement reconciliation

- 222 physical footprints, 213 SMT assembly components.
- 22 grouped sourcing rows, 213 individual placements.
- All 213 placement references match a populated BOM reference.
- 49 PCB-only bulk caps now have unique C501–C549 designators.
- Complete 4-in-1 ESC motor output pad map is in
  ../assembly-wiring.md.

## Test evidence and control

Files saved in this directory:
- drc-final.txt: native physical DRC plus parity.
- erc-final.txt: native ERC on the corrected top-level schematic.
- drc-with-pads in validation/rework/out (local engineering test only).
- nc-route-audit.txt: route geometry around the omitted pads.

The reviewed Gerber ZIP is tagged REVIEW-ONLY. It is not a
manufacturing acceptance or completed aircraft certification.
Power-on, supply transients, MOSFET switching, 4-motor AM32,
thermal, propeller thrust and flight have not been tested.

## Required release gates

1. Restore 16 package pads using correct manufacturer footprints.
2. Reroute all intersecting copper, vias and plane connections
   while maintaining phase-current paths, via design rules and
   6-layer stack impedance/thermal design.
3. Resolve remaining schematic ERC and pin-map issues.
4. KiCad 10 DRC with parity: zero shorts, unconnected items,
   missing pads, unapproved package mismatches and high-severity
   ERC errors.
5. First-article assembly and powered bench validation with
   props removed. Verify DShot, failsafe and bus current/thermal.
6. Only then regenerate fab/assembly exports and call them ready.
