# Four-controller motor / CAD runtime evidence

The local candidate passed the real browser spin-up, selected driver-input fault, pause and reset checks. This package contains actual compiler responses, passive Worker observations, received CAD frames, UI observations and an independent audit.

## Scope

The saved project uses four STM32L476 C controllers and four reduced-order 24 V motor plants. KernelCAD revision 3 consumes the measured motor positions through a generic one-way bridge. The selected physical 4S OpenESC/AM32 and RP2354B/Betaflight hardware is not validated by this motor bench. There is no thrust model, airframe dynamics, attitude controller, MOSFET transient, thermal or flight proof.

The frontend candidates run from the clean commits in `provenance.json`. The recorder serves the KernelCAD candidate from localhost while retaining the production iframe origin. Only the saved-project GET is supplemented with the authored motion metadata. All four compiler POSTs reach the real hosted compiler. The recorder captures Worker messages passively; it never supplies motor telemetry.

## Evidence

- `evidence.json`: compact result, source/ELF hashes and limits.
- `independent-audit.json`: independent field-by-field audit. All 360 CAD motion observations match raw engine angle, RPM, control state and faults with the authored direction sign. No observations are excluded in this final trace.
- `capture-files.json`: byte counts and SHA256 of each uncompressed trace.
- `*.json.gz`: raw cumulative snapshots, compiler results, events and exact project fixture.
- `ui-paused.json` and `ui-pause-held.json`: byte-identical four-pose/RPM observations across a wait of at least five seconds, with every sample marked Last observed.
- `ui-stopped.json`: reset cleared every observation. The receiver briefly reports stopped while controllers reinitialize, then settles paused with zero observations.
- `capture.mjs`: the exact Playwright recorder used for this run. Its workstation paths and local ports are retained for provenance. It requires the two candidate checkouts, actual WASM assets, saved source fixture and authored motion bindings named in the script.
- `video.json`: original WebM path and SHA256. Event elapsed time starts just after page creation, before navigation. Align visible events when editing; the exact video-clock offset was not measured.

## Re-run the independent audit

Run this from a copy of this directory. Python and the compressed evidence are sufficient; no simulator is needed to audit the captured trace.

```bash
python3 -c "from pathlib import Path; import gzip; [p.with_suffix('').write_bytes(gzip.decompress(p.read_bytes())) for p in Path('.').glob('*.json.gz')]"
python3 audit_final_trace.py . --output replayed-audit.json
```

The first successful fault recording is preserved separately in `../fault-run`. One later attempt stopped during an optional Chromium still-image capture before injecting fault; its original files remain at `/tmp/quad-runtime-final-screenshot-failed`. The final recorder uses continuous video and JSON checkpoints. It completes every behavior assertion.

Hosted verification remains separate. PR #3094 was open with API tests in progress at handoff. This package does not set the saved project's verified hash and does not establish a deployed production result.
