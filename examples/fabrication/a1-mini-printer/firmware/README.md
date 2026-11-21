# A1 reference controller firmware

This project builds the exact guarded A1 sketch for the bare STM32F411CEU6
controller with its **8 MHz HSE crystal, 100 MHz CPU and USART2 console**.
It contains the managed startup source used by LabWired. Building only the
sketch with the upstream generic Arduino target would select its 96 MHz HSI
startup. The Black Pill target also uses a different oscillator and UART.

## Build

Install the pinned PlatformIO Core in a virtual environment, then build from
this directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-build.txt
pio run -e a1-reference
sha256sum -c SHA256SUMS
sha256sum .pio/build/a1-reference/firmware.elf
```

`platformio.ini` pins the versions observed in the verified local build:

| Component | Version |
| --- | --- |
| PlatformIO Core | 6.2.0 |
| ST STM32 platform | 20.0.0 |
| STM32duino framework | 3.0.0; package 4.30000.0 |
| CMSIS | package 2.60300.0 |
| CMSIS-DSP | 1.16.2 |
| Arm GNU toolchain | GCC 12.3.1; package 1.120301.0 |

The portable build completed in 11.63 seconds. It used 29,060 bytes of flash and
2,704 bytes of RAM. Its ELF is byte-identical to the local LabWired builder
output tested below. These are observed results from this environment; a
future hosted compiler image has its own separately recorded artifact identity.

## Exact source and binary identity

| Artifact | SHA256 |
| --- | --- |
| `src/main.ino` | `6f1776ae97cd8b3d153e06a2715d23e60a891390a97a7af78041fdfe6a9bfeab` |
| `src/labwired_board_clock.c` | `b2e4b857d2ee1f2336995b3e88c61f1d2dac982e5f00bda134e1ccec8a89dcff` |
| `artifacts/a1-reference.elf` | `1dc47c7c7772a9e9cc65851530e0e885edf2482cd498938a3451fc02de919b14` |

The sketch bytes are unchanged. The startup file is copied byte-for-byte from
LabWired commit [37c63a09ed59c3df743d2e8dd8eeb657ab132c73](https://github.com/w1ne/labwired/commit/37c63a09ed59c3df743d2e8dd8eeb657ab132c73).
The profile identifier includes the startup SHA256; LabWired hashes that
identifier into its compile cache and refuses an incompatible builder revision.
The portable project supplies the same startup as a normal C translation unit.

[provenance.json](provenance.json) records the package versions, relevant
metadata hashes, build configuration, ELF identity and verification inputs.
[SHA256SUMS](SHA256SUMS) covers the shipped source, configuration, binary and
receipts. The supplied ELF is 66,740 bytes and is a local build artifact. The
final saved-project hosted ELF belongs to the parent release evidence.

## Clock, pins and USB scope

The strong `SystemClock_Config` definition replaces the upstream weak generic
startup. The configuration is HSE 8 MHz, PLL M=8/N=200/P=2, voltage scale 1,
AHB divide 1, APB1 divide 2, APB2 divide 1 and three flash wait states.
`HSE_VALUE=8000000U` matches the board crystal. STM32duino reads `F_CPU` from
the initialized `SystemCoreClock`.

`Serial` uses **USART2: PA2 TX, PA3 RX, 115200 baud**. These pins match the
native serial connector. PA10 remains available for the active-low fault LED.
There is no carrier LED or button assumption.

The main PLL Q=4 output is 50 MHz and unused. This 100 MHz profile does not
provide the 48 MHz USB clock. It does not enable USB; enabling `USBCON` fails
the managed startup's compile guard. The board's USB power/protection wiring
does not imply USB firmware enumeration or USB electrical qualification.

The A4988 drivers remain in full-step mode: all MS1/MS2/MS3 straps are grounded.
The sketch's X/Y/Z/E calibration remains 5/5/25/100 steps per millimeter.

## Retained local verification

[local-clock.json](validation/local-clock.json) reads the executed ELF's
`SystemCoreClock`, RCC and USART control registers. It observes 100,000,000 Hz,
HSE selected, M8/N200/P2, APB1 divided by 2, USART2 enabled and USART1 disabled.
The boot also emits `READY` and writes the OLED through I2C.

[local-fault-summary.json](validation/local-fault-summary.json) retains the
five exact native-circuit fault regressions. Every case passes the original
oracle and then holds it for another 10,000,000 cycles:

| Case | Executed cycles | Result |
| --- | ---: | --- |
| Emergency stop during hot printing | 41,000,000 | Pass |
| Sensor out of range | 37,000,000 | Pass |
| X homing timeout | 198,500,000 | Pass |
| Heat without temperature rise | 823,000,000 | Pass |
| Normal print then overtemperature | 57,000,000 | Pass |

All final safety clauses read PB13/PB14/PB15 low, PB12 high and PA10 low.
The normal case also passes all homing/print position markers and actual OLED
ink detection. These receipts use the declared native 160-part circuit and the
pinned WASM engine, with explicit regulated-supply boundaries, an ideal logic
buffer, and scripted endstop/temperature inputs. They do not qualify physical
oscillator startup, thermal behavior, mechanics or board operation. Final
normal saved-project acceptance is recorded outside this portable firmware
folder by the release's hosted verification and live browser evidence.
