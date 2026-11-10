# HeyPCB imported-board acceptance sample (7 PCB designs)

This is an **evidence record**, not a new importer or a claim that the public HeyPCB catalog is supported. The source is the [LabWired importer acceptance PR #2934](https://github.com/w1ne/labwired/pull/2934), which is **unmerged** as of 2026-11-10. All seven pinned KiCad PCB files imported in that engineering-branch test; none was fully simulated or firmware verified as its original board. The independently indexed 239 candidate designs from 30 repositories are **not** 239 successful imports.

[Machine-readable evidence](manifest.json) separates fetched, parsed, imported, mapped, analog simulated, firmware verified, and whole-board verified states. It records the original repository, immutable commit, exact PCB Git blob SHA, and LICENSE Git blob SHA. Individual board results contain mapped/dropped/ignored parts and unmodeled component references. **Imported net and pin completeness were not measured**, so no percentage is assigned. A separate, reproducible **source-side** KiCad topology inventory is now pinned for each board: 129 footprints, 575 physical pads, 510 pads with net names, 65 without net assignments, and 7 pad-to-net SHA-256 digests. Every source footprint is accounted for in the 92 mapped, 17 dropped and 20 ignored import classifications. These counts come from the original PCB files; they do **not** show that all 575 pads or their nets survived import. The SHA-256 covers a canonical sorted multiset of `(reference, physical pad number, net name)` tuples, including pads without a net. It can serve as an oracle for future imported-net comparisons.

The imported `power-kit/boost-1s` feedback divider was tested on a **separate Arduino UNO observer bench** with an ideal 5 V rail. The 15 kΩ / 2 kΩ divider produced the expected serial marker. Swapping resistor values caused a failing negative control. That provides narrow model evidence for the divider, not for the MT3608 converter, SS34 diode, power-up behavior, or a production board.

Run the offline evidence gate:

```sh
python3 scripts/heypcb_evidence.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

To **fetch the upstream sources and compare their actual Git blob SHA** (including pinned LICENSE files and matching their actual MIT/CERN-OHL-S-2.0 text to the recorded SPDX identifier), without storing third-party PCB assets:

```sh
python3 scripts/heypcb_evidence.py --verify-source
```

The gate rejects a fabricated whole-board PASS unless source, model and pin/net completeness, behavioral oracles, and a negative control are present. Raising net or pin completeness to `complete` now also requires a named `labwired_import` replay, LabWired commit SHA, and equal source/imported pad-net digests. `--verify-source` re-fetches the pinned KiCad files and independently recomputes these inventories; missing or changed pad/net assignments fail the check even if the source byte SHA was intentionally updated. It intentionally does **not** invent missing net/pin measurements, substitute MCU models, invoke the simulation runner, or transform PR results into production capability. Future real imports should publish their machine-readable input and output, with a versioned LabWired build and explicit test stimuli, before upgrading stages.

For the public technical summary, see [KiCad PCB import and simulation coverage](https://labwired.com/kicad-pcb-simulation/). HeyPCB is an independent open-hardware publisher and does not endorse LabWired.

The pinned sample also records **18 unmodeled part references** across the seven boards: **17 dropped at import** and **one mapped without a behavioral model** (the `MT3608` in `boost-1s`). Obtain the deterministic component-level gap report with:

```sh
python3 scripts/heypcb_evidence.py --model-gaps
```

This is an engineering backlog for the **recorded 2026-11-10 sample**, not a claim about current model availability or the wider HeyPCB catalog. The validation gate requires every unmodeled reference to have a part identity and import resolution. It checks that the dropped gap count matches the import result; a mapped symbol without behavior cannot silently be counted as a simulated IC. A source pin, partial import or passing subcircuit does not establish whole-board verification.

The evidence gate treats analog and firmware results as **independent proof axes**.
An analog subcircuit can pass while active components remain unmapped, if its test
scope, input/output observations, and negative control are recorded. A digital
firmware test does not require an unrelated analog run. Neither is a full-board
pass. A whole-board PASS requires an explicit declaration of which proof axes
apply, complete net/pin/model coverage, and its own positive and negative controls.
