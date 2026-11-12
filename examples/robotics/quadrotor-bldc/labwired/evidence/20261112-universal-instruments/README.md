# Universal instruments: accepted development preview

The 12 November 2026 R4-02 browser recording passed all 17 native acceptance checks and a separate comparison of native four-state observations with the visible logic-analyzer labels. The [34-second video](../../../media/quadrotor-universal-instruments-preview-20261112.mp4) contains actual LabWired footage at its recorded speed.

This is a four-controller STM32L476 bench with behavioral motor models. It is a development preview. Physical-board simulation, flight, AM32/DShot, and a merged production release are not established by this recording.

## Verified behavior

- Four exact compiled images remain running during instrument insertion, reopening, and both source changes: four initializations and zero browser compiles.
- The universal scope displays native current in amperes, speed in rpm, PWM, and Hall observations. The logic analyzer selects independent controller signals.
- Separate phase A/B/C windows contain 617, 321, and 464 interior PWM periods. Each measured period is 200 cycles at 4 MHz, or 50 microseconds. There are zero interior timing violations and zero high/low gate overlap spans.
- M1 stays disabled in all 72 retained post-disable observations and coasts to effectively zero speed. Each peer remains in inverter mode in all 74 retained observations.
- At the paused 29,200,000-cycle horizon, the analyzer shows PA8 1/HIGH, PB13 Z/Z, PB7 0/LOW, and PB0 1/HIGH. PB13 starts unknown and later has a real native Z event. No initial state is invented.

See [acceptance-summary.json](acceptance-summary.json), [paused-ui-readout-audit.json](paused-ui-readout-audit.json), and [video-visual-qa.json](video-visual-qa.json).

## Exact identity and reproduction

The app source is 3cc33f2c1da8d01e0d8a52053d909c114f72e280. The recorded engine was built from core b7089ceefa4c35193657b0ea9cd8f6e84f77535a plus the 24-file R4 patch. Its SHA-256 is 3a60b6e63146c53e2b63dbb10d6f62fcec31d83a97b0368b5adf589e1190e241. The normal WebAssembly build, runtime interface check, and UI-library build passed. The development engine remains explicitly unstamped.

The [compressed evidence](acceptance-evidence.tar.gz) contains all 28 native-auditor inputs, both reports, all three frozen auditors, the capture driver, source/build receipts, exact ELFs, and four unedited screenshots. All 60 archive members were verified against [input-manifest.json](input-manifest.json). The [package receipt](package-receipt.json) records its SHA-256.

Extract to a new directory, then run:

    tar -xzf acceptance-evidence.tar.gz
    python3 tools/audit-native-acceptance-live.py capture --expected-wasm-sha256 3a60b6e63146c53e2b63dbb10d6f62fcec31d83a97b0368b5adf589e1190e241 --output capture/independent-native-audit.json
    python3 tools/audit-paused-logic-readouts.py capture --expected-wasm-sha256 3a60b6e63146c53e2b63dbb10d6f62fcec31d83a97b0368b5adf589e1190e241 --output capture/paused-ui-readout-audit.json

The [original recording](../../../media/source/quadrotor-universal-instruments-r4-02.webm), [edit list](../../../media/quadrotor-universal-instruments-preview-20261112-edit.json), and [encoding provenance](../../../media/quadrotor-universal-instruments-preview-20261112.provenance.json) preserve the actual source and cuts. The editor is saved beside the video. For local reproduction, copy the edit list and change only its source file paths to the downloaded original recording.

## Corrections and remaining release gates

The [recorded native validation](native-validation.tar.gz) contains 219 passing tests on b708 plus R4, with formatting, Clippy, and the full host Cargo check passing. That archive describes the engine used for the recording.

The recorded UI fixes the LOW/0 label that incorrectly described an actual Z trace when its initial state was unknown. The correction has 47 passing focused tests, including seven new regressions and the unchanged function-size gate. The normal app type check passes; test-type and lint baselines have zero new findings. See [readout-validation.tar.gz](readout-validation.tar.gz).

The historical release snapshot records a source-gate block for seven captured-board profiles without human source acknowledgments. [The historical review packet](core-source-review-packet.json) identifies each exact digest. [The recorded candidate patch](core-candidate.patch) and [the earlier preparation on core main](core-current-main-review.json) preserve that state: the prepared candidate was based on 102f7fc9, with the same 24 changed-file hashes and seven model digests. No source acknowledgment was written in that snapshot.

On 12 November 2026, the project owner authorized removal of the mandatory human source acknowledgment requirement. The decision is implemented in core commit [`a0b0a91c`](https://github.com/w1ne/labwired-core/commit/a0b0a91c1868fe78e4af45e817e566807517ef1e), based on 7778d2500aa05012eb4f0dbc030d0a8f8bb57e24 and pushed in [PR #1852](https://github.com/w1ne/labwired-core/pull/1852). The committed policy uses automated source and provenance integrity checks.

Current-base validation passed 219 native tests, 56 policy tests, and 102 tests through the normal pre-push gate. Formatting, Clippy, the full host Cargo check, the source check, and the drift check also passed. Final-head CI and merge are pending. This authorization records a workflow decision; hardware capture provenance and model validation status remain as recorded. The historical JSON receipts, patch, recording, and encoding provenance are unchanged.

App/core/example merges, deployment, hosted saved-project verification, and public-project publication remain separate. The optional CAD/PCB recording stopped at a loading veil and contributes no footage or claim to this video.
