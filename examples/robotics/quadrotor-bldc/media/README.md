## Latest quadcopter review — native PCB routing and hosted mixed signals

[Watch the 32-second review](labwired-quadcopter-routing-mixed-signal-32s.mp4). The video shows 12 signal nets closed across four real KiCad 10 editing stages (0 other configured DRC violations), the populated PCB model, one hosted STM32L476 mixed-signal run with real PWM, Hall, motor current, fault and inverter-disable trace, and separately recorded motor-twin motion.

The operation restores source-approved PCB tracks, not a novel autoroute. The motor model is reduced order at 24 V, not the physical AT32F421/AM32 board. No calibrated flight, PCB functional equivalence, transistor transient or manufacturing validation is claimed.

[DRC checks, hosted waveform and test details](evidence/native-routing-mixed-signal-20261113/README.md) | [32-second video provenance](labwired-quadcopter-routing-mixed-signal-32s.provenance.json).

## Previous PCB-layer reveal film

## Archived LabWired quadcopter film — PCB routing + 3D digital twin

[Watch the 32.4-second video](labwired-quadrotor-pcb-digital-twin-32s.mp4). Five scenes, 1600 × 900, 30 fps: quadcopter CAD; PCB routing; rotating populated 3D PCB; combined live oscilloscope and logic analyzer; digital twin. The video excludes the previous fault-test sequence and controller-count story. [Source-bound provenance](labwired-quadrotor-pcb-digital-twin-32s.provenance.json) · [Editor](render-quadrotor-pcb-digital-twin.py) · [Routing layer renderer](render-pcb-routing.py) · [3D board turntable renderer](render-pcb-turntable.py).

The completed PCB source derives from OpenDrone OpenESC-30x30 under CERN-OHL-S-2.0; the attribution and full license remain in the hardware source. The route animation is a trace/layer reveal, not a video of an autorouter performing a design.

## Current 39.5-second quadcopter film

[Watch the focused 40-second LabWired quadcopter demo](labwired-quadrotor-focused-demo-short.mp4). Seven readable sequences: parametric CAD, native PCB, compiled motor firmware, live oscilloscope, logic analyzer, fault injection and observed shutdown. The shots use actual source footage, not generated motion or telemetry. [Exact timing, hashes and scope](labwired-quadrotor-focused-demo-short.provenance.json). The earlier 65-second cut remains archived.

## Current focused quadrotor film

[Watch 65-second cut](labwired-quadrotor-focused-demo.mp4) | [source and screenshots](focused-video-README.md). Longer real-runtime scenes, enlarged quadrotor signals and no legacy schematic title. The native ESC source attribution remains in the repository; full flight is not shown.

# Quadrotor engineering-superintelligence demo

[Watch the 44-second flagship MP4](labwired-engineering-superintelligence-quadrotor.mp4). H.264, 1600 × 900, 30 fps, no audio. [Exact provenance](engineering-superintelligence-provenance.json) records every input checksum, live project hash, verification boundary, scene cut and rendering tool version.

The demonstration presents the platform claim:

> **LabWired is engineering superintelligence. From an idea to a validated, manufacturable machine.**

## What the flagship cut shows

1. Editable mechanical CAD and the populated assembly.
2. Native schematic and six-layer PCB evidence.
3. Universal LabWired logic-analyzer and oscilloscope workflows.
4. Four compiled STM32L476 firmware images driving four deterministic motor plants.
5. A selected driver-fault input and selective M1 shutdown while M2–M4 continue.
6. Pause and reset of the deterministic runtime.

The logic-analyzer and oscilloscope scenes use other LabWired examples to show universal platform instruments. They are not aircraft components. The motor runtime is a reduced-order engineering twin. The video does not claim physical flight, calibrated thrust, structural strength, thermal performance, EMI performance or electrical equivalence to the physical AT32F421/AM32 board.

## Live proofs

- [Four-channel flagship project](https://app.labwired.com/p/34b9a67d8727b8b3a152d57ce22e5504/edit): 12 parts, 64 wires, four compiled controllers and a fresh `model_verified` hash covering all four Hall-lock markers.
- [Channel-1 safety campaign](https://app.labwired.com/p/8beab229c9d4ed650ccbdc8725c233cc/edit): fault input at cycle 1,250,000, verified Hall lock, driver-fault detection and latched inverter shutdown.
- [KernelCAD assembly revision 5](https://app.kernelcad.com/p/DyJ405zg?version=5): populated ESC, repaired flight-controller model and four explicit rotor motion bindings.

The direct safety oracle also ends with PB0 low. The saved project requirement evaluator marks that GPIO check as unobservable, so the provenance records the direct result separately instead of presenting it as a saved-project requirement pass.

## Reproduce the flagship edit

The committed renderer uses single-threaded H.264 encoding. Two complete independent renders produced the same SHA-256 on the recorded toolchain.

```bash
python3 render-engineering-superintelligence.py
```

Optional paths:

```bash
python3 render-engineering-superintelligence.py \
  --source-video /path/to/quadrotor-engineering-preview.mp4 \
  --logic-image /path/to/universal-logic-analyzer.png \
  --scope-image /path/to/universal-oscilloscope.png \
  --output /path/to/labwired-engineering-superintelligence-quadrotor.mp4
```

The renderer adds cuts, captions and time compression. It does not synthesize telemetry or machine behavior.

## R4-02 native instrument acceptance recording — 12 November 2026

[Download the 34-second MP4](quadrotor-universal-instruments-preview-20261112.mp4): 1920 x 1080, H.264, 30 fps, 4,298,950 bytes, no audio. SHA-256: 68752b545d413c4bbae80eb9645133e6569430912f3fbdc29a9bc39270dbf53f.

The clip uses actual accepted LabWired footage at its original speed. It shows both universal instruments, independent controller sources, native PWM/Z observations, fault-driven inverter shutdown, and M1 stopped while M2-M4 continue. It carries a persistent development-preview label identifying the four STM32 controllers and behavioral motor models.

- [Original R4-02 recording](source/quadrotor-universal-instruments-r4-02.webm)
- [Exact edit list](quadrotor-universal-instruments-preview-20261112-edit.json)
- [Encoding provenance](quadrotor-universal-instruments-preview-20261112.provenance.json)
- [Editor](edit-universal-instruments-preview.py)
- [Runtime acceptance and final-frame QA](../labwired/evidence/20261112-universal-instruments/)

The optional CAD/PCB capture failed before producing accepted shots and is excluded. Production release and public-project publication remain pending.

## Long-form engineering source cut

[Watch the 75-second engineering preview](quadrotor-engineering-preview.mp4). Its [original provenance](engineering-preview-provenance.json) identifies the model revision, source commits, capture hashes, edit timing and scope.

That recording contains:

1. Actual KernelCAD design and dimensions.
2. Studio exploded-view and reassembly inspection.
3. Native OpenESC schematic sheets and populated PCB rendering from KiCad.
4. An audited candidate LabWired and KernelCAD browser execution with four compiled C controllers.
5. Selected fault input: M1 shuts down while M2–M4 continue.
6. Pause holds measured poses; reset clears every motor sample.

The CAD clips are time-compressed. Runtime clips retain their recorded speed. The movie shows engineering inspection and simulator behavior. It does not show physical manufacturing, aircraft flight or production acceptance.

## Reproduce the long-form cut

`capture-cad-original.cjs` preserves the exact recorder used. `capture-cad-review.cjs` adds portable module, Chrome and output-path defaults. The exact runtime recorder and proof files are in [the final trace package](../labwired/evidence/20261111-final/). Native schematic SVGs and PCB rendering come from the editable KiCad source.

```bash
python3 render-engineering-preview.py \
  --capture-dir /absolute/path/to/capture \
  --runtime-video /absolute/path/to/final-runtime.webm \
  --output /absolute/path/to/quadrotor-engineering-preview.mp4
```

The original [35-second single-channel demo](quadrotor-demo.mp4) remains historical evidence only.
