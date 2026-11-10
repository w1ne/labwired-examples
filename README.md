# LabWired Examples

Real firmware, inspectable circuit diagrams, reproducible simulator oracles, and (when relevant) parametric mechanical models in [KernelCAD](https://kernelcad.com/).

This repository is for runnable hardware verification stories, **not concept art or untested AI-generated designs**. Each example states which behavior was verified, where the simulator approximates hardware, and what remains missing.

## Catalog

| Example | Firmware and electronics | Mechanics | Evidence |
| --- | --- | --- | --- |
| [Game Boy-compatible handheld](examples/gaming/gameboy-handheld/) | STM32F411 C firmware runs Peanut-GB and an original ROM; ILI9341 and eight controls | Shared carrier/case interfaces, routed KiCad source, 14 fixed CAD mates | Driven MCU model verification, host ROM behavior, local browser input, PCB DRC and static CAD checks; no physical hardware |
| [HeyPCB imported-board acceptance sample](examples/pcb/heypcb-import-acceptance/) | Seven pinned KiCad PCB files and model-gap evidence; no full-board pass | No mechanical model | Source blobs verified; seven imports reported in unmerged PR #2934; none completely simulated |
| [Industrial BLDC fault verification](examples/industrial/bldc-fault-verification/) | STM32L476 compiled C, 24 V motor plant, three digital fault flags, inverter shutdown | No mechanical model in this example | Normal spin-up and 3 fault scenarios model-verified; ideal MCU supply, no physical bench |
| [Quadrotor BLDC propulsion](examples/robotics/quadrotor-bldc/) | STM32L476 compiled C, six-step BLDC, Hall/encoder inputs, motor speed + fault shutdown | Four independently articulated rotor joints in KernelCAD | One motor channel model-verified; CAD joints motion-checked. No flight simulation. |

## Featured video

[Watch the 35-second LabWired × KernelCAD quadrotor workflow](examples/robotics/quadrotor-bldc/media/quadrotor-demo.mp4). Recorded from actual CAD, firmware simulation, and live fault injection. It does not show verified aircraft flight.

## Run

Open an example directory. It contains firmware source, the exact LabWired circuit JSON, observed test evidence, editable KernelCAD source when appropriate, and screenshots recorded from the actual tools. Each example links to a runnable LabWired project and a versioned KernelCAD design.

For an introduction to firmware-aware circuit simulation, use the [LabWired circuit simulator guide](https://labwired.com/circuit-simulator/). It links to a GPIO-to-RC oscilloscope demonstration and explains the different browser linear-circuit and native ngspice capabilities. The quadrotor example above is a separate motor-control verification.

## Contribution standard

New examples need catalog-validated connectivity, compilable firmware, an explicit test oracle, and precise model limits. For mechanical projects, keep editable KernelCAD source and verified joints. See [CONTRIBUTING.md](CONTRIBUTING.md).

**Core simulator and firmware-model changes belong in [w1ne/labwired-core](https://github.com/w1ne/labwired-core).** This repository stores reproducible consumers of that engine, not copies of the engine.

## Licensing

Example source and scripts are MIT licensed. Individual CAD assets may carry CC0-1.0 declarations in their metadata. Manufacturer names (including ODrive) are descriptive and do not imply endorsement, compatibility or use of proprietary software.
