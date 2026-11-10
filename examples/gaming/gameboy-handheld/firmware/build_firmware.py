#!/usr/bin/env python3
"""Create the exact single-file C source accepted by the hosted compiler."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parent
source = (root / "main.c").read_text()
for header in ("peanut_gb.h", "wire_runner_rom.h"):
    source = source.replace(f'#include "{header}"', (root / header).read_text())
(root / "gameboy.c").write_text(source)
print(f"gameboy.c: {len(source.encode())} bytes, sha256:{hashlib.sha256(source.encode()).hexdigest()}")
