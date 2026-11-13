# Readable LabWired quadrotor film — 13 November 2026

[Watch the 65.3-second focused MP4](labwired-quadrotor-focused-demo.mp4).
1600 × 900, H.264, 30 fps. SHA-256: `937664d9a25e78152e4dd78e6721274f5b0f04c1d3b2263cadfb0863da01fa9d`.

This is the primary **LabWired quadrotor motor-bench and CAD** presentation.
It preserves real captured motion at original speed and uses eight extended scenes,
compared with twelve short scenes in the previous 44-second cut. Full-size
closeups of the actual quadrotor universal oscilloscope and logic analyzer make
native PWM, current and fault signals readable. The former OpenDrone-labeled
schematic shot and unrelated example-instrument stills are excluded.

## Frame exports

- [Parametric 3D aircraft](quadrotor-focused-cad.jpg)
- [Live analog oscilloscope](quadrotor-focused-oscilloscope.jpg)
- [Live digital logic analyzer](quadrotor-focused-logic-analyzer.jpg)
- [Driver-fault test](quadrotor-focused-fault.jpg)

## Reproduce and audit

- [Renderer](render-focused-quadrotor-demo.py)
- [Exact source hashes, shot time ranges and scope](labwired-quadrotor-focused-demo.provenance.json)
- [Actual accepted R4-02 browser recording](source/quadrotor-universal-instruments-r4-02.webm)
- [Native source and CERN-OHL-S-2.0 attribution](../hardware/esc-4in1/README.md)
- [Earlier 44-second flagship cut](labwired-engineering-superintelligence-quadrotor.mp4) — retained for historical comparison.

This showcases a four-controller deterministic motor bench, not a verified
flying aircraft. The native ESC layout derives from OpenDrone OpenESC-30x30,
commit `bf306934b5decc130ab1df6b653563ea16165e8e`, under
CERN-OHL-S-2.0. LabWired integration, model testing and adapted native board
work are distinct from ownership of that original source. Original hardware
and model boundaries remain documented in the [system README](../README.md).
