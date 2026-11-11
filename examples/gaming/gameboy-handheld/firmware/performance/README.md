# Simulation speed candidate

**The firmware candidate completes 39 DMG frames in the same 50,000,000-step
hosted STM32 run where the saved baseline completes 16.** The six-clause oracle
and four input events are unchanged. This is a 2.44× bounded instruction-budget
result, including boot. It is not a browser wall-clock frame-rate measurement.
The candidate is isolated in a temporary lab; this checkpoint does not replace
the saved project or the original recording ROM.

## Cause and changes

The cartridge polls the DMG LY register until VBlank. Peanut-GB therefore
executes thousands of waiting instructions inside the already simulated STM32.
The candidate uses the DMG VBlank interrupt and `HALT` to wait for the same next
frame. Its main game logic still executes in the cartridge.

The MCU already skips unchanged scanlines, but a changed scanline sends all
240 scaled pixels. The candidate caches native shade pixels and writes only the
changed horizontal span through the same STM32 SPI and ILI9341 window commands.
This includes old sprite positions, so movement erases the previous pixels.
It preserves the exact integer 160×144 → 240×216 mapping and RGB565 palette.

The hosted scaffold uses GCC `-Os`. The candidate requests GCC `O3` for this
CPU-heavy translation unit. It uses ordinary integer optimization, without
fast-math, different simulated clocks, host-side game execution or frame skips.

| Variant | Completed DMG frames at 50M steps |
|---|---:|
| Saved baseline | 16 |
| VBlank / HALT | 25 |
| VBlank / HALT + dirty spans | 29 |
| VBlank / HALT + dirty spans + O3 | 39 |

## Evidence

[performance-comparison.json](performance-comparison.json) names exact hashes,
requests and results. [candidate-verification.json](candidate-verification.json)
records all six oracle clauses passing and all four input events applied.
The baseline run and both exact request objects are retained beside it.

The same input script produces identical per-frame LCD hashes and all 13 game
state bytes across 2,400 frames for the old and new ROM. Both traces have SHA-256
`b0f207665b1be8c3fdd9d7cd2dd6b66a0b975c764cb64be51b67d04d2111514f`.
Both complete the controls/collision checks with score 47, 25 paddle bounces and
three lives. ROM reads during the same 2,400-frame sequence fall from 31,807,096
to 619,132.

The pixel fixture executes both actual C LCD draw functions on the same frames.
Every RGB565 framebuffer and full-frame hash matches. It also checks one-pixel
changes and erasures across all 160 source columns. Pixel bytes fall from
19,663,200 to 1,468,626 (92.53% fewer); both paths issue 27,315 windows. These
counts are from the deterministic fixture, not inferred from an overflowed
logic-analyzer trace.

The candidate ELF has 56,820 bytes of code/read-only data, 104 bytes of `.data`,
40,156 bytes of `.bss` and 1,540 bytes of reserved heap/stack plus alignment.
The linker sets `_estack` to `0x20020000`. Static RAM plus that reservation is
41,800 of 131,072 bytes; 89,272 bytes remain outside those allocations. This is
linker accounting, not a measured worst-case stack watermark.

The baseline ELF is
`sha256:cfa5fd07dbaa457d7e3315d69d5076c90b70f453d490229889e440a595ea4681`.
The candidate ELF is
`sha256:e7f8031ab996136da9202409bc7ec3fef12510d262c2da7266a20247ca299f28`.
The candidate source tree is
`sha256:5cbc1cb8e76bb37a3ae892b6891a76d1dbd7a95f7da01f1ad93d03093bb9979e`.

## Reproduce in isolated checkouts

The patch targets the example at repository commit
`e5606fb14eb88292d2064810cf4075c67e5e55c8`. Keep one checkout as the baseline.
Apply [candidate-source.patch](candidate-source.patch) to a separate checkout,
then run its existing `firmware/build_brick_breaker.py` and
`firmware/build_brick_breaker_firmware.py`. The resulting source and ROM hashes
must match the candidate receipt. The original saved-project sources and movie
inputs do not need to be changed for this comparison.

Compile `host_equivalence.c` with each checkout's firmware directory as its
include path. Run each binary and compare its standard-output trace. Diagnostics
on standard error report the ROM-read count and gameplay checks. The trace
hash above binds the tested per-frame states.

Generate the LCD fixture from the two actual MCU source files:

```sh
python3 make_display_test.py \
  --baseline-main <baseline>/firmware/brick_breaker_main.c \
  --candidate-main <candidate>/firmware/brick_breaker_main.c \
  --rom-dir <candidate>/firmware \
  --output /tmp/display_test.c
cc -std=c99 -O2 /tmp/display_test.c -o /tmp/display-test
/tmp/display-test
```

For hosted reproduction, use the existing generic `labwired_put_source`,
`labwired_compile` and `labwired_verify` calls in the adjacent JSON receipts.
Do not shorten or remove oracle clauses. Browser throughput and the separate
CAD display-bridge throttle need an independent wall-clock comparison.

## Scope

The candidate still runs the ROM inside Peanut-GB on the modeled STM32F411.
GPIO inputs, all eight CAD controls, the LCD binding, real SPI writes, CAD
geometry, native PCB reference and unlisted visibility are preserved.
The hosted model retains its documented CPU-derived timing and ideal-supply
approximations. No physical-hardware timing is measured.
