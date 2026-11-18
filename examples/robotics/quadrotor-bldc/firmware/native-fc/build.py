#!/usr/bin/env python3
"""Build the physical RP2354B target in a separate output directory.

Linux x86-64. Python 3.12+, Git, GNU make, CMake, a native C++ compiler and
libusb development files are needed. Downloads are immutable and checked.
No firmware is flashed by this script.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request

PACKAGE = Path(__file__).resolve().parent
VERSIONS = json.loads((PACKAGE / "source-versions.json").read_text())
TARGET = "OPENFC_LITE_REV2_LW1"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, cwd=None, env=None):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)

def output(args, cwd=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, text=True).strip()

def exact_tree(path, url, commit):
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        if any(path.iterdir()):
            raise RuntimeError(f"Refusing nonempty non-Git directory: {path}")
        run(["git", "init", path])
        run(["git", "remote", "add", "origin", url], path)
        run(["git", "fetch", "--depth=1", "origin", commit], path)
        run(["git", "checkout", "--detach", "FETCH_HEAD"], path)
    if output(["git", "rev-parse", "HEAD"], path) != commit:
        raise RuntimeError(f"Wrong source commit at {path}")
    run(["git", "diff", "--quiet", "--ignore-submodules=all", "HEAD", "--"], path)
    if output(["git", "ls-files", "--others", "--exclude-standard"], path):
        raise RuntimeError(f"Untracked source files can affect the build: {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work-dir", required=True, type=Path)
    ap.add_argument("--source-tree", type=Path, help="Reuse an exact clean source checkout")
    ap.add_argument("--toolchain", type=Path, help="Exact Arm GNU 13.3.Rel1 directory")
    ap.add_argument("--picotool", type=Path, help="Existing picotool 2.1.1 executable")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    work = args.work_dir.resolve()
    source = args.source_tree.resolve() if args.source_tree else work / "betaflight"
    for path in [work, source, PACKAGE]:
        if not re.fullmatch(r"[/A-Za-z0-9_.-]+", str(path)):
            raise RuntimeError("GNU make paths must contain only letters, digits, /, _, -, .")
    if args.jobs < 1:
        raise RuntimeError("--jobs must be positive")
    work.mkdir(parents=True, exist_ok=True)
    obj = work / "obj"
    if obj.exists():
        raise RuntimeError("Use a new --work-dir; existing objects must not affect reproduction")
    config_hash = hashlib.sha256(b"".join((PACKAGE / "configs" / TARGET / n).read_bytes()
        for n in ["config.h", "pico_flash_mem.ld"])).hexdigest()
    if config_hash != VERSIONS["config_content_sha256"]:
        raise RuntimeError("Config differs from source-versions.json; identify a new build")
    run(["python3", PACKAGE / "verify_native_pins.py"])
    exact_tree(source, VERSIONS["source_repo"], VERSIONS["source_commit"])
    run(["git", "submodule", "update", "--init", "--checkout", "--depth=1", "--",
         "lib/modules/pico-sdk", "lib/modules/dronecan/libcanard"], source)
    sdk = source / "lib/modules/pico-sdk"
    run(["git", "submodule", "update", "--init", "--checkout", "--depth=1", "--", "lib/tinyusb"], sdk)
    for tree, expected in [(sdk, VERSIONS["pico_sdk_commit"]),
            (sdk / "lib/tinyusb", VERSIONS["tinyusb_commit"]),
            (source / "lib/modules/dronecan/libcanard", VERSIONS["libcanard_commit"])]:
        if output(["git", "rev-parse", "HEAD"], tree) != expected:
            raise RuntimeError(f"Submodule mismatch: {tree}")
        run(["git", "diff", "--quiet", "HEAD", "--"], tree)
    toolchain = args.toolchain.resolve() if args.toolchain else work / "arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi"
    if not toolchain.exists():
        archive = work / "toolchain.tar.xz"
        with urllib.request.urlopen(VERSIONS["gcc_archive_url"]) as response, archive.open("wb") as dest:
            shutil.copyfileobj(response, dest)
        if sha(archive) != VERSIONS["gcc_archive_sha256"]:
            raise RuntimeError("Arm toolchain archive checksum mismatch")
        with tarfile.open(archive) as tar:
            tar.extractall(work, filter="data")
    gcc = toolchain / "bin/arm-none-eabi-gcc"
    if output([gcc, "-dumpversion"]) != VERSIONS["gcc_version"]:
        raise RuntimeError("Exact GCC 13.3.1 is required")
    picotool = args.picotool.resolve() if args.picotool else work / "picotool-build/picotool"
    if not picotool.exists():
        picotool_source = work / "picotool-source"
        exact_tree(picotool_source, "https://github.com/raspberrypi/picotool", VERSIONS["picotool_commit"])
        run(["cmake", "-S", picotool_source, "-B", picotool.parent, f"-DPICO_SDK_PATH={sdk}"])
        run(["cmake", "--build", picotool.parent, "--parallel", str(args.jobs)])
    version = output([picotool, "version"])
    if "2.1.1" not in version:
        raise RuntimeError(f"Exact picotool 2.1.1 required, got {version}")
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(VERSIONS["source_date_epoch"])
    revision = config_hash[:7]
    command = ["make", f"-j{args.jobs}", f"CONFIG={TARGET}", f"CONFIG_DIR={PACKAGE}",
        f"OBJECT_DIR={obj / 'main'}", f"BIN_DIR={obj}", f"ARM_SDK_DIR={toolchain}",
        f"PICOTOOL={picotool}", f"CONFIG_REVISION={revision}",
        f"CONFIG_REVISION_DEFINE=-D'__CONFIG_REVISION__=\"{revision}\"'",
        f"EXTRA_FLAGS=-ffile-prefix-map={source}=/src/betaflight -ffile-prefix-map={PACKAGE}=/src/native-fc",
        "uf2"]
    start = time.monotonic()
    run(command, source, env)
    # The upstream phony goals each launch recursive make. Run them serially
    # so separate recursive processes cannot race while writing the same ELF.
    binary_command = command[:-1] + ["binary"]
    run(binary_command, source, env)
    artifacts = work / "artifacts"
    artifacts.mkdir()
    files = [obj / "main" / f"betaflight_RP2350B_{TARGET}.elf",
             obj / "main" / f"betaflight_RP2350B_{TARGET}.map"]
    files += list(obj.glob(f"betaflight_*_RP2350B_{TARGET}.uf2"))
    files += list(obj.glob(f"betaflight_*_RP2350B_{TARGET}.bin"))
    if len(files) != 4:
        raise RuntimeError(f"Expected ELF/map/UF2/bin, found {files}")
    hashes = {}
    for source_file in files:
        dest = artifacts / source_file.name
        shutil.copyfile(source_file, dest)
        hashes[dest.name] = {"bytes": dest.stat().st_size, "sha256": sha(dest)}
    run(["python3", PACKAGE / "verify_artifacts.py", "--artifacts", artifacts,
         "--output", artifacts / "artifact-contract.json"])
    receipt = {"status": "pass", "source": VERSIONS, "argv": [command, binary_command],
        "source_date_epoch": env["SOURCE_DATE_EPOCH"], "seconds": time.monotonic() - start,
        "gcc": output([gcc, "--version"]).splitlines()[0], "picotool": version,
        "picotool_executable_sha256": sha(picotool), "artifacts": hashes,
        "physical_hardware_tested": False}
    (artifacts / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    main()
