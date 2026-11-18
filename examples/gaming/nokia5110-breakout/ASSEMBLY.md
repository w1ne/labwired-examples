# Nokia Breakout assembly and bring-up

This procedure assembles the enclosure revision B engineering candidate (carrier PCB revision A). The native PCB, firmware and enclosure are supplied together. No fabricated, printed or powered prototype has been recorded. Record the checks below before treating the package as physically qualified.

## Parts and build outputs

Use the exact parts in [bom.csv](bom.csv). The carrier-only placement list is [electronics-bom.csv](electronics-bom.csv). Buy an intact **NUCLEO-L476RG**, **Joy-IT SBC-LCD84x48 REVISION 2**, and **Adafruit 3942 HC-SR04**. Their physical and electrical identities are part of this revision.

The case is 122 × 104 mm in plan. Its closed plastic body is 66 mm tall; the clear window and cap-screw heads bring the complete modeled height to 70.5 mm. Print one base, one lid, two LCD clamps, and two sonar clamps. Cut one 58 × 58 × 2 mm clear PMMA window from the DXF. All model and drawing units are millimetres.

Use PETG for the printed parts. The STL exports already have their intended print orientation: base open side up, lid outside face down, and clamps flat. A 0.4 mm nozzle and 0.2 mm layers are the starting process assumptions. Provide local slicer support under the **18 mm USB opening roof**. The source's 6 mm unsupported-bridge assumption does not cover that roof; the CAD export is not a support-free print qualification. Keep supports out of the nut pockets where possible, remove them completely, and check the pockets with the specified hardware before assembly.

The base wall is 2.5 mm, floor 3 mm, and lid 2 mm. Do not scale an STL to change fit: that also moves connector and mounting-hole positions. Edit the source dimensions, regenerate the outputs, and repeat the checks.

## 1. Measure the purchased parts

Use the revision B files in this package. The saved Studio revision 1 has the superseded board orientation. Case coordinates follow native STEP: X is unchanged from the PCB editor, Y is reversed, and the boards face up at positive Z. The USB opening lies at the positive-Y rear. The registration receipt checks every one of the 26 mating header contacts and all seven native mounting axes.

The two board outlines and mounting positions come from native CAD. Several purchased-module details are not published. They are declared in [mechanical-interface.json](mechanical-interface.json); do these measurements before committing to a complete case print.

| Interface | Candidate value or feature | Required check |
| --- | --- | --- |
| Nucleo Arduino socket height | 8.51 mm assumed above the Nucleo PCB | Measure the actual factory socket. The nominal gap to the carrier header insulator is only 0.359 mm. Do not pull the boards into an incompatible stack with screws. |
| Nucleo board | Intact MB1136 outline, 70 × 82.5 mm | Confirm the purchased revision, mounting holes and Mini-B location. |
| LCD | REV2, 45 × 45 × 14 mm published envelope | Measure board thickness, rear header and glass projection. Confirm the narrow PCB edge strips are clear before clamping. |
| HC-SR04 | 45.5 × 20 × 15.5 mm body, excluding header | Check the actual rear header, components and clear PCB edges. The can locations in the model are illustrative. |
| USB cable | Adafruit 260; 18 × 10 mm case opening | Measure the overmold. The checked plug envelope is 16 × 8 mm, with 1 mm base clearance. |
| Window | 58 × 58 × 2 mm, R2 corners | Use 2.0 ± 0.1 mm stock. Check four 2.9 mm holes on a 50 × 50 mm pitch. |

The clamps grip PCB edges. They must not press on the LCD glass, solder joints, ultrasonic cans, ceramic components or wiring. If the purchased revision differs from a declared assumption, correct the parametric model and BOM before assembly.

## 2. Build and inspect the carrier

Fabricate the carrier from manufacturing/nokia-carrier-fabrication.zip. Specify FR-4, two 35 micrometre copper layers, 1.6 mm finished thickness, and ENIG. Use the separate plated and non-plated drill files. The native KiCad project includes the schematic, routed board and local libraries.

Populate R1, R2 and C1–C3 first. R1 must be **10 kilohms**, and R2 must be **18 kilohms**. Fit J4 and J5 on the component side. Fit J1, J2 and J3 on the underside. Use the unpowered Nucleo sockets as a loose alignment jig while soldering the underside headers; remove the carrier before final inspection.

Inspect solder joints and check continuity against the schematic. Verify that +5 V and +3.3 V are not shorted to ground or to each other. Confirm R1 connects the raw sensor ECHO to PB10 and R2 connects PB10 to ground. Check the five labeled test points.

Do not attach the LCD to 5 V. Do not connect raw 5 V ECHO directly to PB10. The divider produces a nominal 3.214 V from 5 V; its calculated upper result is 3.399 V for 5.25 V and opposing 1% resistor tolerances. This calculation does not replace measuring the populated board.

## 3. Prepare the base

Install three M2 nuts in the underside pockets for the Nucleo bosses. Place the Nucleo on its bosses, with Mini-B toward the rear opening. Fit the three **M2 × 10** cap screws. Their small heads are intentional; larger heads or added washers can collide with adjacent socket pads.

Install four **Würth 970200144, M2.5 × 20 mm** female/female standoffs above the floor. Secure each from underneath with an **M2.5 × 6 countersunk screw**. Check that the screw heads do not protrude below the case and that each standoff sits flat.

Insert the four M2.5 lid nuts through the inward side-loading slots near the top corners. Seat them under their retaining roofs. Do this before the wire bundles obstruct access.

Plug the carrier into Nucleo CN5, CN6 and CN9, using the PCB labels to align pin 1. CN8 remains unused. The carrier should seat on its four standoffs without force or bowing either PCB. Fit four **M2.5 × 5** top screws. Check the two large carrier holes remain over the USER and RESET buttons.

## 4. Build the lid module assembly

Install four M2.5 window nuts in the underside window-boss pockets. Place the clear window on the lid outside face, then fit four **M2.5 × 8** cap screws from above. Tighten evenly by hand until retained. Do not distort or crack the PMMA. No torque setting has been qualified.

Fit the specified TSW-108-07-G-S header to the LCD rear if its installed strip does not match the specified stack. Identify the module by its REV2 label and pad labels. Do not use the square pad as an assumed ground or pin-1 indication: the square pad is **RST** on this module.

With the lid face down on a clean pad, place the LCD between its side rails and end stops. The front PCB edges seat against the narrow front lips; the glass remains clear of the window. Insert four M2 clamp nuts into the rail pockets. Fit the two LCD rear clamps with four **M2 × 8** cap screws from the rear. Rotate the second copy of the clamp 180 degrees in the lid plane. The clamps should retain the board without bending it.

Repeat for the HC-SR04 with the two shorter clamps, four M2 nuts and four **M2 × 8** cap screws. Both transducer faces point out of the lid opening. The single rectangular opening clears the module face without relying on an undocumented transducer-center tolerance.

The rail and end-stop clearances are 0.3 mm per side. The nominal edge capture is 0.6 mm. Inspect the actual contact strips and rear components before tightening. No adhesive is required by this design.

## 5. Wire the modules

Use twelve of the twenty 150 mm wires from **Adafruit 1950**. Fit one wire per labeled signal; wire color is an assembly aid, not an electrical identifier.

| Carrier contact | Module label | Supply or MCU function |
| --- | --- | --- |
| J4.1 | LCD GND | Ground |
| J4.2 | LCD LIGHT | Ground for REV2 active-low backlight |
| J4.3 | LCD VCC | 3.3 V |
| J4.4 | LCD CLK | PA5 / SPI1 clock |
| J4.5 | LCD DIN | PA7 / SPI1 data |
| J4.6 | LCD DC | PC7 |
| J4.7 | LCD CE | PB6 |
| J4.8 | LCD RST | PA9 |
| J5.1 | HC-SR04 VCC | 5 V |
| J5.2 | HC-SR04 TRIG | PA8 |
| J5.3 | HC-SR04 ECHO | Raw ECHO into the carrier divider |
| J5.4 | HC-SR04 GND | Ground |

Viewed from the LCD front, the REV2 labels run **GND, LIGHT, VCC, CLK, DIN, DC, CE, RST** from left to right. The manufacturer does not number them. J4 numbering belongs to this carrier's harness contract.

Route service loops around the carrier, with space to lift the lid and unplug the module wires. Use two Panduit PLT1M-C ties through the printed bridges to retain the bundles. Keep conductors clear of screw tips, standoff edges and the USB opening. Full wire bend geometry and jumper retention are physical checks; the CAD model does not prove them.

## 6. Program and perform electrical bring-up

Keep the lid accessible for the first electrical checks. Use the Nucleo's normal ST-LINK Mini-B USB supply configuration described in the linked ST manual. Connect one power source. Do not simultaneously feed an external 5 V source into the carrier or Nucleo header.

Program firmware/artifacts/nokia-breakout.elf over ST-LINK/SWD, verify the programmed bytes, and reset. The raw BIN alternative starts at **0x08000000**. The same ELF passed the simulator behavior tests.

Measure +3.3 V at TP2, +5 V at TP3, raw ECHO at TP4 and divided ECHO at TP5, relative to TP1 ground. Confirm the actual divider output and firmware pulse timing with the assembled sensor. Record the USB supply current and the 3.3 V rail behavior with the backlight on.

Confirm that the LCD shows the splash and game. Move a flat target through 10, 30 and 50 cm and check right, center and left paddle positions. Check nearer and farther valid distances clamp to the ends. Disconnect ECHO, then test a controlled stuck-high input through the intended circuit: the paddle must center while game animation continues. Record these as bench results only after they are observed.

## 7. Close, inspect and service

Check the cable loop with the lid partly lowered. No wire should cross the mating rim or run under a clamp. Fit four **M2.5 × 8** lid screws and tighten evenly into the captured nuts. Confirm that the clear window and ultrasonic faces remain unobstructed.

Run the game again with the case closed. Compare the sensor response with the open-lid result; the digital model does not establish acoustic reflections, temperature effects or the sensor's real accuracy. Verify that the USB connector can be inserted and removed without loading the Nucleo board.

Disconnect USB before opening the case. Remove the four corner lid screws, lift the lid only as far as the service loop permits, then unplug the labeled module wires. Window screws and module clamps are separate from the lid retainers. Preserve the connector labels when replacing a wire.

## Acceptance record

The release manifest distinguishes evidence from qualification. Digital evidence currently includes zero ERC/DRC violations, all seven native firmware behavior checks, seven CAD fit requirements, seven visual checks, and 85 valid STEP solids. It does not include a completed physical build or a complete collision-free assembly sequence.

Record the board and module revisions, measured stack dimensions, printer/material/settings, fastener seating, cable fit, powered rail/ECHO measurements, supply current, firmware hashes and closed-case behavior. Attach those results to the existing [Nokia issue](https://github.com/w1ne/labwired/issues/3551).
