# Native OpenFC-Lite rev2-LW1 firmware

This package builds the firmware for the routed **RP2354B QFN80** flight
controller in `hardware/flight-controller-openfc-lite-rev2-lw1`. It uses the
populated BMI270 and the native connector nets. The ELF and UF2 are
byte-identical in two separate output directories. Physical board bring-up,
sensor motion, motor direction and flight qualification have not been run.
The existing STM32 motor bench is a separate electrical test fixture; it is
not the runtime proof for this RP2354B image.

## Hardware identity and defaults

| Function | Native GPIO / connector | Configured behavior |
| --- | --- | --- |
| MCU | U2 RP2354B, 520 KiB SRAM, 2 MiB stacked flash | RP2350B target, ARM Secure image |
| Motors M1 / M2 / M3 / M4 | GPIO31 / 30 / 29 / 28; P1.5 / 6 / 7 / 8 | DShot600 with bidirectional DShot |
| CRSF receiver | CN1.3 GPIO3 RX; CN1.4 GPIO2 TX; CN1.1 +5V; CN1.2 GND | PIOUART0, CRSF |
| Digital VTX | U8.3 GPIO0 TX; U8.4 GPIO1 RX | UART0 MSP DisplayPort |
| Auxiliary UART | GPIO22 TX / GPIO21 RX | UART1; not the receiver default |
| Auxiliary PIO UART | GPIO26 TX / GPIO27 RX | PIOUART1; no serial ESC sensor |
| Gyro / accelerometer | U9 BMI270; SPI0 GPIO18 SCK, 19 SDO, 20 SDI; CS14; INT13 | BMI270 only; CW180 alignment |
| Analog OSD | GPIO4 write, 5 enable, 6 sync | Framebuffer OSD on PIO2 |
| I2C pads | GPIO16 SDA / GPIO17 SCL | I2C0 |
| microSD | SPI1 GPIO42 SCK, 43 SDO, 44 SDI; CS46 | Blackbox on SD card |
| Current / voltage ADC | GPIO40 / GPIO41 | ADC current scale 100, voltage scale 110 |
| RSSI / external ADC | GPIO45 / GPIO47 | Analog inputs 5 / 7 |
| 10V rail / status LED / beeper | GPIO11 / GPIO12 / GPIO7 | Native enable and indicator pins |
| LED strip | GPIO23 | PIO1, non-inverted level shifter |

The current meter measures battery-feed current. The native ESC has an
INA186A3 with gain 100 and two 0.2 mΩ shunts in parallel: the ideal transfer
is 10 mV/A. Betaflight expresses its default scale in mV per 10 A, hence 100.
The voltage divider is 100 kΩ / 10 kΩ, hence scale 110. These are
source-derived nominal values; physical calibration is still required.

The package uses a 4S battery. It does not carry the upstream rev3.3 voltage
rating. ESC J1.4 is unconnected, so `FEATURE_ESC_SENSOR` and
`ESC_SENSOR_UART` are absent. Bidirectional DShot uses the four motor signal
wires. GPIO15 is the BMI270 INT2 net; this target does not drive it as an
invented external gyro clock. See [axes.md](axes.md) for the source-based
sensor and body-frame registration.

## Source and build

The complete version authority is [source-versions.json](source-versions.json).
The main source is
[OpenDrone Betaflight 31066c0](https://github.com/OpenDrone-hw/betaflight/tree/31066c0f3789d2dbc34b394cf383b04394d43724).
The nominal target starts from
[config dd0e3200](https://github.com/OpenDrone-hw/betaflight-config/blob/dd0e3200b27f43b581f4559574ddc5d12e6040f0/configs/OPDR/OPENFC_LITE_RP2350B/config.h).
The fork's older config submodule describes manually repaired boards with
motor GPIO21/30/29/22 and UART GPIO16/17. Those nets do not match this native
derivative and are rejected by `verify_native_pins.py`.

The package config selects the supported macros in the pinned source. It
sets CN1 PIOUART0 as the receiver, removes unsupported serial ESC telemetry,
selects the populated BMI270 and its supported `CW180_DEG` alignment, and
places the LED-strip program on PIO1 to leave space for the 31-instruction
OSD program on PIO2. It does not rely on the later, unconsumed
`ENABLE_BMI270_ALIGN_AS_ICM` macro.

Build on Linux x86-64 with Python 3.12+, Git, GNU make, CMake and a native C++
compiler. USB development libraries are optional for the offline picotool
UF2 conversion; a USB-enabled picotool is needed for USB command-line
flashing. The script fetches exact source and dependency commits, downloads
and verifies Arm GNU 13.3.Rel1, and builds picotool 2.1.1. It writes all
objects outside the source tree and refuses an existing object directory.
The complete tracked source of the fork, SDK, TinyUSB, libcanard and picotool
is also supplied in `source/`; `source/archives.json` records each commit,
restore location and archive hash. The build script uses Git checkouts to
retain the source revision metadata used by the firmware build.

```sh
python3 firmware/native-fc/verify_native_pins.py
python3 firmware/native-fc/verify_artifacts.py
python3 firmware/native-fc/build.py --work-dir /tmp/openfc-lw1-build --jobs 4
```

Run these commands from `examples/robotics/quadrotor-bldc`. To reuse installed
tools, pass `--source-tree`, `--toolchain` and `--picotool`. Their exact
versions and source state are checked. `SOURCE_DATE_EPOCH`, the config
revision and source-path mappings are fixed. The script runs the upstream
UF2 and binary goals sequentially: each goal starts recursive make, so
parallel top-level goals would race while writing the same ELF.

## Artifacts and validation

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `betaflight_RP2350B_OPENFC_LITE_REV2_LW1.elf` |752808|`8c0a2953dbb7a65e1e22d949c5fd08f68a1babdeda88d13b14b2632bbc7ce43a`|
| `betaflight_2026.6.0-alpha_RP2350B_OPENFC_LITE_REV2_LW1.uf2` |860672|`0bdbdbe6f9f5f91b76285cef41a198bf866b400c76ee677887d93f60cb11a433`|
| `betaflight_2026.6.0-alpha_RP2350B_OPENFC_LITE_REV2_LW1.bin` |430128|`2cf345e0fa6f9b60b7039d568b52221059d6cdb68d6bf7c1ad9babf437f47ca5`|

The artifacts include the full link map and build receipt. The link uses
430128 bytes of its 1968 KiB application flash region, reserves 64 KiB for
configuration and 16 KiB for fonts, and uses 506832 of 524288 bytes in the main
RAM region (96.67%). SCRATCH_X uses 4096 bytes. This is the pinned fork's
hybrid RAM/flash layout; the high RAM allocation leaves limited headroom
for later feature changes. The upstream linker emits one RWX LOAD-segment
warning, retained in the build log.

`validation/native-pin-contract.json` verifies all 34 configured GPIO macros
against the immutable KiCad netlist and connector/component pads. It also
checks the LED/resistor and beeper-switch nets and rejects seven deliberately
wrong targets. `validation/artifact-contract.json` reads the actual ELF
reset templates to prove LED inversion1 and beeper inversion1/open-drain0;
the historical compiled image fails that check. The two flags mean active-high
outputs in the pinned driver. They do not invert the native pin assignments. `validation/reproduction.json`
records byte identity of the ELF and UF2 across separate build directories.
The map is retained as produced and can contain absolute build paths.
`validation/uf2-layout.json` checks block numbering, flash extent, RP2350
family and agreement with the raw binary. `validation/picotool-info.txt`
records the actual image metadata.

## Loading and qualification

The UF2 is the physical flash artifact. With the controller in its normal
RP2350 BOOTSEL mass-storage mode, copy that UF2 to the mounted RP2350 drive.
The BIN is an application image based at 0x10000000; it is not an ESC image.
This build script does not operate a connected board or change configuration.

First bench bring-up must confirm USB enumeration, the board's actual
receiver wiring, the six sensor axis directions described in `axes.md`,
voltage/current calibration and the native motor channel order. Propellers
must be removed for powered motor direction checks. The runtime folder
records the simulator's actual acceptance boundary and any executed model
gaps; successful compilation is not a flight-control runtime assertion.

The target and Betaflight source use GPL-3.0-or-later; see [LICENSE](LICENSE),
the exact source references and source archives. SDK and library licenses
remain in their corresponding source trees. No generated binary is presented
as a replacement for its corresponding source.
