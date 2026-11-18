# ESP32-S3 Doom desktop device — revision A

This package supplies an editable KiCad 10 carrier, manufacturing outputs, physical ESP-IDF firmware, a fitted desktop enclosure, an exact bill of materials, and retained validation evidence. It targets **ESP32-S3-DevKitC-1-N16R8 PCB v1.0** and **LCDWiki MRB3205**. It is a release candidate. Hardware current, temperature, cable dress and printed fit remain unmeasured; see [the acceptance record](validation/acceptance.json) and [issue #3552](https://github.com/w1ne/labwired/issues/3552).

## What the device does

The ESP32-S3 runs the Doom engine from flash and an 8 MB octal PSRAM. An ILI9341 panel receives a 16-bit 8080 bus through the chip's LCD_CAM/GDMA hardware. The display is 320 × 240; Doom uses a 320 × 200 image with a 20-pixel border above and below. A PC terminal connected to the board's UART USB socket supplies keyboard input. The carrier does not include dedicated game buttons, audio, a battery, touch input or an SD card.

The fresh physical firmware has booted from the real mask ROM in LabWired and produced the title screen on the existing I80 panel model. The captured image is a framebuffer dump, not a mock-up. A simulated frame rate is not a physical-device benchmark.

## Package contents

| Directory or file | Purpose |
|---|---|
| `electronics/doom-carrier.kicad_pro` | Native KiCad project, local symbol/footprint libraries and design rules |
| `electronics/doom-carrier.kicad_sch` | Complete carrier schematic |
| `electronics/doom-carrier.kicad_pcb` | Routed 80 × 100 × 1.6 mm carrier, two copper layers |
| `manufacturing/` | Gerbers, plated/non-plated drills, assembly positions, netlist and PDF drawings |
| `bom.csv` | Exact ordering codes and quantities, including case hardware |
| `connector-map.csv` | All 34 display connector positions and their signal destinations |
| `firmware/source/` | Complete GPL-2.0 Doom/ESP-IDF application source |
| `firmware/build.sh` | Digest-pinned ESP-IDF container build and complete-flash assembly |
| `firmware/artifacts/` | ELF, application, bootloader, partition table, full flash image and checksums |
| `mechanical/doom-desktop.kcad.ts` | Editable source for the assembly, base, lid and ribbon depth spacer |
| `mechanical/*.step` | Neutral CAD exports |
| `mechanical/*-print.stl`, `*-print.3mf` | Millimetre print exports in their intended print orientations |
| `validation/` | Electrical, mechanical, build and simulation receipts, plus real renders |
| `release-manifest.json` | File inventory, hashes, declared scope and release state |

## Exact hardware contract

Use the listed PCB v1.0 DevKit. That revision routes its RGB LED to GPIO48. PCB v1.1 changes the LED route to GPIO38, which this package uses for LCD reset. A board sold under a similar name is not sufficient evidence of compatibility. Check the revision marking and component layout before insertion. The firmware clears the v1.0 RGB LED at startup and does not enable the radio.

Use MRB3205, the **34-pin, 16-bit** module. Set R16 to 0 Ω and leave R8 open. The carrier supplies 3.3 V; close the display module's J1 bypass as specified by its schematic. Do not substitute the visually similar SPI, 8-bit or 40-pin products.

| Signal | ESP32-S3 GPIO | MRB3205 pin |
|---|---:|---:|
| D0…D15 | 1…16, in the same order | 6…21 |
| WR | 17 | 3 |
| DC/RS | 18 | 2 |
| CS | 21 | 1 |
| RST | 38 | 5 |
| BL | 39 | 23 |
| RD | 10 kΩ pull-up to 3.3 V | 4 |
| VDD | 3.3 V | 24, 25 |
| GND | Ground | 26, 27 |

Each of the 21 MCU-driven data/control signals has its own 33 Ω source resistor. The three unused SD/flash/touch chip selects have separate 10 kΩ pull-ups. NC, MISO, MOSI, PEN and CLK are unconnected because their associated functions are not used. GPIO26…37 are reserved for the N16R8 memory configuration. GPIO3 is a strapping pin; the selected LCD data input does not add an external pull-up or pull-down to it.

The ribbon cable is **IDSD-17-D-04.00-G**, straight 1:1, with no reverse-wiring suffix. Pin 1 is marked on the carrier and identified by the cable's red edge. Check continuity from carrier J3.1 to display pin 1 before power. Do not infer pin numbers from the direction the cable exits its housing.

## Power

Connect the Adafruit 592 data cable to the DevKit's **UART** Micro-USB connector. It powers the board and carries programming, logs and keyboard input. The carrier takes 3.3 V from the DevKit. The factory v1.0 schematic identifies the SGM2212-3.3 regulator; the manufacturer rates that regulator for 800 mA, subject to thermal conditions. This is a component rating, not a measured allowance for the finished device. The display manual leaves its power consumption unspecified.

Before physical acceptance, measure total current and 3.3 V at TP1/TP2 during startup, a fully lit screen and continuous gameplay. Check regulator temperature with the case closed. Record supply/cable, ambient temperature, current, rail minimum and test duration. Do not add another supply to the 3.3 V rail while USB powers the board. Full-backlight current and thermal margin are open items in issue #3552.

## Manufacture and assemble

1. Manufacture the carrier from the supplied Gerbers and drill files. Use the native 1.6 mm, two-layer design. The routed board contains 38 footprints: 30 populated electrical components, four mounting holes and four test pads. Check the schematic and BOM together before assembly.
2. Populate the 25 resistors and two capacitors. C1 is the TDK 10 µF X7R part; C2 is the TDK 100 nF X8R part. Solder the two 22-way sockets and the 34-way display header. Keep them perpendicular to the board. Inspect every joint and check that 3.3 V is not shorted to ground.
3. Print the base and lid in PETG with a 0.4 mm nozzle, 0.2 mm layers and four perimeters. The exports already place each part on its print face. The USB aperture has a 45° roof and a 6 mm top bridge. Inspect the four nut pockets and registration tabs; remove debris before inserting hardware. These settings define the candidate process and have not been physically qualified.
4. Print the ribbon depth spacer with 0.1 mm layers. Its nominal thickness is 1.1 mm. Measure the display header's exposed pin length and subtract the measured spacer thickness: the result must be **5.59–6.22 mm**. The drawing's nominal 7.0 mm pins and the 1.1 mm spacer give 5.9 mm insertion. Change the single `ribbonSpacerT` constant in the editable source when the measured stack requires it; regenerate and validate the export. Never force the socket against its internal stop.
5. Insert four M3 nuts into the base's inward-facing pockets while the base is empty. Fit the four 7 mm Harwin standoffs over 0.5 mm nylon washers. Retain them from below with M2.5 × 5 mm countersunk screws. Fit the carrier with four M2.5 × 5 mm cap screws. The lower and upper screws do not meet inside the 7 mm through-threaded standoffs.
6. Insert the exact DevKit with its USB edge toward the case's rear aperture. Align all 44 pins before applying even pressure. Keep the antenna region free of added metal and wiring. The PCB includes a copper keep-out; RF performance is not qualified.
7. Assemble the display and lid on the bench. Put a 4 mm nylon spacer at each display mounting hole between the PCB front and lid underside. Use M2.5 × 12 mm screws through the lid, with nylon washers and M2.5 nuts behind the display PCB. Hold the nuts with a 5 mm tool. Support the module at its PCB, not the glass. Tighten only enough to retain it; the candidate contains no measured torque specification.
8. Put the printed depth spacer over the display header and mate the display-end IDC socket against it. Mate the other socket to carrier J3. Confirm the red-edge/pin-1 continuity. Support the lid separately while open. Dress the ribbon in the open bay without a sharp crease, pinching it under a screw boss, or loading either connector. The cable's exact flex shape is not represented as a rigid CAD solid.
9. Lower the lid without trapping the ribbon and install the four M3 × 10 mm case screws. Verify that both USB sockets remain reachable through the rear aperture. Connect the UART USB cable and run the checks below. For service, disconnect USB, remove those four screws and support the lid before disconnecting the ribbon.

The case footprint is 100 × 120 mm. The shell and lid are 65.5 mm high before protruding screw heads. Turn the finished case so its long axis is horizontal for the landscape display.

## Native checks and CAD source

Run `python3 authoring/verify_package.py` after downloading the complete package. It checks all manifest hashes, the 197 reviewed firmware source files, nine build artifacts, the merged flash layout, all 34 ribbon pins, 21 firmware-to-schematic signal paths, four pull-ups, and the recorded native and mechanical evidence. This is an integrity check; it does not rerun the engines or qualify physical hardware. Maintainers refresh the manifest only after reviewing a deliberate change with `python3 authoring/verify_package.py --write-manifest`.

Run `bash authoring/verify_native.sh` with KiCad 10 installed to rerun ERC, DRC, zone fill and schematic parity without modifying the accepted board. Reports go to `validation/recheck/`. Run `bash authoring/export_native.sh` to regenerate the manufacturing files and engineering views.

The [previous saved CAD candidate v1](https://app.kernelcad.com/p/sZrRpIhi?version=1) is superseded because its populated layout had reversed handedness. Use the corrected package source: edit `mechanical/doom-desktop.kcad.ts` locally with its `inputs/` folder. Run `/usr/bin/python3 authoring/check_registration.py` with KiCad installed to verify 78 native header pads, 44 exported socket/DevKit axes and four mounting axes. The three asymmetric native pad witnesses retain component-side +Z and reject the former mirrored layout. The source's `output` choice selects the assembly, base, lid or connector spacer. Use the existing KernelCAD evaluate, design-loop and export commands. The retained review passes all 10 declared fit requirements and all seven visual checks. Its negative control closes the USB opening and fails the 0.5 mm plug-clearance requirement. Native drawings and stated vendor-envelope limits still control the physical acceptance scope. The existing saved v1 revision reports a mesh worker memory failure and is not the corrected package source. Its replacement is pending the normal imported-asset update path. The corrected batch construction passes full hosted evaluation under the unchanged 1024 MB limit; two fresh-worker mesh replays also pass the unchanged 896 MB limit, with no failed mesh features. The deployed saved revision remains a separate pending check.

## Build, program and run

From this package directory:

```bash
bash firmware/build.sh
```

The script uses `espressif/idf@sha256:55ab243e87584859c9af3acc124b0b9423a9d8b44fc99a5d5055d7bd7312722d` (ESP-IDF v5.3.1), the checked-in configuration and a fixed project version. `prepare_wad.py` verifies the complete source release image and the extracted shareware IWAD. It does not accept an arbitrary local WAD silently. See `firmware/artifacts/build-manifest.json` for the resulting hashes.

Program `firmware/artifacts/doom-s3-flash.bin` at flash address 0. It includes the bootloader at 0, partition table at 0x8000, application at 0x10000 and IWAD at 0x410000. Select ESP32-S3, 16 MB flash and 80 MHz flash clock. Use the UART USB port; hold BOOT while pressing RESET if automatic download mode does not enter. Do not program only the application file onto an empty device.

Open a 115200-baud, 8-N-1 terminal on the same UART USB connection. The boot log should identify the 16 MB flash and 8 MB PSRAM, map the 4,196,020-byte IWAD, initialize the I80 panel, and enter the Doom tick loop. The LCD bus runs at 10 MHz with 16 data bits.

| Input | Action |
|---|---|
| Enter | Select/start |
| Escape | Menu/back |
| W/S or up/down arrows | Forward/backward or menu navigation |
| A/D or left/right arrows | Turn left/right |
| Q/E | Strafe left/right |
| F | Fire |
| Space | Use/open |
| M or Tab | Automap |
| P | Pause |

The terminal sends key-down bytes and no key-up messages. Firmware releases a key after 140 ms unless auto-repeat refreshes it. Dedicated physical controls are outside this revision's hardware contract.

## Reproduce the digital firmware checks

Build the LabWired CLI from core commit `31730dd16391495aed6045ffb52b1aee62d3ceab`. Use the two ESP32-S3 mask ROM assets identified by exact hashes in `runtime/provenance.json`. Run from the package directory:

```bash
python3 authoring/verify_runtime.py --labwired /path/to/labwired \
  --rom /path/to/esp32s3_rom.bin --drom /path/to/esp32s3_drom.bin \
  --output /path/to/new-doom-runtime-recheck
```

The runner verifies the ROM hashes, disables the optional fastboot path, and runs the packaged ELF with the complete packaged flash image. Both runs execute 900 million steps. The second injects Escape through the declared `uart0` at cycle 650 million. Acceptance requires three runtime assertions per run, confirmed UART delivery, the exact reviewed title/menu framebuffers, and 23,079 changed framebuffer bytes. An undelivered input cannot pass by displaying the unchanged title. `validation/runtime/` retains the original reports, logs, invocation hashes, raw pixels and actual PNG frames. The recorded title and menu contain 236 and 232 distinct RGB colors respectively.

These checks exercise the same physical firmware through the declared digital model. The model assumes ideal MCU supply voltage. Its generic static SRAM percentage excludes the external PSRAM capacity; it is not a physical heap or power measurement.

## Evidence and limits

Native KiCad ERC and final PCB DRC report zero findings, zero unrouted connections and zero schematic/PCB parity errors. The untouched autorouter input and the precise cleanup records are retained; cleanup removed only reported dangling vias/track stubs and added connected ground pours. No rule or clearance limit was disabled to obtain the result.

The CAD imports the routed carrier's native STEP. It uses the factory DevKit v1.0 DXF outline and the MRB3205 mechanical drawing, with manufacturer dimensions for purchased sockets and fasteners. Espressif's PDF rounds the length to 62.74 mm while its DXF outline is 62.865 mm; the model follows the DXF and preserves the factory header coordinates. KiCad's board-only STEP represents a 1.51 mm laminate core; the CAD scales only that thickness to the specified 1.6 mm finished board. The final native transform retains X, native Y and component-side +Z. Batch boolean operations reduce capture features from 962 to 631 while retaining all 48 named parts, 2,371 faces, identical volume and bounds; both review sheets remain byte-identical.

The DevKit's populated components are not represented by an unavailable vendor STEP. A 12 mm component-height allowance is checked against the display rear allowance. The USB plug is a bounded design envelope. These are stated fit assumptions, not measured manufacturer component geometry. Ribbon contact springs and flexible cable dress are also outside the rigid-body proof. The assembly remains a candidate until the outstanding physical checks are recorded.

## Sources and licenses

- [Espressif PCB v1.0 guide](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html), [native DXF](https://dl.espressif.com/dl/DXF_ESP32-S3-DevKitC-1_V1_20210312CB.dxf) and [factory schematic](https://dl.espressif.com/dl/SCH_ESP32-S3-DEVKITC-1_V1_20210312C.pdf).
- [MRB3205 product page](https://www.lcdwiki.com/3.2inch_16BIT_Module_ILI9341_SKU%3AMRB3205), [dimension drawing](https://www.lcdwiki.com/res/MRB3205/MRB3205_Size.pdf) and [schematic](https://www.lcdwiki.com/res/MRB3205/3.2inch_MRB3205_Schematic.pdf). The pin map follows the schematic where manual prose is inconsistent.
- [Samtec SSW drawing](https://suddendocs.samtec.com/prints/ssw-1xx-xx-xxx-x-xx-xxx-xx-mkt.pdf), [TSW drawing](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf) and [IDSD catalog](https://suddendocs.samtec.com/catalog_english/idsd.pdf). The double-row IDC body uses the +1.50 mm length allowance; the single-row +0.48 mm formula does not apply.
- [SGMICRO SGM2212](https://www.sg-micro.com/product/SGM2212). Additional source links are recorded per BOM row and in `validation/manufacturer-provenance.json`.

The Doom firmware retains its upstream GPL-2.0 license in `firmware/source/LICENSE`. Source provenance records the input commit and changed files. The shareware IWAD and rendered game artwork remain copyright id Software and are separate from that source-code license. The build obtains the pinned existing shareware release payload; it does not grant a license for other WADs. Manufacturer drawings and product names retain their owners' rights; the package links to those sources rather than relicensing them.
