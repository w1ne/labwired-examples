# Physical three-node station runtime

The packaged master and both packaged device images pass together in the
existing LabWired digital World. The master reaches OPERATE on both ports,
reads independent `A5` / `3C` input bytes, and then reads `5A` / `C3` after
changing the two native input banks. All three images run their physical
ST HAL clock, GPIO, interrupt, I2C and UART code at 80 MHz.

The [runtime manifest](../evidence/physical-runtime-station/manifest.json)
records the exact core source, firmware hashes, invocation and complete
network trace. The immutable core commit is
`0916c184059ad4a83b6dbe13a027ad6d36d98f0d`; normal commit hooks passed. The [system files](physical-station/environment.yaml) use
the existing embedded STM32L476 and UID descriptors; distinct synthetic
UIDs are per-instance reset fixtures, not device-specific descriptor files.

| Contract | Value |
|---|---|
| Master controller | NUCLEO-L476RG; USART1 PA9/PA10 and UART4 PA0/PA1 |
| Master PHYs | L6360, I2C1 PB8/PB9, addresses `0x60` and `0x61` |
| Device controllers | Two NUCLEO-L476RG; USART1 PA9/PA10 |
| Device PHYs | L6362A; EN PC7, OL PA6, DIAG PA4, IN1 grounded |
| Digital inputs | Each SN74HC165: latch PC6, clock PB13, data PB14 |
| Serial protocol | COM2, nominal 38,400 bit/s, 8E1, BRR 2083 |
| Cyclic data | TYPE_2_1, one input byte per port, 10 ms cycle |
| Timing | One-cycle peripheral interval; 1 us World quantum |
| Identity | Two declared synthetic 96-bit UID fixtures |

The two L6360 interfaces use the sourced inversion and receive-disable
behavior. Device UART TXINV and RXINV are enabled in the unchanged HAL
image. The timed UART network transports the resulting C/Q wire format;
its inversion fields are therefore not a substitute for the MCU register
configuration. Both devices observe exactly one opposed-line wake-up and
one OL falling edge. Startup, PHY, UART, overflow and transmit-deadline
counters are zero. All four wire directions have zero parity, framing,
overrun, false-start, misframed, truncated and late events in the receipt.

## Reproduce

Check out the exact core commit in the manifest, then run from that checkout:

```sh
IOLINK_STATION_FIRMWARE_DIR=/absolute/package/firmware/release \
IOLINK_STATION_REPORT_DIR=/absolute/output/station-run \
cargo test --locked -p labwired-core --features event-scheduler \
  --test world world_iolink_physical:: -- --ignored --nocapture
```

The test verifies both immutable ELF hashes before boot. It uses the
existing `World::from_resolved` API with supplied firmware bytes. It runs
for 680 ms of simulated time, changes actual `ch0` through `ch7` input
channels at 650 ms, and observes the firmware's process-data variables.
The package environment has only its firmware paths relocated relative
to this package; the original executed environment is retained in evidence.

Run `python3 runtime/verify-station-proof.py` from the package root to
check the retained image hashes, observed node states, input transitions,
identities, error counters and wire statistics. The earlier isolated
physical-device proof remains in [device-only-proof.md](device-only-proof.md)
for regression provenance; it does not replace this station result.

## Qualification boundary

This receipt is digital execution evidence for the physical firmware.
Valid 24 V PHY supplies and nominal digital propagation times are explicit
scenarios. The model does not calculate voltage, current, slew rate,
clamp energy, regulator dynamics or temperature. Wiring, oscillator and
C/Q waveform measurements, physical power checks and an assembled
hardware acceptance run remain required. Browser integration is verified
separately against the same images and system descriptors.
