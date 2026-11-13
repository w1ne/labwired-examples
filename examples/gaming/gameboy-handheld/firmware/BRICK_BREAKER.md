# Game Boy recreation — Brick Breaker

An original, playable 32 KiB Game Boy cartridge runs inside Peanut-GB on the simulated STM32F411 Black Pill. The MCU reads the controls through GPIO and writes the ILI9341 through SPI. The saved KernelCAD assembly maps the actual display framebuffer and all eight physical controls.

## Play

- LEFT / RIGHT: move the paddle.
- A: launch the ball; restart after game over.
- B: restart with three lives and 24 bricks.
- START: pause or resume.
- SELECT: alternate the monochrome palette.

The contact point on the paddle changes the ball's direction and angle. Each broken brick adds one point. Clearing all 24 bricks starts a new board. A missed ball costs a life. UP and DOWN remain electrical input targets but have no action in this game. The firmware has no autoplay.

[Open the saved project directly in KernelCAD with Run enabled](https://app.labwired.com/p/f44771855a18a70d418e363622de2e28/edit?run=1&view=kernelcad). Wait for the LCD to initialize, click A to launch, then hold LEFT or RIGHT to steer. The mapped buttons drive the same MCU simulation that produces the LCD updates. The project remains unlisted. Interactive CAD requires WebGL2; the promotional video's 60 fps does not measure browser or MCU wall-clock performance.

## Exact firmware

- ROM SHA-256: `92782644b70e39c9314c345fc991447f51937486570c177be01be6cb38ae610b`.
- Hosted C source SHA-256: `0035482806916ad05e4446ebece8bb284103473c1bfda5318e75460d5b3fb2a0`.
- Compiled firmware: `sha256:e7f8031ab996136da9202409bc7ec3fef12510d262c2da7266a20247ca299f28`.
- Board: `stm32f411ceu6-blackpill`; language: C; entry: `src/main.c`.

The exact current source is the `source` field of [the saved update request](performance/promotion-update-request.json). The [performance patch and build instructions](performance/README.md) reproduce it from the original recording source. The top-level `brick_breaker.c`, ROM, generators and capture harness retain that earlier recording baseline. The previous Wire Runner source remains a separate original example.

## Model evidence

The original recording baseline passed six declared behavioral checks within 50,000,000 MCU steps: Brick Breaker ROM initialization; RIGHT input; A input; paddle movement from x=68 to x=86; launched-ball state; and a painted ILI9341 framebuffer containing 153,600 bytes. All four press/release stimuli were applied. The actual logged ball moved from (97,114) to (107,104).

After the speed optimization was promoted, saved-project verification through MCP passed the same six clauses with `max_steps: 50000000`. The input events and oracle are unchanged. The [promotion and readback receipt](performance/promotion-receipt.json) binds fresh proof to content hash `2d1cfec8…4781a2` and confirms the exact O3 source and pinned ELF afterward. The earlier [baseline verification](brick-breaker-saved-project-verification-mcp.json) remains historical evidence. The [generic MCP recipe](../MCP_RECIPE.md) documents the calls and the separate movie/browser-QA boundary.

The same-ROM host test additionally passed left/right movement, launch, pause/resume, restart, palette, brick scoring, paddle bounces and missed-ball life loss. Scripted button play broke 47 bricks across two boards during the bounded test. These are simulation results.

The promotional capture uses the exact ROM executed by Peanut-GB at the native Game Boy frame cadence, with an external scripted button track, then samples those frames for a 60 fps CAD animation. This is not a measurement of STM32 or browser simulator wall-clock frame rate. No autoplay or capture script is embedded in the device firmware.

## Current simulation speed

The installed [performance revision](performance/README.md) completes 39 DMG frames in the same 50,000,000-step budget where the baseline completes 16. It uses VBlank/HALT, exact dirty LCD spans and compiler optimization. Its per-frame game state and LCD output match the baseline across 2,400 test frames. One sequential Circuit-browser comparison observed approximately 5.5 to 18.6 game frames/s. That observation does not measure raster display FPS, CAD performance, input latency or real-time 60 fps. The saved project runs the optimized revision; the original recording ROM remains intact.

## Assembly and PCB

KernelCAD revision 3 (`kQAFdaQs`) retains 59 parts, the LCD face binding and eight button bindings. The native routed carrier remains attached as board `pcb_c8da1d7776dba9bc`, revision 0. Mechanical geometry, routing and electrical mappings are unchanged by this game update.

The controller is USB powered. The enclosure reserves battery and speaker volume; audio, a cartridge socket, save storage and battery charging are not implemented. The purchased module datum and cable fit require measurement.

## Reproduce the recording baseline

```sh
python3 build_brick_breaker.py
python3 build_brick_breaker_firmware.py
cc -std=c99 -O2 host_brick_breaker.c -o /tmp/host-brick-breaker
/tmp/host-brick-breaker
```

These commands rebuild the original recording baseline. To reproduce the current saved firmware, follow [performance/README.md](performance/README.md): apply the verified patch in an isolated checkout and run the same two generators. Upload the resulting `brick_breaker.c` with `labwired_put_source`, compile for `stm32f411ceu6-blackpill`, then use the returned firmware reference with the unchanged oracle in `performance/candidate-verification-request.json`.

## Deterministic promotional capture

```sh
/tmp/host-brick-breaker /tmp/brick-breaker.rgb /tmp/brick-breaker-state.jsonl --promo
python3 capture_brick_breaker.py /tmp/brick-breaker.rgb /tmp/brick-breaker-state.jsonl /tmp/brick-breaker-lcd
```

The harness scripts real button inputs: B resets at native frame 693, then A launches at frame 729. The converter maps actual ROM pixels to the firmware's 320 × 240 LCD layout and samples the native Game Boy cadence for an 18-second, 60 fps animation. It does not fabricate game states, interpolate game pixels, or measure MCU wall-clock performance.

## Limits and license

Timing is model-derived. The hosted model reports a CPU-time approximation and assumes an ideal 3.3 V supply. Hardware frame rate, power draw, regulator margin, signal integrity, component heights and printed enclosure fit have not been measured. Diagram validation reports three generic SPI-capability warnings on PB0, PB1 and PA8; these are the LCD's control/backlight GPIO lines, not SPI data or clock.

The original Brick Breaker cartridge, generator and integration are MIT-licensed example code. Peanut-GB's MIT notice is retained. No commercial game ROM or proprietary boot ROM is included.

