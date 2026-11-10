# U6/U10 QFN NC-pad restoration — KiCad 10 evidence

Reviewed on 2026-11-10 with the actual six-layer KiCad PCB.

## Exact changes

| Driver | Physical NC pins restored |
|---|---|
| U6 NSG2065Q | 5, 7 |
| U10 NSG2065Q | 5, 7, 8 |

Each pad uses the matching pinned KiCad footprint geometry and has one
independent unconnected net identity matching the schematic. No NC pad
is connected to a real signal, GND or power rail.

Three original GND copper items were removed to clear the real pad areas:

- One B.Cu GND track from (65.6801, 42.0100) to (65.6801, 42.6301) mm.
- GND through-via at (85.1249, 38.6229) mm near U6.
- GND through-via at (86.1029, 39.5050) mm near U6.

KiCad connectivity still reports zero unrouted items, but loss of GND
stitching needs thermal, EMI and return-current review.

## Native KiCad 10 comparison

| Finding | Before | After |
|---|---:|---:|
| Missing real package pads | 16 | 11 |
| Footprint library mismatches | 6 | 4 |
| Schematic parity findings | 16 | 11 |
| Copper shorts | 0 | 0 |
| Clearance errors | 0 | 0 |
| Unrouted connections | 0 | 0 |
| Total PCB footprints | 222 | 222 |
| Track/via items | 2,922 | 2,919 |
| Original routed nets | 195 | 195 |
| Isolated NC pad net names | 0 | 5 |

The schematic ERC still contains **352 inherited findings**. The eleven
AT32F421 physical pads have NOT been repaired. This board is review-only,
not approved for fabrication or any powered test.

All Gerbers, drill and placement artifacts were regenerated from the same
PCB revision and retain the REVIEW-ONLY label. Run validation/run_drc.sh
on every subsequent source change.

## Rejected trials

- Restoring all 16 pads directly caused 17 physical shorts.
- Removing all 24 interfering tracks and vias cleared those shorts but
  left 13 unrouted connections.
- A naive new through-via plan beneath populated front-side capacitors
  created new short and clearance findings.
- A headless Freerouting Specctra pass read the clean 13-unrouted board
  as 455 unrouted items and 16,999 fixed clearance violations. Native
  KiCad did not corroborate these counts. No SES import was accepted.
