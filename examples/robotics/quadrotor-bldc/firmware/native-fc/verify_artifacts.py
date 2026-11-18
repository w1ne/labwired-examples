#!/usr/bin/env python3
"""Verify real ELF reset defaults, UF2 layout and BIN agreement; no hardware writes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PACKAGE = Path(__file__).resolve().parent

def require(value, message):
    if not value:
        raise ValueError(message)

def elf_symbols(raw):
    require(raw[:7] == b"\x7fELF\x01\x01\x01", "Expected ELF32 little-endian")
    require(struct.unpack_from("<HH", raw, 16) == (2, 40), "Expected ARM executable")
    shoff = struct.unpack_from("<I", raw, 32)[0]
    shsize, count = struct.unpack_from("<HH", raw, 46)
    require(shsize == 40, "ELF32 section size")
    sections = [struct.unpack_from("<10I", raw, shoff + i * shsize) for i in range(count)]
    result = {}
    for section in sections:
        if section[1] != 2:
            continue
        strings_section = sections[section[6]]
        strings = raw[strings_section[4]:strings_section[4] + strings_section[5]]
        require(section[9] == 16, "ELF32 symbol size")
        for offset in range(section[4], section[4] + section[5], section[9]):
            name, address, size, _, _, index = struct.unpack_from("<IIIBBH", raw, offset)
            name = strings[name:strings.index(b"\0", name)].decode()
            if not name or index == 0 or index >= len(sections):
                continue
            data = sections[index]
            file_offset = data[4] + address - data[3]
            result[name] = (file_offset, size, address)
    return result

def defaults(raw):
    symbols = elf_symbols(raw)
    checks = {}
    # PICO ioTag uses a six-bit pin field: portA tag = 0x40 | GPIO.
    # Actual pinned structs: statusLedConfig has ioTags[3], inversion;
    # beeperDevConfig has tag, inverted, openDrain, pad, u16 frequency.
    for name, expected in {
        "pgResetTemplate_statusLedConfig": bytes.fromhex("4c000001"),
        "pgResetTemplate_beeperDevConfig": bytes.fromhex("470100000000"),
    }.items():
        offset, size, address = symbols[name]
        actual = raw[offset:offset + size]
        require(actual == expected, f"{name}: {actual.hex()} != {expected.hex()}")
        checks[name] = {"address": hex(address), "bytes": actual.hex()}
    return checks, symbols

def uf2_contract(uf2, binary):
    require(len(uf2) % 512 == 0 and len(uf2) > 0, "UF2 block size")
    blocks = [struct.unpack_from("<8I", uf2, i) for i in range(0, len(uf2), 512)]
    require(all(b[0] == 0x0a324655 and b[1] == 0x9e5d5157 for b in blocks), "UF2 start magic")
    require(all(struct.unpack_from("<I", uf2, i + 508)[0] == 0x0ab16f30 for i in range(0, len(uf2), 512)), "UF2 end magic")
    require([b[5] for b in blocks] == list(range(len(blocks))), "UF2 block numbering")
    require(all(b[6] == len(blocks) for b in blocks), "UF2 total count")
    require(all(b[2] == 0x2000 and b[7] == 0xe48bff59 for b in blocks), "RP2350 ARM Secure family")
    require(all(b[4] == 256 for b in blocks), "UF2 payload size")
    start = min(b[3] for b in blocks)
    end = max(b[3] + b[4] for b in blocks)
    require(start == 0x10000000 and end <= 0x10200000, "RP2354B 2 MiB flash bounds")
    require([b[3] for b in blocks] == list(range(start, end, 256)), "UF2 contiguous addresses")
    payload = b"".join(uf2[i + 32:i + 288] for i in range(0, len(uf2), 512))
    require(payload[:len(binary)] == binary, "UF2 payload differs from BIN")
    return {"blocks": len(blocks), "family": "0xe48bff59", "start": hex(start), "end_exclusive": hex(end), "bin_bytes": len(binary), "payload_matches_bin": True}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", type=Path, default=PACKAGE / "artifacts")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--historical-elf", type=Path)
    args = ap.parse_args()
    files = {suffix: next(args.artifacts.glob("*" + suffix)) for suffix in [".elf", ".uf2", ".bin"]}
    raw = files[".elf"].read_bytes()
    checked_defaults, symbols = defaults(raw)
    layout = uf2_contract(files[".uf2"].read_bytes(), files[".bin"].read_bytes())
    controls = {}
    for label, name, replacements in [
        ("active_low_led", "pgResetTemplate_statusLedConfig", {3: 0}),
        ("open_drain_active_low_beeper", "pgResetTemplate_beeperDevConfig", {1: 0, 2: 1}),
    ]:
        offset, _, _ = symbols[name]
        changed = bytearray(raw)
        for byte, value in replacements.items():
            changed[offset + byte] = value
        try:
            defaults(changed)
        except ValueError as error:
            controls[label] = {"rejected": True, "reason": str(error)}
        else:
            raise ValueError(f"Negative control passed: {label}")
    if args.historical_elf:
        old = args.historical_elf.read_bytes()
        try:
            defaults(old)
        except ValueError as error:
            controls["historical_compiled_target"] = {"rejected": True, "sha256": hashlib.sha256(old).hexdigest(), "reason": str(error)}
        else:
            raise ValueError("Historical target unexpectedly has corrected defaults")
    report = {"status": "pass", "compiled_defaults": checked_defaults, "uf2": layout,
        "negative_controls": controls, "artifacts": {f.name: {"bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()} for f in files.values()},
        "physical_hardware_tested": False}
    result = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    print(result, end="")

if __name__ == "__main__":
    main()
