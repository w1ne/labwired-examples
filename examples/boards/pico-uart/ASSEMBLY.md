# Assembly and physical bring-up

Status: procedure prepared; no hardware execution has been recorded.

## Prepare the parts

Use the exact part numbers in [bom.csv](bom.csv). Fabricate one 60 × 70 × 1.6 mm two-layer carrier from the fabrication ZIP. Use separate PTH and NPTH drill files; the four 2.9 mm mounting holes are unplated. The 1.0 mm plated holes accept the specified connector tails. The two routing vias use 0.3 mm drills.

Print one base and one lid in PETG. Use the supplied STL orientations: base floor on the bed, and lid outer face on the bed with registration tabs upward. Start with a 0.4 mm nozzle, 0.2 mm layers and four perimeters. These are process starting values, not a recorded printer qualification. Inspect the first print for warped corners, undersized holes and cable-opening clearance.

Use a 2 mm hex driver for the cap screws, a 1.5 mm hex driver for the countersunk screws, and a 5 mm wrench for the standoffs. Remove burrs from the holes. Do not enlarge or drill the Pico PCB.

## Populate the carrier

1. Keep all power and USB cables disconnected. Inspect the bare PCB for manufacturing faults.
2. Solder J1 and J2, the two SSW-120-01-G-S sockets, on the carrier's upper side. Their pin-1 ends face the USB edge, Y=0.
3. Solder J3, the TSW-103-07-G-S header, on the upper side. Its square pad is pin 1, GND.
4. Solder two TSW-120-07-G-S male headers into the plain Pico SC0915. The 2.54 mm solder tails point through the Pico PCB; the 5.842 mm mating posts point down into the carrier sockets. Keep the insulators seated against the underside of the Pico. Use a non-powered alignment fixture and inspect all joints.
5. Inspect for solder bridges. Check continuity from J3.1 to Pico GND, J3.2 to GP0, and J3.3 to GP1. Check that TX and RX are not shorted to each other or GND. VBUS, VSYS and 3V3 must remain isolated from carrier wiring.
6. Insert the Pico with its USB connector facing Y=0. Apply even force to both header rows. Confirm both rows are fully seated and no pin has missed its socket.

The module is a purchased, populated PCB. Do not desolder its small components to follow the CAD part tree. The separate bodies in CAD preserve the manufacturer's component geometry.

## Build the fixture

1. Put four 0.5 mm nylon washers on the inside floor at the carrier holes (4,4), (56,4), (4,66), (56,66) mm.
2. Place the four 5 mm female/female M2.5 standoffs on the washers. Hold each standoff with the wrench and install an M2.5 × 5 countersunk screw from below. Keep the underside heads recessed or flush.
3. Fit four 25 mm female/female M2.5 standoffs directly on the base floor at the lid positions. Retain each with one M2.5 × 5 countersunk screw from below. Hold the standoff while tightening.
4. Lower the populated carrier onto the four short standoffs. The Pico USB connector must point into the front notch. Fit four M2.5 × 4 cap screws through the carrier mounting holes. Apply only the torque needed to seat the board; do not bend it or crush the nylon washers.
5. With power still off, connect the Adafruit 954 leads: black to J3.1, white to J3.2, green to J3.3. Isolate the red 5 V lead individually and leave it outside the case.
6. Pass the three connected UART leads through the lid opening. Leave enough slack to lift the lid without pulling J3. Fit one Panduit PLT1M-C tie through the two slots and around the insulated lead bundle. Tighten it enough to restrain the bundle without cutting the insulation. Cut the tail flush.
7. Seat the lid's three registration tabs. Fit four M2.5 × 8 cap screws into the 25 mm standoffs. Check that no lead crosses the lid seam.
8. Insert the selected micro-USB cable through the front notch. Confirm that the plug reaches the receptacle fully and does not press on the lid or case wall.

Nominal thread engagement is about 2.16 mm for the lower carrier screws, 2.4 mm for the upper carrier screws, 2.66 mm for the lower lid-post screws and 6 mm for the lid screws. The model leaves 0.44 mm between opposing carrier screw tips. Check received screw lengths and spacer thread depth before assembly.

Support the case while operating underside fasteners. Support the carrier and Pico while inserting or removing the module. The current full-scene assembly-path run was computation-budget limited; it is not evidence that every tool reach or hold has been proven.

## Electrical bring-up

1. Recheck the red adapter lead. It must not touch the Pico, carrier or hardware.
2. With both cables disconnected, check for shorts between Pico 3V3/GND and VBUS/GND. Confirm the J3 pin order against the schematic.
3. Remove the lid, flash the released UF2 using BOOTSEL, and observe the Pico LED. Confirm that the module is a Pico RP2040, not Pico W, Pico 2, or a board with a different header arrangement.
4. Open the adapter serial port at 115200 8N1. Reconnect the Pico power after opening the terminal.
5. Record RP2040_SMOKE_OK and at least four alternating PICO_LED=1 / PICO_LED=0 lines. Observe the on-board LED in both states.
6. Measure GP0-to-GND and verify a 3.3 V logic waveform at the connector. Check the physical UART bit period against 115200 baud. A model transition count does not replace this measurement.
7. If receiving is later added to the sketch, test GP1 separately. The released sketch does not echo data.
8. Refit the lid. Check that UART output continues and that moderate cable movement does not interrupt either USB connection.

## Acceptance record to complete on the first unit

Record the PCB fabricator and lot, Pico SKU/revision, connector part labels, finished board thickness, actual mated header height, print material/printer/settings, measured USB overmold dimensions, and screw/thread-depth measurements. Record supply voltage, UART measurement, observed LED behavior, cable retention and removal/reassembly observations. Attach photos and instrument traces to issue #3553.

No water, dust, drop, thermal, ESD or EMC rating is claimed for this bench fixture.
