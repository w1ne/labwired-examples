# Handheld carrier PCB

The routed two-layer carrier passes KiCad 9.0.2 DRC with **0 violations and 0 unconnected items**. The board is an engineering prototype. No physical PCB or assembled handheld has been tested.

## Files

- `handheld-carrier.kicad_pcb`: authoritative routed board, pads, nets and filled copper.
- `handheld-carrier.kicad_pro`: KiCad project settings used for DRC.
- `bom.csv` / `positions.csv`: assembly proposal and footprint origins.
- `carrier-layout.json`: physical pads, nets and transform to the shared case coordinate system.
- `simulation-binding.json`: correspondence between PCB references and the verified LabWired circuit.
- `drc-routed.json` / `routing-report.json`: exact checks and source hashes.
- `export-validation.json`: final Gerber, drill and STEP byte/hash verification, all 124 drill coordinates, and the exact PCB/layout/interface identities.
- `final-import-report.json`: current LabWired design-context coverage bound to the final native PCB hash.
- `native-preserve-preflight/`: exact-source local preservation, generated rules and independent KiCad DRC evidence.
- `hosted-native-integration/`: production source/rules readback, separate hosted KiCad DRC and the verified owner project attachment.
- `import-report.json`: historical import coverage before the connector correction.

Generated fabrication and plot binaries are omitted from this compact contribution. Use the editable routed board to regenerate Gerber, drill, STEP and layer plots in KiCad 9 after rerunning DRC.

## Electrical and mechanical design

The carrier measures 78 × 132 mm with two copper layers and a nominal 1.6 mm substrate. It has 16 footprints: one rear-mounted WeAct Black Pill, one LCD cable header, eight buttons, two bypass capacitors and four mounting holes. The carrier uses 0.25 mm signal tracks, 0.6 / 0.3 mm vias, at least 0.2 mm track clearance and 0.25 mm copper-plane clearance. KiCad fills the ground planes and checks the final geometry.

The module footprint comes from WeAct's published Black Pill v3 KiCad library. The physical module has two 20-pin headers on a 15.24 mm row spacing, plus four optional SWD pins. The carrier main-header holes are 1.02 mm nominal for two Samtec TSW-120-07-G-S strips, following the manufacturer's recommended PCB footprint. The upstream vendor file remains unchanged; the carrier generator applies the selected assembly hole sizes. The four optional SWD positions remain unpopulated. The duplicate power pins are connected on the module; the carrier assigns the required rail pads and leaves unused GPIO pads unconnected.

J1 uses the JST B8B-PH-K-S(LF)(SN) vertical 8-pin header at 2.0 mm pitch. Pin 1 is at PCB (32, 64) mm, below the LCD envelope; the original (56, 17) mm position put the mated connector under the display. Its required signal order is VCC, GND, DIN, CLK/SCK, CS, DC, RST, BL. The official module schematic assigns the same signal sequence; this does not establish the supplied cable wiring or housing orientation. The LCD itself mounts above the PCB. It is not a generic 8-pin footprint soldered directly to the carrier.

The shared interface uses rear-bottom-center case coordinates. The PCB transform is `case_x = pcb_x - 39`, `case_y = 140 - pcb_y`; the nominal PCB center plane is `case_z = 14.2 mm`. Four 2.8 mm holes lie at case x ±29 mm, y 16 / 132 mm. Four concave 4.3 mm radius corner notches clear the case closure posts. The notch arcs are sampled with less than 0.01 mm chord error. The nearest hole-to-notch material web is approximately 2.36 mm.

Power enters the Black Pill through USB. The proposed enclosure gives direct access to the module USB-C connector; the separate extension/pigtail is no longer in the assembly proposal. The LCD receives 3.3 V from the module regulator. The design does not include a battery, charging circuit, speaker driver or cartridge socket.

## Checks and remaining limits

The current DRC report checks the complete routed KiCad board. It is not a schematic ERC result. The PCB pad netlist and `simulation-binding.json` provide the electrical handoff. The final mount coordinates match `../design-interfaces.json`. The current detailed assembly and its exact PCB source identity are recorded in `../kernelcad-reference.json`.

The PCB has not been ordered or assembled. Before fabrication, measure the purchased Black Pill, LCD cable and switch actuator heights. Check USB plug access, regulator current margin, display backlight current, cable exit, mechanical clearances and soldering access. The CAD uses component envelopes and does not establish exact component or connector fit.

A fresh `labwired_import` of the final native PCB accepts the design context but does not map the WeAct module or these switch footprints to a runnable twin. It maps the two capacitors, marks nine components design-only and ignores five non-simulated connectors or mounting holes. `final-import-report.json` records the exact source hash and result: `mode: design_only`, `twin_buildable: false`.

The final connector-corrected board passes both the local preflight in `native-preserve-preflight/` and the later independent hosted KiCad 9.0.2 DRC in `hosted-native-integration/`. The normal owner API attached `pcb_c8da1d7776dba9bc`, revision 0, on 2026-11-11 at 14:49 UTC. Downloaded PCB and rule artifacts match the exact authored/preflight bytes. The fresh attachment comparison changed only `pcb_board_id` and `pcb_board_rev`; editable source, circuit, stimuli, CAD revision and unlisted visibility were preserved. The stored import record reports routing and DRC as not run because preservation and independent validation are separate operations. The runnable circuit continues to use the explicit simulation binding; native import does not automatically create its MCU models.

## Rebuild

The generators require Python with KiCad 9 `pcbnew` and NumPy. On Debian-based KiCad installations, use the distribution Python interpreter:

```sh
/usr/bin/python3 build_carrier.py
/usr/bin/python3 route_carrier.py
kicad-cli pcb drc --format json -o drc-routed.json handheld-carrier.kicad_pcb
```

`build_carrier.py` reads the shared interface file. `route_carrier.py` uses a clearance-aware two-layer grid for the signal routes, adds the ground escape/stitch, then fills the ground planes. KiCad DRC is the authority; rerun DRC after every regeneration and before exporting fabrication files.

## Sources

- [WeAct Black Pill hardware library and pinout](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/tree/master/Hardware/KiCAD)
- [Waveshare 2.4-inch ILI9341 module interface and outline](https://www.waveshare.com/wiki/2.4inch_LCD_Module)
- Stock KiCad 9 footprint libraries for JST PH, 6 mm switches and capacitors.

The WeAct vendor files retain their upstream content. The KiCad 9 adaptation changes only the file version and removes the KiCad 10-only `duplicate_pad_numbers_are_jumpers` field. No pin number, pad position, or module outline was changed by that compatibility edit.

## Header and backlight interface review

`assembly-interfaces.json` records the selected header candidate and the official display schematic. The 40 main header holes changed from 0.8 mm to the Samtec-recommended 1.02 mm. The old hole was smaller than the nominal 0.898 mm diagonal of a 0.635 mm square terminal. That earlier header-only correction left copper, pad centers, net assignments and placement unchanged; the later connector relocation is recorded separately below. KiCad 9.0.2 DRC was rerun and reports zero violations and zero unconnected items. The nominal annular ring on the narrow pad axis is 0.29 mm.

The Samtec footprint gives the nominal hole size; it does not establish finished-hole tolerance. The terminal section is a reference dimension in its marketing drawing. Confirm the manufactured hole limits, purchased module holes, terminal tolerance, module thickness, seating and solder access. The selected strips are not validated for the purchased WeAct V3.0 module. Their nominal 0.898026 mm pin diagonal would leave only 0.001974 mm diametral clearance in a 0.9 mm module hole, before tolerances. Confirm module-side insertion fit separately from the carrier-side 1.02 mm nominal-hole choice.

The [Waveshare schematic](https://files.waveshare.com/upload/1/18/2.4inch_LCD_Module_Sch.pdf) shows BL feeding the base of U2 through R5 (1 kOhm), with a 10 kOhm pull-up and four separate 39 Ohm LED cathode resistors. PA8 therefore controls the module transistor; it does not supply raw LED current. This applies to that Waveshare module. Regulator and backlight current margins still need measurement.

Header sources: [TSW-120-07-G-S](https://www.samtec.com/products/tsw-120-07-g-s), [Samtec drawing](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf), and [recommended PCB footprint](https://suddendocs.samtec.com/prints/tsw-xxx-xx-x-x-xx-xxx-footprint.pdf).

## LCD header and control-switch review

The selected **JST B8B-PH-K-S(LF)(SN)** has nominal 0.5 mm square, kinked terminals and a 3.4 mm reference tail. The general catalog hole drawing is 0.7 +0.1/0 mm, but it explicitly requires consideration of larger holes for fiberglass boards. JST's material-specific FAQ recommends **0.85-0.90 mm finished plated holes** for 3-16 circuit PH headers on glass-epoxy PCBs. J1 therefore uses a centered **0.875 mm nominal CAD/Excellon target**. This is a design requirement, not a measured finished hole or a prescription for the fabricator's pre-plating drill. The fabricator must select drill compensation and confirm the 0.85-0.90 mm final range, 2.00 mm pitch with non-accumulating ±0.05 mm positional tolerance, and annular ring after registration and etch tolerances. The 1.20 mm narrow pad dimension gives a nominal 0.1625 mm annular ring, or 0.15 mm at the largest specified finished hole; the board's design minimum is 0.10 mm.

The J1 header body is 17.9 × 4.5 × 6 mm. The sourced PHR-8 mating-envelope reference gives an 8 mm mated height. The connector now sits below the LCD, with a local support-plate notch and a separate wire-exit reservation in the mechanical assembly. Those reservations do not establish the bend radius or strain relief of the supplied cable. Confirm the purchased housing, crimp, pin order and cable routing.

The selected switch is **Omron B3F-1000**. Its 6.5 ±0.1 × 4.5 ±0.1 mm hole pattern matches the carrier. In the datasheet top view, terminals 4-3 form one horizontal common pair and 2-1 form the other; these match the carrier's two duplicate-pad groups. The footprint's pad numbers 1/2 represent electrical groups, not the manufacturer's four terminal numbers. The carrier now uses the centered 1.0 mm nominal hole recommendation with a 0.9-1.1 mm finished-hole acceptance range. The 4.3 ±0.2 mm actuator height and 0.15-0.45 mm pretravel are recorded for the enclosure. Generic 6 mm tactile switches are unsupported until their own drawings are checked.

The connector relocation reroutes 3V3, GND, PA4, PA5, PA7, PB0, PB1 and PA8. PB9 and PB10 each receive one local same-layer dogleg between PCB y = 61.5 and 66.5 mm because their prior paths intersected the new J1 pad row. The remaining six button-net track/via geometries, all other component positions and all pad-net identities are retained. The ground escape is reserved before signal routing. Final DRC reports zero violations and zero unconnected items. `connector-correction.json` records the before/after source identity, placement and hole changes, retained-copper checks and final DRC. The two central silkscreen labels move below the relocated connector.

For an incremental route after an explicit board-placement edit, the existing example router accepts `--input <board.kicad_pcb> --nets <net names>`. It removes only selected-net tracks, reserves the retained tracks/vias as obstacles, and refills the existing ground zones. A full clean rebuild still uses the default unrouted input.

Primary sources: [JST current PH catalog](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf), [JST finished-hole guidance](https://www.jst.com/resources/faq/), [JST terminal drawing (manufacturer PDF mirrored by Pololu)](https://www.pololu.com/file/0J373/JST_ePH.pdf), and [Omron B3F datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf). See `assembly-interfaces.json` for exact dimensions, sources and limits.

## LCD harness assembly

Waveshare supplies a [PH2.0 8-pin 20 cm cable](https://www.waveshare.com/2.4inch-LCD-Module.htm). That description does not establish a PH-to-PH assembly compatible with this carrier. The included controller-end GPIO sockets require re-termination. Retain the LCD-end plug and terminate the eight conductors into **one JST PHR-8** carrier housing. **Eight new SPH-002T-P0.5S contacts** are candidates only if the actual conductors are AWG 30-24 (0.05-0.22 mm²) with 0.8-1.5 mm insulation diameter, as specified in the JST catalog. Verify the supplied wire and correct crimp process; use a compatible replacement wire/contact assembly if those limits do not match.

| Carrier J1 pad | Carrier net | LCD signal contact | LCD function |
| --- | --- | --- | --- |
| 1 | 3V3 | 1 | VCC |
| 2 | GND | 2 | GND |
| 3 | PA7 | 3 | DIN |
| 4 | PA5 | 4 | SCK / CLK |
| 5 | PA4 | 5 | CS |
| 6 | PB0 | 6 | DC |
| 7 | PB1 | 7 | RST |
| 8 | PA8 | 8 | BL |

This table specifies the required endpoint continuity from the [official LCD schematic](https://files.waveshare.com/upload/1/18/2.4inch_LCD_Module_Sch.pdf), where the PH connector is J2 and the parallel header J1 has the same signal numbers. It does not assume an existing cable is straight-through. Identify each conductor by continuity to the actual LCD pin/function and identify housing pin 1 from the mating-face drawing/mark. Wire colors and left-to-right viewing order are not sufficient. With the harness disconnected and unpowered, verify the eight intended connections and isolation between every other conductor, then confirm the actual VCC/GND labels before mating.

The harness has not been assembled or tested. Its supplied 200 mm length, exit, bend radius and strain relief are not yet validated in the enclosure. The mechanical wire-exit reservation is a design allowance, not a vendor bend limit. `assembly-interfaces.json` contains the same endpoint map and assembly requirements.
