# Quadrotor mechanical model

The current [`drone.kcad.ts`](drone.kcad.ts) candidate contains the pinned 226 mm
OpenFrame-5F frame, native ESC substrate and population, and the repaired native
OpenFC-Lite substrate with all 107 assigned component models. Hosted evaluation
passes with **38 parts and 37 mates**. It is saved as
[Studio revision 5](https://app.kernelcad.com/p/DyJ405zg?version=5), with a ready
cloud mesh and 12 immutable inputs. The [release receipt](evidence/studio-v5-release-20261112.json)
records the source identity, asset hashes, build result and failed full-physical-review gate.

## Saved native FC revision, 12 November 2026

| Check | Result |
| --- | --- |
| Full hosted build | Pass; 146 features, 38 parts, no build diagnostics |
| Rotor mechanism screen | 13 poses across four joints; mates satisfied; no reported collision |
| FC model resolution | 107 of 107 assigned models resolved; 53 bare contacts and four testpoints have no assigned 3D body |
| Exact populated FC STEP | 164 valid solids, including the substrate and separate model details |
| Display population | 47,786 triangles; source poses preserved; binary STL conversion error below 0.000001 mm |
| FC substrate | Real scalloped outline and four open 4 mm mounting cutouts on 30.5 mm centres |
| FC versus frame, lower supports, ESC and rotor envelopes | 31 conservative separating bounds; minimum 0.96499 mm above the populated ESC |
| FC components versus four upper support rings | All 652 solid/ring pairs separated; minimum conservative lower bound 0.62879 mm |
| Board/support contact | Four coplanar substrate-bottom/ring-top contacts; no positive-volume intersection |
| Full mechanical acceptance | False; solder, selected fasteners/mounts and physical motor support remain unmodeled |

The native board declares nominal thickness **1.0 mm**. Its detailed stackup
exports a substrate from Z = 0 to **0.9378 mm**; outer copper and mask use the
original exporter convention. The original stackup sums to 1.0078 mm including
outer copper and 1.0278 mm including mask. No scale or thickness correction was
applied. Source model offsets and component placement are unchanged.

The FC export origin is the mounting-pattern centre at native KiCad
(153.0912, 87.1597) mm. The assembly translation is [0, -12.75, 22] mm. The full
populated FC occupies Z = **18.615 to 24.0228 mm**. The populated ESC reaches
Z = 17.65 mm, so the conservative nominal vertical gap is **0.965 mm**. The
previous 4.35 mm claim covered only the empty FC envelope and is superseded.

The ring proof uses every imported STEP solid's enclosing box and each ring's
outer cylinder. Positive distance between these enclosing shapes proves that
the source bodies cannot overlap. A 0.00001 mm allowance is subtracted from the
reported bounds. This is a geometric proof; it does not qualify manufacturing,
mount compression, solder, wiring or vibration tolerances.

## Reproduce and inspect

Run from any working directory:

```sh
python3 examples/robotics/quadrotor-bldc/cad/checks/check-native-fc-clearance.py
```

The script verifies the design-source and populated-STEP hashes before
recomputing the 31 external bounds and 652 ring/component bounds. It refuses
non-positive bounds rather than treating overlapping boxes as a passing result.
Its inputs and receipts are:

- [`native-fc-step-inspection-20261112.json`](evidence/native-fc-step-inspection-20261112.json): all 164 source-bound BREP solid boxes and validity results.
- [`native-fc-assembly-inventory-20261112.json`](evidence/native-fc-assembly-inventory-20261112.json): the 38-part evaluated assembly inventory.
- [`native-fc-clearance-audit-20261112.json`](evidence/native-fc-clearance-audit-20261112.json): every external separating bound and each support-ring minimum.
- [`native-fc-design-review-20261112.json`](evidence/native-fc-design-review-20261112.json): full build, production review, path-planning and bounded-job failure results.
- [`mechanical-review/`](../hardware/flight-controller-openfc-lite-rev2-lw1/mechanical-review/): immutable native substrate, populated STEP, component STL, exporter commands, 107-model resolution inventory and hashes.
- [`reviewed-models/`](../hardware/flight-controller-openfc-lite-rev2-lw1/reviewed-models/): the 17 missing stock model files, immutable upstream identities and license.

The direct populated-compound/ring Boolean review reached the existing 1000 MB
job limit. The conservative bound proof covers all component/ring pairs without
raising that limit. The production review remains false: imported population
meshes contain separate component bodies without solder-joint load paths, and
nominal motors lack physical bearing/support geometry. Mixed-mesh assembly-path
planning reports that it cannot transform an imported mesh. These failures are
retained; the model does not claim a production assembly sequence or strength.

## Prior ESC evidence and saved revision 4

Revision 4 contains 37 parts, 213 native ESC reference instances and 56,072
component triangles. Its ten immutable inputs and mesh-ready readback remain in
`evidence/`. It has the earlier FC envelope, not the repaired populated FC.

The native ESC STEP check found a **0.0863 mm³** overlap with a 7 mm OD upper
support ring. Reducing the nominal ring OD to 6 mm removed that overlap. The
negative result and corrected eight-ring check remain in
`checks/populated-esc-ring-collision-negative.kcad.ts` and
`checks/populated-esc-ring-clearance.kcad.ts`. The original eight-ring report
retains its false full-mechanical verdict because the PCB is a compound of 214
separate solids without solder attachment.

The ESC substrate starts at Z = 14.4 mm. Its lowest component is Z = 11.32 mm,
**2.32 mm** above the middle-frame top. This placement and the four rotor pivots
are unchanged by the native FC replacement.

## Runtime bindings

`runtime-bindings.json` retains these four rotor interfaces:

| Component | Display | CAD corner | Pivot, mm | Sign |
| --- | --- | --- | --- | --- |
| rotor1 | M1 | rear-right | [89, 69.534420756, 9.3] | +1 |
| rotor2 | M2 | front-right | [89, -69.534420756, 9.3] | -1 |
| rotor3 | M3 | rear-left | [-89, 69.534420756, 9.3] | -1 |
| rotor4 | M4 | front-left | [-89, -69.534420756, 9.3] | +1 |

All axes are [0, 0, 1]. A runtime receiver must use observed simulator angle and
speed. The standalone CAD animation is a visual joint demonstration. The canonical four-channel circuit pins revision 5 and contains these exact bindings.
Runtime acceptance is recorded separately from the CAD save receipt.

## Remaining model limits

- Motor, propeller and soft-mount geometry remains explicitly nominal.
- L1/L2/L3 preserve original package proxies. Resolved model files do not prove exact vendor construction or tolerance.
- Display meshes have one material and carry no BREP topology or solid-volume evidence. The source STEP files remain the geometry reference.
- Bare contacts and testpoints have no separate package body. Cables, mating plugs and an inserted microSD card are absent.
- No complete physical assembly path, gravity stability, solder joint, fastener torque, structural, thermal or flight acceptance is established.

The earlier mixed-mesh inventory and hosted attempt-staging tool failures have
been repaired in the generic CAD service. The current candidate evaluates and
its assembly inventory succeeds under the existing resource limits; historical
failure receipts remain intact.
