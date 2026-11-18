# Nokia 5110 Breakout device

This package uses the existing Nokia Lab's **NUCLEO-L476RG** and PCD8544 display interface. The physical display is **Joy-IT SBC-LCD84x48 REVISION 2**. The distance input is **Adafruit 3942 HC-SR04**, powered at 5 V. The routed carrier provides a 10 kΩ / 18 kΩ ECHO divider for PB10, separate 3.3 V LCD power, local decoupling, and five test points.

Canonical Lab: [Nokia 5110 Breakout](https://app.labwired.com/?lab=nokia5110-invaders-lab). The internal invaders identifier is retained; the firmware implements Breakout.

## Native carrier

Open electronics/nokia-carrier.kicad_pro in KiCad 10. The schematic, routed PCB, symbols, footprints, electrical BOM, and fabrication outputs are included. No footprint download or browser layout reconstruction is needed.

The carrier is 90 × 66 × 1.6 mm, two copper layers, with four 2.9 mm NPTH mounting holes. J1, J2, and J3 face down and plug into the Nucleo Arduino sockets CN5, CN6, and CN9. J4, J5, resistors, capacitors, and test points face up. The unused CN8 socket has no mating header. Two 10 mm holes expose the Nucleo USER and RESET buttons while the carrier is fitted.

KiCad checks are recorded in validation/erc.json and validation/drc.json. The candidate has zero ERC violations, zero DRC violations, zero unconnected items, and zero schematic parity differences. These checks do not establish assembly quality or physical operation.

### Pin contract

| Carrier | Contact | Function | Nucleo / module contact |
| --- | --- | --- | --- |
| J1 | 1 | LCD reset | CN5.1 / PA9 / D8 |
| J1 | 2 | LCD D/C | CN5.2 / PC7 / D9 |
| J1 | 3 | LCD chip enable | CN5.3 / PB6 / D10 |
| J1 | 4 | LCD data | CN5.4 / PA7 / D11 |
| J1 | 6 | LCD clock | CN5.6 / PA5 / D13 |
| J1 | 7 | Ground | CN5.7 |
| J2 | 4 | 3.3 V | CN6.4 |
| J2 | 5 | 5 V | CN6.5 |
| J2 | 6, 7 | Ground | CN6.6, CN6.7 |
| J3 | 7 | Divided ECHO | CN9.7 / PB10 / D6 |
| J3 | 8 | Trigger | CN9.8 / PA8 / D7 |
| J4 | 1, 2 | GND, active-low LIGHT | Joy-IT pads GND, LIGHT |
| J4 | 3 | 3.3 V | Joy-IT pad VCC |
| J4 | 4, 5 | CLK, DIN | Joy-IT pads CLK, DIN |
| J4 | 6, 7, 8 | DC, CE, RST | Joy-IT pads DC, CE, RST |
| J5 | 1, 2, 3, 4 | 5 V, TRIG, ECHO, GND | HC-SR04 labels in that order |

The Joy-IT manual labels its pads but does not number them. Viewed from the display front, they read GND, LIGHT, VCC, CLK, DIN, DC, CE, RST from left to right. The square module pad is RST. Our J4.1-to-J4.8 numbering is the carrier harness contract; match the module labels.

All other Nucleo header contacts are intentionally unconnected. J4 is specific to Joy-IT REV2; REV1 changes both pin order and backlight wiring.

Use the Nucleo USB Mini-B input as the power source. R1 is 10 kΩ from sensor ECHO to PB10; R2 is 18 kΩ from PB10 to GND. The nominal divider output is 3.214 V for 5 V ECHO, with a calculated 3.399 V upper value at 5.25 V and opposing 1% resistor tolerances. Verify the populated divider and actual ECHO high level before the first bench run.

### Fabrication and assembly

Use the Gerber and separate PTH/NPTH drill files under manufacturing/. Specify FR-4, 1.6 mm finished thickness, two 35 µm copper layers, and ENIG. Design rules are 0.20 mm clearance, at least 0.25 mm track width, 0.60/0.30 mm vias, and at least 0.50 mm copper-to-edge clearance. Actual signal tracks use 0.30 mm and power/ground branches use 0.50 mm.

Populate the five SMD passives first. Inspect R1 and R2 values, then fit J4/J5 on top. Use the unpowered Nucleo sockets as a loose alignment jig for J1/J2/J3 while soldering the underside headers. Inspect for bridges and continuity before power.

The electrical BOM uses current TDK C1608X7R1H104K080AA 100 nF / 50 V X7R capacitors and C2012X5R1E106K125AB 10 µF / 25 V X5R. The initial Murata candidates were removed after the manufacturer's lifecycle check identified them for discontinuation.

## Mechanical provenance

The Nucleo header and mounting-hole coordinates come from ST's native MB1136C PcbDoc, included in the unmodified archive under references/st/. KiCad imported the PCB with zero warnings or errors. Its default imported Edge.Cuts rectangle is not the finished perimeter: the manufacturer's Mechanical 1 layer defines the rounded 70 × 82.5 mm board and breakaway slots. The derivative uses that finished contour and records two small closure repairs in references/st/provenance.json.

The Nucleo reference STEP is a bare board derived from that source. The source has no component STEP models. It is not a fully detailed vendor PCBA model.

## Primary references

- [ST Nucleo-64 MB1136 manual, UM1724](https://www.st.com/resource/en/user_manual/dm00105823-stm32-nucleo-64-boards-mb1136-stmicroelectronics.pdf)
- [ST MB1136 native design archive](https://www.st.com/resource/en/board_manufacturing_specification/mb1136_bdp.zip)
- [Joy-IT display product](https://www.joy-it.net/en/products/SBC-LCD84x48) and [REV2 pinout manual](https://www.joy-it.net/files/files/Produkte/SBC-LCD84x48/SBC-LCD84x48_Manual_2024-03-18.pdf)
- [Adafruit 3942 HC-SR04](https://www.adafruit.com/product/3942)
- [Samtec TSW terminal-strip drawing](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf)
- [TDK 100 nF capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1H104K080AA)
- [TDK 10 µF capacitor](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012X5R1E106K125AB)
