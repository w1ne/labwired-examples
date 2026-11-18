#!/usr/bin/env python3
"""Create the complete editable external-build source archive deterministically."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
NAME = "openesc30-native-source-v1.tar.gz"
ENTRY = "am32-f421/Src/main.c"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "sources")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    records = json.loads((HERE / "sources/source-archives.json").read_text())
    with tempfile.TemporaryDirectory(prefix="openesc30-source-") as temporary:
        root = Path(temporary)
        for record in records:
            source = HERE / "sources" / record["path"]
            if sha(source.read_bytes()) != record["sha256"]:
                raise SystemExit("Source archive identity differs: " + record["path"])
            with tarfile.open(source, "r:gz") as archive:
                archive.extractall(root, filter="data")
        for relative in [
            "build.py", "pack-flash.py", "package-source.py",
            "sources/source-archives.json", "sources/toolchain.json",
            "sources/openesc30-native-target.patch.gz", "sources/AM32-LICENSE",
            "sources/BOOTLOADER-LICENSE", "artifacts/openesc30-bench-eeprom.bin",
            "artifacts/openesc30-bench-eeprom.json",
        ] + ["sources/" + record["path"] for record in records]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / relative, target)
        (root / "BUILD.md").write_text(
            "# Native OPENESC30 complete-image source\n\n"
            "The editable entry is am32-f421/Src/main.c. The build copies these expanded source trees into a new empty work directory and compiles them. It does not replace this entry with a hidden simulator fixture.\n\n"
            "Use the exact xPack Arm GNU 10.3.1-2.3 compiler identified in sources/toolchain.json, Python 3.12+ and GNU make. From this extracted directory run:\n\n"
            "    python3 build.py --source-dir . --toolchain-dir /absolute/toolchain --work-dir /absolute/new-empty-build\n\n"
            "The command reproduces the native AM32 application, unchanged PB4 bootloader and complete ELF/BIN/HEX. The complete image uses the explicit EEPROM bytes in artifacts/. No binary application or bootloader is needed as a build input. All image identities are checked, and build-receipt.json records the actual expanded source files and output hashes.\n\n"
            "Application source is pinned to OpenDrone-hw/AM32 upstream 5f8978eeb618c14bb396af7ac049d2a5e7b5a508 plus the included native target patch (source commit 19df1ecfef4982302cacdd35bb0d921ceac83217). Bootloader source is am32-firmware/AM32-bootloader a340e23f4fe270bf7a767156d3c24b10f22b521a. Original licenses and archives remain included.\n\n"
            "This is the exact recorded engineering candidate. Source changes require a new artifact identity and runtime qualification before a saved Lab can use them. The source archive alone does not claim physical or five-node acceptance.\n"
        )
        files = []
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append({"path": path.relative_to(root).as_posix(),
                              "bytes": path.stat().st_size,
                              "sha256": sha(path.read_bytes())})
        target = out / NAME
        with target.open("wb") as stream:
            with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    for path in sorted(root.rglob("*")):
                        relative = path.relative_to(root).as_posix()
                        info = archive.gettarinfo(str(path), arcname=relative)
                        info.uid = info.gid = 0
                        info.uname = info.gname = ""
                        info.mtime = 0
                        if path.is_file():
                            with path.open("rb") as content:
                                archive.addfile(info, content)
                        else:
                            archive.addfile(info)
        entry = next(record for record in files if record["path"] == ENTRY)
        tree = "".join(f"{item['path']}\0{item['sha256']}\0{item['bytes']}\n" for item in files)
        receipt = {
            "schema": "labwired.native-source-bundle.v1", "archive": NAME,
            "bytes": target.stat().st_size, "sha256": sha(target.read_bytes()),
            "entry": entry, "files": files, "treeSha256": sha(tree.encode()),
            "treeAlgorithm": "SHA256 of sorted path + NUL + SHA256 + NUL + decimal bytes + LF",
            "buildCommand": "python3 build.py --source-dir . --toolchain-dir /absolute/toolchain --work-dir /absolute/new-empty-build",
            "scope": "Complete corresponding application and bootloader sources, explicit EEPROM, source/flash build tools, pinned compiler identification, original archives, target patch and licenses. Compiler binaries are downloaded separately by their pinned hash.",
        }
        (out / "source-bundle.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({key: receipt[key] for key in ["archive", "bytes", "sha256", "entry"]}, indent=2))

if __name__ == "__main__":
    main()
