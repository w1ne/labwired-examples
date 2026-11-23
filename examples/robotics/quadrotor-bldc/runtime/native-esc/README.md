# Native AT32F421 ESC execution

The conventional and bidirectional input proofs load the exact complete
OPENESC_30_F421_complete.elf through the ordinary loader. The image contains
the original PB4 bootloader, native AM32 application and explicit EEPROM
fixture. The model is AT32F421G8U7 at 120 MHz with peripheral tick interval 1.

The executed core source is
[c29e0e367d0075975e4d555f8135b6f668e57f7b](https://github.com/w1ne/labwired-core/tree/c29e0e367d0075975e4d555f8135b6f668e57f7b).
The [firmware manifest](../../firmware/native-esc/package-manifest.json) binds
the exact source and evidence files. All recorded source hashes match before
and after execution. The shared timer path emits native update/compare DMA
requests; the existing DMA engine performs the transfers.

## Replay

Check out that core revision. The tests require the packaged external firmware
files, so run their explicit artifact-backed invocations:

```sh
AT32_NATIVE_ARTIFACTS=/absolute/quadrotor-bldc/firmware/native-esc/artifacts \
AT32_NATIVE_PROTOCOL_REPORT=/absolute/new-evidence/conventional-result.json \
cargo test --locked -p labwired-core --features event-scheduler \
  --test vendor at32_am32_protocol:: -- --ignored --nocapture

AT32_NATIVE_ARTIFACTS=/absolute/quadrotor-bldc/firmware/native-esc/artifacts \
AT32_NATIVE_BIDIR_REPORT=/absolute/new-evidence/bidirectional-result.json \
cargo test --locked -p labwired-core --features event-scheduler \
  --test vendor at32_am32_bidir:: -- --include-ignored --nocapture
```

Both tests verify the exact ELF hashes. Their explicit 1 kHz input has 200 core
cycles per DShot600 bit, with 75 active cycles for 0 and 150 for 1. The
bidirectional test uses the inverted checksum and releases the external
driver before measuring the native PB4 reply. This is a digital transmitter
fixture, not execution of the FC image or a measured physical transmitter.

## Recorded acceptance

Conventional acquisition accepts 39 zero frames. The corrupt frame increments
the bad counter and leaves the input at 0; the following valid frame is accepted
as 100. The bidirectional test records good 14/bad 100 after mode acquisition,
good 14/bad 101 after the deliberate corrupt frame, then good 15/bad 101 with
requested and adjusted input 100. Both retain sensor_error 0 and armed 0.

The actual bidirectional reply has 17 driven edges and a 154-cycle bit period.
Independent GCR/checksum decoding returns 0xFFF (stopped). The pad releases
afterward, with no contention and no trace overflow. Invalid GCR, checksum,
missing-edge and timing controls reject their altered inputs. The native
runtime and complete source-test logs are in evidence/.

AM32 programs a compare value above the auto-reload value for its reply output.
The shared timer now produces the natural-wrap comparison instead of
silently suppressing it. The relevant STM32 timer behavior is documented in
RM0386; applying that compatible behavior to AT32 is an explicit model
inference because the sourced AT32 manual does not state that corner case.
No AT32 physical waveform measurement is claimed.

The current single-node system declares no motor plant with guessed electrical
parameters. Connected native five-node acceptance is separate, and must verify
actual PIO-driven GPIO31/30/29/28, PB4 replies, natural ESC arming, UART commands,
and loss/lease behavior. Physical power, thermal, rotor/load and flight
qualification are not established by these digital protocol receipts.
