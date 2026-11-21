# AXIOM H1 robot controller

This example is exported from a **real saved LabWired project**, not a proposed design.

- [Open the original project in LabWired](https://app.labwired.com/p/e6b30d45ba55e64aa450a2aa292edd4b/edit)
- [Project source, diagram, stimuli and oracle input](project.input.json)
- [Revision-pinned saved evidence](evidence.json)
- Board: `esp32-c3-supermini`
- Saved content hash: `3fbbe85932524caaf21b5f63d2c2333e177c32320d4e162370c288964cd7cfb3`
- Original simulator evidence on this exact revision: **model_verified**
- Individual saved requirement results: **3/3 verified**

## Reproduce

1. Inspect `project.input.json`, which contains the original editable firmware source, circuit/netlist, input stimuli and explicit verification requirements.
2. Use LabWired's `labwired_project_create` with the input fields, or open the original saved project above. The imported copy is **unlisted**, and it does not automatically inherit a PCB, CAD attachment or verification receipt.
3. Run `labwired_project_verify` against the copied project with the saved requirements. Inspect the returned exact content hash and all clause results. Do not treat compilation alone as verified.
4. Inspect PCB and mechanical artifacts separately in the original project; record a fresh verification when changing firmware, wiring, source, or CAD identity.

## Proven boundary

PCA9685 register writes and sensor/controller behavior are verified; PCA9685-driven servo motion, firmware-to-MuJoCo coupling and physical robot response are not.

The linked PCB/CAD items, if present, are **not** reconstructed by the project-input import. The `evidence.json` file is a readback of the original saved project on 2026-11-21, not a promise that any future deployment or new copy has passed.
