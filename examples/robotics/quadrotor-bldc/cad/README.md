# Quadrotor mechanical model

The current editable drone.kcad.ts uses the pinned 226 mm OpenFrame-5F frame,
the native ESC substrate and population, and the current repaired OpenFC-Lite
board. [Studio revision 6](https://app.kernelcad.com/p/DyJ405zg?version=6)
is saved with 12 exact imported assets and a ready cloud display mesh.

## Full native-solid assembly checkpoint — 18 November 2026

The editable `drone-native-solids.kcad.ts` retains all 378 imported FC/ESC
solids as separate parts with explicit fixed relationships. USB contact and
shell bodies attach to their native connector housing; microSD contacts and
shell bodies attach to their native socket housing. The native poses and all
frame, motor and propeller bodies remain present.

The [local full evaluator receipt](evidence/native-solid-evaluation-20261118/local-evaluation.json)
passes with **894 features, 412 parts, 411 mates and zero diagnostics**. It checks
13 poses across four rotor joints in 334.976 seconds on private runtime commit
`b89aceba980c12ed404ce3963add0ee26106be0f`. Exact downloaded STEP bytes were
staged locally; their original URLs and hashes are in the receipt. The source
SHA-256 is `72810ad3fbf9ceb53b29d3fc50abbb2567e3416552b4df77d87d111884098dcb`.

This evaluator checks joint limits, rigid attachment and sampled interference.
Its own review hint still requires strict pose-envelope, support-intent and
gravity review. The run used an 8 GiB local Node heap and does not establish
hosted memory acceptance. Motor/propeller/support envelopes and physical load
qualification remain separate from the exact imported PCB bodies. Studio
revision 6 remains the earlier saved checkpoint until the complete strict
review and hosted save succeed.

## Corrected native model datums — 18 November 2026

The native boards now contain two source-qualified **3D model transform**
corrections. The routed copper, drill centres, component placements and
project rules remain unchanged. The matching library footprints carry the
same corrections.

| Component | Correction | Source/geometry check |
| --- | --- | --- |
| FC Card1, Shouhan TF PUSH | Model offset Y = -2.45 mm | Both 0.8 mm locating pegs align with the existing 1.2 mm native holes on 8 mm centres; all nine contact rows align |
| ESC U12, INA186A3IDCKR | Model offset Z = +0.5 mm; rotation Z = +90 degrees | All six lead soles align with the existing lands; the pin 1 marker faces pad 1; 0.95 mm model height and 0.05 mm standoff agree with TI DCK0006A ranges |

The corrected FC PCB SHA-256 is
`3216b761288ee06f01527d14041d6debaa2d89da46da4ced76b320c98cc60348`;
the corrected ESC PCB is
`13a9b74e8a0afc65c016302d155bd7b4e10d3edd8cc331822bfb9ccc9e182249`.
KiCad 10.0.8 DRC and schematic parity report zero violations and zero
unconnected items for both boards under their existing project rules.

The new native STEP files retain **164 valid FC solids and 214 valid ESC
solids**. Only Card1's eleven solids and ESC U12 move. All other body bounds
are unchanged within the inspection API's 0.00001 mm comparison tolerance;
all solid volumes are unchanged within 0.000001 mm3. This is a native datum
proof. The corrected all-solid evaluator replay above passes; strict physical
review remains outstanding.

- [Manufacturer drawing identity, exact datum calculations and limits](evidence/model-datum-correction-20261118/component-datums.json)
- [Four native-source transform-only checks](evidence/model-datum-correction-20261118/source-transform-proof.json)
- [All-solid before/after comparison](evidence/model-datum-correction-20261118/native-solid-comparison.json)
- [Exact KiCad export commands and hashes](evidence/model-datum-correction-20261118/native-exports.json)

Rebuild these outputs from the package's checked-in model directories:

```sh
python3 examples/robotics/quadrotor-bldc/cad/rebuild-native-models.py
```

## Published native source checkpoint before datum correction — 18 November 2026

The currently saved revision 6 FC input binds to the earlier PCB SHA-256
5c458e5101e154ade50d4f46838bfef8431463d00d7e8059d6d342e8b68a4dc9 and
asset commit f741c8ca2ed11c9b55c84bcdae6cc6dec888a676. All 107 assigned
component models resolve. The current display mesh has 47,778 facets.

The full build passes with 146 features, 38 parts and 37 mates. The shallow
mechanism screen checks 13 poses across the four rotor joints. The actual
[strict review](evidence/native-current-design-loop-20261118.json) remains
**false**: the two population meshes contain 213 and 146 disconnected bodies,
the articulated assembly lacks a physical-use-case declaration, and exact
interference coverage is incomplete for the display-mesh pairs. These are
active package defects, not accepted waivers. Native solid relationships and
physical-support qualification are the next CAD repair.

The [source binding receipt](evidence/native-current-lab-binding-20261118.json)
records only native board and model identity. The existing Lab retains its
unpublished five-controller flight draft, unchanged source/firmware/stimuli,
and unchanged airframe parameters. Its public revision was not replaced.
Neither identity metadata nor the shallow motion badge is a full fit result.

Current evidence:

- [Native evaluation](evidence/native-current-evaluate-20261118.json)
- [Strict physical review](evidence/native-current-design-loop-20261118.json)
- [Observed visual review](evidence/native-current-visual-review-20261118.json)
- [Saved revision and ready-mesh readback](evidence/native-current-studio-readback-20261118.json)
- [Isometric view](evidence/native-current-iso-20261118.png) and [top view](evidence/native-current-top-20261118.png)

The measurements below remain historical source-bound evidence. The legacy
clearance checker refuses the newer source hash; it must not be presented as
current full-assembly acceptance.

## Native FC candidate, 12 November 2026

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

## Historical clearance check and inputs

The following archived check applies to the earlier source and export hashes:

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
speed. The standalone CAD animation is a visual joint demonstration. Its
revision attachment must be updated and checked when this candidate is saved.

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

The ESC PCB metadata follow-up corrects 16 copied pin-function labels. The
[byte-level correction receipt](../hardware/esc-4in1/validation/pad-function-correction-20261118.json)
proves all non-label PCB bytes are unchanged. The existing native STEP
geometry and its original export receipt therefore remain unchanged; the
new PCB hash does not imply a mechanical redesign.
