# Quadrotor co-design: LabWired + KernelCAD

This package contains a versioned **KernelCAD assembly**, a real **six-layer OpenESC schematic and PCB**, and a **four-channel STM32 propulsion bench**. The motor bench uses real compiled firmware and reduced-order motor models. It does not yet simulate the electronics or flight controller on the physical boards.

## Recorded engineering preview

[Watch the 75-second co-design video](media/quadrotor-engineering-preview.mp4). It uses actual KernelCAD screens, native KiCad exports and an audited candidate browser run. CAD inspection is time-compressed; runtime scenes play at recorded speed. The final scene states that physical-board simulation and flight control remain open.

[Video provenance and reproduction](media/README.md) · [Final runtime evidence](labwired/evidence/20261111-final/evidence.json)

## Open the projects

- [Four-channel LabWired propulsion project](https://app.labwired.com/p/7c92d38a4f2ac205aa91502291fde0d8/edit)
- [KernelCAD populated OpenFrame-5F assembly, revision 4](https://app.kernelcad.com/p/DyJ405zg?version=4)
- [Complete system identity and model boundaries](system-integration.json)
- [Physical wiring and system BOM](hardware/assembly-wiring.md)
- [Native ESC schematic, PCB and manufacturing review](hardware/esc-4in1/)
- [Copied OpenFC-Lite repair revision 2-LW1](hardware/flight-controller-openfc-lite-rev2-lw1/) — zero active ERC/physical DRC errors, one retained microSD-pad parity omission; no native boot or manufacturing acceptance.

The saved LabWired project links to the versioned KernelCAD model. Its circuit contains four controllers, four motors, four independent fault inputs and 64 wires. A logic analyzer can appear as an extra editor instrument; it is not a physical component of the aircraft.

## What the artifacts establish

| Artifact | Current scope | Evidence |
| --- | --- | --- |
| KernelCAD source | Pinned OpenFrame-5F rev2.2 frame, electronic stack, four rotor joints | [Mechanical checks and source identity](cad/README.md) |
| Physical OpenESC | Four AT32F421 controllers, four gate drivers, 24 MOSFETs; six copper layers | [Native electrical/layout review](hardware/esc-4in1/validation/) |
| Firmware bench | Four independent STM32L476 six-step commutators, Hall/encoder feedback, latched inverter shutdown | [Exact source and circuit manifest](labwired/four-channel-project.json) |
| Motor-to-CAD binding | Observed motor position/RPM mapped to explicit rotor/propeller groups | [Revision-pinned mapping](cad/runtime-bindings.json) |
| Aircraft flight | No connected IMU, flight-controller firmware, thrust model or six-degree-of-freedom body | Not implemented |

The CAD exploded view is an assembly illustration. The mechanism check samples rotor poses. Neither establishes a complete physical assembly path, frame strength or flight performance.

## Physical board and simulated bench

These are two distinct electrical targets. Keep this distinction visible in recordings and demonstrations.

| Property | Physical aircraft design | Firmware simulation |
| --- | --- | --- |
| ESC MCU | Four AT32F421G8U7 | Four STM32L476 |
| ESC firmware | AM32 / DShot | Inspectable six-step commutator |
| Flight controller | RP2354B / Betaflight | Not running |
| DC supply | 4S LiPo: 14.8 V nominal, 16.8 V full | Ideal 24 V |
| Motor | EMAX ECO II 2306 2400KV | Reduced-order BLDC plant; Ke and Kt are both 0.04 in their SI units |
| Gate drivers and MOSFETs | Native schematic and PCB | Functional motor/inverter plant, no transistor transients |
| PCB-to-simulation equivalence | Required for a full hardware twin | Not established |

The native PCB has **222 footprints, 1,067 pads and 210 nets**. KiCad 10.0.8 reports zero ERC errors/warnings, zero DRC violations, zero unconnected items and zero schematic/PCB parity differences within the configured checks. The importer retains all components, nets and pin endpoints. However, **37 catalog entries remain unsupported for simulation**; nine further inert entries are connectors/testpoints. The actual board remains design-only. A clean rule check does not provide motor-current, thermal, switching-transient or flight evidence.

The populated visual assembly now passes hosted evaluation and rendering in [KernelCAD revision 4](https://app.kernelcad.com/p/DyJ405zg?version=4): 37 parts, 213 native KiCad component references and an exact substrate. Bounded native checks cover all 35 external PCB-to-part pairs. The stack lift gives 2.32 mm lower frame separation; 6 mm OD support rings remove a measured 0.0863 mm³ component overlap. This establishes the declared geometry fit, not solder, hardware, strength or flight acceptance. See [mechanical evidence and limits](cad/README.md).

## Reproduce the four-channel bench

1. Load [four-channel-circuit.json](labwired/four-channel-circuit.json).
2. Use the exact source identified for each controller in [four-channel-project.json](labwired/four-channel-project.json). Compile each as C with board `stm32l476` and entry path `src/main.c`.
3. Run all four controllers together. Their duty commands are 600, 640, 680 and 720 per mille. Require observed rotor motion and the firmware's Hall/encoder feedback markers.
4. Drive `fault1` through `fault4` independently. Require the selected controller's `FAULT DRIVER` and `INVERTER OFF` markers and its inverter-enable output low. Confirm that the other channels continue before faulting them.
5. Use `cad/runtime-bindings.json` for the evaluated KernelCAD revision. The bridge must receive real `positionRad` and `speedRpm`; a timed visual animation is not a substitute.
6. Pause and stop the simulation. Verify that the viewer stops advancing and does not reuse stale telemetry as a new run.

The multi-MCU loader correction [LabWired PR #3094](https://github.com/w1ne/labwired/pull/3094) merged after required CI passed. Hosted deployment and model verification are separate gates. The generic live bridge is in [LabWired PR #3106](https://github.com/w1ne/labwired/pull/3106) and [KernelCAD-app PR #121](https://github.com/w1ne/kernelCAD-app/pull/121). The candidate diagram with authored motion metadata is [four-channel-circuit.runtime-candidate.json](labwired/four-channel-circuit.runtime-candidate.json); it does not imply that production has deployed these changes.

## Observed candidate behavior

The [independent final audit](labwired/evidence/20261111-final/independent-audit.json) establishes:

- Four hosted compilations match the exact saved C sources. The four worker channels report their separate identifiers and duty commands.
- **360 of 360** received CAD motion observations match raw motor angle, RPM, control state and faults, with only the authored direction sign applied. No final-run observations are excluded.
- Fault1 disables M1 and remains latched after release. All **244** post-fault M1 observations are off; each other channel stays in inverter state for **243 of 243** observations before pause.
- Pause holds all four observed poses across at least five seconds and labels samples Last observed. Worker stepping stops.
- Reset reinitializes all four controllers and clears every motor sample. The receiver briefly reports stopped, then settles paused with no samples.

This is a browser candidate result, not a physical-board or flight result. The preserved receipts include source/ELF hashes, passive Worker and CAD frames, the exact recorder, and replayable Python audits. [Re-run the audit](labwired/evidence/20261111-final/README.md).

## Complete the physical hardware twin

The remaining work is concrete:

- Onboard the actual AT32F421 peripheral model and run the intended AM32 build.
- Run the RP2354B flight-controller firmware with IMU inputs and four DShot channels.
- Add the actual power stage, motor parameters, battery behavior and propeller loads. Calibrate them against component data and measured behavior.
- Connect forces and moments to the airframe dynamics, then test arming, command loss, attitude control and individual motor faults.
- Establish copper-to-model equivalence and a physical assembly/power-on validation record.

Until those gates pass, use **co-design engineering preview** or **four-channel propulsion bench** to describe this example.

## Files and earlier evidence

- [firmware/channels/](firmware/channels/) stores the four exact saved-project sources, with SHA-256 digests in the project manifest.
- [cad/drone.kcad.ts](cad/drone.kcad.ts) matches the saved revision and imports immutable source CAD.
- [cad/evidence/](cad/evidence/) contains full evaluation, motion, assembly-budget and export receipts.
- [hardware/esc-4in1/](hardware/esc-4in1/) contains editable native electrical files, local libraries and validation reports.
- [media/](media/) contains recordings and the scripts that produced them.

The original [35-second single-channel recording](media/quadrotor-demo.mp4), [single-channel circuit](labwired/circuit.json), [firmware](firmware/main.c) and [evidence](labwired/evidence.json) are retained as historical reference. They do not establish four-channel operation. The original motor test uses a simulated inverter; it does not run ODrive firmware or reproduce a proprietary ODrive PCB.
