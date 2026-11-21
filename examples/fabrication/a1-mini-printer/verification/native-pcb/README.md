# A1 PrintCore — complete native KiCad project

The native PCB passes KiCad 10.0.8 with **0 DRC violations, 0 unconnected items and 0 schematic-parity findings**. Native schematic ERC has **0 errors** and **9 retained `isolated_pin_label` warnings** for intentional NC or reserved signals. The project rules are byte-identical to the accepted starting project. No check was suppressed to obtain these results. The raw DRC report retains the same five ignored checks present in the accepted starting file.

From `examples/fabrication/a1-mini-printer/`, open `hardware/a1-printcore.kicad_pro` with KiCad 10. The editable schematic and PCB use the same component UUID paths. All project footprint and symbol libraries are included. Six project STEP files serve 12 component references; the other 133 modeled component references use the standard `KICAD10_3DMODEL_DIR`. No active native source, footprint, symbol or model reference depends on a `/data` or `/home` path.

## Accepted source and geometry

| Artifact | SHA256 |
|---|---|
| Final PCB | `b5c0150f327aae1f248b9a61d6feccc1185ad7934152249f1155c6fc3bb36c99` |
| Final schematic | `04543f9e7ed5b629feae1b4300723c32c0f89aa326c1aea4d836a97bd52fd97f` |
| Original project rules | `aadb3db043caa9fc08d5f006143fa1742f7c7971c417f6408140782370a78c71` |
| Accepted physical PCB before editable-project metadata | `55b7162b73d0d9675725c5ea9211b6c633feeb2bd298e9a1e6209b5e5c25a6ad` |
| Populated STEP | `4fa338f753a8c8a17331facabd8ee8d3698bc0a0cd3fa152b71749e88baa2e2a` |
| Populated STEP including copper pads | `fba783fc8c4a4c968b5c63f6dfcc8607fa2c381eaa90d0806394d5c0281cc8e7` |

The board contains 157 footprints, 604 physical pads, 1,763 track segments and 251 vias. All 156 original footprint UUIDs and 602 original pad UUIDs remain; C10 adds one footprint and two pads. Board outline, copper-zone outlines and zone nets remain unchanged from the accepted starting board.

The two STEP files retain native KiCad coordinates: [PCB X, −PCB Y, native Z], with the PCB bottom at Z=0. The final source retains their physical geometry. `native-metadata-only-provenance.json` proves that reversing only the listed metadata changes restores every byte of the accepted `55b…` physical PCB. The original physical source is included under `verification/native-pcb/physical-source/`.

## Electrical corrections

The source audit records 26 intentional changes to original pad nets:

- U10–U13 MS1/MS2/MS3 use GND for full-step operation. VDD, RESET and SLEEP remain on +3V3.
- R126/R127 separate the buffer outputs from the MOSFET gates. Both 100 ohm resistors are in series; their pulldowns remain on the respective MOSFET gate nets.
- D10/D11 use the KiCad LED convention: pad 1 cathode and pad 2 anode. Rotating each footprint 180 degrees preserves its absolute copper endpoints.
- U1.9, C8.1, J33.1 and J34.1 use the powered +3V3 rail. The former +3V3A copper has a routed supply feed. C10 adds 100 nF decoupling beside U1.9, paired with C8=1 uF, following the [STM32F411CE power-supply scheme](https://www.st.com/resource/en/datasheet/stm32f411ce.pdf).

The MCU step, direction, driver-enable, endstop, thermistor, heater, fan and I2C pad assignments are asserted in `native-source-audit.json`. The native oscillator remains Y1=8 MHz with C1=C2=12 pF; no hardware value was changed to fit a compiler profile.

## Editable-project metadata

These later changes do not alter conductive connectivity or physical geometry:

- 153 electrical footprints receive schematic UUID paths.
- Six inherited absolute model filename strings become project-relative paths. The three copied model files retain their exact bytes. All other model transforms and model bytes remain unchanged.
- H1–H4, the four unnumbered M3 NPTH mounting holes, receive an explicit board-only attribute.
- Twelve isolated A4988 pads receive distinct schematic NC net names. Each new NC net contains exactly one physical pad and has no other connected pad, track, via or zone. These are pads 7, 20 and 25 on U10–U13, identified as NC in the [Allegro A4988 terminal table, page 18](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf). These names are recorded separately from the 26 intentional electrical corrections.
- 156 inherited footprint IDs receive local library namespaces while preserving their item names. `A1_Native.pretty` contains 31 exact KiCad-exported snapshots. C10 uses its exact variant in `A1_Native_C10.pretty`. J20 retains `LabWired_GCT:USB4216-03-A`.
- The schematic includes explicit external power intent for GND, +24V and USB_VBUS, exact embedded-symbol library snapshots, and matching Description/BOM/footprint metadata.

The six MP mounting-pad groups on J10–J13/J22–J23 remain no-net. They are mechanical retention features, shown by schematic annotations and recorded by all 12 physical pad UUIDs, positions and dimensions in `native-mechanical-pad-inventory.json`. They were not assigned shared electrical nets.

All physical pads are reconciled:

| Physical pad category | Count |
|---|---:|
| Electrical pad instances | 548 |
| Numbered mechanical retention pads | 12 |
| Unnumbered paste apertures | 36 |
| Unnumbered mounting holes | 8 |
| **Total** | **604** |

There are 153 electrical references and 526 unique electrical pad numbers. Their values, qualified footprint IDs, nets, vendor fields, Description and BOM flags match KiCad's own schematic netlist. The twelve explicitly isolated IC NC names are included in this electrical pad count.

## Physical models and connector source

J20 uses the GCT USB4216-03-A rev A2 land pattern and source-backed clearance model. Four shell pads and two locating holes receive the six drawing-derived offsets; signal pad geometry and mapping remain unchanged. U10–U13 and U20 use the drawing-qualified A4988 and LMR36520 STEP models. The source qualification reports are included.

The U12 GND via is centered in the exposed ground pad. The [Allegro A4988 datasheet, page 19 note C and page 12 layout](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf) permits thermal vias in this land. Its 0.60/0.30 mm diameter/drill and both tenting settings remain unchanged.

## Verification evidence

`verification/native-pcb/` contains the complete raw DRC and ERC reports, exact validation commands, physical pad map, source audit, metadata inverse proof, library/model portability inventory, schematic read-back parity, source drawings' identity evidence and source-reproduction tools. `manifest.json` lists each archive payload and SHA256. The adjacent external archive manifest records the ZIP's SHA256 and byte count.

The nine retained ERC warnings are all `isolated_pin_label`: `NC_PC15`, `SPI_SCK`, `SPI_MISO`, `SPI_MOSI`, `NC_SBU1`, `NC_SBU2`, `NC_LDO`, `NC_SWD7` and `NC_SWD8`. They remain visible in the raw ERC result. There are no missing-symbol-library or missing-footprint-library warnings.

From this extracted project directory, rerun the native checks with:

```sh
kicad-cli pcb drc --schematic-parity --format json \
  --output /tmp/a1-native-drc.json hardware/a1-printcore.kicad_pcb
kicad-cli sch erc --format json \
  --output /tmp/a1-native-erc.json hardware/a1-printcore.kicad_sch
/usr/bin/python3 verification/native-pcb/tools/audit_native.py \
  verification/native-pcb/accepted-baseline/accepted-baseline.kicad_pcb \
  hardware/a1-printcore.kicad_pcb \
  --evidence verification/native-pcb --require-clean --require-portable --schematic-parity
```

The system Python must provide KiCad's `pcbnew` module. The physical-routing reproduction pipeline starts from the included fixed routing exchange input and exact original rules. Freshly created KiCad object UUIDs can differ in a new reproduction; the acceptance evidence checks geometry, connectivity and source contracts. The immutable final editable source and its byte-level inverse proof are included directly.

The existing hosted native-import gate has a narrower dependency scope: it imports one PCB, generates project/custom rules from structured routing rules, and does not fetch sibling native dependencies. Its summary also filters library-environment findings. `hosted-native-import-limitations.json` records the reviewed source implementation. Full native-project acceptance is based on the complete project and raw local KiCad results in this archive.
