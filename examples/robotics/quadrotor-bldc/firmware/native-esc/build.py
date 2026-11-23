#!/usr/bin/env python3
"""Rebuild the exact F421 application and PB4 bootloader from bundled source."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import tarfile
import time

PACKAGE = Path(__file__).resolve().parent
TOOLS = {
    "bin/arm-none-eabi-gcc": "a14075417c1aad6236a6203c8521408fa7d55d8b20e190c9c3b51bec6b5c153f",
    "bin/arm-none-eabi-objcopy": "b5b2370f52d9af2ed124c2583d18abac410faca70cc17abeefd2f1ad5cffcfe5",
    "libexec/gcc/arm-none-eabi/10.3.1/cc1": "aa5a504b019372a65cbc1ad96861a5c7a4048775d0e2f6ee65c6acc96f9ff8b4",
}
APP = {
    ".elf": "2dc65fec5924f31548cc3041690b9b5a1645466832a09e46d012c33b14f8452d",
    ".bin": "51ed224be09069f0e105517ba7021c8a750f9608470e3d685a7e711767e69843",
    ".hex": "66b0f22b0bef9b2c52d27ffb75cfa32748f5f47254e229e11a513877a3f5c7b0",
}
BOOT = {
    ".bin": "0403603dac776f22c1e8d9b2a227f3fe9068e3e099893cb91243621fb49cc248",
    ".hex": "4e6d7fe4f0ab68493dc733c31a6dbbf7a5e098fc445b9575ada3ecefd6e2407f",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True,
                        help="New or empty directory for source extraction and build outputs")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--source-dir", type=Path,
                        help="Expanded source bundle containing am32-f421 and am32-bootloader-f421; edits here are the actual build inputs")
    args = parser.parse_args()
    tool, work = args.toolchain_dir.resolve(), args.work_dir.resolve()
    if work.exists() and any(work.iterdir()):
        raise SystemExit("The work directory must be empty; existing files are not removed.")
    work.mkdir(parents=True, exist_ok=True)
    if args.jobs < 1:
        raise SystemExit("--jobs must be positive")
    for relative, expected in TOOLS.items():
        if sha(tool / relative) != expected:
            raise SystemExit("Unexpected toolchain executable: " + relative)
    records = json.loads((PACKAGE / "sources/source-archives.json").read_text())
    receipt = {
        "schema": "labwired.native-esc-build.v1", "toolchain": json.loads(
            (PACKAGE / "sources/toolchain.json").read_text()),
        "compilerVersion": subprocess.check_output(
            [str(tool / "bin/arm-none-eabi-gcc"), "--version"], text=True),
        "runs": [], "scope": "Application ELF/BIN/HEX identity and bootloader BIN/HEX identity. Bootloader debug ELF paths and temporary assembler filenames are not normalized by the unchanged vendor source.",
    }
    for record in records:
        archive = PACKAGE / "sources" / record["path"]
        if sha(archive) != record["sha256"]:
            raise SystemExit("Source archive hash mismatch: " + archive.name)
        if args.source_dir is not None:
            expanded = args.source_dir.resolve() / record["name"]
            if not expanded.is_dir():
                raise SystemExit("Expanded source is missing: " + str(expanded))
            shutil.copytree(expanded, work / record["name"])
        else:
            with tarfile.open(archive, "r:gz") as source:
                source.extractall(work, filter="data")
        is_app = record["name"] == "am32-f421"
        root = work / record["name"]
        target = "OPENESC_30_F421" if is_app else "AM32_F421_BOOTLOADER_PB4"
        prefix_map = " -ffile-prefix-map=" + str(root) + "=. -ffile-prefix-map=" + str(tool) + "=/opt/gcc-arm-none-eabi"
        if is_app:
            flags = "CFLAGS_COMMON=$(CFLAGS_BASE)" + prefix_map + " -Wa,--debug-prefix-map=" + str(root) + "=."
        else:
            # The bootloader uses CFLAGS_BASE directly in its generated target.
            flags = "CFLAGS_BASE=-fsingle-precision-constant -fomit-frame-pointer -ffast-math --specs=nosys.specs -IInc -g3 -Os -ffunction-sections -fdata-sections -funsigned-char -flto -Wall -Wextra -Wundef -Werror -Wno-unused-parameter -include Inc/targets.h" + prefix_map
        cmd = ["make", "-j" + str(args.jobs), target,
               "ARM_SDK_PREFIX=" + str(tool / "bin/arm-none-eabi-"),
               "PART=AT32F421G8U7", "OBJ=obj", flags]
        start = time.monotonic()
        log = work / (record["name"] + "-build.log")
        with log.open("w") as stream:
            result = subprocess.run(cmd, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
        source_files = [{"path": str(p.relative_to(root)), "sha256": sha(p)}
                        for p in sorted(root.rglob("*")) if p.is_file() and "obj" not in p.relative_to(root).parts]
        run = {"source": record, "actualSourceFiles": source_files, "command": cmd, "cwd": str(root),
               "exit": result.returncode, "seconds": time.monotonic() - start,
               "log": log.name, "artifacts": {}}
        receipt["runs"].append(run)
        if result.returncode == 0:
            basename = "AM32_OPENESC_30_F421_2.21" if is_app else "AM32_F421_BOOTLOADER_PB4_V19"
            expected = APP if is_app else BOOT
            for suffix in [".elf", ".bin", ".hex"]:
                path = root / "obj" / (basename + suffix)
                run["artifacts"][suffix] = {
                    "path": str(path.relative_to(work)), "bytes": path.stat().st_size,
                    "sha256": sha(path), "expectedSha256": expected.get(suffix),
                }
            run["reproduced"] = all(run["artifacts"][suffix]["sha256"] == digest
                                     for suffix, digest in expected.items())
        (work / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if result.returncode or not run.get("reproduced"):
            raise SystemExit("Build or artifact identity failed; inspect " + str(work / "build-receipt.json"))
    artifacts = work / "artifacts"
    artifacts.mkdir()
    for run in receipt["runs"]:
        for item in run["artifacts"].values():
            path = work / item["path"]
            shutil.copy2(path, artifacts / path.name)
    shutil.copy2(PACKAGE / "artifacts/openesc30-bench-eeprom.bin", artifacts)
    command = ["python3", str(PACKAGE / "pack-flash.py"), "--toolchain-dir", str(tool),
               "--artifacts-dir", str(artifacts), "--output-dir", str(work / "complete")]
    start = time.monotonic()
    with (work / "complete-build.log").open("w") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    complete_expected = {
        ".elf": "c6ae7b29e1fe35dd56070435aa271b18ec9cba77ec5329f092b3296776664e2a",
        ".bin": "aa0ec2324ea7e5011a49d4ac2e722ec601599d3837de9004f06e13e80c6a07ab",
        ".hex": "c8a51dd0dab4fb62260ed14b5b2716e4a01dce383626f31d72ca6be820075d78",
    }
    complete = {"command": command, "exit": result.returncode,
                "seconds": time.monotonic() - start, "artifacts": {}}
    for suffix, expected in complete_expected.items():
        path = work / "complete" / ("OPENESC_30_F421_complete" + suffix)
        if path.is_file():
            complete["artifacts"][suffix] = {"path": str(path.relative_to(work)),
                "bytes": path.stat().st_size, "sha256": sha(path), "expectedSha256": expected}
    complete["reproduced"] = result.returncode == 0 and all(
        complete["artifacts"].get(suffix, {}).get("sha256") == digest
        for suffix, digest in complete_expected.items())
    receipt["complete"] = complete
    (work / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not complete["reproduced"]:
        raise SystemExit("Complete image failed; inspect " + str(work / "build-receipt.json"))
    print("PASS: application, bootloader flash and complete ELF/BIN/HEX reproduce")
    print(work / "build-receipt.json")


if __name__ == "__main__":
    main()
