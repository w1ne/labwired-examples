# Native OpenESC 30 firmware

This package targets the four **AT32F421G8U7** controllers in the routed
quadrotor ESC board. It builds AM32 `OPENESC_30_F421` for the native PB4
DShot input, six gate outputs and three comparator inputs. The source
archive and patch include the complete corresponding F421 source. The
application uses AM32 2.21; the unchanged PB4 bootloader is release 19.0.0.

The historical four-STM32L476 motor bench is a different circuit and
firmware contract. Its runtime results do not qualify this board.

## Source and build identity

| Item | Pinned identity |
|---|---|
| Application upstream | `OpenDrone-hw/AM32`, commit `5f8978eeb618c14bb396af7ac049d2a5e7b5a508` |
| Native target patch | Local source commit `19df1ecfef4982302cacdd35bb0d921ceac83217`; complete archive and patch included |
| Bootloader | `am32-firmware/AM32-bootloader`, commit `a340e23f4fe270bf7a767156d3c24b10f22b521a` |
| Compiler | xPack Arm GNU 10.3.1-2.3, Linux x64 |
| MCU define | `AT32F421G8U7`; Cortex-M4 |
| Application target | `OPENESC_30_F421` |
| Bootloader target | `AM32_F421_BOOTLOADER_PB4` |
| Application flash use | 20,920 bytes, plus 32-byte target-name region |
| Application static/heap/stack RAM | 3,672 bytes under the selected linker script |

The source commit is retained in the included archive and patch. The
application repository denied this account's upstream push, so reproducing
the package does not depend on that unpublished branch. Archive hashes and
included paths are in [source-archives.json](sources/source-archives.json).
The original target patch is retained byte-for-byte as
sources/openesc30-native-target.patch.gz; decompress it before git apply.
All common C source, headers, F421 vendor/startup files, make scripts, root
makefiles and licenses needed for this target are included. Source for
other MCU targets and binary manuals is excluded.

A complete editable export is also supplied as
[sources/openesc30-native-source-v1.tar.gz](sources/openesc30-native-source-v1.tar.gz).
Extract it into an empty directory. The entry source is
am32-f421/Src/main.c; its expanded contents are the actual build inputs.
From that directory, run the following command:

```sh
python3 build.py --source-dir . \
  --toolchain-dir /absolute/xpack-arm-none-eabi-gcc-10.3.1-2.3 \
  --work-dir /absolute/new-empty-build-directory
```

The source bundle includes the complete target application and bootloader
sources, licences, explicit EEPROM fixture and flash-container tools.
The fresh expanded-archive replay reproduces the application ELF/BIN/HEX,
bootloader BIN/HEX, and complete flash ELF/BIN/HEX. Its per-file source
identity and build receipt are retained beside the archive and in evidence/.

Obtain the exact compiler archive identified by
[sources/toolchain.json](sources/toolchain.json), verify its SHA-256 and
extract it. Use Python 3.12+, GNU make and that compiler distribution:

```sh
python3 build.py \
  --toolchain-dir /absolute/xpack-arm-none-eabi-gcc-10.3.1-2.3 \
  --work-dir /absolute/new-empty-build-directory
```

The command checks the bundled source archives and compiler executables,
extracts the source into an empty directory, builds only the F421 targets,
and verifies the packaged application and bootloader flash hashes. It
retains the commands and logs in `build-receipt.json`. The application
startup assembler has an explicit source filename, and the build maps
compiler and assembler debug paths. These metadata changes do not alter
the application BIN or HEX. The unchanged bootloader source retains
location-dependent debug metadata; its reproducibility check covers the
BIN and official release HEX.

Run the source-to-board check with KiCad 10's Python installation:

```sh
/usr/bin/python3 validate-target.py \
  /absolute/build/am32-f421 \
  --output /absolute/output/target-validation.json
```

The validator resolves `hardware/esc-4in1/4in1.kicad_pcb` within this
package and checks its pinned hash. It verifies physical pad numbers and nets, compiled
target macros, all four DShot routes, all 24 gate routes, all 12 comparator
routes and absence of the unsupported sensor and telemetry paths. Five
negative binding controls and 23 sensor-configuration cases must pass.

## Native electrical contract

The same application runs on U2, U5, U7 and U9. The corresponding drivers
are U4, U6, U8 and U10, all NSG2065Q. The table describes each repeated
controller/driver channel.

| Function | MCU pin / QFN28 pad | Driver or connector path |
|---|---|---|
| DShot capture | PB4 / 25 | J1.5, .6, .7 or .8 through R20, R39, R57 or R87 respectively |
| Phase A high | PA10 / 20 | HIN1 / driver pad 22 |
| Phase A low | PB1 / 15 | LIN1 / driver pad 1 |
| Phase B high | PA9 / 19 | HIN2 / driver pad 23 |
| Phase B low | PB0 / 14 | LIN2 / driver pad 2 |
| Phase C high | PA8 / 18 | HIN3 / driver pad 24 |
| Phase C low | PA7 / 13 | LIN3 / driver pad 3 |
| Phase feedback A/B/C | PA0 / 6, PA4 / 10, PA5 / 11 | Three native comparator phase nets |
| Comparator reference | PA1 / 7 | Native common reference net |
| Voltage/current ADC | PA3 / 9 and PA6 / 12 | Not connected on this native board |
| Serial ESC telemetry | PB6 / 27 and J1.4 | Not connected on this native board |

The native board uses the internal HICK source. The pinned vendor clock code
selects HICK/2 x30, with AHB/APB1/APB2 dividers of 1, for the nominal 120 MHz
core and timer clock. No external crystal is substituted.

Capture uses TMR3 channel 1 with the default fixed DMA1 channel 4 route.
The target uses `AT_B`, `AT_045` and `DEAD_TIME=60`; at the nominal 120 MHz
timer clock the dead-time count is 0.5 us. That calculation is not a
measured gate waveform or a switching-loss qualification.

The validator uses the manufacturer QFN28 physical pad map. The prior
PCB copied adjacent `pin_function` text when restoring 16 omitted pads.
That metadata is now corrected, with every other PCB byte unchanged; see
`hardware/esc-4in1/validation/pad-function-correction-20261118.json`. The
qualified sources are the Artery AT32F421 datasheet v2.03, Figure 5 and pin
tables, and reference manual v2.05, the timer chapter and Table 9-3.
Their original URLs and document hashes are retained in `evidence/`.

## Sensing and configuration

The native ESC has no per-controller battery-voltage or current ADC path.
Its shared INA186 output is routed to the flight controller. The nominal
transfer is 10 mV/A from gain 100 and the two parallel 0.2 milliohm shunts;
physical calibration remains required.

`TARGET_NO_EXTERNAL_SENSE` prevents the firmware from interpreting floating
PA3/PA6 pins as measurements. The ADC sequence contains the internal VREF
and temperature channels only. Unsupported per-ESC current and voltage
telemetry are omitted. A stored EEPROM configuration that enables local
voltage cutoff or current limiting sets `sensor_configuration_error` and
prevents arming. Unsupported analog-input, external-NTC, voltage-ramp,
fixed-duty and fixed-speed compile modes fail compilation for this target.

The included 192-byte EEPROM is an explicit bench fixture. It selects
DShot, disables unavailable per-ESC voltage/current functions, retains the
100 C internal-temperature setting and encodes nominal 2400 KV as 2380 KV
under AM32's byte encoding. Its inherited 14-pole value is not a measured
motor parameter. The source, every changed byte and the exact fixture hash
are in `artifacts/openesc30-bench-eeprom.json`. Do not treat this fixture as
completed motor calibration or a flight configuration.

## Flash layout

| Region | Start | File / meaning |
|---|---|---|
| PB4 bootloader | `0x08000000` | `AM32_F421_BOOTLOADER_PB4_V19.hex`; 4,092 BIN bytes |
| Application | `0x08001000` | `AM32_OPENESC_30_F421_2.21.hex`; 27,648 BIN bytes |
| Target identity | `0x08007BE0` | Final 32 bytes of the application image |
| Configuration | `0x08007C00` | 192-byte bench EEPROM; remaining page bytes erased |
| Upper flash | `0x08008000` onward | Unused by this selected 32 KiB application layout on the 64 KiB MCU |

The application ELF includes a program-header segment at `0x08000000`.
Loading that ELF as a standalone reset image overwrites the boot vector
with ELF header bytes. Use the address-bearing HEX files for flashing, or
load the bootloader plus the application BIN at the specified address and
explicit EEPROM data. The packaged runtime proof loads the complete ELF
below through the ordinary loader and retains the real bootloader entry path.

`OPENESC_30_F421_complete.elf` is a standard loadable container for the
existing Lab/World loader. It contains the unchanged bootloader, unchanged
application and explicit EEPROM fixture in a 32,768-byte flash region,
with erased gaps filled by `0xFF`. Its entry is the bootloader reset vector.
The [container receipt](evidence/flash-container-receipt.json) checks every
loaded byte against those three input images. Application symbols are
retained for inspection; no instruction or peripheral operation is patched.
Reproduce it with `python3 pack-flash.py --toolchain-dir /absolute/toolchain
--output-dir /absolute/new-container-directory`. Its actual runtime
acceptance is recorded separately from byte-container verification.

## Acceptance state

The application ELF/BIN/HEX reproduce across the checkout and independent
archive builds. The unchanged bootloader BIN/HEX reproduce, including the
official PB4 release HEX. The complete 32,768-byte flash container also
reproduces from the expanded source bundle. Native validation covers
24 gate routes, four DShot routes, 12 comparator routes, five binding
negative controls and 23 unsupported-sensor configuration cases.

The exact complete ELF boots through the original bootloader and application.
The conventional DShot600 receipt records 39 accepted zero frames, rejection
of a corrupt checksum, and acceptance of the next value 100 frame. The separate
inverted DShot600 receipt confirms bidirectional mode, rejection of a corrupt
checksum, and acceptance of value 100. The actual PB4 reply has 17 driven edges,
releases afterward, and has no strong contention. An independent wire decoder
reads payload 0xFFF with 154 core cycles per reply bit and a valid checksum.
Invalid GCR, invalid checksum, missing-edge and timing negatives are retained.

These single-controller tests use a declared 1 kHz digital input waveform.
They do not execute an FC node, force AM32 arming, inject firmware memory or
qualify a motor plant. The separate connected five-controller World must
execute the actual RP2354B bench image and all four AM32 images before that
integration is accepted. Physical analog power, rotor/load and full flight
qualification remain separate.

Run python3 verify_artifacts.py to check all packaged hashes, expanded source
contents, exact flash composition and both recorded protocol oracles. See
[the native runtime record](../../runtime/native-esc/README.md) for the pinned
core revision, actual commands, source hashes and replay instructions.
