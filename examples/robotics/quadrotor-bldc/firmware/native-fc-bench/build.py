#!/usr/bin/env python3
"""Build the physical RP2354B motor bench from pinned local source archives.

Requires Linux x86-64, Python3.12+, CMake, make and a host C++ compiler.
The optional toolchain download is SHA256 checked. This script does not flash.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
import urllib.request

PACKAGE = Path(__file__).resolve().parent
VERSIONS = json.loads((PACKAGE / "source-versions.json").read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, *, env, cwd=None):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)

def output(args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()

def unpack(name, dest):
    archive = PACKAGE / "source" / name
    if sha(archive) != VERSIONS["source_archives"][name]:
        raise RuntimeError(f"Source checksum mismatch: {archive}")
    dest.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="data")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work-dir", required=True, type=Path)
    ap.add_argument("--toolchain", type=Path, help="Exact Arm GNU13.3.Rel1 directory")
    ap.add_argument("--jobs", type=int, default=2)
    args = ap.parse_args()
    work = args.work_dir.resolve()
    if args.jobs < 1:
        raise RuntimeError("--jobs must be positive")
    if work.exists() and any(work.iterdir()):
        raise RuntimeError("Use an empty work directory; prior objects must not affect reproduction")
    work.mkdir(parents=True, exist_ok=True)
    if work == PACKAGE or PACKAGE in work.parents:
        raise RuntimeError("Build outside the source package")
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(VERSIONS["source_date_epoch"])
    if sha(PACKAGE / "source/upstream-dshot.pio") != VERSIONS["pio_source"]["sha256"]:
        raise RuntimeError("Pinned PIO source mismatch")
    if sha(PACKAGE / "src/dshot.pio") != VERSIONS["pio_source"]["local_source_sha256"]:
        raise RuntimeError("Identify the modified bench PIO source before building")
    sdk = work / "pico-sdk"
    picotool_source = work / "picotool-source"
    unpack("pico-sdk-ee68c78d0afa.tar.gz", sdk)
    unpack("picotool-de8ae5ac334e.tar.gz", picotool_source)
    toolchain = args.toolchain.resolve() if args.toolchain else work / "arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi"
    if not toolchain.exists():
        archive = work / "toolchain.tar.xz"
        with urllib.request.urlopen(VERSIONS["gcc_archive_url"]) as src, archive.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if sha(archive) != VERSIONS["gcc_archive_sha256"]:
            raise RuntimeError("Arm toolchain archive checksum mismatch")
        with tarfile.open(archive) as tar:
            tar.extractall(work, filter="data")
    gcc = toolchain / "bin/arm-none-eabi-gcc"
    if output([gcc, "-dumpversion"]) != VERSIONS["gcc_version"]:
        raise RuntimeError("Exact GCC13.3.1 is required")
    env["PATH"] = str(toolchain / "bin") + os.pathsep + env["PATH"]
    env["PICO_SDK_PATH"] = str(sdk)
    env["PICO_TOOLCHAIN_PATH"] = str(toolchain)
    picotool_build = work / "picotool-build"
    picotool_install = work / "picotool-install"
    run(["cmake", "-S", picotool_source, "-B", picotool_build,
         f"-DPICO_SDK_PATH={sdk}", "-DPICOTOOL_NO_LIBUSB=1", "-DPICOTOOL_FLAT_INSTALL=1",
         f"-DCMAKE_INSTALL_PREFIX={picotool_install}"], env=env)
    run(["cmake", "--build", picotool_build, "--parallel", args.jobs], env=env)
    run(["cmake", "--install", picotool_build], env=env)
    picotool = picotool_install / "picotool/picotool"
    tool_version = output([picotool, "version"])
    if "2.1.1" not in tool_version:
        raise RuntimeError(f"Wrong picotool version: {tool_version}")
    obj = work / "obj"
    configure = ["cmake", "-S", PACKAGE, "-B", obj, "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
        f"-DBENCH_REPRO_ROOT={work}",
        f"-Dpicotool_DIR={picotool_install}/picotool", "-DPICO_PLATFORM=rp2350-arm-s",
        "-DPICO_BOARD=openfc_lite_rp2354b_bench"]
    start = time.monotonic()
    run(configure, env=env)
    run(["cmake", "--build", obj, "--parallel", args.jobs], env=env)
    artifacts = work / "artifacts"
    artifacts.mkdir()
    hashes = {}
    for ext in ["elf", "uf2", "bin", "elf.map"]:
        name = "openfc_motor_bench." + ext
        source = obj / name
        if not source.is_file():
            raise RuntimeError(f"Missing native build artifact: {source}")
        dest = artifacts / name
        shutil.copyfile(source, dest)
        hashes[name] = {"bytes": dest.stat().st_size, "sha256": sha(dest)}
    run(["python3", PACKAGE / "verify_artifacts.py", "--artifacts", artifacts,
         "--output", artifacts / "artifact-contract.json"], env=env)
    identity = output([picotool, "info", "-a", artifacts / "openfc_motor_bench.elf"])
    (artifacts / "picotool-info.txt").write_text(identity + "\n")
    receipt = {"status": "built-not-runtime-qualified", "source": VERSIONS,
        "source_files": {str(q.relative_to(PACKAGE)): sha(q) for q in
                         sorted([PACKAGE / name for name in ["CMakeLists.txt", "build.py", "verify_artifacts.py"]]
                         + [q for root in ["src", "boards"] for q in (PACKAGE / root).rglob("*") if q.is_file()])},
        "configure": list(map(str, configure)), "seconds": time.monotonic() - start,
        "gcc": output([gcc, "--version"]).splitlines()[0], "picotool": tool_version,
        "picotool_executable_sha256": sha(picotool), "artifacts": hashes,
        "physical_hardware_tested": False}
    (artifacts / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    main()
