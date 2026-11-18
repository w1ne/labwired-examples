#!/usr/bin/env python3
"""Run the physical profile through the pinned real-stack byte fixture."""
from pathlib import Path
import argparse
import os
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--iolinki", type=Path, default=root / "master/.deps/iolinki")
parser.add_argument("--master", type=Path, default=root / "master/.deps/labwired-core/third_party/iolinki-master")
args = parser.parse_args()
iolinki, master = args.iolinki.resolve(), args.master.resolve()
output = root / "master/build/protocol-profile"
output.parent.mkdir(exist_ok=True)
device_sources = ["device", "phy_generic", "phy_virtual", "dll", "isdu", "events",
                  "platform", "params", "data_storage", "device_info",
                  "platform_stubs", "frame", "crc"]
sources = [str(p) for p in sorted((master / "src").glob("*.c"))]
sources += [str(iolinki / "src" / (name + ".c")) for name in device_sources]
sources += [str(iolinki / "src/platform/linux/time_utils.c"),
            str(iolinki / "src/platform/linux/nvm_mock.c")]
subprocess.run([os.environ.get("HOSTCC", "cc"), "-std=c11", "-D_POSIX_C_SOURCE=200809L",
                "-Wall", "-Wextra", "-Werror", "-O1", "-g",
                "-I" + str(root / "common"), "-I" + str(master / "tests"),
                "-I" + str(master / "include"), "-I" + str(iolinki / "include"),
                str(root / "tests/protocol_profile.c"), *sources,
                "-lcmocka", "-o", str(output)], check=True)
subprocess.run([str(output)], check=True, cwd=output.parent)
print("PASS: four TYPE_2_1 one-byte input profiles through real master/device stacks")
print("Scope: host byte protocol only; fixture timing enforcement disabled; no physical HAL/PHY or concurrent three-MCU run")
