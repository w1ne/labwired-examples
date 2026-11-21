# AXIOM H1 robot controller

The original saved AXIOM project now contains **20 explicitly wired servo models** and an ideal external 5 V rail. The unchanged ESP32-C3 firmware drove all 20 channels in a local run of the real simulator. Three channels changed angle during its wave sequence. Proximity and tilt faults disabled both PCA banks and recovered. Emergency stop remained latched after release.

- [Open the original LabWired project](https://app.labwired.com/p/e6b30d45ba55e64aa450a2aa292edd4b/edit).
- Current source: [current-project.input.json](current-project.input.json), 31 parts and 88 wires.
- Current saved hash: `0487080a9c2eaf9e45fd2fbad8ad42603fdffc09a0aac2ff9bca0146c6d785ee`.
- [Promotion receipt](original-project-promotion.json): the guarded update preserved firmware, metadata, media and `pcb_172fd76a950f0bd9` revision 2.
- **Hosted acceptance is pending.** The three earlier controller requirements became stale after the diagram update. The local result below does not establish deployed servo support.

The linked PCB is the existing controller board. It does not include the added servo loads or external servo rail.

## Firmware-driven actuator evidence — 21 November 2026

[Runtime receipt](actuator-runtime-evidence.json) records 185,000,000 instructions through the real `WasmSimulator`, using app-generated YAML and the exact saved Arduino source. Inputs used the existing `set_inputs` API. The test did not write PCA registers or output-enable GPIO registers directly.

| Check | Observed result |
| --- | --- |
| Startup | All 20 command states started inactive, with zero pulse width. |
| Valid firmware output | All 20 became active with `source_status: modeled_pwm` and nonzero pulse widths. |
| Neck yaw, `servo0` | Modeled angle changed from 95.9495° to 108.4320°. |
| Left shoulder pitch, `servo2` | Modeled angle changed from 95.9495° to 74.2206°. |
| Left elbow, `servo4` | Modeled angle changed from 10.4211° to 86.7032°. |
| Proximity input: 100 mm | All 20 sources became disabled. Commands remained unchanged during an additional 5,000,000 instructions. Restoring 1500 mm re-enabled output. |
| Tilt input: ax = 1 g, az = 1 g | All sources became disabled. Restoring ax = 0 g, az = 1 g re-enabled output. |
| Emergency stop | All sources became disabled. Releasing the button kept the firmware latch and commands unchanged. |
| Remove the `servo19` PWM wire | The compiler omitted that servo model and reported a floating input and no MCU signal path. |

These angles are the SG90 model's pulse interpretation. They are not calibrated AXIOM joint angles. `active` and angle retain the last modeled command when output-enable goes high; `source_status` reports the modeled source configuration. Servo current, voltage sag, torque and physical hardware are outside this evidence.

### Reproduce the local run

[Input provenance](actuator-runtime-inputs.json) pins the unchanged source hash, four hosted compile blobs and their flash offsets. It also identifies the successful exact-core WASM workflow [44580096395](https://github.com/w1ne/labwired-core/actions/runs/44580096395), artifact `exact-core-5af794-wasm-glue`, core `5af794255a13949c3d3e1e0f0f3f6723579e1253`.

1. Build `packages/board-config` in the recorded LabWired app revision from the runtime receipt.
2. Download the named WASM artifact and verify its `SHA256SUMS` against the corresponding basenames. Its manifest records absolute CI paths.
3. Download the four content-addressed blobs listed in `actuator-runtime-inputs.json`. Verify each SHA-256. Place each at its recorded offset in a 4 MiB flash image filled with `0xff`. Verify `combined_flash_sha256`.
4. Run the bounded source acceptance script:

```sh
node scripts/check-axiom-actuator-runtime.mjs \
  --app /path/to/labwired \
  --wasm /path/to/exact-core-5af794-wasm-glue \
  --flash /path/to/combined-flash.bin \
  --output /path/to/axiom-runtime-receipt.json
```

The script checks all 20 channel identities, changing commands, fault recovery, the E-stop latch and disconnected-signal rejection. It writes a failure receipt if an assertion fails. It keeps the simulator's default peripheral tick interval of one and records flash fast-start use.

## Mechanical integration

[Immutable KernelCAD source](mechanical/QC9kIRT9-v1.kcad.ts) preserves [QC9kIRT9 version 1](https://app.kernelcad.com/p/QC9kIRT9?version=1). The [source audit](mechanical-audit.json) identifies 27 bodies and 20 named revolute channels, but the helper functions only declare connectors: they make **zero `robot.mate` calls**. The saved LabWired diagram has no mechanical bindings.

The CAD shoulder-roll range is ±75° on both sides. The firmware maps the left shoulder to −70°/+80° and the right shoulder to −80°/+70°. A real joint graph, clearance validation and an explicit pulse-to-joint mapping are required before firmware-driven CAD motion can be claimed. The local actuator run does not prove hierarchical CAD transforms or firmware-to-MuJoCo coupling.

## Earlier source and hosted receipts

[project.input.json](project.input.json) and [evidence.json](evidence.json) preserve the original 10-part/27-wire controller revision. Its three serial requirements were verified on hash `3fbbe85932524caaf21b5f63d2c2333e177c32320d4e162370c288964cd7cfb3`.

[20-servo-candidate.json](20-servo-candidate.json) preserves the unpowered topology baseline. [20-servo-powered-input.json](20-servo-powered-input.json) adds the ideal 5 V rail and is the exact runtime input. The [separate candidate project](https://app.labwired.com/p/dab8622b41adbf3b9e2175909146b207/edit) retains its [controller-only hosted receipt](live-20-servo-evidence.json), hash `386b3ec5442960f58e4ed8c383810ca704af76de657256ce831ff8fbc6112548`. That earlier deployment reported 20 `SERVO_EXPANDER_UNMODELED` warnings and zero unconnected-supply warnings.

To make a new saved copy, use `labwired_project_create` with `current-project.input.json`. It does not inherit PCB, CAD, media or verification records. Run `labwired_project_verify` against the exact saved revision after the required runtime is deployed.

## Earlier live Studio screenshot

![AXIOM H1 controller, PCB view](media/labwired-live-pcb-20261121.png)

[Source-pinned screenshot and scope](../../flagship-live-snapshots-20261121.json). This shows the original controller PCB with 9/9 nets connected. It does not show the newly added servo loads or mechanical motion.
