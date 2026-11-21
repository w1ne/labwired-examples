# P.I.G. six-axis arm

This example is exported from a **real saved LabWired project**, not a proposed design.

- [Open the original project in LabWired](https://app.labwired.com/p/db959cbc4ca34a1a6fe6738b153b9a14/edit)
- [Project source, diagram, stimuli and oracle input](project.input.json)
- [Revision-pinned saved evidence](evidence.json)
- Board: `nucleo-f401re`
- Saved content hash: `5745ef9b5f844b01c9cebf3977e4b814fe9f83aca1d651cab63797b1bb4931c9`
- Original simulator evidence on this exact revision: **model_verified**
- Individual saved requirement results: **3/3 verified**

## Reproduce

1. Inspect `project.input.json`, which contains the original editable firmware source, circuit/netlist, input stimuli and explicit verification requirements.
2. Use LabWired's `labwired_project_create` with the input fields, or open the original saved project above. The imported copy is **unlisted**, and it does not automatically inherit a PCB, CAD attachment or verification receipt.
3. Run `labwired_project_verify` against the copied project with the saved requirements. Inspect the returned exact content hash and all clause results. Do not treat compilation alone as verified.
4. Inspect PCB and mechanical artifacts separately in the original project; record a fresh verification when changing firmware, wiring, source, or CAD identity.

## Proven boundary

PCA9685 pose register sequence, joint limit logic and emergency-stop state are verified; servo motion, collision, torque and physical arm operation are not.

The linked PCB/CAD items, if present, are **not** reconstructed by the project-input import. The `evidence.json` file is a readback of the original saved project on 2026-11-21, not a promise that any future deployment or new copy has passed.
