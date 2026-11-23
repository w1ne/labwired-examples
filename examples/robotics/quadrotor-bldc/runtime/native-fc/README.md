# Native RP2354B runtime boundary

`system.yaml` declares the physical RP2354B controller, a 150 MHz model
clock, BMI270 on SPI0 with CS14/INT13, and the active-high status LED on
GPIO12. The native pin assignments and the physical firmware are preserved.

The current 2 MiB image is ELF SHA256
`cfb1f6a19225695804d79200ddc7158bc421365af9cc8b8c74ab06170980d27b`.
Two clean builds produce identical ELF, UF2 and BIN files. Both linked SDK
flash functions check the actual 2,097,152-byte physical capacity. Build
identity and the exact bounds instructions are in
`../../firmware/native-fc/artifacts/build-receipt.json`.

## Executed boundary

The current recorded run uses core source
`9a325465b59542320e1d13d4fd86d4f8e9a6a2e0` and immutable CLI SHA256
`59080a8d557b7a182e392fbecabcadd41a70c759625077ea7393f6ca80a5a4b1`.
The generic boot-vector and DEMCR repairs allow the firmware to reach flash
configuration initialization. It then halts at 550,000 instructions in
`__assert_func` / `_exit`: the clean-room RP2350 ROM returns NULL for
`flash_range_erase`. The SDK correctly rejects the missing API. Its flash
initialization and assertions remain unchanged. No SPI events occur before
this stop. This is a failed execution receipt; full initialization is pending.

`validation/pre-rom-flash/` contains the current run, exact inputs, raw
snapshot and result, decoded assertion, disassembly and CLI provenance.
`validation/pre-demcr/` retains the earlier image's precise DEMCR BusFault
as historical evidence. The shared Cortex-M DEMCR repair is merged in
[core PR2043](https://github.com/w1ne/labwired-core/pull/2043). The RP2354B
package/GPIO descriptor and generic ROM/XIP flash support must complete their
normal gates before a final runtime proof can be accepted.

## Repeating the probe

Run from `examples/robotics/quadrotor-bldc` with a CLI that includes the
RP2354B descriptor:

```sh
labwired test --script runtime/native-fc/probe.yaml \
  --output-dir /tmp/openfc-native-runtime --run-manifest
```

The bounded probe requires reaching its instruction limit without a CPU
fault. It does not establish boot completion, gyro accuracy, receiver input,
DShot timing or motor response. Those need separate observable oracles after
the executed model gaps are resolved. The model uses a fixed 150 MHz clock
and an ideal supply; it does not yet track PLL changes or board brown-out.

The full station must derive each motor pad's drive from the FC's real
IO_BANK0/PIO initialization. The RP2354B pads start released; forcing an
initial high would hold the native PB4 ESC bootloader in programming
recognition. No motor waveform or successful initialization is injected.
Physical flashing, sensor motion, motor direction and flight qualification
remain unperformed.
