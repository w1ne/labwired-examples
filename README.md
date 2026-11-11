# LabWired Examples

Real firmware, inspectable circuit diagrams, reproducible simulator oracles, and (when relevant) parametric mechanical models in [KernelCAD](https://kernelcad.com/).

This repository is for runnable hardware verification stories, **not concept art or untested AI-generated designs**. Each example states which behavior was verified, where the simulator approximates hardware, and what remains missing.

## Catalog

| Example | Firmware and electronics | Mechanics | Evidence |
| --- | --- | --- | --- |
| [Game Boy-compatible handheld](examples/gaming/gameboy-handheld/) | STM32F411 C firmware runs Peanut-GB and an original ROM; ILI9341 and eight controls | Shared carrier/case interfaces, routed KiCad source, 14 fixed CAD mates | Driven MCU model verification, host ROM behavior, local browser input, PCB DRC and static CAD checks; no physical hardware |
| [HeyPCB imported-board acceptance sample](examples/pcb/heypcb-import-acceptance/) | Seven pinned KiCad PCB files and model-gap evidence; no full-board pass | No mechanical model | Source blobs verified; seven imports reported in unmerged PR #2934; none completely simulated |
| [Industrial BLDC fault verification](examples/industrial/bldc-fault-verification/) | STM32L476 compiled C, 24 V motor plant, three digital fault flags, inverter shutdown | No mechanical model in this example | Normal spin-up and 3 fault scenarios model-verified; ideal MCU supply, no physical bench |
| [Quadrotor co-design](examples/robotics/quadrotor-bldc/) | Four STM32L476 C channels; separate native six-layer ESC with zero configured ERC/DRC findings | 36-part KernelCAD frame and four rotor joints; populated-board assembly candidate remains blocked | Candidate browser: 360 exact motor/CAD observations, isolated fault, pause and reset. Actual board simulation and flight remain open. |

## Featured video

[Watch the 75-second quadrotor co-design engineering preview](examples/robotics/quadrotor-bldc/media/quadrotor-engineering-preview.mp4): editable CAD, exploded assembly, native schematic/PCB, four live motor channels, a selected-channel fault, pause and reset. This is actual application footage of a candidate STM32 propulsion bench. The physical OpenESC board and aircraft flight are not simulated by that bench.

## Run

Open an example directory. It contains firmware source, the exact LabWired circuit JSON, observed test evidence, editable KernelCAD source when appropriate, and screenshots recorded from the actual tools. Each example links to a runnable LabWired project and a versioned KernelCAD design.

For an introduction to firmware-aware circuit simulation, use the [LabWired circuit simulator guide](https://labwired.com/circuit-simulator/). It links to a GPIO-to-RC oscilloscope demonstration and explains the different browser linear-circuit and native ngspice capabilities. The quadrotor example above is a separate motor-control verification.

## Contribution standard

New examples need catalog-validated connectivity, compilable firmware, an explicit test oracle, and precise model limits. For mechanical projects, keep editable KernelCAD source and verified joints. See [CONTRIBUTING.md](CONTRIBUTING.md).

**Core simulator and firmware-model changes belong in [w1ne/labwired-core](https://github.com/w1ne/labwired-core).** This repository stores reproducible consumers of that engine, not copies of the engine.

## Licensing

Example source and scripts are MIT licensed. Individual CAD assets may carry CC0-1.0 declarations in their metadata. Manufacturer names (including ODrive) are descriptive and do not imply endorsement, compatibility or use of proprietary software.
