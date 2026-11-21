# A1 reference mechanical integration

The final populated native PCB STEP fits the reference enclosure. Its geometry is the routed native board accepted by KiCad DRC; later schematic linkage, NC naming and portable library metadata are tracked separately in the hardware audit. The four A4988 packages and the LMR36520 package have drawing-checked STEP geometry. The USB connector uses an explicitly identified drawing-derived clearance model.

This is original A1-inspired reference geometry. It is not OEM Bambu geometry or a physical printer qualification.

## Package geometry

| Instances | Model and verified dimensions | Primary drawing |
|---|---|---|
| U10–U13 | A4988SETTR-T ET: 5 × 5 × 0.92 mm body, 28 contacts, 0.50 mm pitch, 0.25 mm contact width, 0.55 mm heels, 3.15 × 3.15 mm exposed pad | Allegro A4988, pages 18–19 |
| U20 | LMR36520ADDAR DDA: 6.00 mm lead span, 4.90 mm body length, 1.55 mm model height, 8 contacts at 1.27 mm pitch, 2.29 × 3.00 mm exposed pad | TI DDA0008B, 4214849/B, September 2025 |
| J20 | USB4216-03-A: 8.94 × 6.50 × 3.16 mm shell, 0.10 mm standoff, 11.14 mm overall shell-tab width, 16 contacts, two 0.49 mm locating pegs at 6.00 mm spacing | GCT USB4216 revision A2, 28 July 2025 |

The prior QFN filename said “EP3.35,” but the actual solid already had the correct 3.15 mm exposed pad. Its contact heels were extended from 0.40 mm to 0.55 mm. The prior SOIC exposed-pad length was 3.81 mm; the selected 3.00 mm variant lies within TI's 2.80–3.40 mm limit.

The USB STEP is an original clearance model derived from the primary drawing. It is not a supplier native CAD file. The public drawing does not dimension all spring, latch, forming or peg-depth details. Those details remain nominal and are identified in the model record. The existing USB4110 model was removed.

## USB land pattern

The connector keeps its placement at PCB (35, 97) mm and its signal pad centers at y = 93.320 mm. The GCT recommended layout requires a 3.925 mm shell-pad center pitch, 3.30 mm from the lower shell center to the peg centers, and 4.00 mm from the lower shell center to the signal-pad inner edge.

| Feature | Previous y, mm | Correct y, mm | Change, mm |
|---|---:|---:|---:|
| Upper shell pads | 93.890 | 93.970 | +0.080 |
| Lower shell pads | 97.920 | 97.895 | −0.025 |
| Locating holes | 94.570 | 94.595 | +0.025 |

All signal pad positions, sizes and net assignments remain unchanged by the mechanical patch. The patch also replaces the inherited USB4110 outline and model references.

## Enclosure fit

The fit check imports the native KiCad board STEP and exact enclosure/tray STEP files exported by KernelCAD. It uses OCCT BRep intersections, surface distances and cylindrical mounting-hole axes.

| Check | Result |
|---|---:|
| Populated PCB to enclosure overlap | 0 mm³ |
| Populated PCB to tray overlap | 0 mm³ |
| Minimum populated PCB to enclosure clearance | 1.200 mm |
| Nominal board outline to cavity sidewall clearance | 2.500 mm |
| Four mounting-hole axis errors | Less than 0.000001 mm |
| Mounting-hole diameter | 3.200 mm |
| Reference plug to enclosure overlap | 0 mm³ |
| Minimum reference plug passage clearance | 0.7076 mm |
| Continuous downward removal envelopes | No enclosure overlap |

The native board is rotated 90° about Z and translated by (57, −49, 17.205) mm. The four world mounting coordinates are (95, −44.5), (95, 46.5), (152.5, −44.5), and (61.5, 46.5) mm. The source places the mounting bosses on the removable bottom tray and opens the cavity through the bottom.

The USB mouth is at (156.995, −14, 20.480) mm and faces +X. Its passage is 14 × 8 mm. The checked plug envelope is 12 × 6.5 mm; the 12 mm width is a declared design assumption. This does not cover every commercial cable overmold.

The native export leaves a 0.005 mm nominal separation between the dielectric bottom and tray bosses because of the chosen export datum. The audit does not qualify soldermask thickness, fastener preload, manufacturing tolerance stacks, thermal behavior, vibration or wire-harness routing.

## Source and evidence

- `a1-native-fit.kcad.ts` is the authored source. It imports the final native populated PCB from immutable examples commit `539dff7c2c9a78790aeb159daefd04527fabe074`. Its SHA-256 is `5ac9ba79f62d2b2cd5841b6c94a430c3c34a320253f77813626a8baf09c4fdff`.
- `a1-native-fit.saved.kcad.ts` is the exact read-back source of KernelCAD project `MwczxIII`, revision 7. Its SHA-256 is `7017ff83d1c28f7fa30717c545e2e0edc3f26fe43ecfe0116844a312cef89478`. The sole source change is the STEP reference: the immutable URL becomes `./inputs/4fa338f753a8.step`.
- `inputs/4fa338f753a8.step` is the saved attachment. Its SHA-256 is `4fa338f753a8c8a17331facabd8ee8d3698bc0a0cd3fa152b71749e88baa2e2a`, identical to `../hardware/exports/a1-printcore-populated.step`.
- `source-materialization-receipt.json` and `authored-to-saved-source.diff` reconcile authored input, transient hosted evaluation and saved revision identities. These are distinct byte sequences. The transient evaluated SHA is `b0f3371600d4686c893aff3c622329e66ab45ba892c5799abf9d7f6689f5fd73`; its temporary file path is not reconstructed.
- `kernelcad-evaluate-request.json`, `kernelcad-evaluation.json` and `kernelcad-saved-revision.json` retain the actual request and read-back evidence. The full evaluation reports 59 parts, 10,015 faces and 273 features, with valid finite geometry. The existing generic mechanism check covers ten poses and four joints.
- `enclosure-fit.json` binds the final authored source and populated STEP to the exact numeric fit checks.
- `a1-fit-enclosure.step` and `a1-fit-bottom.step` are the exact KernelCAD exports used by the fit audit.

The display mesh is a separate hosted artifact. Solid evaluation and nominal fit do not imply that browser display or physical hardware has been accepted. The final live-view evidence records mesh availability and motion/OLED behavior for the pinned revision.

The original `a1-populated-fit-baseline.step`, if retained in repository history, is a superseded copper baseline. It is not the final fit input or fabrication output.

## Reproduce

Use KiCad's Python module for native board edits. Use `cadquery-ocp==8.0.1.1.0` for the BRep checks.

```bash
python qualify_package_solids.py --models-dir ../hardware/models
python build_usb4216_clearance.py --models-dir ../hardware/models
python3 apply_mechanical_patch.py INPUT.kicad_pcb OUTPUT.kicad_pcb \
  --models-dir ../hardware/models --model-prefix '${KIPRJMOD}/models'
python verify_enclosure_fit.py \
  --board-step ../hardware/exports/a1-printcore-populated.step \
  --source a1-native-fit.kcad.ts \
  --enclosure-step a1-fit-enclosure.step \
  --bottom-step a1-fit-bottom.step
```

The released native board already contains the mechanical patch. Apply it only when reproducing from the identified original input. Refill zones and run the original project DRC after any board change. The package generators retain source provenance and license headers. They require the KiCad standard STEP library named in the scripts.

## Primary sources

- [Allegro A4988 datasheet](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf), pinout and ET package on pages 18–19.
- [TI LMR36520 datasheet](https://www.ti.com/lit/ds/symlink/lmr36520.pdf), pinout on page 4 and the appended DDA0008B package drawing.
- [GCT USB4216 revision A2 drawing](https://www.mouser.lt/datasheet/3/1507/1/usb4216.pdf), recommended layout and mechanical interfaces on page 1.

Downloaded drawing hashes are in `primary-drawing-sha256.json`. The PDFs are retained with the working evidence and are not redistributed in this repository.

