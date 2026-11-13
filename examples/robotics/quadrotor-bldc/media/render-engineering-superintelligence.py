#!/usr/bin/env python3
"""Render the LabWired engineering-superintelligence quadrotor video.

The renderer uses retained application footage and captured instrument UI. It
adds only cuts, timing changes and captions. It does not fabricate telemetry.
Requires ffmpeg and the DejaVu Sans fonts.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

W, H, FPS = 1600, 900, 30
ACCENT = "0x4fc3f7"
BG = "0x080d14"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-video",
        type=Path,
        default=here / "quadrotor-engineering-preview.mp4",
    )
    parser.add_argument(
        "--logic-image",
        type=Path,
        default=here / "universal-logic-analyzer.png",
    )
    parser.add_argument(
        "--scope-image",
        type=Path,
        default=here / "universal-oscilloscope.png",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=here / "labwired-engineering-superintelligence-quadrotor.mp4",
    )
    return parser.parse_args()


def run(args: list[str]) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
    )


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")


def top_label(title: str, subtitle: str = "") -> str:
    filters = [
        "drawbox=x=0:y=0:w=1600:h=112:color=0x080d14@0.86:t=fill",
        f"drawbox=x=38:y=32:w=7:h=48:color={ACCENT}@1:t=fill",
        f"drawtext=fontfile={BOLD}:text='{esc(title)}':fontcolor=white:fontsize=35:x=64:y=24",
    ]
    if subtitle:
        filters.append(
            f"drawtext=fontfile={FONT}:text='{esc(subtitle)}':"
            "fontcolor=0xb9c7d8:fontsize=19:x=65:y=70"
        )
    return ",".join(filters)


def render_video(
    edit_dir: Path,
    source: Path,
    name: str,
    start: float,
    end: float,
    duration: float,
    title: str,
    subtitle: str,
) -> Path:
    output = edit_dir / f"{name}.mp4"
    ratio = duration / (end - start)
    filters = ",".join(
        [
            f"setpts={ratio:.8f}*(PTS-STARTPTS)",
            f"fps={FPS}",
            f"scale={W}:{H}:flags=lanczos",
            top_label(title, subtitle),
            "fade=t=in:st=0:d=0.12",
            f"fade=t=out:st={max(duration - 0.14, 0):.3f}:d=0.14",
        ]
    )
    run(
        [
            "-ss",
            str(start),
            "-t",
            str(end - start),
            "-i",
            str(source),
            "-vf",
            filters,
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-preset",
            "faster",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return output


def render_still(
    edit_dir: Path,
    image: Path,
    name: str,
    duration: float,
    title: str,
    subtitle: str,
    crop: str | None = None,
) -> Path:
    output = edit_dir / f"{name}.mp4"
    filters: list[str] = []
    if crop:
        filters.append(crop)
    filters += [
        f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos",
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG}",
        "zoompan=z='min(1.018,1+on*0.00008)':"
        "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1600x900:fps=30",
        top_label(title, subtitle),
        "fade=t=in:st=0:d=0.14",
        f"fade=t=out:st={max(duration - 0.16, 0):.3f}:d=0.16",
    ]
    run(
        [
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(image),
            "-t",
            str(duration),
            "-vf",
            ",".join(filters),
            "-an",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-preset",
            "faster",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return output


def render_card(
    edit_dir: Path,
    name: str,
    duration: float,
    lines: list[tuple[str, int, int, str]],
    footer: str | None = None,
) -> Path:
    output = edit_dir / f"{name}.mp4"
    filters = ["drawbox=x=110:y=170:w=12:h=430:color=0x4fc3f7:t=fill"]
    for value, size, y, color in lines:
        font = BOLD if size >= 44 else FONT
        filters.append(
            f"drawtext=fontfile={font}:text='{esc(value)}':"
            f"fontcolor={color}:fontsize={size}:x=155:y={y}"
        )
    if footer:
        filters.append(
            f"drawtext=fontfile={FONT}:text='{esc(footer)}':"
            "fontcolor=0x91a1b5:fontsize=22:x=155:y=730"
        )
    filters += [
        "fade=t=in:st=0:d=0.25",
        f"fade=t=out:st={max(duration - 0.3, 0):.3f}:d=0.3",
    ]
    run(
        [
            "-f",
            "lavfi",
            "-i",
            f"color=c={BG}:s={W}x{H}:r={FPS}:d={duration}",
            "-vf",
            ",".join(filters),
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-preset",
            "faster",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )
    return output


def render(args: argparse.Namespace) -> dict[str, object]:
    for path in (args.source_video, args.logic_image, args.scope_image):
        if not path.is_file():
            raise FileNotFoundError(path)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="labwired-quadrotor-edit-") as tmp:
        edit_dir = Path(tmp)
        clips: list[Path] = []
        clips.append(
            render_card(
                edit_dir,
                "00-intro",
                2.6,
                [
                    ("LABWIRED", 72, 205, "white"),
                    ("ENGINEERING SUPERINTELLIGENCE", 49, 315, ACCENT),
                    (
                        "From an idea to a validated, manufacturable machine.",
                        31,
                        410,
                        "0xd7e1ec",
                    ),
                ],
                "Actual CAD · native PCB · compiled firmware · deterministic simulation",
            )
        )
        scenes = [
            ("01-design", 7.0, 15.0, 4.5, "01 / DESIGN THE MACHINE", "Mechanics, electronics and firmware"),
            ("02-assembly", 15.0, 22.7, 4.5, "02 / INSPECT THE ASSEMBLY", "Native geometry, component placement and motion"),
            ("03-electronics", 23.0, 29.6, 3.5, "03 / TRACE THE ELECTRONICS", "Power, sensing and control paths"),
            ("04-pcb", 30.0, 36.5, 4.0, "04 / REVIEW THE MANUFACTURING PCB", "Six layers · 222 footprints · 1,067 pads"),
        ]
        for scene in scenes:
            clips.append(render_video(edit_dir, args.source_video, *scene))
        clips.append(
            render_still(
                edit_dir,
                args.logic_image,
                "05-logic",
                2.5,
                "05 / UNIVERSAL LOGIC ANALYZER",
                "Protocol traces on any LabWired device",
            )
        )
        clips.append(
            render_still(
                edit_dir,
                args.scope_image,
                "06-scope",
                2.5,
                "06 / UNIVERSAL OSCILLOSCOPE",
                "Live analog and digital waveforms",
                "crop=1920:960:0:80",
            )
        )
        runtime_scenes = [
            ("07-live", 37.0, 44.5, 5.5, "07 / RUN FOUR FIRMWARE CONTROLLERS", "Four compiled STM32 images drive four motor plants"),
            ("08-fault", 45.0, 50.0, 3.0, "08 / INJECT A DRIVER FAULT", "Change the machine while it is running"),
            ("09-proof", 50.0, 56.8, 4.5, "09 / PROVE SELECTIVE SHUTDOWN", "M1 inverter off · M2–M4 continue"),
            ("10-repeat", 57.0, 69.6, 3.5, "PAUSE. RESET. REPEAT.", "Deterministic tests, not a one-off animation"),
        ]
        for scene in runtime_scenes:
            clips.append(render_video(edit_dir, args.source_video, *scene))
        clips.append(
            render_card(
                edit_dir,
                "11-outro",
                3.5,
                [
                    ("LABWIRED IS ENGINEERING SUPERINTELLIGENCE.", 40, 230, "white"),
                    ("DESIGN IT. RUN IT. BREAK IT. FIX IT.", 38, 340, ACCENT),
                    ("VALIDATE IT FOR MANUFACTURING.", 38, 420, ACCENT),
                ],
                "labwired.com",
            )
        )
        concat = edit_dir / "concat.txt"
        concat.write_text("".join(f"file '{clip.resolve()}'\n" for clip in clips))
        run(
            [
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-an",
                "-c:v",
                "libx264",
                "-threads",
                "1",
                "-preset",
                "faster",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-metadata",
                "title=LabWired engineering superintelligence — quadrotor demo",
                "-metadata",
                "comment=Edited from retained application footage and instrument captures. No fabricated telemetry. This is a reduced-order engineering twin, not physical flight proof.",
                str(args.output),
            ]
        )

    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size:stream=codec_name,width,height,r_frame_rate",
                "-of",
                "json",
                str(args.output),
            ],
            text=True,
        )
    )
    return {"output": str(args.output), "clips": 12, "ffprobe": probe}


def main() -> None:
    print(json.dumps(render(parse_args()), indent=2))


if __name__ == "__main__":
    main()
