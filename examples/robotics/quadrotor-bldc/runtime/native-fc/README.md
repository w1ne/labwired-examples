# Native RP2354B runtime boundary

`system.yaml` declares the physical controller's RP2354B, 150 MHz model
clock, BMI270 on SPI0 with CS14/INT13, and the native active-high status LED
on GPIO12. It preserves the physical pins and image. It does not use the
separate STM32 motor bench as a substitute controller.

The final physical image is the ELF with SHA256
`8c0a2953dbb7a65e1e22d949c5fd08f68a1babdeda88d13b14b2632bbc7ce43a`.
The current recorded run loads that exact image and passes the earlier
SDK IRQ-vector assertion after the generic boot-vector repair. At step
470000 it encounters the first confirmed missing runtime register:
DEMCR at 0xE000EDFC, accessed by `systemInit` / `cycleCounterInit`. The engine
raises a precise BusFault and escalates to HardFault. No SPI events occur
before that stop. This is a failed execution receipt, not a boot pass.

The generic RP2354B repair adds the exact package, 48 GPIO pads and nine ADC
mux inputs. Its 184 existing/extended RP tests and seven package tests pass
with event scheduling enabled and disabled. A generated descriptor entry
is required for the standalone built-in `rp2354b` name. A separate Cortex-M
repair makes firmware trace control available without attaching a debugger;
the final image must be replayed against those merged repairs before any
complete runtime acceptance is claimed.

Run the bounded probe with a LabWired CLI that includes the RP2354B model:

```sh
labwired test --script runtime/native-fc/probe.yaml \
  --output-dir /tmp/openfc-native-runtime --run-manifest
```

The probe checks only that bounded execution reaches its instruction limit
without a CPU fault. It cannot establish boot completion, gyro accuracy,
receiver control, DShot timing or motor response. Those require separate
observable oracles once the first executed model gaps are resolved. The
model does not inject a fake voltage/current or fake sensor response to
hide startup behavior. Unconnected analog inputs retain their model defaults.

`validation/pre-demcr/` retains the actual command, firmware hash, immutable
CLI hash, model source-diff identity, raw failure and empty bus trace. Its
file-backed descriptor points to the exact candidate source used for that
run; it is historical evidence. The portable system above uses the built-in
chip name. Physical flash, sensor motion, motor direction and flight
qualification remain unperformed.
