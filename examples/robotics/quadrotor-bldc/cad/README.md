# Quadrotor mechanical model

The saved [KernelCAD model, revision 4](https://app.kernelcad.com/p/DyJ405zg?version=4)
contains the 226 mm OpenFrame-5F frame, exact native ESC substrate and the native
KiCad component mesh. The model is ready for visual assembly inspection.
Revision 3 remains available in project history.

## Verified on 12 November 2026

| Check | Result |
| --- | --- |
| Full hosted evaluation | Pass; 37 named parts, no diagnostics |
| Component geometry | 213 native KiCad reference instances; 56,072 triangles |
| Exact native substrate | Retained once; excluded from the component mesh |
| Rotor mechanism screen | 13 poses across four joints; mates satisfied; no reported collision |
| Default bounds | 277.9073 × 251.5513 × 39.3 mm |
| Studio revision | Revision 4 saved; meshReady=true; ten immutable input attachments |
| Native PCB against frame and FC envelope | 27 pairs have strictly separated conservative BREP bounds |
| Native PCB against support rings | All eight 6 mm OD rings have no reported exact-BREP interference |
| Visual review | Isometric and front views show top and underside component populations |
| Hardware acceptance | Not established |

The native STEP check first found a **0.0863 mm³** collision between a 7 mm OD
upper support ring and a PCB component. The corrected nominal ring OD is 6 mm,
with a 4 mm bore. Both the negative result and corrected eight-ring check are
retained. No ignore list or enlarged tolerance was used.

The complete populated PCB is 41.6208 × 42.5 × 6.33 mm. With the ESC underside at
Z = 14.4 mm, its lowest component is Z = 11.32 mm. The middle-frame top is
Z = 9 mm, so the conservative lower separation is **2.32 mm**. The populated PCB
top is Z = 17.65 mm. The FC envelope begins at Z = 22 mm, giving **4.35 mm**
separation. Its top remains 5.4 mm below the top-frame underside.

## Source and evidence

- `drone.kcad.ts` is the revision-4 design source. It uses existing generic
  KernelCAD imports, parts, connectors and mates.
- `revision-3-source.json` preserves the prior substrate-only source identity.
- `inputs/esc-population-native.provenance.json` records the native GLB hash,
  all 213 component references, the coordinate transformation and STL digest.
  The mesh uses native component geometry, not invented component boxes.
- `checks/populated-esc-ring-collision-negative.kcad.ts` reproduces the old
  ring collision. `checks/populated-esc-ring-clearance.kcad.ts` checks all
  eight corrected rings against the exact populated STEP.
- `checks/populated-esc-frame-bounds.kcad.ts` supplies the 36 solid-body
  bounding boxes. `evidence/populated-clearance-audit-20261112.json` records
  every PCB-to-part separating axis and lower distance bound.
- `evidence/populated-display-evaluate-20261112.json`,
  `populated-display-render-20261112.json`, `populated-studio-save-20261112.json`
  and `populated-studio-readback-20261112.json` retain hosted receipts.

The eight-ring tool returns overall `ok:false` because the populated STEP is a
compound of 214 distinct solids and modeled solder attachment is absent.
Its interference stage reports no overlap for the corrected rings. This result
supports geometric fit only; it is not a complete mechanical acceptance pass.

## Runtime bindings

`runtime-bindings.json` retains all four rotor interfaces unchanged:

| Component | Display | CAD corner | Pivot, mm | Sign |
| --- | --- | --- | --- | --- |
| rotor1 | M1 | rear-right | [89, 69.534420756, 9.3] | +1 |
| rotor2 | M2 | front-right | [89, -69.534420756, 9.3] | -1 |
| rotor3 | M3 | rear-left | [-89, 69.534420756, 9.3] | -1 |
| rotor4 | M4 | front-left | [-89, -69.534420756, 9.3] | +1 |

All axes are [0, 0, 1]. Revision 4 changes the stack and adds component geometry;
it does not move the rotor pivots or rename their parts/joints. The receiver must
use observed simulator angle and speed. The standalone CAD animation remains
a visual joint demonstration. A live revision-4 LabWired bridge must be checked
separately after its attachment is updated.

## Limits

- Motors, propeller blades, FC board and soft mounts remain labeled
  `ENVELOPE`. Vendor geometry, compressed grommet dimensions, FC component
  heights and connector overhang are not established.
- Native component STL uses one material. The source GLB retains native
  materials. Display meshes do not carry BREP topology or solid volume.
- The full native STEP remains the machining/geometry reference. The display
  model does not replace that native file.
- No complete physical assembly path, gravity stability, solder joint,
  fastener torque, strength, thermal or flight acceptance is established.
- The generic `inspect(of:'assembly')` path currently throws on mixed
  display-mesh bodies. The hosted `design_loop` wrapper also fails to stage
  imports within `attempts[].code`. Their failure receipts are retained;
  explicit evaluation, rendering and bounded native checks succeeded.

## Earlier limits and resolution

On 11 November, the complete populated STEP plus airframe exceeded the
1,024 MB evaluator cap. Its standalone interactive display exceeded the
896 MB worker cap. The immutable original receipts remain in `evidence/`.

[KernelCAD-server PR #655](https://github.com/w1ne/kernelCAD-server/pull/655)
fixed generic hosted STL staging and merged on 11 November. Revision 4 uses
that path: exact substrate plus native component display mesh. It evaluates,
renders and persists under the existing caps. No memory limit was increased.

Use Studio's exploded view to inspect the stack and frame. Exploded views are
presentation layouts, not an accepted physical assembly sequence.
