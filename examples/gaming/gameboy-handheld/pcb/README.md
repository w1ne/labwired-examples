# Handheld carrier PCB

The routed two-layer carrier passes KiCad 9.0.2 DRC with **0 violations and 0 unconnected items**. The board is an engineering prototype. No physical PCB or assembled handheld has been tested.

## Files

- `handheld-carrier.kicad_pcb`: authoritative routed board, pads, nets and filled copper.
- `handheld-carrier.kicad_pro`: KiCad project settings used for DRC.
- `bom.csv` / `positions.csv`: assembly proposal and footprint origins.
- `carrier-layout.json`: physical pads, nets and transform to the shared case coordinate system.
- `simulation-binding.json`: correspondence between PCB references and the verified LabWired circuit.
- `drc-routed.json` / `routing-report.json`: exact checks and source hashes.
- `import-report.json`: the current LabWired import coverage result.

Generated fabrication and plot binaries are omitted from this compact contribution. Use the editable routed board to regenerate Gerber, drill, STEP and layer plots in KiCad 9 after rerunning DRC.

## Electrical and mechanical design

The carrier measures 78 × 132 mm with two copper layers and a nominal 1.6 mm substrate. It has 16 footprints: one rear-mounted WeAct Black Pill, one LCD cable header, eight buttons, two bypass capacitors and four mounting holes. The carrier uses 0.25 mm signal tracks, 0.6 / 0.3 mm vias, at least 0.2 mm track clearance and 0.25 mm copper-plane clearance. KiCad fills the ground planes and checks the final geometry.

The module footprint comes from WeAct's published Black Pill v3 KiCad library. The physical module has two 20-pin headers on a 15.24 mm row spacing, plus four optional SWD pins. The carrier main-header holes are 1.02 mm nominal for two Samtec TSW-120-07-G-S strips, following the manufacturer's recommended PCB footprint. The upstream vendor file remains unchanged; the carrier generator changes only main-header drill diameters. The four optional SWD positions remain unpopulated. The duplicate power pins are connected on the module; the carrier assigns the required rail pads and leaves unused GPIO pads unconnected.

J1 is the KiCad JST PH 2.0 mm vertical 8-pin footprint. Its order is VCC, GND, DIN, CLK, CS, DC, RST, BL, matching the Waveshare 2.4-inch module cable. The LCD itself mounts above the PCB. It is not a generic 8-pin footprint soldered directly to the carrier.

The shared interface uses rear-bottom-center case coordinates. The PCB transform is `case_x = pcb_x - 39`, `case_y = 140 - pcb_y`; the nominal PCB center plane is `case_z = 14.2 mm`. Four 2.8 mm holes lie at case x ±29 mm, y 16 / 132 mm. Four concave 4.3 mm radius corner notches clear the case closure posts. The notch arcs are sampled with less than 0.01 mm chord error. The nearest hole-to-notch material web is approximately 2.36 mm.

Power enters the Black Pill through USB. The top case connector uses a panel-mounted USB-C extension/pigtail. The LCD receives 3.3 V from the module regulator. The design does not include a battery, charging circuit, speaker driver or cartridge socket.

## Checks and remaining limits

The current DRC report checks the complete routed KiCad board. It is not a schematic ERC result. The PCB pad netlist and `simulation-binding.json` provide the electrical handoff. The final mount coordinates match `../design-interfaces.json` and KernelCAD revision 2.

The PCB has not been ordered or assembled. Before fabrication, measure the purchased Black Pill, LCD cable and switch actuator heights. Check the USB extension fit, regulator current margin, display backlight current, mechanical clearances and soldering access. The CAD uses component envelopes and does not establish exact component or connector fit.

The existing `labwired_import` accepts this file as design context but does not map the WeAct module or these switch footprints to a runnable twin. It maps the two capacitors, marks nine components design-only and ignores five non-simulated connectors or mounting holes. The verified LabWired circuit therefore remains linked through the explicit simulation binding, not through an automatic import claim. No placeholder PCB is attached to the saved project.

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

`assembly-interfaces.json` records the selected header candidate and the official display schematic. The 40 main header holes changed from 0.8 mm to the Samtec-recommended 1.02 mm. The old hole was smaller than the nominal 0.898 mm diagonal of a 0.635 mm square terminal. The copper, pad centers, net assignments and placement are unchanged. KiCad 9.0.2 DRC was rerun and reports zero violations and zero unconnected items. The nominal annular ring on the narrow pad axis is 0.29 mm.

The Samtec footprint gives the nominal hole size; it does not establish finished-hole tolerance. The terminal section is a reference dimension in its marketing drawing. Confirm the manufactured hole limits, purchased module holes, terminal tolerance, module thickness, seating and solder access. This revision is a documented nominal-fit correction, not a measured assembly-fit result.

The [Waveshare schematic](https://files.waveshare.com/upload/1/18/2.4inch_LCD_Module_Sch.pdf) shows BL feeding the base of U2 through R5 (1 kOhm), with a 10 kOhm pull-up and four separate 39 Ohm LED cathode resistors. PA8 therefore controls the module transistor; it does not supply raw LED current. This applies to that Waveshare module. Regulator and backlight current margins still need measurement.

Header sources: [TSW-120-07-G-S](https://www.samtec.com/products/tsw-120-07-g-s), [Samtec drawing](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf), and [recommended PCB footprint](https://suddendocs.samtec.com/prints/tsw-xxx-xx-x-x-xx-xxx-footprint.pdf).
