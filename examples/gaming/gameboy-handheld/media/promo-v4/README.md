# LabWired closing edit and interactive browser entry

The final movie is `LabWired-KernelCAD-BrickBreaker.mp4`: 20.000 seconds,
1920 × 1080, 60 fps, 1,200 frames, with stereo audio.
The reviewed export contains **6,662,219 bytes**, SHA-256
`b45e26fce48d73a59347ff5c8d6a4f12008eb7f025af54c57a1d2bd5b13a2731`.

The existing 18-second CAD movie is reused. A 24-frame dissolve starts at 17.6 s.
The closing card is fully visible from 18.0 to 20.0 s and reads:

> LabWired
>
> The easy way to make hardware with agents.

The card uses the existing light background and navy typography. It adds no
decorative lines. The original synthesized score's final tonic bar is placed at
18.0 s. Its existing decay ends at 19.875 s, followed by 125 ms of silence.

## Rebuild

Requires Python 3, NumPy, Pillow, FFmpeg with libass/libx264, and DejaVu Sans fonts.
Use the pinned Python dependencies from `../promo-v3/requirements.txt`. From this
directory, first rebuild the caption-free geometry master and original score
through the existing [v3 pipeline](../promo-v3/README.md), then add the ending:

```sh
python3 -m pip install -r ../promo-v3/requirements.txt
python3 ../promo-v3/rebuild.py --output-dir /tmp/brick-breaker-base
python3 finish_brand_ending.py \
  --video /tmp/brick-breaker-base/motion/geometry-master.mp4 \
  --audio /tmp/brick-breaker-base/audio/wire-runner-original-30s.wav \
  --output /tmp/brick-breaker-final/LabWired-KernelCAD-BrickBreaker.mp4
```

If the v3 outputs already exist, run only `finish_brand_ending.py`. The
compositor uses this directory's approved `promo.ass` by default. Its video and
audio defaults also accept a standard `../promo-v3/build/` tree. The optional
`--font-dir` selects the directory containing `DejaVuSans.ttf` and
`DejaVuSans-Bold.ttf`; the default is `/usr/share/fonts/truetype/dejavu`.

The script generates the card and closing score, encodes the movie, verifies the
duration and frame count, and writes provenance and FFprobe reports beside the
output movie. `--work-dir` can place the generated card, score, captions, encode
log and reports elsewhere. `--assets-only` prepares those assets without encoding.
The committed evidence is not overwritten by the default command. MP4, PNG, WAV,
raw framebuffer streams and other generated binaries are not added to Git.

The portable copy changes input/output paths and font selection only. Card
layout, score samples, dissolve timing, captions and encoder settings remain the
approved values. The [portability check](portable-rebuild.json) reproduced the
card, closing WAV and captions byte for byte. The source master SHA-256 is
`de651c6dacca981829de10155904da2d65bf545b7c3df4f51f5f5d8cbd2a660f`;
the 30-second synthesized score SHA-256 is
`99a796c97f8086d11407a96332cd34e0411ce145b4077906f8c1e2509a37ef40`.
Encoder and font versions can change output bytes; the final-file hash identifies
the reviewed export, not every possible rebuild environment.

This script does not rerender geometry or change the public project. The footage
uses actual CAD geometry and recorded original-ROM framebuffer pixels. The 60 fps
export rate does not measure browser or simulated STM32 wall-clock performance.

`ending-qa.json` records the full decode, frame timing, ending audio level, and
the inspected transition and final frames. `ending-provenance.json` records
source hashes, exact copy, transition timing, and the final movie hash.

## Play the actual browser simulation

[Open the handheld in LabWired + KernelCAD](https://app.labwired.com/p/f44771855a18a70d418e363622de2e28/edit?run=1&view=kernelcad).
The URL selects KernelCAD and starts the MCU simulation. Wait for the LCD to
initialize, click **A** to launch, then hold **LEFT** or **RIGHT** to steer. B
restarts, START pauses or resumes, and SELECT changes the palette. The CAD LCD
receives actual simulated display updates; its mapped controls feed that same
simulation. WebGL2 is required for the interactive CAD view. The project remains
unlisted and retains its existing firmware, geometry and nine electronics bindings.

The [visible production-browser receipt](browser-verification.json), recorded on
2026-11-11, verifies revision 3 geometry and all nine LCD/control bindings in a
separate Chrome profile using software WebGL. Real pointer presses on the model
moved the paddle from x=68 to x=113 with RIGHT, then launched the ball with A;
the LCD hash changed from `152236bb` to `0a80022b`. At 60% native explosion,
display observations advanced from 266 to 289 while simulation remained running.
The browser was left open in the assembled front view after native B reset,
with score 0, three lives and all inputs released.

These observations are independent of the video and the
[hosted MCU oracle](../../firmware/brick-breaker-verification.json). The receipt
retains nonblocking telemetry CORS and HTTP 401 errors. Native PCB authentication
and board mapping, physical hardware, and real-time 60 fps are outside its scope.
The [earlier cloud-browser observation](../promo-v3/evidence/public-ui-observation.json)
retains that environment's WebGL initialization limit as a separate result.
