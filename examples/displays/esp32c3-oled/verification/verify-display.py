#!/usr/bin/env python3
"""Check output from the existing LabWired CLI; no separate device model."""
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text())
assert len(result["assertions"]) >= 5
assert all(item["passed"] for item in result["assertions"]), "CLI behavior checks failed"
display = next(item for item in result["inspect"]["devices"] if item["id"] == "oled")
assert display["attachment"]["address"] == 0x3C
frame = next(item for item in display["artifacts"] if item["kind"] == "framebuffer")
meta = frame["meta"]
assert (meta["w"], meta["h"]) == (128, 64)
assert meta["powered"] is True
frames = [item for item in meta["frames_seen"] if item["ink_bytes"] > 0]
assert len({item["sha256"] for item in frames}) >= 2, "Display did not change"
print(json.dumps({"checks_passed": len(result["assertions"]),
                  "distinct_nonblank_frames": len({item["sha256"] for item in frames}),
                  "frames": frames, "final_lit_pixels": meta["lit_pixels"]}, indent=2))
