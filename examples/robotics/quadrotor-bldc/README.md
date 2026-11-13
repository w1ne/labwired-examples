# Quadrotor co-design: LabWired + KernelCAD

This package contains a versioned **KernelCAD assembly**, a real **six-layer OpenESC schematic and PCB**, an accepted **four-channel STM32 propulsion bench**, and a **five-controller flight candidate**. The simulated controllers run compiled STM32 firmware with behavioral motor and flight models. The physical OpenESC and OpenFC-Lite board designs remain design-only; this example does not run their native controllers.

## Saved native FC revision, 12 November 2026

The [current CAD source and evidence](cad/README.md) replace the FC envelope with
the repaired native PCB and all 107 assigned component models. Hosted evaluation
passes with 38 parts and 37 mates. Conservative geometric checks cover 31
external pairs and 652 FC-component/support-ring pairs. The source is saved as
[Studio revision 5](https://app.kernelcad.com/p/DyJ405zg?version=5), with a ready
cloud mesh and 12 immutable inputs. The firmware bench remains a separate
target; native electrical onboarding is tracked in
[LabWired PR #3148](https://github.com/w1ne/labwired/pull/3148).

## Five-controller flight candidate, 13 November 2026

The [flight circuit](labwired/five-controller-flight-circuit.json) connects five STM32L476 firmware instances: one flight controller, four command-driven ESCs, four BLDC motor models, four fault inputs, a BMI270 model, a universal oscilloscope, and a universal logic analyzer. Its 16 parts and 78 wires include four FC command nets and four ESC health nets. [The project manifest](labwired/five-controller-flight-project.json) binds each exact source to its controller.

All five sources compiled on the hosted STM32L476 profile. The four ESCs retain the reviewed Hall-lock predicate, including the 1–20 control-tick period bound, and emit the exact existing `ROTOR n HALL LOCKED` requirements. [The compilation receipt](labwired/evidence/20261113-production/five-controller-compilation.json) identifies the sources and ELF artifacts. Compilation does not establish flight behavior.

The corrected design is saved in the original project, with its original PCB attachment and CAD revision 5. The source approval gate removal is merged in core PR1852. The body/rotor receiver is merged in KernelCAD PR139. The app integration, unchanged-budget hosted verification, production browser acceptance, and final 40–45 second video remain pending. The current public revision and the older videos below are historical bench evidence.

The flight runtime uses observed native motor RPM and clocks to advance a bounded body model and feed six IMU channels back to the compiled FC. Its planned acceptance includes takeoff, hover, commanded attitude changes, recovery, pause retention, and an injected fault followed by all-ESC disarm. The FC's `SAFE LANDING VERIFIED` text checks its estimated altitude; it does not establish a controlled or safe landing of physical hardware.

## Recorded universal-instrument preview, 12 November 2026

[Watch the 34-second LabWired video](media/quadrotor-universal-instruments-preview-20261112.mp4). It shows the universal oscilloscope and logic analyzer, independent controller selection, PWM/high-impedance observations, and M1 shutdown while the other three modeled motors continue. Every shot comes from the accepted R4-02 browser recording at its original speed.

The video is a labeled development preview of four STM32 controllers with behavioral motor models. [All 17 native acceptance checks and the separate native-to-UI readout comparison passed](labwired/evidence/20261112-universal-instruments/). That recording predates the current release work. Its engine identity and four-controller scope remain fixed in the retained receipts.

[Original recording and edit provenance](media/README.md) · [Acceptance evidence](labwired/evidence/20261112-universal-instruments/)

### Earlier engineering preview

[Watch the 75-second co-design video](media/quadrotor-engineering-preview.mp4). It uses actual KernelCAD screens, native KiCad exports and an audited candidate browser run. CAD inspection is time-compressed; runtime scenes play at recorded speed. The final scene states that physical-board simulation and flight control remain open.

[Video provenance and reproduction](media/README.md) · [Final runtime evidence](labwired/evidence/20261111-final/evidence.json)

## Open the projects

- [Four-channel LabWired propulsion project](https://app.labwired.com/p/7c92d38a4f2ac205aa91502291fde0d8/edit?view=kernelcad)
- [KernelCAD populated OpenFrame-5F assembly, revision 5](https://app.kernelcad.com/p/DyJ405zg?version=5)
- [Complete system identity and model boundaries](system-integration.json)
- [Physical wiring and system BOM](hardware/assembly-wiring.md)
- [Native ESC schematic, PCB and manufacturing review](hardware/esc-4in1/)
- [Copied OpenFC-Lite repair revision 2-LW1](hardware/flight-controller-openfc-lite-rev2-lw1/) — zero active ERC/physical DRC errors, one retained microSD-pad parity omission; no native boot or manufacturing acceptance.

The four-channel bench circuit links to the versioned KernelCAD model. It contains four controllers, four motors, four independent fault inputs, 64 wires, an oscilloscope and a logic analyzer. The five-controller flight candidate is a separate manifest and circuit. Both instruments observe simulator signals; they are not physical aircraft components. Publication of the new original-project revision is pending deployment and execution acceptance.

## What the artifacts establish

| Artifact | Current scope | Evidence |
| --- | --- | --- |
| KernelCAD source | Pinned OpenFrame-5F rev2.2 frame, electronic stack, four rotor joints | [Mechanical checks and source identity](cad/README.md) |
| Physical OpenESC | Four AT32F421 controllers, four gate drivers, 24 MOSFETs; six copper layers | [Native electrical/layout review](hardware/esc-4in1/validation/) |
| Firmware bench | Four independent STM32L476 six-step commutators, Hall/encoder feedback, latched inverter shutdown | [Exact source and circuit manifest](labwired/four-channel-project.json) |
| Motor-to-CAD binding | Observed motor position/RPM mapped to explicit rotor/propeller groups | [Revision-pinned mapping](cad/runtime-bindings.json) |
| Aircraft flight candidate | Five STM32 firmware instances, connected BMI270 model and bounded body dynamics | Compiles; production flight execution acceptance pending |

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

[KernelCAD revision 5](https://app.kernelcad.com/p/DyJ405zg?version=5) contains 38 parts, the exact ESC substrate and 213 component references, plus the repaired native FC substrate and all 107 assigned FC models. Hosted evaluation passes with 146 features and zero build diagnostics. The saved mesh is ready; full mechanical acceptance remains false. The FC clearance proof covers 31 external pairs and 652 component/support-ring pairs. The earlier ESC stack lift and 6 mm OD support-ring correction are preserved. See [mechanical evidence and limits](cad/README.md).

## Reproduce the four-channel bench

1. Load [four-channel-circuit.json](labwired/four-channel-circuit.json).
2. Use the exact source identified for each controller in [four-channel-project.json](labwired/four-channel-project.json). Compile each as C with board `stm32l476` and entry path `src/main.c`.
3. Use the declared 4 MHz board clock for each controller and motor model. The firmware configures a 20 kHz PWM timer and a 10 kHz control tick. Run all four controllers together. Their duty commands are 600, 640, 680 and 720 per mille. Require observed rotor motion and the firmware's Hall/encoder feedback markers.
4. Drive `fault1` through `fault4` independently. Require the selected controller's `FAULT DRIVER` and `INVERTER OFF` markers and its inverter-enable output low. Confirm that the other channels continue before faulting them.
5. Use `cad/runtime-bindings.json` for the evaluated KernelCAD revision. The bridge must receive real `positionRad` and `speedRpm`; a timed visual animation is not a substitute.
6. Pause and stop the simulation. Verify that the viewer stops advancing and does not reuse stale telemetry as a new run.

The multi-MCU loader correction [LabWired PR #3094](https://github.com/w1ne/labwired/pull/3094) merged after required CI passed. Hosted deployment and model verification are separate gates. The generic live bridge is in [LabWired PR #3106](https://github.com/w1ne/labwired/pull/3106) and [KernelCAD-app PR #121](https://github.com/w1ne/kernelCAD-app/pull/121). The canonical [four-channel-circuit.json](labwired/four-channel-circuit.json) contains the four authored motor-to-CAD bindings and pins saved CAD revision 5. The earlier runtime-candidate file remains historical evidence. Repository contents alone do not prove production deployment.

## Universal mixed-signal instruments

The oscilloscope selects any published numeric source with its native units, or a digital source. The logic analyzer selects board GPIO and published digital wires. Both retain the selected controller identity. The saved selections show M1 current, speed, PWM and Hall A on the scope, and PWM, low-side drive, fault input and enable on the logic analyzer. Source changes do not require a firmware change.

The current firmware uses immediate compare updates (`OCxPE=0`). A high-side phase receives the duty command; the selected N-only low-side phase stays on for its commutation sector (`CCR=ARR+1`). PA8 shows the carrier during active sectors; PB13 shows the low-side commutation gate. This configuration does not enable both outputs of a phase and does not establish complementary dead-time insertion. The four-lane analyzer can inspect phases A, B and C in separate capture windows.

The behavioral plants consume the configured timer output stages directly. Changing GPIO mode or alternate function does not disconnect the plant. The firmware configures PA8–PA10 and PB13–PB15 as AF1, and native pad observations require a separate check. The [current source and compile receipt](labwired/evidence/20261112-gate-candidate/) identifies the exact four images. The [R4-02 browser acceptance](labwired/evidence/20261112-universal-instruments/) now passes; hosted saved-project verification and production deployment remain separate.

The shared instrument and runtime fixes are tracked in [LabWired PR #3163](https://github.com/w1ne/labwired/pull/3163). The [corrected-clock candidate](labwired/evidence/20261112-clock-candidate/) confirms four executed ELF identities, Hall feedback, the high-side carrier and source switching. That earlier candidate failed at coast-down and found missing native complementary-pad output. The [new R4-02 acceptance and 34-second recording](labwired/evidence/20261112-universal-instruments/) pass after the native and readout corrections.

Mandatory human source acknowledgments, expiry and renewal gates were removed in [core PR #1852](https://github.com/w1ne/labwired-core/pull/1852), merged on 13 November 2026 as [`cfe553f6`](https://github.com/w1ne/labwired-core/commit/cfe553f69dfa17e4c1beaaf10046712283722234). The exact tested head completed 59 CI checks successfully; six were skipped. Automated source and provenance integrity checks remain. Source-only drift is informational, and absent model digests remain unverified. [Merge and check evidence](labwired/evidence/20261113-production/core-release.json) records the exact commits. Normal app tests and CI, hosted verification, deployment, and publication remain release requirements. The instruments expose missing observations and capture limits; a retained sample is not proof of a live value.

## Earlier motion-binding evidence, 11 November 2026

These receipts predate the correction that aligns the L476 system and motor model at 4 MHz. They retain evidence for source identity, motion binding, fault latching and pause/reset behavior. They do not establish timing or motor-model behavior for the current corrected firmware.

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

The physical-board gates above remain separate from the behavioral STM32 flight example. Describe each recording by its verified scope; the historical previews do not establish the new flight acceptance.

## Files and earlier evidence

- [firmware/channels/](firmware/channels/) stores the four canonical candidate sources, with SHA-256 digests in the project manifest. Publication status is recorded in the integration manifest.
- [cad/drone.kcad.ts](cad/drone.kcad.ts) contains the current native FC candidate and imports immutable source CAD.
- [cad/evidence/](cad/evidence/) contains full evaluation, motion, assembly-budget and export receipts.
- [hardware/esc-4in1/](hardware/esc-4in1/) contains editable native electrical files, local libraries and validation reports.
- [media/](media/) contains recordings and the scripts that produced them.

The original [35-second single-channel recording](media/quadrotor-demo.mp4), [single-channel circuit](labwired/circuit.json), [firmware](firmware/main.c) and [evidence](labwired/evidence.json) are retained as historical reference. They do not establish four-channel operation. The original motor test uses a simulated inverter; it does not run ODrive firmware or reproduce a proprietary ODrive PCB.
