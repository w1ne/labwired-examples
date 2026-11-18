# STM32H563 UDS ECU bench fixture

This package adds a routed, protected CAN interface to the existing
[STM32H5 UDS Lab](https://app.labwired.com/?lab=stm32h5-uds-ecu). It preserves
the NUCLEO-H563ZI and PD1 transmit / PD0 receive assignment.

KiCad 10.0.8 reports **0 ERC violations, 0 DRC violations, 0 open connections,
and 0 schematic parity issues**. The physical firmware compiles and passes the packaged 16-step simulator
protocol test. No physical
prototype has been assembled, flashed, electrically measured, or qualified.

## Firmware and evidence

| Target | Verified result | Limits |
|---|---|---|
| Existing simulator fixture, core 941a6c5caf0c53b66aa5af9290e5ecba5972ec72 | CLI 0.26.0: 16/16 diagnostic exchanges, 3/3 assertions, 603-byte response, negative response, reset and reconnect | Does not test physical clock, pin mux, transceiver, or elapsed time |
| Physical HAL target in firmware/ | Same flashable ELF: CLI 0.26.0 passes 16/16 exchanges and 3/3 assertions; all 603 calibration bytes match; AIRCR reset and reconnect pass | Generic FDCAN frame model; no analog MCP2562FD, electrical wire timing, or physical board measurement |

The simulator firmware advances its time callback once per loop and omits
physical FDCAN timing and pin setup. Do not flash that image as this hardware
release. The physical build uses ST HAL/CMSIS for clock selection, PD0/PD1 AF9,
FDCAN filters/message RAM, SysTick milliseconds, and reset. Both targets reuse
the same UDSLib 2.0.0 application and post-transmit reset deferral.

## Native electrical design

Open electronics/can-interface.kicad_pro in KiCad 10. The board is
**60 × 40 × 1.6 mm**, two layers. Four 3.2 mm NPTH mounting holes are at
(4,4), (56,4), (4,36), (56,36) mm. The native board is the final routed
source. Order one bare carrier from these manufacturing files; PCB1 in the
assembly BOM is separate from its populated components. Manufacturing includes
Gerber, drill, netlist, and schematic PDF.
cad/can-interface.step is the populated native export. JP1 uses the source-dimensioned
Samtec TSW-102-07-G-S envelope from cad/references/samtec, with zero model
offset and rotation. Its nominal 2.54 mm tail and 5.84 mm post replace the
previous generic header model. The model record separates nominal dimensions
and tolerances; native copper and all other PCB bytes are unchanged.
The replacement passes DRC, open-connection and schematic-parity checks;
see evidence/jp1-model/native-model-replacement.json.

- **MCP2562FD-E/SN**, SOIC-8: pin 3 gets 5 V, pin 5 gets 3.3 V, pin 8 STBY
  is grounded. C1/C2 decouple each supply; C3 is local bulk capacitance.
- **PESD2CAN,215** protects the bus. D1 pin 1 is CANL, 2 CANH, 3 ground.
- JP1 enables the **120 Ω, 1%, 0.5 W** termination. Fit it at a bus end only.
- Connect the BOM cable, StarTech.com USB2AC1M (1 m, USB-A to USB-C,
  USB 2.0 data and power), from a host USB-A port to the STLINK-V3EC
  USB-C connector CN1. Keep JP2 at its default STLK [1-2] setting.
  UM3115 specifies a 500 mA maximum for this supply path; the cable
  does not increase that board limit. CN1 is the only fixture power source. This carrier has no
  galvanic isolation or vehicle battery input.
- Physical firmware uses **11-bit IDs**, request 0x7E0 and response 0x7E8,
  **500 kbit/s nominal / 2 Mbit/s data**, ISO CAN FD with BRS for frames
  longer than eight bytes. Short frames use classic CAN without BRS.
  Unmatched IDs and remote frames are rejected.

ST's 8 MHz ST-LINK MCO clock recipe supplies PLL1Q at 250 MHz. Nominal
prescaler 2, segment 1 187, segment 2/SJW 62 gives 500 kbit/s and 75.2%
sample point. Data prescaler 5, segment 1 19, segment 2/SJW 5 gives
2 Mbit/s and 80% sample point. Keep default MB1404 ST-LINK MCO/HSE routing
and CN1 USB connected. Initialization stops if the external clock is absent.

## Exact harness

J1 mates with JST XHP-6 using SXH-001T-P0.6 contacts. Make six identified
150 mm, 24 AWG conductors. Two Samtec TSW-103-07-G-S headers form the
Nucleo ends; solder and individually insulate their wire tails. These native
Nucleo connections are **not keyed**. Label the pins and check continuity.

| J1 pin | Net | NUCLEO-H563ZI connection |
|---|---|---|
| 1 | Ground | CN8 pin 11 |
| 2 | +5 V | CN8 pin 9 |
| 3 | +3.3 V | CN8 pin 7 |
| 4 | TXD input to transceiver | CN9 pin 27, PD1 / FDCAN1_TX |
| 5 | RXD output from transceiver | CN9 pin 25, PD0 / FDCAN1_RX |
| 6 | Ground | CN9 pin 23 |

Each header occupies one odd-numbered row: CN8 pins 7/9/11 and CN9 pins
23/25/27. Do not bridge adjacent odd/even rows. Morpho CN11/CN12 is unused.

J2 mates with XHP-3: **1 CANH, 2 CANL, 3 GND**. Build the CAN lead from
LAPP **2170261**, a 120 Ω nominal, 2-pair 24 AWG cable. Use 1.1 m rough
stock and trim to **1.0 m between the connector rear faces**. Retain the
white/brown pair twist to within 10 mm of the contact terminations.

| XHP-3 pin | Cable conductor | Amphenol L177SDE09S contact |
|---|---|---|
| 1, CANH | White | 7 |
| 2, CANL | Brown | 2 |
| 3, signal ground | Green | 3 |
| No connection | Yellow | Insulate separately at both ends |

Fit the **8655MH0901BLF** metal hood and its supplied UNC 4-40 hardware to
the D-sub. Its cable clamp accepts 5–8 mm cable; measure the purchased
cable before assembly. The cable datasheet gives approximately 7.5 mm jacket
and 1.4 mm core diameters. Confirm that each core lies within the XH
contact's 1.3–1.9 mm insulation range before crimping. Preserve the braid
under the hood's metal clamp; keep it separate from the signal contacts.
At the ECU end, trim and insulate the braid edge under a 30 mm piece of
TE **5053192058** tubing. Keep the JST fanout at most 50 mm. Restrain the
jacket at the mount before that fanout. The heat-shrink sleeve is insulation,
not the cable restraint. Route the external cable with a bend radius of at
least **10 times its measured outside diameter**; reserve 80 mm for the
selected clamp-compatible cable. This fixed-installation cable is not a
continuous-flex lead.

Use TE **5052942064** tubing on the six Nucleo header solder tails, the
three D-sub solder cups and both unused yellow ends. Install sleeves before
soldering, cover all exposed metal, and keep the mating header posts clear.
Check the dressed sleeve envelopes in the fitted assembly; the tubing's
fully recovered wall is 0.5 ±0.2 mm, so nominal wire diameter alone does
not prove adjacent-sleeve clearance.

At the tester, insert **PEAK IPEK-003002-Mini** between the cable and the
PCAN-USB FD. It provides the exact remote 120 Ω termination. Keep the
carrier JP1 shunt installed and the tester's optional internal termination
disabled. Leave all optional tester power contacts disconnected. The
result is two bus-end terminations; confirm approximately 60 Ω across H/L
with both nodes unpowered before applying power. See
[evidence/harness-components.json](evidence/harness-components.json) for
manufacturer drawings, revisions, cable limits and connector provenance.

## Mechanical mounting

The editable bench assembly is cad/bench-assembly.kcad.ts. The printable part
is cad/bench-mount-print.kcad.ts, with matching STEP and STL exports. It is a
**222 × 90 mm open bench mount**, with a 3 mm base, four 7 mm carrier bosses,
a holeless Nucleo cradle, and two harness tie slots.

Print the flat base on the bed in PETG. Check the 0.35 mm nominal edge
clearance against the purchased Nucleo board before pressing its edge under
the catches. The carrier sits 7 mm above the base. Ream the four modeled
2.459 mm pilot bores to 2.5 mm and tap M3 × 0.5 to the 7 mm boss depth with
a bottoming tap; the supplied STL has pilot bores, not helical printed threads.
Fit four ISO 4762 M3 × 8 screws through the PCB. Nominal engagement is 6.4 mm.
Do not force a screw against the blind-hole floor or distort the PCB. Retain
the harness with two HellermannTyton **111-01910 / T18R-PA66-BK** ties through the slots.

The carrier uses its exact populated KiCad STEP. The Nucleo reference is the
**133.34 × 70 mm board outline**, with an 8 mm under-board gap; its populated
connector and component geometry is not present. Verify purchased-board fit,
USB and Ethernet access, edge retention, harness routing, and underside
clearance on the physical assembly. The cradle is an editable fit candidate.

The print-only model passed the hosted geometry and visual review
(evidence/mount-review.json). The full assembly records two bounded contacts
for the stock JST XH model's clinched leads: 0.08 mm³ maximum overlap and
0.08 mm maximum thickness at each header/PCB pair. The original measured
lead contact is 0.066 mm³ / 0.069 mm. The manufacturer's XH drawing identifies
these retention kinks. Moving the J2 housing 1 mm down is rejected; that
negative control is retained in evidence/housing-collision-negative.json.
The full assembly now passes the local strict design loop against the
reviewed generic contact-propagation fix in KernelCAD PR759: functional and
quality verdicts are true with zero blockers. The same housing-shift negative
remains rejected. Exact connector frames replace four unresolved topology
references without changing geometry. See the local-strict receipts and
scope file. Hosted strict acceptance remains pending deployment/replay; the
local result is not a hosted or physical qualification. No physical retention,
print tolerance, or screw load is qualified.

## Build and flash

From firmware/:

~~~sh
git clone --branch v1.4.0 --depth 1 https://github.com/STMicroelectronics/STM32CubeH5.git deps/STM32CubeH5
git -C deps/STM32CubeH5 submodule update --init --depth 1 Drivers/CMSIS/Device/ST/STM32H5xx Drivers/STM32H5xx_HAL_Driver
git clone --branch v2.0.0 --depth 1 https://github.com/w1ne/udslib.git deps/udslib
make
~~~

The Makefile checks the Cube commit and UDSLib version. It uses GNU Arm
Embedded GCC. build-manifest.json records the actual compiler and binary
hashes. ST-derived files retain their license headers. provenance.json
identifies the exact ST and core application sources.

Connect CN1, retain the board's default non-secure development configuration,
and program h563-uds-physical.elf through onboard ST-LINK using
STM32CubeProgrammer. Reset; open virtual COM at 115200 8N1. Expected:
H563-UDS-ECU PHYSICAL HAL 500K/2M FD, then ECU_READY. These strings alone
do not establish protocol operation.

## Assembly and bring-up

1. Populate semiconductors and passives before connectors. Inspect U1 pin 1
   and D1 orientation against the native board and BOM.
2. With power off, check supply shorts and every harness connection.
3. Fit termination at both bus ends. With the complete bus unpowered,
   measure approximately 60 Ω between CANH and CANL.
4. Apply CN1 USB power. Check J1 5 V and 3.3 V; check RXD idle high.
5. Configure the tester for ISO CAN FD, 500 kbit/s / 2 Mbit/s. Request
   DID 0xF190 at ID 0x7E0; expect 62 F1 90 at response ID 0x7E8.
6. Run the complete 16-step scenario. Record the 603-byte response, negative
   response, extended-session gating, transmit-before-reset, and reconnect.
   Capture bus timing and error counters before physical acceptance.

The model/source package has no recorded EMC, environment, automotive,
or physical security qualification. It is a bench demonstration.

## Repeat simulation

From this package directory, use the pinned LabWired CLI 0.26.0 release:

~~~sh
labwired test --no-key --script runtime/test.yaml --output-dir out/physical-runtime --no-uart-stdout --run-manifest
~~~

The CLI SHA-256 is
`0293aeb9a3bc76f1b0435d2de047ec1c55d6f4ed50dcaf3ad7bc72cd5929866c`.
The portable system uses the release's built-in `stm32h563` descriptor,
`cpu_hz: 250000000`, UART3 for console output, and the existing generic
`uds-tester` on FDCAN1. Request and reply IDs are 0x7E0 and 0x7E8.
`runtime/test.yaml` loads the unchanged `h563-uds-physical.elf` supplied for
flashing. Its SHA-256 is
`d78d30a8ae57835c237e21c99104b56e1fcf50fcd8872440c986132eba67275f`.

`evidence/physical-runtime/` contains the actual result, decoded frame report,
run manifest, UART output and invocation. The test checks the physical-image
boot banner, two ready states across reset, and completion of all 16 tester
steps. The calibration step compares all 603 reassembled bytes. Frames longer
than eight bytes carry FD/BRS; the short responses remain classic CAN. The
recorded CPU-cycle timestamps describe model execution, not measured bus
serialization at 500 kbit/s / 2 Mbit/s. The model does not qualify oscillator
accuracy, analog transceiver behavior, cable loading, or EMC.

The earlier `evidence/simulator-summary.json` and `simulator-result.json`
retain the distinct legacy fixture result at core source commit
941a6c5caf0c53b66aa5af9290e5ecba5972ec72. That source revision is not asserted
as the build revision of the separately pinned 0.26.0 release binary.

## Primary sources

- [StarTech.com USB2AC1M manufacturer datasheet](https://media.startech.com/cms/pdfs/usb2ac1m_datasheet.pdf)
- [ST product and MB1404 design downloads](https://www.st.com/en/evaluation-tools/nucleo-h563zi.html)
- [ST UM3115: CN8/CN9 pinout and board dimensions](https://www.st.com/resource/en/user_manual/dm00936683.pdf)
- [ST HAL FDCAN example, exact source revision](https://github.com/STMicroelectronics/STM32CubeH5/tree/0d526a4930310cf8fa6dce7538ab891cc37eb250/Projects/NUCLEO-H563ZI/Examples/FDCAN/FDCAN_Com_Polling)
- [MCP2562FD datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/20005284A.pdf)
- [PESD2CAN datasheet](https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf)
- [JST XH clinched-lead dimensions](https://www.jst.com/wp-content/uploads/2025/06/eXH.pdf)
- [JST XH family](https://www.jst-mfg.com/product/index.php?lang=en&series=277)
- [PCAN-USB FD](https://www.peak-system.com/products/hardware/external-pc-interfaces/pcan-usb-fd/?L=1)
- [Tracking issue #3554](https://github.com/w1ne/labwired/issues/3554)

## Complete offline firmware source

The complete application and required pinned vendor sources are available in [the source archive](firmware/source/stm32h563-uds-complete-source.tar.gz). The archive is 1,635,372 bytes. [Build instructions](firmware/source/BUILD.md), the [per-file source manifest](firmware/source/source-bundle.json), and the [fresh extracted-source rebuild receipt](firmware/source/rebuild-evidence.json) are included.

The fresh rebuild matches the accepted flash BIN and every loadable ELF segment, including address, data, memory extent, flags and entry point. Relocated debug paths change the rebuilt ELF file hash; the original tested ELF files remain unchanged. Both an altered vendor byte and an unlisted dependency file are rejected by the source verification gate. This source rebuild adds no physical test claim.
