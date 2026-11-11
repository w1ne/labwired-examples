# Hosted native PCB integration

The exact authored carrier was admitted in `preserve` mode, independently checked by hosted KiCad 9.0.2, and attached to the saved Game Boy example on 2026-11-11. The attachment readback completed at **14:49:20 UTC**.

| Identity or check | Recorded result |
| --- | --- |
| Native import job | `15645376-e293-4b4a-b94b-bfbd8b011e49` |
| Stored board | `pcb_c8da1d7776dba9bc`, revision `0` |
| Authored and downloaded PCB | 573,344 bytes; SHA-256 `e7224485efa449271fa0512791f898469b48650111884b55052957224e9cb9df` |
| Downloaded resolved rules | 12,524 bytes; SHA-256 `389ac1b2b1d20720e62044bddd96947134d28b1bdad5cd4ec13597fb4be20819` |
| Resolved rules digest | `85915592fc0647b75a752e74a1cb3bf552990c2d538ce6f1156da769b9fe1b2e` |
| Independent hosted DRC | `drc_passed`, KiCad 9.0.2, `passed: true`, zero warnings |
| Preserved board view | 78 × 132 mm, two copper layers, 16 footprints, 16/16 nets complete |
| Project update | Only `pcb_board_id` and `pcb_board_rev` changed |
| Project visibility | Unlisted before and after attachment |

## Evidence and boundaries

`request-summary.json` identifies the exact input and declared prototype rules. `admission.json` retains the actual running response and the terminal response from polling that same job. `source-and-rules-readback.json` records normal owner downloads and byte/hash checks. The downloaded KiCad project and custom-rule text also match the local preflight files exactly.

`independent-drc.json` records the separate `validate_imported` operation against those exact PCB and rules references. Its response includes the generated export file inventory and artifact hash; expiring signed download URLs and generated binaries are omitted. The API returned a completed result in this request, so no second DRC submission or job poll was needed.

Source preservation did not run a router. The stored import record therefore retains `routing_status: not_run` and `drc_status: not_run`. The separate DRC result does not update those BoardDoc fields. The 16/16-net result in `board-view.json` describes the supplied native copper. It is not evidence of new routing or independent rules validation by the view endpoint.

`attachment-readback.json` compares fresh owner project reads immediately before and after the normal project-board PUT. Exactly two PCB fields changed. Editable firmware source, the diagram, stimuli, pinned ELF, CAD revision 3, content hash and its matching verified hash remained equal for that operation. This comparison is scoped to the attachment at 14:49 UTC. A later save of generic electronics bindings is a separate project revision and requires its own saved-project verification record.

`transport-recovery.json` retains the failed first browser attempt and its narrow recovery: two owner/project/hash-scoped read-only lookups found no matching admitted job and wrote zero rows. The hung task tab was closed. One subsequent normal owner request returned the job above, and only that returned job was polled. Credentials, unrelated owner records and raw database contents are not included.

`deployments.json` identifies the API ownership/CORS fix and the source-preserving API/builder deployment that preceded this operation.

The native importer still reports two mapped, nine design-only and five ignored components; `twin_buildable` is false. The runnable MCU circuit remains the separately verified explicit binding. KiCad DRC does not establish schematic parity, real hardware behavior, supplier process capability, cable wiring, mechanical fit or fabrication sign-off. No PCB was fabricated or assembled.

## Reproduce through the existing owner API

1. Read the saved project with the normal signed-in owner session and retain its source/content identities.
2. Call the existing `route_imported` action in `preserve` mode with `../handheld-carrier.kicad_pcb` as `content` and the exact rules in `../native-preserve-preflight/requested-rules.json`. Send the start request once, then poll its returned job ID.
3. Require the terminal PCB and rules references above. Download both through the normal owner blob endpoint and check the bytes and SHA-256 hashes.
4. Call the existing `validate_imported` action with those exact `pcb_ref` and `rules_ref` values. Require a completed passing KiCad result.
5. Attach the actual board ID and revision with the normal project-board PUT. Read back both the project and its board reference. Compare firmware, source, diagram, stimuli, CAD reference and visibility against the fresh baseline.

An existing attached board needs no new import merely to view it. After any PCB change, retain the new source identity and repeat the applicable validation before attachment.
