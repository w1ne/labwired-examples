# Pathfinder hobby rocket

This example is exported from a **real saved LabWired project**, not a proposed design.

- [Open the original project in LabWired](https://app.labwired.com/p/c9ede30a619b12d7c97056a2da040cc1/edit)
- [Project source, diagram, stimuli and oracle input](project.input.json)
- [Revision-pinned saved evidence](evidence.json)
- Board: `stm32f411ceu6-blackpill`
- Saved content hash: `2e8fef00dc7123091c40e3079e7d127604d5f5c8bb691da02bcd1a230fd70663`
- Original simulator evidence on this exact revision: **model_verified**
- Individual saved requirement results: **5/5 verified**

## Reproduce

1. Inspect `project.input.json`, which contains the original editable firmware source, circuit/netlist, input stimuli and explicit verification requirements.
2. Use LabWired's `labwired_project_create` with the input fields, or open the original saved project above. The imported copy is **unlisted**, and it does not automatically inherit a PCB, CAD attachment or verification receipt.
3. Run `labwired_project_verify` against the copied project with the saved requirements. Inspect the returned exact content hash and all clause results. Do not treat compilation alone as verified.
4. Inspect PCB and mechanical artifacts separately in the original project; record a fresh verification when changing firmware, wiring, source, or CAD identity.

## Proven boundary

Firmware phase transitions and saved simulated pressure/acceleration cases are verified; firmware-to-flight dynamics, fabrication, PCB fit and physical flight are not. This is the hobby-rocket showcase, not OLGA.

The linked PCB/CAD items, if present, are **not** reconstructed by the project-input import. The `evidence.json` file is a readback of the original saved project on 2026-11-21, not a promise that any future deployment or new copy has passed.
