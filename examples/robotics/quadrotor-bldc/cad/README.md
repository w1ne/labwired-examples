# Quadrotor mechanical model

The saved [KernelCAD model, revision 3](https://app.kernelcad.com/p/DyJ405zg?version=3)
is the 226 mm OpenFrame-5F integration model. This directory restores its source
to the examples repository. The prior local file described the older oversized
concept and did not match the saved model.

## Model and inputs

- `drone.kcad.ts` imports the pinned OpenFrame-5F rev2.2 STEP parts and the real
  ESC substrate from the KiCad STEP export. All source URLs are revision-pinned.
- `revision-3-source.json` records the saved project revision and input SHA-256
  digests. The matching source STEP files are already tracked in
  `../hardware/frame-openframe-5f/releases/rev2.2/step/` and
  `../hardware/esc-4in1/fabrication-review/`.
- Parts ending in `ENVELOPE` are nominal motor, propeller, flight-controller or
  soft-mount geometry. They are not manufacturer STEP models. The propeller
  sweep is 129.7 mm; blade profiles are illustrative, not aerodynamic surfaces.
- The four independent rotor joints use `rotor1Angle` through `rotor4Angle`.
  The built-in animation is a visual joint demonstration.

Use the viewer's **Exploded view** control and **Explode distance** slider to
inspect the stack and frame assembly. The exploded layout is a presentation
tool; it is not an accepted physical assembly procedure.

## Fresh evidence — 11 November 2026

| Check | Result |
| --- | --- |
| Full OpenCASCADE evaluation | Valid; 36 parts, 2,176 faces |
| Combined solid volume | 158,451.1378 mm³ |
| Default-pose bounds | 277.9073 × 251.5513 × 39.3 mm |
| Rotor mechanism screen | 13 poses across four joints; all mates satisfied; no collisions |
| STEP re-import | 36 solids; every solid reports valid BREP |
| STEP and GLB export | Both complete; sizes and SHA-256 digests are in `evidence/` |
| Full assembly-path and stability | Unknown: the default work budget expired before paths were established |
| Design-loop wrapper | Returned `feature.invalid-args`; evaluation and export succeeded separately |
| Flight, strength, fastener torque, battery and thermal behavior | Not verified by this mechanical model |

The source and JSON receipts preserve these limits. Geometry validation does
not establish a safe physical aircraft or a finished flight-control system.

## Runtime binding fixture

`runtime-bindings.json` maps the four existing LabWired motor components to
the evaluated model's named rotor and propeller groups:

| LabWired component | Display ID | CAD corner | Pivot, mm | Sign |
| --- | --- | --- | --- | --- |
| rotor1 | M1 | rear-right | [89, 69.534420756, 9.3] | +1 |
| rotor2 | M2 | front-right | [89, -69.534420756, 9.3] | -1 |
| rotor3 | M3 | rear-left | [-89, 69.534420756, 9.3] | -1 |
| rotor4 | M4 | front-left | [-89, -69.534420756, 9.3] | +1 |

All axes are [0, 0, 1]. Signs express the authored motor-to-airframe orientation.
The mapping names the rigid downstream part group explicitly. It does not infer
the assembly graph. It must be pinned to project `DyJ405zg`, revision `3`.

The generic runtime bridge uses the simulator's observed `positionRad` and
`speedRpm`. It does not infer shaft angle from a visual timer. The receiver holds
the last observed pose on pause or missing telemetry and clears on stop.
The bridge must pass its own browser integration test before this fixture is
claimed as a working live connection.

## Populated ESC candidate — not yet validated

The native KiCad populated STEP evaluates by itself. Its measured bounds are
41.6208 × 42.5 × 6.33 mm, with native Z from −3.08 to +3.25 mm. The saved
revision-3 assembly contains the exact substrate only. It has not been replaced.

Two separate limits blocked the complete populated assembly:

| Attempt | Observed result |
| --- | --- |
| Full populated STEP inside the 36-part assembly | The hosted evaluator exceeded its 1,024 MB limit at 1,028 MB and restarted |
| Native component STL alongside the exact BREP substrate | Hosted input staging left `upload:0` unresolved for `lib.meshFromSTL`; geometry evaluation did not begin |

The generic import repair is
[kernelCAD-server PR #655](https://github.com/w1ne/kernelCAD-server/pull/655).
Its 40 input tests and TypeScript check pass. It is not deployed. This repair
does not establish that the full candidate fits the evaluator's memory budget.

`candidates/drone-populated-step.kcad.ts` preserves the failed full-STEP
attempt. Its input now uses the immutable native export URL instead of the
per-call `upload:0` identifier. Its old stack height is not accepted for the
populated assembly.

`candidates/drone-populated-mesh-stack-lift.kcad.ts` proposes a 2 mm lift of the
ESC and FC stack. It keeps the rotor pivots, part names and joint names unchanged.
It imports `inputs/esc-population-native.stl`, which contains 213 native KiCad
component reference instances and 56,072 triangles. The native PCB mesh was
excluded, so the candidate retains one exact BREP substrate. STL stores a uniform
component color; the original populated GLB retains its native materials.

The native source GLB and STEP are pinned to examples commit
`619a61230add2ea3bd3e8a4f9d278a75ad396d04`. The component mesh provenance records
the source digest, units, coordinate transformation, reference names and output
digest. It contains imported component geometry, not invented component boxes.

### Stack-height finding

The measured middle-frame top is Z = 9 mm. At the old ESC placement of
Z = 12.4 mm, the lowest populated component would reach Z = 9.32 mm. That leaves
only **0.32 mm nominal separation**.

The proposed lift places the ESC at Z = 14.4 mm and the FC envelope at
Z = 22 mm. The lowest ESC component would then reach Z = 11.32 mm, giving
**2.32 mm nominal separation** above the frame. The FC envelope top would be
Z = 23.6 mm, leaving **5.4 mm** below the top-frame underside at Z = 29 mm.

These are coordinate and bounding-envelope calculations. They do not establish
complete component clearance, an assembly path or gravity stability. Compressed
grommet height, FC component heights and connector overhang remain unverified.
Both candidate sources, both failure receipts and the stack calculation are
preserved in this directory. The recorded live-motion fixture remains pinned
to saved revision 3.


## Standalone native PCB display limit

The exact populated STEP remains a valid native geometry export. A separate unlisted KernelCAD project saved its source successfully, but its interactive display mesh failed: the revision-mesh worker used 906 MB against its 896 MB limit. The preview worker separately exceeded the same limit at 903 MB. This is not a ready interactive PCB view, and it does not establish populated in-frame clearance.

The [save and failure receipt](evidence/native-pcb-studio-save-20261111.json) preserves the project/version, exact STEP hash and observed errors. The [native STEP](../hardware/esc-4in1/fabrication-review/esc-board-populated.step) and native KiCad files remain available. The saved airframe project stays at revision 3.
