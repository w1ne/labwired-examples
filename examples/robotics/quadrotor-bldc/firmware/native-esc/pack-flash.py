#!/usr/bin/env python3
"""Package unchanged bootloader, application and EEPROM bytes in one loadable ELF."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

PACKAGE = Path(__file__).resolve().parent
START = 0x08000000
SIZE = 0x8000
INPUTS = {
    "AM32_F421_BOOTLOADER_PB4_V19.bin": (0, 4092, "0403603dac776f22c1e8d9b2a227f3fe9068e3e099893cb91243621fb49cc248"),
    "AM32_OPENESC_30_F421_2.21.bin": (0x1000, 27648, "51ed224be09069f0e105517ba7021c8a750f9608470e3d685a7e711767e69843"),
    "openesc30-bench-eeprom.bin": (0x7C00, 192, "c74c76fa2814bdd5fdeefcc8fadee99d142a6274d3d2ba50c53047d24fabe31b"),
}
APP_ELF_SHA = "2dc65fec5924f31548cc3041690b9b5a1645466832a09e46d012c33b14f8452d"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def loaded_bytes(elf):
    assert elf[:7] == b"\x7fELF\x01\x01\x01", "ELF32 little-endian required"
    entry, phoff = struct.unpack_from("<II", elf, 24)
    phsize, phnum = struct.unpack_from("<HH", elf, 42)
    memory = bytearray([0xFF] * SIZE)
    covered = set()
    for index in range(phnum):
        kind, offset, _virtual, address, filesz, memsz, _flags, _align = struct.unpack_from("<8I", elf, phoff + phsize * index)
        if kind != 1:
            continue
        assert START <= address and address + memsz <= START + SIZE, "load segment outside declared flash"
        assert filesz == memsz, "flash segment must not synthesize zero-fill memory"
        location = address - START
        assert not covered.intersection(range(location, location + filesz)), "overlapping load segments"
        covered.update(range(location, location + filesz))
        memory[location:location + filesz] = elf[offset:offset + filesz]
    assert covered == set(range(SIZE)), "entire declared image must have explicit load bytes"
    return entry, bytes(memory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, default=PACKAGE / "artifacts",
                        help="Application, bootloader and EEPROM inputs; exact hashes are checked")
    args = parser.parse_args()
    tool, out = args.toolchain_dir.resolve(), args.output_dir.resolve()
    inputs = args.artifacts_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    image = bytearray([0xFF] * SIZE)
    source = []
    for name, (offset, length, digest) in INPUTS.items():
        data = (inputs / name).read_bytes()
        assert len(data) == length and sha(data) == digest, name + " identity"
        image[offset:offset + length] = data
        source.append({"path": "artifacts/" + name, "address": START + offset, "bytes": length, "sha256": digest})
    application = inputs / "AM32_OPENESC_30_F421_2.21.elf"
    assert sha(application.read_bytes()) == APP_ELF_SHA
    stack, reset = struct.unpack_from("<II", image)
    assert 0x20000000 < stack <= 0x20004000 and reset & 1
    assert START <= reset < START + 0x1000
    binary = out / "OPENESC_30_F421_complete.bin"
    binary.write_bytes(image)
    script = out / "flash-container.ld"
    script.write_text("OUTPUT_ARCH(arm)\nENTRY(boot_reset_entry)\nboot_reset_entry = " + hex(reset) + ";\nMEMORY { FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 32K }\nSECTIONS { .flash_image : { KEEP(*(.flash_image)) } > FLASH }\n")
    objcopy, linker = tool / "bin/arm-none-eabi-objcopy", tool / "bin/arm-none-eabi-ld"
    commands = [
        [str(objcopy), "-I", "binary", "-O", "elf32-littlearm", "-B", "arm", "--rename-section", ".data=.flash_image,alloc,load,readonly,data,contents", binary.name, "flash-image.o"],
        [str(linker), "-T", script.name, "--just-symbols=" + str(application), "-o", "OPENESC_30_F421_complete.elf", "flash-image.o"],
        [str(objcopy), "-O", "ihex", "OPENESC_30_F421_complete.elf", "OPENESC_30_F421_complete.hex"],
    ]
    for command in commands:
        subprocess.run(command, cwd=out, check=True)
    elf = out / "OPENESC_30_F421_complete.elf"
    entry, loaded = loaded_bytes(elf.read_bytes())
    assert entry == reset and loaded == image, "container changed native flash bytes or boot entry"
    artifacts = [{"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
                 for path in sorted(out.glob("OPENESC_30_F421_complete.*"))]
    receipt = {"schema": "labwired.native-flash-container.v1", "sources": source,
               "applicationSymbolElf": {"path": str(application), "sha256": APP_ELF_SHA},
               "commands": commands, "initialStack": stack, "bootEntry": reset,
               "flashStart": START, "flashBytes": SIZE, "fillByte": 255,
               "loadBytesEqualSourceComposition": True, "artifacts": artifacts,
               "scope": "Standard loadable ELF container of unchanged vendor bootloader, native application and explicit EEPROM fixture. No instruction patch or simulated firmware replacement. Application symbols are retained as absolute symbols for inspection; complete-image DWARF is not provided."}
    (out / "flash-container-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("PASS: native boot entry and all 32768 load bytes match their source images")


if __name__ == "__main__":
    main()
