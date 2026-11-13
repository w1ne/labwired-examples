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
