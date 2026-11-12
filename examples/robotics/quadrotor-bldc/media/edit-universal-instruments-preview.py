#!/usr/bin/env python3
"""Cut verified app recordings at normal speed and retain the source edit list."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def run(*args):
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("edit_list", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.edit_list.read_text())
    if plan["acceptance_status"] != "passed":
        raise SystemExit("A passed app acceptance receipt is required for the final video")
    clips = plan["clips"]
    duration = sum(clip["duration_s"] for clip in clips)
    if not 30 <= duration <= 45:
        raise SystemExit("The final edit must be 30–45 seconds")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not font.is_file():
        raise SystemExit("The caption font is unavailable")
    sources = {}
    with tempfile.TemporaryDirectory(prefix="quad-edit-", dir=output.parent) as temp:
        work = Path(temp)
        segments = []
        for index, clip in enumerate(clips):
            source = Path(clip["file"]).resolve(strict=True)
            digest = sources.setdefault(str(source), sha256(source))
            if digest != clip["sha256"]:
                raise SystemExit(f"Recording identity changed: {source.name}")
            if clip["start_s"] < 0 or clip["duration_s"] <= 0:
                raise SystemExit("Invalid cut interval")
            caption = work / f"caption-{index}.txt"
            caption.write_text(clip["caption"], encoding="utf-8")
            context = work / "context.txt"
            context.write_text(plan["context"], encoding="utf-8")
            segment = work / f"segment-{index}.mp4"
            # Preserve the complete app viewport. Captions sit outside it.
            filters = (
                "scale=1728:972:force_original_aspect_ratio=decrease:flags=lanczos,"
                "pad=1920:1080:(ow-iw)/2:12:color=0x09111b,setsar=1,"
                f"drawtext=fontfile={font}:textfile={caption}:expansion=none:"
                "fontsize=32:fontcolor=white:x=96:y=998,"
                f"drawtext=fontfile={font}:textfile={context}:expansion=none:"
                "fontsize=21:fontcolor=0xa6b8cc:x=96:y=1044"
            )
            run("ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin", "-y",
                "-ss", str(clip["start_s"]), "-i", str(source),
                "-t", str(clip["duration_s"]), "-vf", filters,
                "-an", "-r", "30", "-c:v", "libx264", "-crf", "18",
                "-preset", "medium", "-pix_fmt", "yuv420p", str(segment))
            segments.append(segment)
        concat = work / "concat.txt"
        concat.write_text("".join(f"file '{p.name}'\n" for p in segments))
        run("ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin", "-y",
            "-f", "concat", "-safe", "1", "-i", str(concat), "-c", "copy",
            "-movflags", "+faststart", str(output))
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(output)
    ]))
    actual_duration = float(probe["format"]["duration"])
    if abs(actual_duration - duration) > 0.1:
        raise SystemExit("Encoded duration differs from the edit list")
    provenance = {
        "edit_list": plan,
        "source_sha256": sources,
        "editing": "Straight cuts at original speed; full viewport; captions outside app; no synthesized signals",
        "output": {"file": output.name, "sha256": sha256(output),
                   "bytes": output.stat().st_size, "ffprobe": probe},
    }
    output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"output": str(output), "seconds": actual_duration,
                      "bytes": output.stat().st_size, "sha256": provenance["output"]["sha256"]}))


if __name__ == "__main__":
    main()
