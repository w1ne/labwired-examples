# Actual 5-inch quadrotor: ESC, controller, motors, propellers, battery

This is a physical wiring plan, not a simulated flight receipt. It uses the real
[OpenESC-30x30 board](esc-4in1/), [OpenFC-Lite flight controller](flight-controller-openfc-lite/),
[OpenFrame-5F manufacturer frame](frame-openframe-5f/) and exact commercial motors/props
in [system-bom.csv](system-bom.csv).

## Electrical architecture

- One 4S LiPo pack (14.8 V nominal, 16.8 V full), XT60, feeds both the ESC high-current
  bus and the flight controller supply through the standard eight-wire stack connector.
- Place a separately sourced 470 uF / 50 V low-ESR bulk capacitor directly across
  ESC battery pads, observing capacitor polarity. Select actual part and ripple rating
  before manufacturing.
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

Do not assume connector orientation matches just because both are JST-SH.
Confirm pin 1 at each end against both PCBs before crimping or installing a harness.

### Physical motor connections, 3 wires per motor

The manufacturer's board-outline footprint U3 contains duplicated solder pads for
each phase, but only one electrical net per phase. The real PCB and netlist confirm:

| ESC channel | DShot input | Phase A solder pad | Phase B solder pad | Phase C solder pad | Provisional Quad-X location |
|---|---|---|---|---|---|
| ESC1 | /M1 | U3 pad 23 | U3 pad 22 | U3 pad 21 | Rear right |
| ESC2 | /M2 | U3 pad 20 | U3 pad 19 | U3 pad 18 | Front right |
| ESC3 | /M3 | U3 pad 15 | U3 pad 16 | U3 pad 17 | Rear left |
| ESC4 | /M4 | U3 pad 12 | U3 pad 13 | U3 pad 14 | Front left |

There are 12 separate three-phase motor leads plus battery input and DShot harness.
This pad map is extracted from the actual PCB nets. Check physical silkscreen and
orientation before soldering.

Use Betaflight's Quad-X motor reorder and direction tests with propellers removed.
The location mapping is provisional, not proof of channel order on assembled hardware.

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
