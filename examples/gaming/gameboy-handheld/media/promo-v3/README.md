# Rebuild the 18-second Brick Breaker demonstration

This cut shows the complete handheld, its exploded assembly, the routed carrier,
the STM32F411 controller, and a playable original Brick Breaker game. The output
is **18 seconds, 1920 × 1080, 60 fps, 1,080 frames**, with the original synthesized
score. No decorative horizontal lines or progress bars are added.

The footage is an **offline render of actual KernelCAD geometry with actual ROM
emulator pixels**. Every frame receives its own camera and part transforms. It
does not use optical-flow interpolation, endpoint morphs, or retimed mouse drags.
The 60 fps delivery rate does not measure the wall-clock performance of the MCU
model or browser application.

The reviewed export is `LabWired-KernelCAD-BrickBreaker-18s.mp4`, **6,552,783 bytes**,
SHA-256 `340b7615e02912218b4ce843900f176726e168038549e7f1165f1977f458dea5`.
The master motion audit found 1,080 distinct frame checksums, uniform presentation
timestamps and no adjacent duplicate frames. Final caption review moved the
controller title clear of the rear shell and removed the reassembly title so
parts remain unobscured. See [the final export receipt](evidence/final-video-verification.json),
[the full decoded-motion audit](evidence/audit/master/decode-audit.json), and
[the corrected export audit](evidence/audit/final/export-receipt.json).

## Views

| Time | View |
| --- | --- |
| 0–1.5 s | Complete handheld with active gameplay |
| 1.5–5 s | Continuous exploded assembly reveal |
| 5–6.3 s | Native carrier routing and the selected RIGHT/PB6 connection |
| 6.3–8.5 s | Push toward the visible STM32F411 Black Pill controller |
| 8.5–12 s | Continuous reassembly |
| 12–16 s | Complete device and a fresh round of gameplay |
| 16–18 s | Close view of the LCD, D-pad and action buttons |

Camera motion and exploded poses use continuous quintic easing. The module turn
and exploded offsets are presentation poses; they are not a manufacturing
assembly sequence or changed saved mates.

## Sources and scope

- **CAD:** all 59 source features from KernelCAD `kQAFdaQs`, immutable revision 3.
  The source vertex positions, indices, surface normals and materials are retained.
  `assets.json` pins the mesh URL, byte count and SHA-256.
- **PCB:** the example's exact native `pcb/handheld-carrier.kicad_pcb`. The extractor
  reads 264 tracks, 36 vias, 92 pads and 16 footprints. Track widths, pad dimensions
  and coordinates come from that file. The overlay omits copper zone fills so the
  routes remain legible. Turquoise selects net 12, RIGHT/PB6, from SW4 to A1 pad 14.
  This is a connectivity highlight, not a measured current or signal-timing trace.
- **Controller appearance:** a crop of the official WeAct STM32F411 top render
  is mapped to the existing module envelope. Its immutable Git blob and decoded
  image hashes are pinned. The image adds appearance only; it does not establish
  component package geometry, exact heights or fit. Vendor imagery is fetched
  from the source and is not redistributed in this directory.
- **LCD:** the exact original Brick Breaker ROM executes in Peanut-GB. The host
  harness records real framebuffer pixels and an external scripted button track.
  The native cadence is `4194304 / 70224` frames per second. The sampler uses the
  STM32 firmware's RGB565 palette and integer scaling into a 320 × 240 LCD image.
  At output frame 697, B resets the game; frame 733 applies A to launch the next
  ball. The ROM and device firmware contain no autoplay.
- **Controls:** recorded positive joypad bits drive a short visual travel filter.
  This indicates the applied input; it is not a contact-force simulation.
- **Sound:** the included generator synthesizes the original melody and instruments
  from code, with a fixed random seed. It uses no samples or external audio.

The [hosted firmware evidence](../../firmware/brick-breaker-verification.json)
separately records a passing 50,000,000-step STM32 input/display oracle. The
[public browser observation](evidence/public-ui-observation.json) independently
records the new game boot, A launch, score progression, and RIGHT movement. That
browser could not initialize the KernelCAD 3D view. The offline promo does not
conceal that limitation or replace the independent application observation.

## Rebuild

Use Python 3.12, a C compiler, GCC with OpenMP, FFmpeg with `libx264` and `libass`,
and DejaVu Sans. The recorded environment uses GCC 14.2.0 and FFmpeg 7.1.5.
Python dependencies are pinned in `requirements.txt`.

```sh
python3 -m pip install -r requirements.txt
python3 rebuild.py --output-dir /tmp/brick-breaker-promo
```

The script downloads and verifies the two public visual assets, extracts the
native PCB, executes the ROM capture harness, constructs the render scene,
compiles the CPU triangle renderer, renders every frame, synthesizes the score,
and adds the captions. It writes:

```text
/tmp/brick-breaker-promo/LabWired-KernelCAD-BrickBreaker-18s.mp4
```

The downloads use ordinary system proxy and CA settings. No sign-in, private
credentials, browser storage or saved-project mutation is needed. A hash mismatch
stops the build. The optional `--no-network` switch requires already downloaded,
hash-matching assets in the selected output directory.

To prepare the inputs and compile the renderer without repeating the complete
movie render:

```sh
python3 rebuild.py --output-dir /tmp/brick-breaker-promo --prepare-only
```

After preparation, the renderer can also generate a specific frame. Its stdout is
a PPM image stream, so redirect it to a file:

```sh
/tmp/brick-breaker-promo/motion/render_cpu \
  /tmp/brick-breaker-promo/motion/scene.bin \
  480 481 1920 1080 2 \
  /tmp/brick-breaker-promo/motion/lcd.rgb 320 240 \
  > /tmp/brick-breaker-frame.ppm
```

The CPU renderer uses a triangle depth buffer, source normals, two directional
lights, a shadow map, and four subpixel samples per final output pixel. Raw RGB
streams, generated meshes, renderer binaries, large intermediates and the final
MP4 are deliberately omitted from Git. The final movie is delivered separately;
its metadata and hashes are recorded with the evidence.

## Reproduction evidence

The portable preparation command completed successfully. Rebuilt `scene.bin`,
`controls.bin`, `controller.ppm`, the 248,832,000-byte LCD stream and the original
30-second WAV match the recording inputs byte for byte. A compiled-renderer
smoke check produced frame 480 at 320 × 180. See
[the portability receipt](evidence/portable-rebuild.json).

The accepted master is identified in [the render receipt](evidence/render-receipt.json).
The original recording replaced its last 120 frames after approving a closer
final framing. The committed renderer includes that final camera timeline, so a
full rebuild uses it directly. Codec versions and segment encoding can change
the final MP4 bytes; the frame timing, geometry and source pixels remain explicit.
The delivered-file hash identifies the reviewed export, not every possible
encoder build.

No physical hardware test or wall-clock simulator frame-rate measurement is
claimed. The hosted model's timing and ideal-supply approximations remain part
of the firmware evidence.
