# HeyPCB imported-board acceptance sample (7 PCB designs)

This is an **evidence record**, not a new importer or a claim that the public HeyPCB catalog is supported. The source is the [LabWired importer acceptance PR #2934](https://github.com/w1ne/labwired/pull/2934), which is **unmerged** as of 2026-11-10. All seven pinned KiCad PCB files imported in that engineering-branch test; none was fully simulated or firmware verified as its original board. The independently indexed 239 candidate designs from 30 repositories are **not** 239 successful imports.

[Machine-readable evidence](manifest.json) separates fetched, parsed, imported, mapped, analog simulated, firmware verified, and whole-board verified states. It records the original repository, immutable commit, exact PCB Git blob SHA, and LICENSE Git blob SHA. Individual board results contain mapped/dropped/ignored parts and unmodeled component references. **Net and pin completeness were not measured**, so no percentage is assigned.

The imported `power-kit/boost-1s` feedback divider was tested on a **separate Arduino UNO observer bench** with an ideal 5 V rail. The 15 kΩ / 2 kΩ divider produced the expected serial marker. Swapping resistor values caused a failing negative control. That provides narrow model evidence for the divider, not for the MT3608 converter, SS34 diode, power-up behavior, or a production board.

Run the offline evidence gate:

```sh
python3 scripts/heypcb_evidence.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

To **fetch the upstream sources and compare their actual Git blob SHA** (including pinned LICENSE files), without storing third-party PCB assets:

```sh
python3 scripts/heypcb_evidence.py --verify-source
```

The gate rejects a fabricated whole-board PASS unless source, model and pin/net completeness, behavioral oracles, and a negative control are present. It intentionally does **not** invent missing net/pin measurements, substitute MCU models, invoke the simulation runner, or transform PR results into production capability. Future real imports should publish their machine-readable input and output, with a versioned LabWired build and explicit test stimuli, before upgrading stages.

For the public technical summary, see [KiCad PCB import and simulation coverage](https://labwired.com/kicad-pcb-simulation/). HeyPCB is an independent open-hardware publisher and does not endorse LabWired.
