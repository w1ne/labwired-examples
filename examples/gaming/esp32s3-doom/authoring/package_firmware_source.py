#!/usr/bin/env python3
"""Package exact committed project sources; never include outputs or caches."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
COMMIT = "188016118ac91dae6fca7cac18ba730b7dd271bd"
PREFIX = "examples/gaming/esp32s3-doom/"
EXTRA = {
    "README.md", "firmware/build-inputs.json", "firmware/build.sh",
    "firmware/prepare_wad.py", "firmware/record_build.py",
    "firmware/source-provenance.json", "firmware/artifacts/build-manifest.json",
    "authoring/verify_runtime.py", "validation/runtime/paired-acceptance.json",
    "validation/final-source-rebuild-comparison.json",
    "validation/recipe-rebuild-comparison.json",
}

def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def committed(path):
    return subprocess.check_output(["git", "-C", str(REPO), "show", COMMIT + ":" + PREFIX + path])

def make_archive(members, epoch):
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0, compresslevel=9) as zipped:
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, (data, mode) in sorted(members.items()):
                entry = tarfile.TarInfo("esp32s3-doom/" + name)
                entry.size, entry.mode, entry.mtime = len(data), mode, epoch
                entry.uid = entry.gid = 0
                archive.addfile(entry, io.BytesIO(data))
    return buffer.getvalue()

def main():
    tree = subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", COMMIT, "--", PREFIX], text=True)
    members = {}
    for line in tree.splitlines():
        meta, path = line.split("\t", 1)
        name = path[len(PREFIX):]
        if name.startswith(("firmware/source/", "runtime/")) or name in EXTRA:
            members[name] = (committed(name), int(meta.split()[0], 8) & 0o777)
    assert EXTRA <= members.keys()
    members["SOURCE_ARCHIVE.md"] = ((ROOT / "firmware/SOURCE_ARCHIVE.md").read_bytes(), 0o644)
    reviewed = json.loads(members["firmware/source-provenance.json"][0])
    expected = json.loads(members["firmware/artifacts/build-manifest.json"][0])
    for table in (reviewed["packaged_files_sha256"], expected["source_files_sha256"]):
        for name, digest in table.items():
            assert identity(members["firmware/source/" + name][0])["sha256"] == digest, name
    actual_sources = {name.removeprefix("firmware/source/") for name in members if name.startswith("firmware/source/")}
    assert actual_sources == set(reviewed["packaged_files_sha256"]) | {".gitignore"}, "Source inventory changed"
    epoch = int(subprocess.check_output(["git", "-C", str(REPO), "show", "-s", "--format=%ct", COMMIT], text=True))
    data = make_archive(members, epoch)
    assert data == make_archive(members, epoch), "Archive is not deterministic"
    assert len(data) <= 16 * 1024 * 1024
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        assert len(archive.getmembers()) == len(members)
        for item in archive:
            assert item.isfile() and item.name.startswith("esp32s3-doom/")
            name = item.name.removeprefix("esp32s3-doom/")
            assert archive.extractfile(item).read() == members[name][0]
    output = ROOT / "firmware/doom-project-source.tar.gz"
    output.write_bytes(data)
    entry = "firmware/source/main/main.c"
    manifest = {
        "schema": 1, "source_commit": COMMIT,
        "archive": {"path": "firmware/doom-project-source.tar.gz", **identity(data)},
        "entry": {"path": entry, "editor_profile": "c", "editor_path": "src/main.c", **identity(members[entry][0])},
        "build_inputs": expected["inputs"],
        "expected_artifacts": {name: expected["files"][name] for name in ["doom-s3.elf", "doom-s3-flash.bin"]},
        "verification": {"deterministic_replay": True, "all_members_match_source": True, "reviewed_source_files": len(reviewed["packaged_files_sha256"]), "fresh_compiler_replay": False},
        "files": {name: {**identity(content), "mode": oct(mode)} for name, (content, mode) in sorted(members.items())},
    }
    (ROOT / "firmware/source-archive.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"archive": manifest["archive"], "entry": manifest["entry"], "members": len(members), "reviewed_source_files": len(reviewed["packaged_files_sha256"])}, indent=2))

if __name__ == "__main__":
    main()
