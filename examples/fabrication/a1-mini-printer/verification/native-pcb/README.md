# Native A1 PrintCore PCB source and evidence

The native board passes KiCad 10.0.8 DRC with **0 violations and 0 unconnected items**. The source audit passes. The project rules are unchanged from the accepted starting board.

## Accepted source

- PCB SHA256: `55b7162b73d0d9675725c5ea9211b6c633feeb2bd298e9a1e6209b5e5c25a6ad`.
- Project-rule SHA256: `aadb3db043caa9fc08d5f006143fa1742f7c7971c417f6408140782370a78c71`.
- 157 footprints, 604 physical pads, 1,763 track segments and 251 vias.
- All 156 original footprint identities and all 602 original pad UUIDs remain. C10 adds one footprint and two pads.
- Original board outline, copper-zone outlines and zone nets remain unchanged.
- The five original ignored DRC checks remain unchanged. The report includes all configured error and warning severities.

## Electrical corrections

The audit records 26 explicit changes to original pad nets. U10–U13 MS1/MS2/MS3 now use GND for full-step operation; RESET, SLEEP and VDD retain +3V3. R126/R127 now separate the buffer outputs from the MOSFET gates, so both 100 ohm resistors are in series. Their two gate-side pulldowns remain on the corresponding MOSFET gate nets. D10/D11 use the KiCad LED pad convention, pad1 cathode and pad2 anode; their 180 degree rotation preserves the original absolute copper endpoints.

U1.9, C8.1, J33.1 and J34.1 now use the powered +3V3 rail. The former +3V3A copper is assigned to +3V3 and has a routed feed. New C10 is a 100 nF 0603 ceramic decoupling capacitor at (42.9, 56.0) mm, paired with the existing C8=1 uF. Its supply pad is approximately 3.0 mm from U1.9. This implements the STM32F411CE power-supply scheme: https://www.st.com/resource/en/datasheet/stm32f411ce.pdf .

The MCU step, direction, driver-enable, endstop, thermistor, heater, fan and I2C pad assignments are checked explicitly in `native-source-audit.json`. `native-pad-net-map.json` contains the complete physical pad inventory.

## Physical corrections

J20 uses the GCT USB4216-03-A rev A2 land pattern and its source-backed clearance model. Four shell pads and two locating holes receive the six drawing-derived offsets; signal pads remain fixed. The project includes the corrected local footprint and its library table. The A4988 and LMR36520 models use the drawing-qualified versions recorded in the two qualification reports. The U12 ground via moves into its exposed ground pad, as permitted by the Allegro A4988 datasheet; its 0.60/0.30 mm diameter/drill and both tenting settings remain unchanged.

The final source exports to `hardware/exports/a1-printcore-populated.step` and `a1-printcore-populated-pads.step`. Both exports use native KiCad coordinates: [PCB X, -PCB Y, native Z]. The export logs contain no model warnings. All 145 physical component footprints have model references. The remaining 12 footprints are eight copper testpoints and four mounting holes.

## Verification and reproduction

`native-drc.json` is the independent board-rule and connectivity result. It was run without `--schematic-parity`; schematic ERC and PCB-to-schematic parity are separate evidence produced with the editable schematic. The 55b source hash above records the exact physical source for these STEP exports. A later schematic-link metadata update can preserve this physical geometry while giving the editable pair a new file hash.

Run the audit from the repository root with the system Python that provides `pcbnew`:

```sh
/usr/bin/python3 examples/fabrication/a1-mini-printer/verification/native-pcb/tools/audit_native.py \
  examples/fabrication/a1-mini-printer/verification/native-pcb/accepted-baseline/accepted-baseline.kicad_pcb \
  examples/fabrication/a1-mini-printer/hardware/a1-printcore.kicad_pcb \
  --evidence examples/fabrication/a1-mini-printer/verification/native-pcb --require-clean
```

The patch pipeline uses the fixed routing exchange input, exact original rules, standard C10 footprint snapshot and supplied STEP models. It creates a new output directory and then runs DRC and the source audit. New KiCad item UUIDs can differ between runs; the geometry, electrical contract and acceptance checks must agree.

```sh
/usr/bin/python3 examples/fabrication/a1-mini-printer/verification/native-pcb/tools/reproduce_native.py \
  --routing-base examples/fabrication/a1-mini-printer/hardware/source-inputs/native-pcb/routing-base.kicad_pcb \
  --baseline examples/fabrication/a1-mini-printer/verification/native-pcb/accepted-baseline/accepted-baseline.kicad_pcb \
  --models-dir examples/fabrication/a1-mini-printer/hardware/models \
  --output-dir /tmp/a1-native-reproduction
```

KiCad 10.0.8 and its standard footprint/3D libraries are the recorded verification environment. Only the original routing exchange uses Freerouting 2.5.0; the supplied fixed native input makes the remaining patch and verification sequence reproducible without rerunning the autorouter.
