#!/usr/bin/env python3
"""Edit a real Playwright capture into a 1920x1080, 30 fps H.264 demonstration.

Usage:
  python3 edit-promo.py raw.webm clips.json promo.mp4 --plan-only
  python3 edit-promo.py raw.webm clips.json promo.mp4 --crf 19

The manifest is either a clip array or {"clips": [...], "intro": {...},
"outro": {...}, "brand": "LabWired + KernelCAD"}. Each clip has numeric start
and end times in source seconds, a title, and an optional subtitle.
A clip may also name a source video. Relative source paths resolve beside
the manifest; omitted source uses the command-line video. Every source is
probed independently and hashed in the final edit record.

No crop, retiming, synthetic hardware animation, soundtrack, or external
media is added. The complete source frame fits inside a reserved screen
area; all captions and section labels sit outside that area. Cuts are hard
cuts. Short title cards use plain color and text. Source audio is omitted
because Playwright video captures are silent.

Requirements: Python 3.10+, Pillow for font metrics, FFmpeg/ffprobe with
libx264 and drawtext. This machine already has these dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from fractions import Fraction

from PIL import ImageFont

WIDTH, HEIGHT, FPS = 1920, 1080, 30
SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H = 24, 50, 1872, 918
BG, TEXT, MUTED, ACCENT, RULE = "0x11161c", "0xf2f4f7", "0xa8b2c1", "0x8db7f5", "0x29333f"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


@dataclass(frozen=True)
class Segment:
    kind: str
    title: str
    subtitle: str
    seconds: float
    frames: int
    start: float | None = None
    end: float | None = None
    url: str = ""
    source: str | None = None


def number(value, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if value < 0 or (positive and value == 0):
        raise ValueError(f"{label} must be {'positive' if positive else 'nonnegative'}")
    return float(value)


def line(value, label: str, maximum: int = 180, required: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    result = value.strip()
    if (required and not result) or len(result) > maximum:
        raise ValueError(f"{label} must contain {'1' if required else '0'}–{maximum} characters")
    if any(ord(c) < 32 or ord(c) == 127 for c in result):
        raise ValueError(f"{label} must be one printable line")
    return result


def make_card(kind: str, data, defaults: dict) -> Segment | None:
    if data is False:
        return None
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"{kind} must be an object or false")
    seconds = number(data.get("duration", defaults.get("duration", 2.5)), f"{kind}.duration")
    if seconds == 0:
        return None
    if not 1 <= seconds <= 6:
        raise ValueError(f"{kind}.duration must be 1–6 seconds, or 0 to omit it")
    return Segment(
        kind=kind,
        title=line(data.get("title", defaults["title"]), f"{kind}.title", 90, True),
        subtitle=line(data.get("subtitle", defaults["subtitle"]), f"{kind}.subtitle"),
        seconds=seconds,
        frames=round(seconds * FPS),
        url=line(data.get("url", defaults.get("url", "")), f"{kind}.url", 140),
    )


def resolve_source(value, default_source: Path | None, root: Path) -> str | None:
    if value is None:
        return str(default_source.resolve()) if default_source else None
    name = line(value, "clip.source", 4096, True)
    path = Path(name).expanduser()
    return str((path if path.is_absolute() else root / path).resolve())


def read_manifest(data, source_seconds: float, *, source_durations: dict[str, float] | None = None,
                  source_root: Path | None = None, default_source: Path | None = None) -> tuple[str, list[Segment]]:
    if isinstance(data, list):
        data = {"clips": data}
    if not isinstance(data, dict) or not isinstance(data.get("clips"), list):
        raise ValueError("Manifest must be a clip array or an object containing clips")
    clips = data["clips"]
    if not 1 <= len(clips) <= 20:
        raise ValueError("Provide 1–20 clips")
    brand = line(data.get("brand", "LabWired + KernelCAD"), "brand", 70, True)
    segments: list[Segment] = []
    intro = make_card("intro", data.get("intro"), {
        "title": "Wire Runner",
        "subtitle": "Real firmware. Live controls. Connected CAD.",
    })
    if intro:
        segments.append(intro)
    for i, raw in enumerate(clips):
        prefix = f"clips[{i}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{prefix} must be an object")
        selected_source = resolve_source(raw.get("source"), default_source, source_root or Path.cwd())
        if raw.get("source") is not None and (source_durations is None or selected_source not in source_durations):
            raise ValueError(f"{prefix}.source must be probed before validating its timing")
        limit = source_durations.get(selected_source, source_seconds) if source_durations else source_seconds
        start = number(raw.get("start"), prefix + ".start")
        end = number(raw.get("end"), prefix + ".end", positive=True)
        if end <= start or end - start < 1 / FPS:
            raise ValueError(f"{prefix} must span at least one output frame")
        if end > limit + 1 / FPS:
            raise ValueError(f"{prefix}.end {end:.3f} exceeds selected source duration {limit:.3f}")
        segments.append(Segment(
            kind="clip",
            title=line(raw.get("title"), prefix + ".title", 120, True),
            subtitle=line(raw.get("subtitle", ""), prefix + ".subtitle"),
            seconds=end - start,
            frames=max(1, round((end - start) * FPS)),
            start=start,
            end=end,
            source=selected_source,
        ))
    outro = make_card("outro", data.get("outro"), {
        "title": "Try the working example",
        "subtitle": "LabWired + KernelCAD",
        "url": "https://app.labwired.com/p/f44771855a18a70d418e363622de2e28/edit?run=1",
        "duration": 4,
    })
    if outro:
        segments.append(outro)
    return brand, segments


def probe(path: Path) -> dict:
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,r_frame_rate,nb_frames,duration",
        "-of", "json", str(path),
    ]
    return json.loads(subprocess.check_output(command, text=True))


def video_stream(info: dict) -> dict:
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    if len(streams) != 1:
        raise ValueError(f"Expected one video stream, found {len(streams)}")
    return streams[0]


def duration(info: dict) -> float:
    result = float(info.get("format", {}).get("duration", 0))
    if not math.isfinite(result) or result <= 0:
        raise ValueError("Input has no finite positive duration; finish the recording first")
    return result


def text_file(work: Path, name: str, text: str) -> Path:
    result = work / f"{name}.txt"
    result.write_text(text, encoding="utf-8")
    return result


def fit_size(text: str, font: Path, preferred: int, minimum: int, width: int) -> int:
    for size in range(preferred, minimum - 1, -1):
        if ImageFont.truetype(str(font), size).getlength(text) <= width:
            return size
    raise ValueError(f"Caption is too long for the reserved band: {text!r}")


def wrap_title(text: str, size: int, max_width: int, max_lines: int = 2) -> str:
    font = ImageFont.truetype(str(BOLD), size)
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if not current:
                raise ValueError("A title word is too wide; use a shorter title")
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines or any(font.getlength(item) > max_width for item in lines):
        raise ValueError("Title is too long for a clean two-line card")
    return "\n".join(lines)


def draw_text(path: Path, font: Path, size: int, x: str | int, y: str | int,
              color: str = TEXT, spacing: int = 12) -> str:
    # All text files live in a newly created /tmp/labwired-promo-* directory.
    # Captions are never interpolated into FFmpeg expressions.
    return (
        f"drawtext=fontfile='{font}':textfile='{path}':expansion=none:"
        f"fontsize={size}:fontcolor={color}:x={x}:y={y}:line_spacing={spacing}"
    )


def screen_filter(segment: Segment, index: int, count: int, brand: str, work: Path) -> str:
    title_size = fit_size(segment.title, BOLD, 28, 24, 1840)
    subtitle_size = fit_size(segment.subtitle, FONT, 22, 20, 1840)
    filters = [
        "setpts=PTS-STARTPTS",
        f"fps={FPS}",
        f"scale={SCREEN_W}:{SCREEN_H}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos",
        "setsar=1",
        f"pad={SCREEN_W}:{SCREEN_H}:(ow-iw)/2:(oh-ih)/2:color={BG}",
        f"pad={WIDTH}:{HEIGHT}:{SCREEN_X}:{SCREEN_Y}:color={BG}",
        draw_text(text_file(work, "brand", brand), FONT, 18, 32, 14, MUTED),
        draw_text(text_file(work, f"counter-{index}", f"{index:02d} / {count:02d}"),
                  FONT, 18, "w-tw-32", 14, MUTED),
        draw_text(text_file(work, f"title-{index}", segment.title), BOLD, title_size, 32, 988),
        draw_text(text_file(work, f"subtitle-{index}", segment.subtitle), FONT, subtitle_size, 32, 1028, MUTED),
        f"drawbox=x=32:y=1073:w=1856:h=3:color={RULE}:t=fill",
    ]
    # Static chapter progress. It communicates section position, not fake signal activity.
    gap = 8
    cell = (1856 - gap * (count - 1)) / count
    for item in range(index):
        filters.append(
            f"drawbox=x={32 + item * (cell + gap):.3f}:y=1073:w={cell:.3f}:h=3:color={ACCENT}:t=fill"
        )
    filters.append("format=yuv420p")
    return ",".join(filters)


def card_filter(segment: Segment, brand: str, work: Path) -> str:
    title = wrap_title(segment.title, 72, 1624)
    title_lines = title.count("\n") + 1
    subtitle_y = 370 + title_lines * 86 + 34
    subtitle_size = fit_size(segment.subtitle, FONT, 30, 24, 1624)
    filters = [
        draw_text(text_file(work, "card-brand", brand), FONT, 24, 148, 250, MUTED),
        f"drawbox=x=148:y=314:w=104:h=4:color={ACCENT}:t=fill",
        draw_text(text_file(work, segment.kind + "-title", title), BOLD, 72, 140, 370),
        draw_text(text_file(work, segment.kind + "-subtitle", segment.subtitle),
                  FONT, subtitle_size, 148, subtitle_y, MUTED),
    ]
    if segment.url:
        url_size = fit_size(segment.url, FONT, 24, 20, 1624)
        filters.append(draw_text(text_file(work, segment.kind + "-url", segment.url),
                                 FONT, url_size, 148, subtitle_y + 66, ACCENT))
    filters.append("format=yuv420p")
    return ",".join(filters)


def encode_command(source: Path, segment: Segment, filters: str, target: Path,
                   crf: int, threads: int) -> list[str]:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin", "-y", "-filter_threads", "2"]
    if segment.kind == "clip":
        command += ["-ss", f"{segment.start:.9f}", "-i", str(source)]
    else:
        command += [
            "-f", "lavfi", "-i",
            f"color=c={BG}:s={WIDTH}x{HEIGHT}:r={FPS}:d={segment.frames / FPS:.9f}",
        ]
    return command + [
        "-map", "0:v:0", "-an", "-vf", filters, "-frames:v", str(segment.frames),
        "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-threads", str(threads), "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
        "-video_track_timescale", "30000", "-map_metadata", "-1", str(target),
    ]


def ffmeta(text: str) -> str:
    return text.replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#")


def chapter_metadata(segments: list[Segment], measured: list[float]) -> str:
    rows, position = [";FFMETADATA1", "title=Wire Runner — LabWired + KernelCAD"], 0.0
    for segment, seconds in zip(segments, measured):
        end = position + seconds
        rows += [
            "[CHAPTER]", "TIMEBASE=1/1000", f"START={round(position * 1000)}",
            f"END={round(end * 1000)}", f"title={ffmeta(segment.title)}",
        ]
        position = end
    return "\n".join(rows) + "\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_output(info: dict, expected_seconds: float) -> None:
    stream = video_stream(info)
    if stream.get("codec_name") != "h264" or (stream.get("width"), stream.get("height")) != (WIDTH, HEIGHT):
        raise RuntimeError("Output codec or dimensions do not match H.264 / 1920x1080")
    if Fraction(stream["avg_frame_rate"]) != FPS or stream.get("pix_fmt") != "yuv420p":
        raise RuntimeError("Output frame rate or pixel format does not match 30 fps / yuv420p")
    if abs(duration(info) - expected_seconds) > 2 / FPS:
        raise RuntimeError("Output duration differs from the encoded segment timeline")


def verify_faststart(path: Path) -> None:
    boxes = {}
    total = path.stat().st_size
    with path.open("rb") as stream:
        while stream.tell() + 8 <= total:
            offset = stream.tell()
            header = stream.read(8)
            size, kind = int.from_bytes(header[:4], "big"), header[4:]
            if size == 1:
                size = int.from_bytes(stream.read(8), "big")
            elif size == 0:
                size = total - offset
            if size < 8 or offset + size > total:
                raise RuntimeError("Invalid MP4 box size")
            boxes.setdefault(kind, offset)
            stream.seek(offset + size)
    if b"moov" not in boxes or b"mdat" not in boxes or boxes[b"moov"] > boxes[b"mdat"]:
        raise RuntimeError("MP4 does not have front-loaded faststart metadata")


def args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--crf", type=int, choices=(18, 19, 20), default=19)
    parser.add_argument("--threads", type=int, choices=range(1, 17), default=4)
    parser.add_argument("--plan-only", action="store_true", help="Validate and print the timeline; do not encode any video")
    parser.add_argument("--overwrite", action="store_true", help="Replace the exact requested output file after successful validation")
    parser.add_argument("--keep-work", action="store_true", help="Keep caption files and encoded segments after success")
    return parser


def main() -> int:
    args = args_parser().parse_args()
    source, manifest, output = args.source.resolve(), args.manifest.resolve(), args.output.resolve()
    if output.suffix.lower() != ".mp4" or output == source:
        raise ValueError("Use a new .mp4 output path distinct from the source")
    if output.exists() and not args.overwrite and not args.plan_only:
        raise ValueError(f"Output exists: {output}; use --overwrite to replace it")
    for name in ("ffmpeg", "ffprobe"):
        if not shutil.which(name):
            raise ValueError(f"{name} is required")
    if not FONT.is_file() or not BOLD.is_file():
        raise ValueError("DejaVu Sans and DejaVu Sans Bold font files are required")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    raw_clips = data if isinstance(data, list) else data.get("clips", []) if isinstance(data, dict) else []
    paths = {str(source): source}
    if isinstance(raw_clips, list):
        for raw in raw_clips:
            if isinstance(raw, dict):
                chosen = resolve_source(raw.get("source"), source, manifest.parent)
                paths[chosen] = Path(chosen)
    if str(output) in paths:
        raise ValueError("Output must be distinct from every selected source video")
    source_infos = {name: probe(path) for name, path in paths.items()}
    source_durations = {name: duration(info) for name, info in source_infos.items()}
    source_rows = [{"path": name, "seconds": source_durations[name], "video": video_stream(info)}
                   for name, info in source_infos.items()]
    info = source_infos[str(source)]
    source_seconds = source_durations[str(source)]
    stream = video_stream(info)
    brand, segments = read_manifest(data, source_seconds, source_durations=source_durations,
                                   source_root=manifest.parent, default_source=source)
    clip_count = sum(s.kind == "clip" for s in segments)
    planned_seconds = sum(s.frames / FPS for s in segments)
    plan = {
        "source": str(source), "source_video": stream, "source_seconds": source_seconds, "sources": source_rows,
        "output": str(output), "output_format": {"codec": "h264", "width": WIDTH, "height": HEIGHT, "fps": FPS, "crf": args.crf},
        "screen_rectangle": {"x": SCREEN_X, "y": SCREEN_Y, "width": SCREEN_W, "height": SCREEN_H},
        "brand": brand, "segments": [asdict(s) for s in segments], "planned_seconds": planned_seconds,
        "editing": "Hard cuts; full source frame; real-time playback; silent; no external media.",
    }
    if not 50 <= planned_seconds <= 65:
        print(f"Note: the supplied clips produce {planned_seconds:.2f}s. No speed change will be applied.", file=sys.stderr)
    work = Path(tempfile.mkdtemp(prefix="labwired-promo-", dir="/tmp"))
    commands, targets, clip_index = [], [], 0
    try:
        for index, segment in enumerate(segments):
            if segment.kind == "clip":
                clip_index += 1
                filters = screen_filter(segment, clip_index, clip_count, brand, work)
            else:
                filters = card_filter(segment, brand, work)
            target = work / f"segment-{index:02d}.mp4"
            targets.append(target)
            commands.append(encode_command(Path(segment.source) if segment.source else source, segment, filters, target, args.crf, args.threads))
        if args.plan_only:
            print(json.dumps(plan, indent=2, ensure_ascii=False))
            shutil.rmtree(work)
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        measured = []
        for index, (command, target, segment) in enumerate(zip(commands, targets, segments)):
            print(f"Encoding {index + 1}/{len(segments)}: {segment.title}", file=sys.stderr, flush=True)
            subprocess.run(command, check=True)
            segment_info = probe(target)
            expected = segment.frames / FPS
            verify_output(segment_info, expected)
            measured.append(duration(segment_info))
        concat = work / "concat.txt"
        concat.write_text("".join(f"file '{p.name}'\n" for p in targets), encoding="utf-8")
        chapters = work / "chapters.ffmetadata"
        chapters.write_text(chapter_metadata(segments, measured), encoding="utf-8")
        temporary_output = work / "final.mp4"
        join = [
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin", "-y",
            "-f", "concat", "-safe", "1", "-i", str(concat), "-f", "ffmetadata", "-i", str(chapters),
            "-map", "0:v:0", "-map_metadata", "1", "-map_chapters", "1", "-c:v", "copy", "-an",
            "-movflags", "+faststart", "-video_track_timescale", "30000", str(temporary_output),
        ]
        subprocess.run(join, check=True)
        final_info = probe(temporary_output)
        verify_output(final_info, sum(measured))
        verify_faststart(temporary_output)
        # Work may be on another filesystem. Copy to an exclusive sibling before atomic replace.
        sibling = output.with_name(output.name + "." + work.name + ".tmp")
        try:
            with temporary_output.open("rb") as src, sibling.open("xb") as dest:
                shutil.copyfileobj(src, dest, 4 * 1024 * 1024)
            if args.overwrite:
                os.replace(sibling, output)
            else:
                os.link(sibling, output)
                sibling.unlink()
        finally:
            if sibling.exists():
                sibling.unlink()
        source_hashes = {name: sha256(path) for name, path in paths.items()}
        report = {
            **plan, "source_sha256": source_hashes[str(source)], "output_sha256": sha256(output),
            "sources": [{**row, "sha256": source_hashes[row["path"]]} for row in source_rows],
            "output_probe": final_info, "actual_seconds": duration(final_info), "faststart_verified": True,
            "segment_seconds": measured, "commands": commands + [join],
            "output_size_mib": output.stat().st_size / (1024 * 1024), "transfer_target_mib": 20,
        }
        report_path = output.with_suffix(".edit.json")
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        size_mib = output.stat().st_size / (1024 * 1024)
        print(f"Saved {output}\nDuration: {duration(final_info):.3f}s\nSize: {size_mib:.2f} MiB\nEdit record: {report_path}")
        if size_mib > 20:
            print("Transfer target exceeded: inspect quality before choosing a lower bitrate.", file=sys.stderr)
        if args.keep_work:
            print(f"Working files: {work}")
        else:
            shutil.rmtree(work)
        return 0
    except BaseException:
        print(f"Working files retained for inspection: {work}", file=sys.stderr)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Edit failed: {error}", file=sys.stderr)
        raise SystemExit(1)

