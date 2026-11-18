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

def compiled_contract(raw, binary):
    symbols = elf_symbols(raw)
    checks = {}
    expected = {"motor_pin": struct.pack("<4I", 31, 30, 29, 28),
                "g_bench": struct.pack("<42I", 1, *([0] * 41))}
    for name, data in expected.items():
        offset, size, address = symbols[name]
        actual = raw[offset:offset + size]
        require(actual == data, f"Wrong compiled {name} contract")
        checks[name] = {"address": hex(address), "size": size, "initial_bytes": actual.hex()}
    sp, pc = struct.unpack_from("<II", binary)
    entry = struct.unpack_from("<I", raw, 24)[0]
    require(0x20000000 < sp <= 0x20082000 and sp % 8 == 0, "Native520KiB stack bounds")
    require(pc & 1 and 0x10000000 <= pc < 0x10200000, "Native flash Thumb reset vector")
    require(entry & 1 and 0x10000000 <= entry < 0x10200000, "Native flash Thumb ELF entry")
    checks["vectors"] = {"sp": hex(sp), "reset_pc": hex(pc), "elf_entry": hex(entry)}
    return checks, symbols

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", type=Path, default=PACKAGE / "artifacts")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    files = {suffix: args.artifacts / ("openfc_motor_bench" + suffix)
             for suffix in [".elf", ".uf2", ".bin"]}
    raw = files[".elf"].read_bytes()
    binary = files[".bin"].read_bytes()
    uf2 = files[".uf2"].read_bytes()
    compiled, symbols = compiled_contract(raw, binary)
    layout = uf2_contract(uf2, binary)
    controls = {}
    for label, name, byte in [("wrong_motor_pad", "motor_pin", 0),
                              ("nonzero_startup_command", "g_bench", 4 * 21)]:
        offset, _, _ = symbols[name]
        changed = bytearray(raw); changed[offset + byte] ^= 1
        try:
            compiled_contract(changed, binary)
        except ValueError as error:
            controls[label] = {"rejected": True, "reason": str(error)}
        else:
            raise ValueError(f"Negative control accepted: {label}")
    changed = bytearray(uf2); changed[32] ^= 1
    try:
        uf2_contract(changed, binary)
    except ValueError as error:
        controls["corrupt_flash_byte"] = {"rejected": True, "reason": str(error)}
    else:
        raise ValueError("Corrupt UF2 accepted")
    report = {"status": "pass", "compiled_contract": compiled, "uf2": layout,
        "negative_controls": controls,
        "artifacts": {f.name: {"bytes": f.stat().st_size,
                     "sha256": hashlib.sha256(f.read_bytes()).hexdigest()} for f in files.values()},
        "scope": "Artifact structure, native pads and zero startup state only; runtime and hardware qualification are separate.",
        "physical_hardware_tested": False}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")

if __name__ == "__main__":
    main()
