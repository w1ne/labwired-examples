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

- ROM SHA-256: `708714362154e758603e7a60e811466736348fa8b919be313c56ae1a1656f6a5`.
- Hosted C source SHA-256: `cd30bf4b2ea545786b0fcc7673dc3fd1c1e9a8cb08ed9a37b7ee96f5c649c7e4`.
- Compiled firmware: `sha256:cfa5fd07dbaa457d7e3315d69d5076c90b70f453d490229889e440a595ea4681`.
- Board: `stm32f411ceu6-blackpill`; language: C; entry: `src/main.c`.

The repository's `examples/gaming/gameboy-handheld/firmware/` contains `build_brick_breaker.py`, the cartridge, MCU integration, deterministic host harness and verification receipts. The previous Wire Runner source is retained as a separate original example.

## Model evidence

The hosted run passed six declared behavioral checks within 50,000,000 MCU steps: Brick Breaker ROM initialization; RIGHT input; A input; paddle movement from x=68 to x=86; launched-ball state; and a painted ILI9341 framebuffer containing 153,600 bytes. All four press/release stimuli were applied. The actual logged ball moved from (97,114) to (107,104).

Fresh saved-project verification through MCP passed the same six clauses with `max_steps: 50000000`, without changing source, input events or the oracle. The [request and readback receipt](brick-breaker-saved-project-verification-mcp.json) bind that proof to content hash `626abc0c…60825b`. The [generic MCP recipe](../MCP_RECIPE.md) documents the exact calls and the separate movie/browser-QA boundary.

The same-ROM host test additionally passed left/right movement, launch, pause/resume, restart, palette, brick scoring, paddle bounces and missed-ball life loss. Scripted button play broke 47 bricks across two boards during the bounded test. These are simulation results.

The promotional capture uses the exact ROM executed by Peanut-GB at the native Game Boy frame cadence, with an external scripted button track, then samples those frames for a 60 fps CAD animation. This is not a measurement of STM32 or browser simulator wall-clock frame rate. No autoplay or capture script is embedded in the device firmware.

## Assembly and PCB

KernelCAD revision 3 (`kQAFdaQs`) retains 59 parts, the LCD face binding and eight button bindings. The native routed carrier remains attached as board `pcb_c8da1d7776dba9bc`, revision 0. Mechanical geometry, routing and electrical mappings are unchanged by this game update.

The controller is USB powered. The enclosure reserves battery and speaker volume; audio, a cartridge socket, save storage and battery charging are not implemented. The purchased module datum and cable fit require measurement.

## Reproduce

```sh
python3 build_brick_breaker.py
python3 build_brick_breaker_firmware.py
cc -std=c99 -O2 host_brick_breaker.c -o /tmp/host-brick-breaker
/tmp/host-brick-breaker
```

Upload `brick_breaker.c` with `labwired_put_source`, compile for `stm32f411ceu6-blackpill`, then run the declared oracle in `brick-breaker-verify-request.json` using the returned firmware reference.

## Deterministic promotional capture

```sh
/tmp/host-brick-breaker /tmp/brick-breaker.rgb /tmp/brick-breaker-state.jsonl --promo
python3 capture_brick_breaker.py /tmp/brick-breaker.rgb /tmp/brick-breaker-state.jsonl /tmp/brick-breaker-lcd
```

The harness scripts real button inputs: B resets at native frame 693, then A launches at frame 729. The converter maps actual ROM pixels to the firmware's 320 × 240 LCD layout and samples the native Game Boy cadence for an 18-second, 60 fps animation. It does not fabricate game states, interpolate game pixels, or measure MCU wall-clock performance.

## Limits and license

Timing is model-derived. The hosted model reports a CPU-time approximation and assumes an ideal 3.3 V supply. Hardware frame rate, power draw, regulator margin, signal integrity, component heights and printed enclosure fit have not been measured. Diagram validation reports three generic SPI-capability warnings on PB0, PB1 and PA8; these are the LCD's control/backlight GPIO lines, not SPI data or clock.

The original Brick Breaker cartridge, generator and integration are MIT-licensed example code. Peanut-GB's MIT notice is retained. No commercial game ROM or proprietary boot ROM is included.

