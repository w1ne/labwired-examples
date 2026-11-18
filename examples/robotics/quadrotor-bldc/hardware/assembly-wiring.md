# Actual 5-inch quadrotor: ESC, controller, motors, propellers, battery

This is a physical wiring plan, not a simulated flight receipt. It uses the real
[OpenESC-30x30 board](esc-4in1/), [OpenFC-Lite rev2-LW1 flight controller](flight-controller-openfc-lite-rev2-lw1/),
[OpenFrame-5F manufacturer frame](frame-openframe-5f/) and exact commercial motors/props
in [system-bom.csv](system-bom.csv).

## Electrical architecture

- One 4S LiPo pack (14.8 V nominal, 16.8 V full), XT60, feeds both the ESC high-current
  bus and the flight controller supply through the eight-position stack connector.
  Seven conductors are populated; circuit 4 is empty at both ends.
- Install the selected Panasonic EEUFR1H471, 470 uF / 50 V, at the actual
  battery landing pads: positive to U3.1 `/CSA+`, negative to U3.2 `GND`.
  `/CSA+` is upstream of the current shunt; U3.3 and J1.1 `+BATT` are downstream.
  The [purchased-part record](purchased-part-envelopes.json) retains body/lead
  tolerances, ripple current and impedance. Support the body and insulate the leads.
- OpenESC is a real four-channel design. Four AT32F421G8U7 MCUs implement AM32/DShot,
  with four NSG2065Q gate drivers and 24 SP40N01GHNK MOSFETs.
- OpenFC-Lite uses an RP2354B and Betaflight, 30.5 mm stack spacing. It drives four
  DShot signal lines, with the ESC power stage providing high current.
- Four EMAX ECO II 2306 2400KV motors have three independent phase wires each,
  and are installed on the frame's 16×16 mm M3 motor mounts.

### ESC-to-FC JST-SH 8-pin harness

| Pin | OpenESC signal | OpenFC use | Design acceptance |
|---|---|---|---|
| 1 | +BATT | Pack voltage / FC power | 4S 16.8 V maximum charge |
| 2 | GND | Return | Single common reference |
| 3 | /CURR | FC current-sense ADC | Calibration required |
| 4 | Not connected on OpenESC | FC reserves ESC telemetry UART | No wired UART telemetry; use bidirectional DShot where supported |
| 5 | /M1 | DShot 1 | 3.3 V logic compatibility to verify |
| 6 | /M2 | DShot 2 | 3.3 V logic compatibility to verify |
| 7 | /M3 | DShot 3 | 3.3 V logic compatibility to verify |
| 8 | /M4 | DShot 4 | 3.3 V logic compatibility to verify |

Build `LW-QUAD-SH8-102` from two JST SHR-08V-S-B housings and seven
ASSHSSH28K102 precrimped leads. Populate circuits 1, 2, 3, 5, 6, 7 and 8
straight through; leave circuit 4 empty at both ends. The `-B` housing has
protrusions and an 11 mm nominal width. Its inside wire length is
101.6 +/-5 mm; the overall terminated lead is 109.4 +/-5 mm. Verify the
moulded circuit-1 marks and continuity against the native PCB, then secure
the loop clear of board edges and propeller sweeps. The exact pad centres
and native-to-assembly XY transforms are in
[native-harness-endpoints.json](native-harness-endpoints.json). Pad centres
are not connector mating-face datums.

### Battery connection and retention

The power lead uses an AMASS XT60H-M.G.Y with its 98032.PG cover, plus
150 mm design cuts of red TE 55A0111-12-2 and black 55A0111-12-0 wire.
Red goes to U3.1 `/CSA+`; black goes to U3.2 `GND`. Install the connector
cover and body strain relief so pull does not load the PCB solder joints.
The manufacturer specifies 30 A with 12 AWG at its stated 30 K temperature-rise
condition; the connector name is not a 60 A continuous system rating.

The selected Tattu TA-RL3-120C-1550-4S1P body is nominally 76 x38 x33 mm.
Use two RadioMaster HP0157.0103 straps, 260 x20 mm each, and the fitted
battery support. The cited battery table publishes no dimensional tolerance.
The purchased-part record separates nominal dimensions from actual tolerance
limits; installation and load acceptance belong to the fitted assembly receipt.

The RadioMaster RP1 V2 and its harness are an optional CRSF flight extension.
They are listed explicitly in the BOM, with FC CN1.1 +5V, .2 GND, .3 RX
and .4 TX. Receiver TX connects to CN1.3; receiver RX connects to CN1.4.
They are not required by the native five-controller motor-bench proof.

### Physical motor connections, 3 wires per motor

The manufacturer's board-outline footprint U3 contains duplicated solder pads for
each phase, but only one electrical net per phase. The real PCB and netlist confirm:

| ESC channel | DShot input | Phase A solder pad | Phase B solder pad | Phase C solder pad | Declared Quad-X location and native CAD centre (mm) |
|---|---|---|---|---|---|
| ESC1 | /M1 | U3 pad 23 | U3 pad 22 | U3 pad 21 | Rear right: (-89, +69.534420756) |
| ESC2 | /M2 | U3 pad 20 | U3 pad 19 | U3 pad 18 | Front right: (-89, -69.534420756) |
| ESC3 | /M3 | U3 pad 15 | U3 pad 16 | U3 pad 17 | Rear left: (+89, +69.534420756) |
| ESC4 | /M4 | U3 pad 12 | U3 pad 13 | U3 pad 14 | Front left: (+89, -69.534420756) |

There are 12 separate three-phase motor leads plus battery input and DShot harness.
This pad map is extracted from the actual PCB nets. Check physical silkscreen and
orientation before soldering.

Use Betaflight's Quad-X motor reorder and direction tests with propellers removed.
The source-bound assembly uses +Z up and -Y forward toward the camera.
Body right is -X; body left is +X. The native PCB channel order remains
M1/M2/M3/M4. The CAD rotor controls now use these exact positions. This
corrects the earlier CAD left/right labels without moving the frame or boards.
Physical wiring and rotation checks remain required after assembly.

### Motors and factory propellers

- 4 × EMAX ECO II 2306 2400KV, manufacturer SKU ECO223062400, 16×16 mm M3
  mounting pattern, M5 prop shaft; selected for 4S.
- 1 × Gemfan Hurricane 51433-3 package, four polycarbonate propellers:
  2 CW + 2 CCW, 5.1-inch class, M5 center bore.
- The evaluated OpenFrame-5F has motor axes at [±89, ±69.534420756] mm.
  Its 226 mm diagonal is not a square-X layout. The minimum adjacent-axis
  distance is 139.0688 mm. A 129.7 mm propeller sweep leaves 9.3688 mm
  nominal disk-to-disk clearance. This is a geometric estimate; propeller
  flex, tolerance, frame deformation and wire routing remain untested.
- Opposite motors should rotate in the same direction. Match installed CW/CCW
  props to the measured direction and Betaflight's configured prop-in/prop-out
  convention; never infer direction solely from an ESC channel number.
- Check mounting screw protrusion against stator windings. EMAX includes
  multiple M3 lengths; do not use a longer screw without measuring.

## Preconditions for powered tests

1. Inspect the ESC for assembly defects, solder bridges, capacitor polarity,
   battery and signal connector pinout, and correct voltage.
2. Verify no motor phase short to GND or +BATT and no phase-to-phase hard short.
   Compare with motor winding resistance using an appropriate low-ohm method.
3. Power FC and ESC with propellers removed, using current-limited power or
   appropriate smoke-stop protection for initial tests.
4. Verify DShot motor order, direction, ESC firmware and FC arming behavior.
5. Exercise radio/CRSF loss and arming failsafe before installing props.
6. Validate battery voltage sag, wire and MOSFET temperature, motor current,
   vibration, fasteners, and battery retention under controlled conditions.

No physical power-on, thermal, vibration, aerodynamic, flight or transient
validation has been performed. The reviewed ESC now has 1,067 pads, including
the three MCU package pads omitted by the previous repaired footprint. Native
ERC, DRC, connectivity and schematic-to-PCB parity checks pass within their
configured scope. The 15 microvias, six-layer stackup, assembly clearances and
power behavior still require manufacturing review. See [electrical validation](esc-4in1/validation/README.md).
