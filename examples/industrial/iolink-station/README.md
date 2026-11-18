# Two-port STM32L476 IO-Link input station

This package retains the published station's three **NUCLEO-L476RG** controllers
and two independent device ports. It provides physical ST HAL firmware, two
L6360 master interfaces, two L6362A device interfaces, and a native routed
eight-input PCB for each device. The physical firmware supports **COM2,
38,400 bit/s, 8 data bits, even parity, one stop bit**, with one input process
byte per device, TYPE_2_1 M-sequences and a 10 ms configured cycle.

**Release state:** electrical and firmware build candidate. Both physical
images build, the unchanged device image passes a digital boot/wake/protocol
probe, and the native input PCB has zero ERC,
DRC, unconnected-net and schematic-parity findings. A complete fitted station
mount, physical power/waveform measurements and a two-port hardware acceptance
run are still required. The L6360 source/model review found a stored-parity
reset assumption in the master driver; its repair and full three-node
physical-image runtime proof remain pending. See [the exact device runtime
proof and reproduction command](runtime/README.md).

## Contents and evidence

| Item | Files | Evidence |
|---|---|---|
| Physical master | `firmware/master/`, `firmware/common/` | ST HAL, real I2C L6360 transactions, timer-generated wake-up and two UARTs |
| Physical input devices | `firmware/device/` | L6362A control, overload wake-up, inverted UART interface and HC165 input scan |
| Editable input electronics | `electronics/input-board/` | KiCad 10 project, schematic, PCB and local libraries |
| Fabrication and assembly | `manufacturing/input-board/` | Copper/mask/silkscreen/paste/outline Gerbers, drill, DSN/SES, netlist and schematic PDF |
| Native board geometry | `cad/input-board-populated.step`, `cad/input-board-substrate.step` | KiCad exports; populated render in `cad/input-board-iso.png` |
| Parts and wiring | `hardware/station-bom.csv`, `hardware/input-board-bom.csv`, pin-map and harness JSON | Exact purchased board, PHY routing, connector and passive identities |
| Build and checks | `evidence/` | Source/binary hashes, build logs, host tests, timing calculation, native ERC/DRC and visual review |
| Purchased routed boards | `hardware/vendor-sources.json`, `hardware/fetch-vendor.py` | Exact official ST schematic/BOM/manufacturing archive hashes |

The ST shields are purchased populated boards. Their official manufacturing
archives establish routed-board provenance; they do not make the shield CAD
editable in KiCad. The input PCB is fully editable in this repository.
The common MB1136 Altium design is a Nucleo geometry reference, not a claim
that a generic board BOM reproduces every NUCLEO-L476RG variant.

## Hardware and power

Use one NUCLEO-L476RG with **two STEVAL-IOM001V1** shields for the master.
Use one NUCLEO-L476RG, one **STEVAL-IOD003V1**, and one input PCB for each
device. Keep the ST-LINK section of all three Nucleos attached and USB powered.

The selected field supply is **Mean Well GST25A24-P1J**, 24 V, 1.04 A,
with a centre-positive 2.1 × 5.5 mm output. Connect its plug to an
**Adafruit 368** female terminal adapter. Use separate **WAGO 221-413**
three-way splices for +24 V and return, with one wire per clamp. Feed both
master shields: **CN1.3 = +24 V; CN1.1 = GND**. Leave CN1.2 and the
alternative 7–12 V input CN2 unused. Set SW6 to pins 2–3.

Each three-wire field cable connects a master's **CN3** to the corresponding
device shield's **CN1**: pin **1 = L+**, **3 = GND**, **4 = C/Q**.
Pins 2 and 5 are unused for this Type A package. The exact cable cuts,
colours and terminations are in `hardware/harnesses.json`.
These are screw-terminal bench cables, not an M12 connector assembly.

Supply the Nucleo logic through the three USB/ST-LINK connectors, with each
Nucleo JP5 at **U5V**. On each IOD shield, leave **JP3, JP4 and JP5 open**:
the L6362A generated rails must not backfeed the USB-powered Nucleo rails.
Keep JP1 closed and JP2/JP6 open. A region-approved IEC C13 mains lead for
the selected Class I supply is required; its regional plug part number is
not selected by this package.

Disconnect USB and 24 V before solder-bridge or resistor changes. Identify
connector pin 1 from the board marking and the vendor drawing before wiring.
Check continuity and absence of rail shorts before applying power. This
open bench station does not claim an industrial enclosure, ingress rating,
EMC qualification or galvanic isolation.

## Required Nucleo clock configuration

On **all three** NUCLEO-L476RG boards set **SB16, SB50 and SB54 ON**;
set **SB55 OFF** and leave **R35/R37 not fitted**. UM1724 §7.9.1 documents
the retained ST-LINK's 8 MHz MCO into PH0/HSE. Firmware uses HSE bypass and
PLL /2 ×40 /2 for an 80 MHz CPU/peripheral clock. It fails initialization if
this source is unavailable.

At nominal 80 MHz, the UART divider gives **38,406.145 bit/s**, a
**+160.026 ppm** divider error. The physical C/Q rate remains unmeasured.
The L476 MSI automatic-trim specification is wider than the IO-Link master
±0.1% rate requirement, so the physical target does not use MSI as its
communication clock. The ±5% sweep in the analytical timing receipt is a
margin exercise for the I2C/wake calculation, not an allowed UART frequency
error or a measured oscillator specification.

## Master rework and pin map

Both IOM shields share I2C1: **PB8 AF4 / CN10.3 = SCL** and
**PB9 AF4 / CN10.5 = SDA**. Keep the factory pull-up connections JP2/JP3.
The two local PHY pull-up networks and their routing resistors remain on
the purchased shields; do not add a hard connection between their local VDD
outputs and the Nucleo 3.3 V rail.

| Signal | Port 1: default shield | Port 2: reconfigured shield |
|---|---|---|
| INCQ / transmit | PA9, USART1 AF7, CN10.21, R5 | PA0, UART4 AF8, CN7.28, R115 |
| OUTCQ / receive | PA10, USART1 AF7, CN10.33, R9 | PA1, UART4 AF8, CN7.30, R119 |
| ENCQ | PC0, CN7.38, R3 | PA5, CN10.11, R143 |
| ENL+ | PA6, CN10.13, R4 | PA8, CN10.23, R114 |
| Active-low reset | PB5, CN10.29, R8 | PC1, CN7.36, R108 |
| Active-low IRQ | PA4, CN7.32, R7 | PB0, CN7.34, R117 |
| IPS161H L+ ON | PB4, CN10.27, R162 | PA7, CN10.15, R163 |
| SA2/SA1/SA0 | 000 | 001 |
| Seven-bit I2C / HAL argument | 0x60 / 0xC0 | 0x61 / 0xC2 |

On the second shield remove the seven default routing resistors in the
port 1 column and fit the seven port 2 positions. Use **ERJ3BD1000V,
100 Ω, 0.5%, 0.1 W, 0603**, as identified in the official shield BOM.
Do not substitute zero-ohm links.

SW0/SW1/SW2 select SA0/SA1/SA2; pins 1–2 select ground and pins 2–3 select
VDD. Set all three to 1–2 on port 1; set SW0 to 2–3 and SW1/SW2 to 1–2
on port 2. UM2414's 0/1 address values describe the selectable suffix;
DS8900 §6.8 supplies the fixed 1100 prefix.

On both IOM shields set **SW3 2–3** for 3.3 V logic, **SW4/SW5 1–2**
for MCU enable control, **SW6 2–3** for the CN1 supply and **SW7 1–2**
for Type A. Retain factory J1/J2 routing. Firmware holds the auxiliary
IPS161H enable low; it uses the L6360 L+ path.

On the master Nucleo set **SB56/SB51 ON** and **SB46/SB52 OFF**, preserving
PC1/PC0 on A4/A5 for port 2 reset and port 1 ENCQ. Keep **SB13/SB14 ON**
and **SB62/SB63 OFF** for the existing ST-LINK USART2 routing. Optional
OUTIQ routing is not used.

## Device rework and input harness

On each IOD shield remove **R102** and fit **R112** to hold IN1 at ground.
Remove **R101** and fit **R111** to route IN2 to PA9/USART1 TX. Retain
R103 for OUTIQ/PA10, R109 for EN/PC7, R105 for OL/PA6 and R104 for
DIAG/PA4. Use the same 100 Ω routing part stated above. This requires
four additional resistors for the two devices, giving eleven for the
station's complete rework.

Close all three positions of SW1; retain SW2/SW3 at pins 2–3. The firmware
uses L6362A push-pull signalling, the hardware overload input for physical
wake-up, and **TXINV/RXINV** on USART1 for the resulting logic polarity.
It does not replace wake-up with a UART 0x55 byte.

The six-pin input PCB connector **J1** connects to the Nucleo Morpho
underside. Fit the mating XHP-6 shell with SXH-001T-P0.6 contacts; terminate
the Nucleo ends with four M20-1060100 single shells, one M20-1060200
two-position shell, and six M20-1180042 contacts per device. Put CN10.28
(QH, white) and CN10.30 (CLK, blue) in the shared two-position shell; this
avoids interference between adjacent single housings. Harwin specifies
5.50–6.30 mm mating pin length. Use the mount's controlled insertion stop;
do not force a housing flush against a longer underside header tail.

| Input PCB J1 | Signal | NUCLEO-L476RG |
|---|---|---|
| 1 | GND | CN7.20 |
| 2 | +3.3 V | CN7.16 |
| 3 | HC165 clock | PB13 / CN10.30 |
| 4 | Active-low parallel load | PC6 / CN10.4 |
| 5 | HC165 QH | PB14 / CN10.28 |
| 6 | GND | CN10.20 |

The input PCB runs only at **3.3 V**. Its sixteen-pin J2 has input A–H
on odd pins and ground on even pins. Fit a shunt across each input/ground
pair to read zero; remove it to read one through the 10 kΩ pull-up.
A maps to process bit 0 and H to bit 7. All shunts removed produce 0xFF;
all fitted produce 0x00. The firmware scans the HC165 at 1 kHz.

## Input PCB manufacture and assembly

Fabricate two copies of the supplied **50 × 40 × 1.6 mm**, two-layer board.
Use the checked-in Gerber job and drill, including the NPTH mounting drills.
The four Ø3.2 mm mounting centres are (4,4), (46,4), (4,36), (46,36) mm.
The project requires 0.20 mm electrical clearance, 0.25 mm minimum track
width, 0.60/0.30 mm minimum via diameter/drill and 0.50 mm copper-to-edge
clearance. No DRC exclusions are configured.

Fit the two capacitors and eight pull-up resistors first. Fit U1 with its
pin 1 at the marked notch end, then J1 and J2 with the marked pin 1
orientation. U1 is soldered directly to the DIP footprint; an unmodelled
IC socket changes the mechanical envelope and is not part of this BOM.
Inspect soldering and test 3.3 V/GND continuity before plugging in the
Nucleo harness. The populated STEP contains purchased component models;
the board's fit in the full station remains a separate assembly check.

## Build and flash

Use GNU Arm Embedded GCC 13.2.1 or a compatible Cortex-M4 hard-float
toolchain, Python 3, Git and Make. The optional host protocol test requires
CMocka development headers/library (for example, libcmocka-dev). The reviewed binaries and compiler
receipt are under `firmware/release/` and `evidence/physical-build.json`.
Dependencies are fetched at exact public revisions, with unchanged source
checks before each build.

From this package directory:

```sh
python3 firmware/master/fetch-deps.py
make -C firmware/master -j2
make -C firmware/device -j2
make -C firmware/master test
python3 firmware/tests/run-protocol-profile.py
```

The master and device Makefiles use the ST NUCLEO-L476RG startup, linker
script, CMSIS and HAL from STM32CubeL4 v1.18.2. The device stack pin includes
the reviewed response-start timing and fixed-baud recovery changes in
[iolinki PR55](https://github.com/w1ne/iolinki/pull/55) and
[PR56](https://github.com/w1ne/iolinki/pull/56). It keeps timing enforcement
enabled. The master stack is the exact vendored source from the recorded
labwired-core revision. The manifest distinguishes source revisions from
merge/release status.

With one intended ST-LINK connected at a time, a standard OpenOCD install
with ST-LINK and STM32L4 support can program and verify the selected ELF:

```sh
openocd -f interface/stlink.cfg -f target/stm32l4x.cfg \
  -c "program firmware/master/build/iolink-master.elf verify reset exit"
openocd -f interface/stlink.cfg -f target/stm32l4x.cfg \
  -c "program firmware/device/build/iolink-device.elf verify reset exit"
```

Repeat the device operation for the second device. These commands are
reproduction instructions; no physical flashing receipt is included.

## Firmware behaviour and acceptance

The master initializes both L6360s with checked readback/parity, controls
L+ and C/Q, generates an 80 µs wake pulse with timer outputs, waits the
enable/test guard and runs both COM2 ports. It uses fresh clock samples
for each port. NACK, parity, register mismatch and severe PHY faults disable
the affected outputs and latch a diagnostic. The physical device uses an
IRQ receive queue, waits for transmit complete before releasing C/Q, and
records the last request/reply boundary. Its timing quality is explicitly
**ESTIMATED** because IRQ/software timestamps are not a C/Q hardware capture.

Observe `g_master_state[2]`, `g_master_pd[2]`, `g_master_tick_result[2]`
and `g_startup_error` in the master ELF. On each device observe
`g_device_state`, `g_device_pd`, `g_phy_error`, `g_uart_errors`,
`g_rx_overflows`, `g_wake_events` and `g_tx_deadline_errors`.
Set different input shunts on the two boards and confirm independent
process bytes. The image's unassigned bench identity is vendor **0xFFFF**,
device **0x000001**, product **L476-L6362A-DI8**. The full 96-bit MCU UID
is encoded into a sixteen-character serial number.

The recorded checks cover twelve L6360 host cases, analytical I2C/wake
bounds, 38 shared-stack CTest targets (including response timing and fixed-baud
recovery), four TYPE_2_1 byte profiles, both cross-builds, the device
description and native input PCB checks. The byte-profile fixture disables
its timing gate because it has no timed electrical PHY; the physical image
keeps timing enforcement enabled. They do not establish
physical start-bit delay, wake amplitude/duration, C/Q bitrate, current
limiting, thermal behaviour, cable noise immunity or device conformity.
Before a physical release, capture both ports' wake and request/reply
waveforms, measure the clock/rate under the supported conditions, exercise
disconnect/re-wake and fault recovery, and record independent process data.
The mechanical package must also pass the fitted assembly review.

The canonical simulator remains
[the existing IO-Link station](https://app.labwired.com/?lab=iolink-station-l476).
Its CMSIS byte-wake fixture is not flashed onto these shields. Changes to
physical board support must preserve its separate runtime regressions.

## Device description

The editable JSON and generated IODD are in `description/`. The descriptor
uses the actual five-position screw terminal as `OtherConnectionT`, with
L+/L-/C/Q on pins 1/3/4 and the cable colours in the harness table. Its eight
Boolean process fields map A to bit 0 through H to bit 7. The IODD cycle
value is 10,000 microseconds, distinct from firmware's 100-unit API value
and the direct-page encoded value 0x49.

Generation reuses the pinned iolinki generator and CRC tool. It requires
Node.js 22 and xmllint. Fetch and verify the official schema archive recorded
in `evidence/device-description.json`, extract its Schemas directory, then run:

```sh
python3 description/generate.py --schema /path/to/Schemas/IODD1.1.xsd
```

The recorded semantic subset, CRC and official XSD checks pass. A current
IODD business-rule checker, registered production identity and hardware
conformity evidence are separate outstanding checks.

## Licensing

New package source and authored board files use the repository MIT license.
ST dependencies retain their included vendor licenses. The linked firmware
contains **iolinki and iolinki-master GPL-3.0-or-later** code; the corresponding source revisions,
build scripts and GPL text are supplied/referenced here. This README does
not relicense the linked images as MIT. Official ST board archives retain
ST's source licensing and notices.

## Primary references

- [UM2414 Rev 2: IOM shield routing, switching and power](https://www.st.com/resource/en/user_manual/dm00505670-getting-started-with-the-iolink-phy-master-evaluation-board-with-stm32-nucleo-stmicroelectronics.pdf)
- [UM2424 Rev 2: IOD shield routing, mode and power](https://www.st.com/resource/en/user_manual/um2424-getting-started-with-stevaliod003v1-iolink-phy-device-evaluation-board-compatible-with-stm32-nucleo-stmicroelectronics.pdf)
- [UM1724 Rev 17: Nucleo solder bridges, clocks and connectors](https://www.st.com/resource/en/user_manual/dm00105823-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf)
- [L476 DS10198 Rev 11: alternate functions and clocks](https://www.st.com/resource/en/datasheet/stm32l476rg.pdf)
- [L6360 DS8900 Rev 9](https://www.st.com/resource/en/datasheet/l6360.pdf)
- [L6362A datasheet](https://www.st.com/resource/en/datasheet/l6362a.pdf)
- [SN74HC165 datasheet and package](https://www.ti.com/lit/ds/symlink/sn74hc165.pdf)
- [IO-Link Interface and System Specification v1.1.4: §7.3.2.2, Table 9 and Annex A/B](https://io-link.com/fileadmin/user_upload/Downloads/Package_2024/IOL-Interface-Spec_10002_V114_Jun24.pdf)
- [Tracking issue #3555](https://github.com/w1ne/labwired/issues/3555)
