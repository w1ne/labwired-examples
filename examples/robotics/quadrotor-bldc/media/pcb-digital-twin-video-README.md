# LabWired quadcopter video — 13 November 2026

**Featured 32.4 s cut:** [Watch the MP4](labwired-quadrotor-pcb-digital-twin-32s.mp4).

Five scenes: parametric quadcopter, PCB routing, rotating populated 3D PCB, live oscilloscope and logic analyzer together, digital twin. No separate fault/safety section. No number-of-controllers claim in the film. Audio: none.

- **PCB routing:** `render-pcb-routing.py` reads the exact existing KiCad 10 board file, exposes 1,198 source routing segments and 1,716 vias across six copper layers, and progressively reveals the finished routes. This does not claim a new routing algorithm executed during the recording.
- **3D PCB:** `render-pcb-turntable.py` imports the saved `esc-board-populated.glb` (214 mesh objects). The camera orbit is rendered in Blender and interpolated to 30 fps. Surface color and lighting were adjusted for visibility; geometry and placements remain derived from the source asset.
- **Oscilloscope and logic analyzer:** synchronized crops of the same accepted LabWired R4-02 live browser recording, not unrelated demonstration devices.
- **Digital twin:** captured Quadrotor LabWired and KernelCAD model motion, not aircraft flight-validation evidence.

KiCad **10.0.8** was used to export all six copper layers. Its fresh DRC report lists zero violations, zero unconnected items, and zero schematic parity issues under the configured checks; inherited ignored-rule categories remain documented in [the DRC receipt](pcb-story-kicad10-drc-20261113.txt).

**Source attribution:** the physical ESC source is a derivative of [OpenDrone OpenESC-30x30](https://github.com/OpenDrone-hw/OpenESC-30x30), commit `bf306934b5decc130ab1df6b653563ea16165e8e`, CERN-OHL-S-2.0. See `../hardware/esc-4in1/README.md` and the included `LICENSE.CERN-OHL-S-2.0`.

[Exact edit and input SHA-256 hashes](labwired-quadrotor-pcb-digital-twin-32s.provenance.json).
