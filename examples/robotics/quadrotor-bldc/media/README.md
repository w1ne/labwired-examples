# Quadrotor engineering preview

[Watch the 75-second MP4](quadrotor-engineering-preview.mp4). H.264, 1600 × 900, 30 fps, no audio. [Exact provenance](engineering-preview-provenance.json) identifies model revision, source commits, capture hashes, edit timing and scope.

## What is recorded

1. Actual KernelCAD revision 3, editable source and dimensions.
2. Actual Studio exploded-view and reassembly inspection.
3. Native OpenESC schematic sheets and populated PCB rendering from KiCad.
4. Actual candidate LabWired and KernelCAD browser execution with four compiled C controllers.
5. Selected fault input: M1 shuts down while M2–M4 continue.
6. Pause holds measured poses; reset clears every motor sample.

The CAD clips are time-compressed. All runtime clips retain their recorded speed. The movie shows engineering inspection and simulator behavior. It does not show physical manufacturing, a passing populated in-frame assembly, or aircraft flight.

## Reproduce the recording and edit

`capture-cad-review.cjs` is the CAD recorder with portable module, Chrome and output-path defaults. Set `PLAYWRIGHT_MODULE`, `CHROME_BIN` and `CAPTURE_DIR` only when the defaults do not apply. The exact runtime recorder and its environment/proof files are in [the final trace package](../labwired/evidence/20261111-final/). Native schematic SVGs and PCB rendering come from the native KiCad source.

The edit uses ffmpeg and DejaVu Sans:

```bash
python3 render-engineering-preview.py \
  --capture-dir /absolute/path/to/capture \
  --runtime-video /absolute/path/to/final-runtime.webm \
  --output /absolute/path/to/quadrotor-engineering-preview.mp4
```

The capture directory contains `video/cad-scenes.json` and the three CAD WebMs, plus `pcb/schematic-overview.png`, `pcb/schematic-channel.png` and `pcb/esc-isometric.png`. The renderer uses the displayed, audited final-run cut positions; align visible events before substituting a newly recorded runtime video. The exact raw recordings are retained with the session evidence on work-1; their hashes are in the provenance.

The original [35-second single-channel demo](quadrotor-demo.mp4) remains historical evidence.
