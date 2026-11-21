# LabWired Examples

Real firmware, inspectable circuit diagrams, reproducible simulator oracles, and (when relevant) parametric mechanical models in [KernelCAD](https://kernelcad.com/).

This repository is for runnable hardware verification stories, **not concept art or untested AI-generated designs**. Each example states which behavior was verified, where the simulator approximates hardware, and what remains missing.

## Catalog

| Example | Firmware and electronics | Mechanics | Evidence |
| --- | --- | --- | --- |
| [ESP32-C3 OLED device — Rev A candidate](examples/displays/esp32c3-oled/) | XIAO ESP32C3 clock demo, native KiCad 10 routed carrier, full BOM and pinned firmware | Removable enclosure source and STEP/STL/3MF; full path/review checks remain unresolved | 5/5 ROM-boot assertions, matching browser-WASM frames, zero native ERC/DRC findings; no physical prototype |
| [Game Boy-compatible handheld](examples/gaming/gameboy-handheld/) | STM32F411 C firmware runs Peanut-GB and an original ROM; ILI9341 and eight controls | Shared carrier/case interfaces, attached exact-source KiCad board, 59 CAD parts and 58 fixed mates | Saved-project MCU verification, host ROM behavior, browser input, hosted native PCB DRC/attachment and static CAD checks; no physical hardware |
| [HeyPCB imported-board acceptance sample](examples/pcb/heypcb-import-acceptance/) | Seven pinned KiCad PCB files and model-gap evidence; no full-board pass | No mechanical model | Source blobs verified; seven imports reported in unmerged PR #2934; none completely simulated |
| [Industrial BLDC fault verification](examples/industrial/bldc-fault-verification/) | STM32L476 compiled C, 24 V motor plant, three digital fault flags, inverter shutdown | No mechanical model in this example | Normal spin-up and 3 fault scenarios model-verified; ideal MCU supply, no physical bench |
| [Quadrotor co-design](examples/robotics/quadrotor-bldc/) | Four STM32L476 C channels; separate native six-layer ESC with zero configured ERC/DRC findings | 36-part KernelCAD frame and four rotor joints; populated-board assembly candidate remains blocked | Candidate browser: 360 exact motor/CAD observations, isolated fault, pause and reset. Actual board simulation and flight remain open. |
| [Pathfinder hobby rocket](examples/aerospace/pathfinder-rocket/) | STM32F411 saved firmware/diagram/stimuli; 5/5 saved flight-sequence oracle clauses | Linked CAD; PCB is wider than the stated available sled width | Saved model-verified firmware; **PCB fit and physical flight blocked** |
| [AXIOM H1 humanoid controller](examples/robotics/axiom-h1/) | ESP32-C3 + two PCA9685 expanders, IMU and ToF; 3/3 controller clauses | Separate 20-DOF MuJoCo model and KernelCAD assembly | Saved firmware verified; **no expander-to-servo physics coupling** |
| [A1 mini printer](examples/fabrication/a1-mini-printer/) | STM32F411 four-axis firmware, endstops, heaters and display; 2/2 saved clauses | Linked printer CAD; native cross-domain acceptance pending | Saved firmware verified; **machine/assembly behavior unverified** |
| [P.I.G. robot arm](examples/robotics/pig-arm/) | Six PCA9685 servo channels, nine poses, limits and E-stop; 3/3 saved clauses | Physical motion/kinematics not accepted | Saved controller verified; **joint actuation not verified** |

## Featured video

[Watch the 75-second quadrotor co-design engineering preview](examples/robotics/quadrotor-bldc/media/quadrotor-engineering-preview.mp4): editable CAD, exploded assembly, native schematic/PCB, four live motor channels, a selected-channel fault, pause and reset. This is actual application footage of a candidate STM32 propulsion bench. The physical OpenESC board and aircraft flight are not simulated by that bench.

## Run

Open an example directory. The export-backed packs contain the saved LabWired firmware, circuit, stimuli, and requirements in `project.input.json`, plus revision-pinned evidence in `evidence.json`. They link to existing saved projects. Some require separate linked PCB/CAD assets or further integration. An import does **not** imply the original evidence transfers to the new project. The quadrotor and other engineering demos additionally include native sources and recorded tools.

For an introduction to firmware-aware circuit simulation, use the [LabWired circuit simulator guide](https://labwired.com/circuit-simulator/). It links to a GPIO-to-RC oscilloscope demonstration and explains the different browser linear-circuit and native ngspice capabilities. The quadrotor example above is a separate motor-control verification.

## Contribution standard

New examples need catalog-validated connectivity, compilable firmware, an explicit test oracle, and precise model limits. For mechanical projects, keep editable KernelCAD source and verified joints. See [CONTRIBUTING.md](CONTRIBUTING.md).

**Core simulator and firmware-model changes belong in [w1ne/labwired-core](https://github.com/w1ne/labwired-core).** This repository stores reproducible consumers of that engine, not copies of the engine.

## Licensing

Example source and scripts are MIT licensed. Individual CAD assets may carry CC0-1.0 declarations in their metadata. Manufacturer names (including ODrive) are descriptive and do not imply endorsement, compatibility or use of proprietary software.
