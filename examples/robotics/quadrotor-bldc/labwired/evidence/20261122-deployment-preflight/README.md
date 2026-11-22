# Quadrotor deployment preflight — 22 November 2026

This bundle preserves release preparation and a measured CAD artifact defect. It does **not** establish deployed flight, a saved-project update, browser flight, or corrected CAD rendering. The accepted native flight archive remains unchanged in ../20261122-native-flight.

## Results and limits

| Check | Recorded result |
| --- | --- |
| Accepted app/core source | App integration e3d0cb112606dcbe02c9e9c8c7bc3e919a580f7e retains core 7c0825e7bbcae493b710c5ffeb0d848b4ddd4fa0, all 14 qualified runtime source files, and the same five-node plan/environment. |
| Actual deployed optimized engine | Qualification has not run. The earlier accepted engine used --no-opt; its receipt does not qualify different deployed bytes. |
| Saved project and browser | No project mutation or browser flight is recorded here. The connected local-browser attempt returned an access-context error before tab/account access. |
| Saved CAD source | DyJ405zg@6 remains source SHA-256 f87316c6a9de81148c8985e9387641a0ead22d5d2744186d2041678c0364a10e, 9,688 UTF-8 bytes. The retained source differs only by 15 asset-import localizations and one trailing newline. All 12 attached asset hashes match. |
| Stored and public CAD artifact | Both current endpoints returned identical 12,865,247 bytes, SHA-256 e041191cfd930893229d3d569dece43dc5ed8441dff865270f65e09b1f78e141. Their producer pin is 98618663029a83e4c28d833e398203f0510277938e07128a05dafe1c1a1be348. |
| Old producer pin | The CDN accepted old f810d150… but returned the new producer's bytes. The strict stored-only endpoint rejected that pin with HTTP 404, verified_mesh_artifact_missing. A query parameter alone does not prove artifact identity. |
| Part and rotor bindings | All 38 assembly part names and initial identity transforms are present. All four rotor cylinder axes match the retained LabWired origins and axes. These checks do not prove complete geometry. |
| FC population topology | **Defect reproduced:** 28 source corners are replaced by the first output vertex. Maximum displacement is 28.023209685591127 mm. Complete current-source geometry acceptance remains open. |

## CAD reader correction and retained negative

cad/cad-readiness-report.json is the first reader output. It counted BRep faces only. Its 57,852-triangle total and null population bounds are incomplete.

cad/cad-readiness-report-v2.json supersedes those counts. Imported STL geometry is stored under each feature's separate mesh.positions / mesh.indices fields. The corrected inventory is 161,702 triangles: 57,852 BRep, 56,072 ESC population and 47,778 FC population. Both imported population fields are present.

The oriented triangle comparison then exposed the FC defect. cad/imported-population-geometry.json preserves that failure. The ESC's 56,072 triangles match the original asset under its authored translation and 1 µm serialization. The FC has 28 mismatches; they are not a rounding error. cad/crease-normal-corner-repro.json binds the deployed producer, the original STL and the observed artifact. A minimal two-triangle input demonstrates the same first-vertex substitution. The generic function's exact deployed code reproduced every stored FC position and index before the fix. Product runtime source copies are not included in this evidence bundle.

No old raw f810… mesh was found in the retained later archive. This bundle cannot establish byte-for-byte or triangle-for-triangle equality to that old producer. Current source, attached assets, initial bindings and the separate topology defect have their own explicit evidence. No CAD source, revision, transform, flight plant or acceptance threshold was changed during this check.

## Local correction result

cad/crease-normal-corrected-local.json records an independent full-input check of corrected function SHA-256 a35a61f22730d2f7259d17e8e8ccb1d4cdc8483f1b53f079850922dbba1678ff. Every expanded corner of both full source meshes matches exactly after the correction. ESC position, normal and index buffers are unchanged. FC position and normal buffers are unchanged; exactly the 28 previously wrong indices change. The minimal two-triangle regression also passes. This is local function evidence; the captured deployed artifact remains the failing one, and actual repaired-artifact qualification is pending.

## Portable offline verification

From any working directory, run:

~~~sh
node /path/to/20261122-deployment-preflight/audit_preflight.mjs
~~~

The neighboring 20261122-native-flight bundle must be present, or pass its absolute directory as the first argument. The audit checks every packaged file and deterministic gzip payload, preserves the reviewed script identities, recomputes CAD source/asset/binding checks, and reproduces the expected FC topology failure. A successful **record audit** does not mean the release or geometry passed.

artifacts.json binds the packaged bytes. payloads.json records original decompressed identities. All four successful mesh responses shared one body, so one deterministic gzip copy retains those exact response bytes. The original HTTP receipts remain separate. The captured adapter patch is also stored as deterministic gzip; its decompressed bytes retain the original literal patch context, including blank context lines.

## Reviewed release checks

release-checks/ contains the reviewed execution scripts and staged receipts without edits. The shipped replay adapter remains SHA-256 33a6eacc83065d950406cbc883e5dc4a56662956c20e2a1c753bff440f6ec6b2. Its integration, clock, stimulus and oracle loop remains the archived accepted loop.

These captured scripts retain the explicit work-1 checkout paths under which they were reviewed. The offline audit is portable; this bundle does not claim that the captured execution scripts have been relocated. No captured command is executed by the offline audit.

The staged qualification requires the exact live manifest, downloaded content-hashed JS/WASM, a normal planner-helper build at the deployed commit, the same five ELF/source identities and 14 runtime source identities. Its seven cases are nominal at 5,000 rounds per poll, nominal at 1,000 rounds, and button/inverter/overcurrent/undervoltage/stall faults. It keeps browser acceptance separate.

The compare-and-swap payload is a prepared candidate with the original expected project hash. Its presence does not skip fresh readback or deployment gates, and is not a receipt of mutation. The five-controller firmware, body model and native flight oracle remain in the accepted archive.
