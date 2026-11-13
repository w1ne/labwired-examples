#!/usr/bin/env python3
"""Amalgamate the Brick Breaker MCU entry and exact ROM for hosted builds."""
from pathlib import Path
import hashlib
root = Path(__file__).resolve().parent
source = (root / 'brick_breaker_main.c').read_text()
for header in ('peanut_gb.h', 'brick_breaker_rom.h'):
    source = source.replace(f'#include "{header}"', (root / header).read_text())
(root / 'brick_breaker.c').write_text(source)
print(f'brick_breaker.c: {len(source.encode())} bytes, sha256:{hashlib.sha256(source.encode()).hexdigest()}')
