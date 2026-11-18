#!/usr/bin/env python3
"""Rebuild the exact native PCB STEP/STL/GLB outputs with KiCad 10.

Uses the package's checked-in model directories. Does not refill or alter copper.
Outputs include the source PCB hash, model directory, command and tool version.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "cad/evidence/model-datum-correction-20261118"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def binary_stl(path):
    """Pack the native ASCII triangles as standard float32 binary STL."""
    raw = path.read_bytes()
    triangles, normal, vertices = [], None, []
    max_coordinate_rounding = 0.0
    for line in raw.decode("ascii").splitlines():
        fields = line.strip().split()
        if fields[:2] == ["facet", "normal"]:
            assert normal is None and not vertices
            normal = list(map(float, fields[2:]))
            assert len(normal) == 3
        elif fields[:1] == ["vertex"]:
            vertex = list(map(float, fields[1:]))
            assert len(vertex) == 3 and normal is not None
            for value in vertex:
                rounded = struct.unpack("<f", struct.pack("<f", value))[0]
                max_coordinate_rounding = max(max_coordinate_rounding, abs(value - rounded))
            vertices.extend(vertex)
        elif fields == ["endfacet"]:
            assert normal is not None and len(vertices) == 9
            triangles.append(struct.pack("<12fH", *normal, *vertices, 0))
            normal, vertices = None, []
    assert normal is None and not vertices and triangles
    assert max_coordinate_rounding < 0.00001
    header = b"LabWired native KiCad triangles; binary encoding only".ljust(80, b"\0")
    path.write_bytes(header + struct.pack("<I", len(triangles)) + b"".join(triangles))
    return {"method": "ASCII-to-binary STL; same triangle order and coordinates rounded to IEEE754 float32", "sourceBytes": len(raw), "sourceSha256": hashlib.sha256(raw).hexdigest(), "triangles": len(triangles), "maximumCoordinateRoundingMm": max_coordinate_rounding}

def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    version = subprocess.check_output(["kicad-cli", "version"], text=True).strip()
    jobs = [
        ("esc", "esc-4in1", "4in1.kicad_pcb", "fabrication-review", [], [
            ("esc-board-populated", "step", []),
            ("esc-board-populated", "glb", []),
        ]),
        ("fc", "flight-controller-openfc-lite-rev2-lw1", "hardware/OpenFC.kicad_pcb", "mechanical-review", ["--user-origin", "153.0912x87.1597mm"], [
            ("fc-substrate", "step", ["--board-only"]),
            ("fc-populated", "step", []),
            ("fc-components", "stl", ["--no-board-body"]),
        ]),
    ]
    receipts = []
    for label, folder, board, outdir, origin, exports in jobs:
        base = ROOT / "hardware" / folder
        pcb = base / board
        models = base / "reviewed-models"
        env = os.environ.copy()
        for key in ("KICAD10_3DMODEL_DIR", "KICAD9_3DMODEL_DIR", "KISYS3DMOD"):
            env[key] = str(models)
        drc = EVIDENCE / (label + "-drc.json")
        command = ["kicad-cli", "pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all", "--exit-code-violations", "--output", str(drc), str(pcb)]
        run = subprocess.run(command, env=env, capture_output=True, text=True)
        (EVIDENCE / (label + "-drc.log")).write_text(run.stdout + run.stderr)
        if run.returncode:
            raise SystemExit(f"{label} DRC failed: {run.returncode}; see {drc}")
        for name, fmt, flags in exports:
            path = base / outdir / (name + "." + fmt)
            command = ["kicad-cli", "pcb", "export", fmt, "--force", "--subst-models", "--no-dnp", *origin, *flags, "--output", str(path), str(pcb)]
            started = time.monotonic()
            run = subprocess.run(command, env=env, capture_output=True, text=True)
            log = EVIDENCE / (name + "-" + fmt + "-export.log")
            log.write_text(run.stdout + run.stderr)
            if run.returncode:
                raise SystemExit(f"{name} {fmt} failed: {run.returncode}; see {log}")
            conversion = binary_stl(path) if fmt == "stl" else None
            receipt = {"artifact": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path), "sourceBoard": str(pcb.relative_to(ROOT)), "sourceBoardSha256": sha(pcb), "modelDirectory": str(models.relative_to(ROOT)), "kicadVersion": version, "command": command, "exit": run.returncode, "seconds": time.monotonic() - started}
            if conversion is not None:
                receipt["conversion"] = conversion
            receipts.append(receipt)
            (EVIDENCE / "native-exports.json").write_text(json.dumps(receipts, indent=2) + "\n")
            print(json.dumps(receipt), flush=True)
    print("Native exports and unchanged-rule DRC checks complete.")

if __name__ == "__main__":
    main()
