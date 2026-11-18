# Native OpenFC motor bench

This is the physical commissioning image for OpenFC-Lite rev2-LW1, its RP2354B and four native AM32/AT32F421 ESC controllers. It is a separate application from the pinned Betaflight image in `../native-fc`. Full flight qualification remains LabWired issue #3190.

## Exact hardware and wire contract

The native PCB/netlist, not a historical reworked board target, defines these routes:

| Function | RP2354B GPIO | Native connector |
| --- | ---: | --- |
| Motor1 bidirectional DShot600 |31|P1.5|
| Motor2 bidirectional DShot600 |30|P1.6|
| Motor3 bidirectional DShot600 |29|P1.7|
| Motor4 bidirectional DShot600 |28|P1.8|
| Host UART0 transmit |0|U8.3; test pad J49.1|
| Host UART0 receive |1|U8.4; test pad J48.1|
| Active-high status LED |12|D1|

The processor is the QFN80 / 48 GPIO RP2354B with 2 MiB stacked flash. The SDK configures 150 MHz. PIO0 state machines 0–3 run at 75 MHz, and eight real DMA channels feed four transmit FIFOs and drain four receive FIFOs. Each output bit takes 125 PIO clocks. A zero uses 41 clocks low and 84 high; a one uses 84 low and 41 high. The wire is inverted and each request carries an inverted DShot checksum.

The FC releases its motor pads, with its pulls disabled, for 750 ms after application startup. This lets the unchanged AM32 PB4 bootloader observe its own pull-down. It then enables the FC pull-ups, waits 1 ms and sends zero frames at 1 kHz. GPIO output-enable changes, PIO instructions and DMA transfers own the wire; no CPU bit-banging or fabricated reply path exists.

The receive program releases output-enable, waits for an actual falling edge and captures 128 samples at 18 PIO clocks per sample. The C decoder checks the GCR/RLL encoding and inverted checksum. Only normalized eRPM encodings or the 0xFFF stopped sentinel count as motor feedback. Reserved/extended telemetry encodings do not become eRPM values. Reported eRPM is electrical RPM; it is not converted to shaft RPM.

## Host commands

Use the packaged FTDI `TTL-232R-3V3-WE` solder harness. Set 115200 baud, 8 data bits, no parity and 1 stop bit. Disable RTS/CTS and XON/XOFF flow control. The board's USB port is for ROM BOOTSEL flashing; this application does not implement a USB console.

| FTDI conductor | Connection on the FC | Signal |
| --- | --- | --- |
| Orange TXD | J48.1 | GPIO1, UART0 receive |
| Yellow RXD | J49.1 | GPIO0, UART0 transmit |
| Black GND | J51.1 | Common ground |
| Red +5 V | Individually insulated, unconnected | Cable power output |
| Brown CTS# | Individually insulated, unconnected | Unused handshake input |
| Green RTS# | Individually insulated, unconnected | Unused handshake output |

The adapter uses 3.3 V signals, but its red power lead is +5 V. Use the assembly's documented power input and leave that lead insulated. The three solder connections, restraint and unused-conductor parking are specified by `source/host-console-harness.json` and the main package's assembly instructions. Verify the native pad reference and signal before soldering; the label correction changed hidden values only and preserved every copper connection.

For electrical tracing, the existing U8 connector is JST `SM06B-SRSS-TB(LF)(SN)`: pin 1 is +10 V, pin 2 GND, pin 3 GPIO0/UART0 TX, pin 4 GPIO1/UART0 RX, pin 5 GND and pin 6 UART1 RX. U8 is an electrical reference here; the packaged console uses the three solder pads in the table.

Commands are ASCII lines terminated by LF. CR before LF is accepted. Commission the motor bench with propellers removed.

| Command | Result |
| --- | --- |
|`status`|Print bench state and each motor's request, reply/timeout/error counters, raw payload, period and eRPM.|
|`arm`|Enable nonzero bench commands only after 1,250 zero frames, at least 128 valid replies per motor and feedback no older than 100 ms.|
|`set 2 100`|Request DShot value 100 from motor 2; motor numbers are 1–4.|
|`all 100`|Request value 100 from all four motors.|
|`set 2 0`|Set motor 2 to zero.|
|`stop` or `all 0`|Set all requests to zero, disable nonzero bench commands and restart zero qualification.|

Only 0 and 48–2047 are accepted as values. DShot command IDs 1–47 are not exposed. Invalid syntax, overflow, an out-of-range motor and an overlong line are rejected. A nonzero request requires `arm`. Each accepted value command refreshes a 500 ms command lease. Expiry sets all requests to zero. Loss of valid feedback for 100 ms also stops the requests. Repeated `status` commands do not keep a request alive.

The bench `armed` flag controls this command permission. It does not report the separate AM32 firmware's internal arm state. The status LED is solid while the bench permits nonzero requests and blinks otherwise. Zero traffic may leave an ESC internally armed; a stop means an actual zero request, not a claim that its internal arm latch has cleared.

UART output uses a bounded nonblocking ring. PIO/DMA continues while the CPU services console and receive deadlines at 25 µs intervals. A full log ring drops a whole message and increments `log_dropped`; logging cannot block the frame schedule.

## Reproducible build

The package includes complete SDK/picotool source archives and the application source. Linux x86-64, Python 3.12+, CMake, make and a native C++ compiler are required. Arm GNU 13.3.Rel1 is required; the script can download and SHA256-check it or use an existing exact toolchain.

```sh
python3 build.py --work-dir /tmp/openfc-bench-build --toolchain /opt/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi --jobs 2
```

Use a fresh empty build directory. Outputs are under its `artifacts/` directory: `openfc_motor_bench.elf`, `.uf2`, `.bin`, `.elf.map`, structural checks and a build receipt. The SDK's Cortex-M33 flags and assertions remain enabled. The UF2 family is the native RP2350 Arm Secure family; its flash payload must match the BIN byte for byte and stay within 2 MiB. The artifact check also reads the actual linked motor-pad array and zero-initialized bench state, with corruption controls.

To test the pure decoder on the host:

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror -Isrc src/protocol.c tests/protocol_test.c -o /tmp/openfc-bench-protocol-test
/tmp/openfc-bench-protocol-test
```

## Evidence and limits

Two fresh source-archive builds produced byte-identical ELF, BIN and UF2 files. The final ELF SHA256 is `f38456f3c78197f9168e26a095c6f7f19afd044ef338825d25afdbd167dd418b`; the flash BIN contains 21,884 bytes. `validation/reproducibility.json` records both build locations and artifact identities. These are build results; they do not establish the five-node runtime result.

The host suite covers 16,406 cases. It exhausts all 4,096 telemetry payloads at three nearby wire periods, rejects bad checksums and reserved eRPM meanings, and decodes four sampling phases of a real native-simulation PB4 edge capture from the unchanged AM32 image. `tests/fixtures/am32-stopped.json` records that capture's exact image hashes, 120 MHz timestamps and provenance. This is simulator evidence, not a physical capture.

The standalone runtime descriptor is `../../runtime/native-fc-bench/system.yaml`. A standalone FC has no ESC reply source: timeouts are expected. Five-node acceptance must additionally prove the actual PIO pad edges, four unchanged ESC images and their natural internal arm transitions, accepted requests, decoded replies and both stop paths. That acceptance is pending until its source-bound receipt is included. No physical hardware qualification is claimed.

The board's gyro, receiver, SD card, video, current/voltage ADCs and flight-control functions are outside this commissioning application's acceptance. The separate Betaflight package retains its own startup evidence and qualifications.

## Source provenance

`source-versions.json` pins the native board/schematic/netlist, SDK, picotool and compiler. The PIO source is derived from [OpenDrone-hw/betaflight 31066c0f](https://github.com/OpenDrone-hw/betaflight/blob/31066c0f3789d2dbc34b394cf383b04394d43724/src/platform/PICO/dshot.pio). The untouched file is `source/upstream-dshot.pio`; `source/dshot-bench.patch` corrects an 11-clock comment and implements the intended five-iteration 2 µs tail delay. The native SDK is [Raspberry Pi pico-sdk ee68c78d](https://github.com/raspberrypi/pico-sdk/tree/ee68c78d0afae2b69c03ae1a72bf5cc267a2d94c). The C protocol follows the pinned upstream decoder and the native AM32 encoder. The application is GPL-3.0-or-later; bundled upstream source retains its licenses.
