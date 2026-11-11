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
