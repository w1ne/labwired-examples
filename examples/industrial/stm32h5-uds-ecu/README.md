# STM32H563 UDS ECU bench fixture

This package adds a routed, protected CAN interface to the existing
[STM32H5 UDS Lab](https://app.labwired.com/?lab=stm32h5-uds-ecu). It preserves
the NUCLEO-H563ZI and PD1 transmit / PD0 receive assignment.

KiCad 10.0.8 reports **0 ERC violations, 0 DRC violations, 0 open connections,
and 0 schematic parity issues**. The physical firmware compiles. No physical
prototype has been assembled, flashed, electrically measured, or qualified.

## Firmware and evidence

| Target | Verified result | Limits |
|---|---|---|
| Existing simulator fixture, core 941a6c5caf0c53b66aa5af9290e5ecba5972ec72 | CLI 0.26.0: 16/16 diagnostic exchanges, 3/3 assertions, 603-byte response, negative response, reset and reconnect | Does not test physical clock, pin mux, transceiver, or elapsed time |
| Physical HAL target in firmware/ | Compiles with STM32CubeH5 v1.4.0 and UDSLib v2.0.0; binary hashes in build-manifest.json | No physical bus or simulator equivalence receipt |

The simulator firmware advances its time callback once per loop and omits
physical FDCAN timing and pin setup. Do not flash that image as this hardware
release. The physical build uses ST HAL/CMSIS for clock selection, PD0/PD1 AF9,
FDCAN filters/message RAM, SysTick milliseconds, and reset. Both targets reuse
the same UDSLib 2.0.0 application and post-transmit reset deferral.

## Native electrical design

Open electronics/can-interface.kicad_pro in KiCad 10. The board is
**60 × 40 × 1.6 mm**, two layers. Four 3.2 mm NPTH mounting holes are at
(4,4), (56,4), (4,36), (56,36) mm. The native board is the final routed
source. Manufacturing includes Gerber, drill, netlist, and schematic PDF.
cad/can-interface.step is the populated native export.

- **MCP2562FD-E/SN**, SOIC-8: pin 3 gets 5 V, pin 5 gets 3.3 V, pin 8 STBY
  is grounded. C1/C2 decouple each supply; C3 is local bulk capacitance.
- **PESD2CAN,215** protects the bus. D1 pin 1 is CANL, 2 CANH, 3 ground.
- JP1 enables the **120 Ω, 1%, 0.5 W** termination. Fit it at a bus end only.
- USB at NUCLEO CN1 is the only fixture power source. This carrier has no
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

J2 mates with XHP-3: **1 CANH, 2 CANL, 3 GND**. Twist H/L together.
With PEAK PCAN-USB FD IPEH-004022, connect J2.1 to D-sub pin 7, J2.2 to
pin 2, J2.3 to pin 3. Leave optional tester power pins disconnected. Fit
the tester's documented termination or an external 120 Ω termination.

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
the harness with two HellermannTyton T18R ties through the slots.

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
The full assembly acceptance remains pending the generic contact-check
correction. No physical retention, print tolerance, or screw load is qualified.

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

From core commit 941a6c5caf0c53b66aa5af9290e5ecba5972ec72, use CLI 0.26.0:

~~~sh
labwired test --script examples/h563-uds-ecu/uds-evidence.yaml --output-dir out/uds-evidence --no-uart-stdout
~~~

evidence/simulator-summary.json pins the CLI and committed simulator image.
evidence/simulator-result.json contains actual decoded traffic.

## Primary sources

- [ST product and MB1404 design downloads](https://www.st.com/en/evaluation-tools/nucleo-h563zi.html)
- [ST UM3115: CN8/CN9 pinout and board dimensions](https://www.st.com/resource/en/user_manual/dm00936683.pdf)
- [ST HAL FDCAN example, exact source revision](https://github.com/STMicroelectronics/STM32CubeH5/tree/0d526a4930310cf8fa6dce7538ab891cc37eb250/Projects/NUCLEO-H563ZI/Examples/FDCAN/FDCAN_Com_Polling)
- [MCP2562FD datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/20005284A.pdf)
- [PESD2CAN datasheet](https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf)
- [JST XH clinched-lead dimensions](https://www.jst.com/wp-content/uploads/2025/06/eXH.pdf)
- [JST XH family](https://www.jst-mfg.com/product/index.php?lang=en&series=277)
- [PCAN-USB FD](https://www.peak-system.com/products/hardware/external-pc-interfaces/pcan-usb-fd/?L=1)
- [Tracking issue #3554](https://github.com/w1ne/labwired/issues/3554)
