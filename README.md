# LabWired Examples

Real firmware, inspectable circuit diagrams, reproducible simulator oracles, and (when relevant) parametric mechanical models in [KernelCAD](https://kernelcad.com/).

This repository is for runnable hardware verification stories, **not concept art or untested AI-generated designs**. Each example states which behavior was verified, where the simulator approximates hardware, and what remains missing.

## Catalog

| Example | Firmware and electronics | Mechanics | Evidence |
| --- | --- | --- | --- |
| [Quadrotor BLDC propulsion](examples/robotics/quadrotor-bldc/) | STM32L476 compiled C, six-step BLDC, Hall/encoder inputs, motor speed + fault shutdown | Four independently articulated rotor joints in KernelCAD | One motor channel model-verified; CAD joints motion-checked. No flight simulation. |

## Run

Open an example directory. It contains firmware source, the exact LabWired circuit JSON, observed test evidence, editable KernelCAD source when appropriate, and screenshots recorded from the actual tools. Each example links to a runnable LabWired project and a versioned KernelCAD design.

## Contribution standard

New examples need catalog-validated connectivity, compilable firmware, an explicit test oracle, and precise model limits. For mechanical projects, keep editable KernelCAD source and verified joints. See [CONTRIBUTING.md](CONTRIBUTING.md).

**Core simulator and firmware-model changes belong in [w1ne/labwired-core](https://github.com/w1ne/labwired-core).** This repository stores reproducible consumers of that engine, not copies of the engine.

## Licensing

Example source and scripts are MIT licensed. Individual CAD assets may carry CC0-1.0 declarations in their metadata. Manufacturer names (including ODrive) are descriptive and do not imply endorsement, compatibility or use of proprietary software.
