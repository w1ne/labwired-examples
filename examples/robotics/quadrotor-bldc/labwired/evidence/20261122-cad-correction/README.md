# Deployed quadrotor CAD correction — 22 November 2026

The actual repaired DyJ405zg revision 6 artifact passes the source-bound geometry comparison. This follow-up records the deployed CAD result. The prior 20261122-deployment-preflight archive remains unchanged, including its failed artifact and historical false acceptance flags.

## Verified result

| Check | Result |
| --- | --- |
| Deployed producer | Server fd52f2c20b801c8a7ab875ebeb6b844a928baf97; runtime f00d5beda7bb1f5befa8f001329013b0c2b1e6b9ae85019837415deee2d89977. |
| Editable source | DyJ405zg@6, 9,688 UTF-8 bytes, source SHA-256 f87316c6a9de81148c8985e9387641a0ead22d5d2744186d2041678c0364a10e. Saved time, source, parameters and all 12 attached assets match the preserved readback. |
| Actual API/CDN bytes | Both returned 12,865,359 identical bytes, SHA-256 166131d834781b76829ffa8d591da349e8c05b7a1206f2338c62cb73de748082. Both URL pins equal the canonical hash of the body's actual provenance: 7f92c6bc2c640367d6e5767f3a3c45179f6f7be336a9b4c65c78975a1455b563. |
| ESC population | All 56,072 source triangles preserve their expanded corners. No index, position or normal change. |
| FC population | All 47,778 source triangles preserve their expanded corners. Exactly the 28 previously incorrect indices change. Positions and normals remain unchanged. |
| Complete artifact | 39 feature records: 38 named assembly parts plus one virtual feature. All remaining geometry and transform fields match the expected correction exactly. The artifact retains 161,702 triangles. |
| Serialization bound | Maximum source-to-serialized coordinate difference is 0.0004999847412108238 mm, within the existing 1 micrometer coordinate rounding. This bound is separate from the eliminated 28-corner topology defect. |

The old artifact replaced 28 FC corners with the first output vertex. The generic crease-normal reindexer now preserves each actual triangle corner. The deployed geometry digest after applying precisely those 28 expected index corrections is 853fde6738b69cdab1fcc221ce48b86488304cf401d3f7903bf6d1265e11680e.

An independent direct-source audit confirms all 28 corrected FC corner coordinates and all 39 feature records: 38 named assembly parts plus one virtual feature. Its maximum coordinate error of 0.0003012084960936079 mm is measured over those corrected corners; the table above reports the larger bound over every imported corner. The independent receipt is qualification/independent-production-review.json.

The retained-old-artifact control still fails with exactly 28 wrong FC corners. It passes its source, asset and producer checks before that geometry rejection. The old failure remains in qualification/negative-old.json and in the unchanged preflight bundle.

## Retrieval and scope

The ordinary read-only get_project and get_project_revision calls returned the same saved revision and source. Initial metadata reported building; subsequent metadata reported ready after the service's existing automatic artifact repair. The capture then fetched the returned stored-only API and public CDN URLs with default Node fetch, without credentials or custom headers. No source or asset update was submitted and no manual meshing command was called.

The comparison baseline is the captured predecessor artifact e041191cfd930893229d3d569dece43dc5ed8441dff865270f65e09b1f78e141. Earlier unavailable producer bytes remain outside this comparison, as recorded in the preflight archive.

This result accepts the recorded CAD artifact. The LabWired deployed optimized-engine flight qualification, saved-project compare-and-swap, and actual Studio browser flight gates remain pending. The accepted native flight sources, model, clocks, thresholds and prior scenario traces are unchanged.

## Visual record

The inspected visual record remains pending. The scoped observer attached to an owned browser context, but the existing DemoPlayer did not become ready within its time limit and no frames were captured. This revision publishes the independently verified deployed mesh and its geometry receipts. Any later successful capture will be an additive follow-up using the exact qualified stored bytes. It will remain distinct from a hosted Studio viewer or flight observation. The exact failed receipt is visual/capture-failed.json. Its resource summary records exit 1 after 15.98 seconds, 225,216 KiB peak resident memory, zero transfers and zero frames; owned-context cleanup completed. Private renderer implementations are excluded.

## Evidence files

The compressed artifact retains the exact decoded body identity in payloads.json. Both HTTP receipts remain separate. The source links identify the reviewed repair and the actual producer. qualification/qualify-repaired-cad.mjs is the reviewed read-only verifier, preserved byte-for-byte at SHA-256 a26b40eff0c40dc0d0e64563be9c93e780e1f5c0248c4c4993d9c6cd8885d677. It performs no network request, meshing, firmware execution, or project mutation.

Run `node audit.mjs` from this directory, or invoke the file by its absolute path from any directory. The audit verifies every file in artifacts.json, expands the exact recorded mesh, then reruns the unchanged verifier against the preserved source and prior failure. The normal examples CI invokes this audit through scripts/test_quadrotor_deployed_cad.py. A passing result verifies the CAD record and explicitly retains false values for inspected video, deployed flight engine, saved-project update and browser flight.
