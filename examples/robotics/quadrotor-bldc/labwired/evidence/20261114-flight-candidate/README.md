# Five-controller quadrotor — 14 November 2026

**Result: source-integrity, electrical rule check, host PWM safety unit test, and five ARM ELF links pass. Complete flight simulation is not verified.** The existing public four-ESC project remains the current release.

## Executed checks

- Python `unittest` source, wiring and manifest suite: **63 passed**.
- Diagram with 5 STM32L476 MCUs (one flight controller and four ESCs), 4 motor models, 4 independent ESC fault switches, BMI270, FC emergency-stop input, oscilloscope, logic analyzer: **17 parts / 81 wires / 0 errors / 0 warnings** from `labwired_validate`.
- `arm-none-eabi-gcc` with LabWired's STM32L476 startup and linker script built 5 ARM Cortex-M4 executable ELF images. Per-image SHA-256 and compiler flags are in [build-link-and-validation.json](build-link-and-validation.json).
- Native host C test executes the real `command_high_mask()` implementation. Zero-width disarm clears all four outputs even after a previously nonzero PWM command.

The compile evidence is a **local target build**, not a hosted toolchain receipt or proof of Cortex-M execution. The historical five-controller hosted compile record predates FC safety edits and must not be attributed to the new FC hash. The MCP compile wrapper currently fails with `INVALID_ENTRY_PATH` because its exposed signature has no `entryPath` field even though the deployed handler requires `src/main.c`.

## End-to-end acceptance — not yet passed

| Test | Required observable result | Current status |
| --- | --- | --- |
| Five MCU boots | Five firmware hashes match the running ELF identities | Not run |
| Closed-loop sensor | BMI270 acceleration + angular rate originate from one observed body timestep | Not run |
| Arm / takeoff | Measured altitude rises above 0.5 m only after arming and valid health | Not run |
| Hover | Measured altitude stays within 0.15 m of 1.0 m for 1 second | Not run |
| Roll, pitch, yaw | Body quaternion / rates respond to commanded axes and recover | Not run |
| Operator kill | Any command-high pin becomes low and stays low, ESCs coast | Not run (host command-mask test passed) |
| Driver fault | Selected ESC latches off and the FC drives all four commands low | Not run |
| IMU fault | Three consecutive failed I2C samples force latched disarm | Not run |
| Reset / pause | Shared clock stops, physics and CAD pose stop, reset clears old samples | Not run |
| Power, thermal, battery | Actual electrical power stage and 4S LiPo behavior agree with PCB/silicon | Not modeled |
| Native FC / ESC | RP2354B + AT32F421 binaries execute on these exact physical netlists | Not modeled |

Use this candidate for integration and fault testing, not as a production flight-ready design. Never label an inertial-only altitude estimate as verified safe landing.
