# Five-controller quadrotor — 14 November 2026

**Result: five-controller MCP motor startup and driver-fault shutdown now pass explicit serial oracles. Complete six-DOF aircraft flight is not verified.** The existing public four-ESC project remains the current release.

## Executed checks

- Python `unittest` source, wiring and manifest suite: **63 passed**.
- Diagram with 5 STM32L476 MCUs (one flight controller and four ESCs), 4 motor models, 4 independent ESC fault switches, BMI270, FC emergency-stop input, oscilloscope, logic analyzer: **17 parts / 81 wires / 0 errors / 0 warnings** from `labwired_validate`.
- `arm-none-eabi-gcc` with LabWired's STM32L476 startup and linker script built 5 ARM Cortex-M4 executable ELF images. Per-image SHA-256 and compiler flags are in [build-link-and-validation.json](build-link-and-validation.json).
- Native host C test executes the real `command_high_mask()` implementation. Zero-width disarm clears all four outputs even after a previously nonzero PWM command.

The compile evidence is a **local target build**, not a hosted toolchain receipt or proof of Cortex-M execution. The historical five-controller hosted compile record predates FC safety edits and must not be attributed to the new FC hash. The MCP compile wrapper currently fails with `INVALID_ENTRY_PATH` because its exposed signature has no `entryPath` field even though the deployed handler requires `src/main.c`.

## Hosted MCP World verification, 14 November 2026

Two independent `labwired_verify` experiments used all **five** distinct STM32L476 firmware sources, the actual shared GPIO nets and reduced-order four-motor plants:

1. **Normal arming/startup:** exact `firmware/flight/esc1.c`..`esc4.c`, `firmware/flight/fc.c` and `labwired/five-controller-flight-circuit.json` (17 parts / 81 wires) with explicit oracle requiring all four `ROTOR n HALL LOCKED` markers. Result: **model_verified**, four of four serial clauses passed, with `FC READY BMI270 ONLINE`, `FC ARM COMMAND` and `FC TAKEOFF COMMAND`. These are electrical/controller observations, *not* airframe flight measurements.
2. **Driver-fault injection:** [fault-injection-circuit.json](fault-injection-circuit.json) (16 parts / 79 wires) replaces `fault1` with a test-only wire from FC PC12 to ESC1 PB7, and [fc-driver-fault-test-only.c](fc-driver-fault-test-only.c) drives PC12 high at the 1.5-second firmware tick. The other four controller sources are unchanged. Explicit oracle asserted nine separate serial markers: Hall locks on M2/M3/M4; `ESC 1 FAULT DRIVER`, `ESC 1 LATCHED OFF`, `FC FAULT DETECTED - ALL ESC DISARM`, and `ESC 2/3/4 DISARMED`. **All 9/9 passed; status=model_verified**. M1 Hall lock was deliberately *not asserted* because the fault injection occurs before that marker. No unobserved behavior is claimed.

The production ESC behavioral profile uses 1 kHz inverter carrier at a 4 MHz STM32 clock (TIM1 PSC=3, ARR=999), 10 kHz command decoding and a separate 500 Hz Hall-control loop. It is **not** the physical AM32/AT32F421 20 kHz hardware design.

`labwired_project_verify` is known to return a false-positive stored proof on failing multi-MCU worlds. This defect is documented in [LabWired issue #3248](https://github.com/w1ne/labwired/issues/3248) and the fail-closed patch in [PR #3249](https://github.com/w1ne/labwired/pull/3249). Use direct `labwired_verify` for the above evidence. The current project draft must not be published until the full-flight acceptance and deployment gate pass.

## End-to-end acceptance — not yet passed

| Test | Required observable result | Current status |
| --- | --- | --- |
| Five MCU electrical startup | All five sources run; ESC1..4 Hall lock; FC BMI270 online | **MCP model_verified (4/4 motor lock)** |
| Closed-loop sensor | BMI270 acceleration + angular rate originate from one observed body timestep | Not run |
| Arm / takeoff | Measured altitude rises above 0.5 m only after arming and valid health | Not run |
| Hover | Measured altitude stays within 0.15 m of 1.0 m for 1 second | Not run |
| Roll, pitch, yaw | Body quaternion / rates respond to commanded axes and recover | Not run |
| Operator kill | Any command-high pin becomes low and stays low, ESCs coast | Not run (host command-mask test passed) |
| Driver fault | ESC1 latches off; FC commands all ESCs off; ESC2-4 report disarmed | **MCP model_verified (9/9 serial clauses)** |
| IMU fault | Three consecutive failed I2C samples force latched disarm | Not run |
| Reset / pause | Shared clock stops, physics and CAD pose stop, reset clears old samples | Not run |
| Power, thermal, battery | Actual electrical power stage and 4S LiPo behavior agree with PCB/silicon | Not modeled |
| Native FC / ESC | RP2354B + AT32F421 binaries execute on these exact physical netlists | Not modeled |

Use this candidate for integration and fault testing, not as a production flight-ready design. Never label an inertial-only altitude estimate as verified safe landing.
