#!/usr/bin/env python3
"""Re-export the current OpenFC PCB with its pinned native component models."""
from pathlib import Path
import hashlib
import json
import math
import os
import struct
import subprocess
import time

import pcbnew

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
PCB = ROOT / "hardware/OpenFC.kicad_pcb"
REVIEW = OUT / "model-resolution-review.json"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")

def vector(value):
    return [value.x, value.y, value.z]

board = pcbnew.LoadBoard(str(PCB))
prior = json.loads(REVIEW.read_text())
prior_by_ref = {entry["ref"]: entry for entry in prior["models"]}
models = []
for footprint in board.GetFootprints():
    for model in footprint.Models():
        if not model.m_Show:
            continue
        ref = footprint.GetReference()
        if ref not in prior_by_ref:
            raise SystemExit(f"Unreviewed model reference: {ref}")
        entry = dict(prior_by_ref[ref])
        # A changed placement needs a fresh review, not silent inheritance.
        current = {
            "path": model.m_Filename,
            "offset_mm": vector(model.m_Offset),
            "rotation_degrees": vector(model.m_Rotation),
            "scale": vector(model.m_Scale),
        }
        for key, value in current.items():
            if entry[key] != value:
                raise SystemExit(f"Model {ref} changed {key}; review required")
        asset = ROOT / entry["reviewed_asset"]
        if not asset.is_file() or digest(asset) != entry["asset_sha256"]:
            raise SystemExit(f"Missing or changed pinned model: {asset}")
        entry.update(current)
        entry["resolved_path"] = str(asset)
        entry["exists"] = True
        entry["footprint_position_mm"] = [
            pcbnew.ToMM(footprint.GetPosition().x),
            pcbnew.ToMM(footprint.GetPosition().y),
        ]
        entry["footprint_rotation_degrees"] = footprint.GetOrientationDegrees()
        entry["footprint_layer"] = board.GetLayerName(footprint.GetLayer())
        models.append(entry)
if len(models) != len(prior_by_ref):
    raise SystemExit("Enabled model reference set changed; review required")

env = os.environ.copy()
for key in ("KICAD10_3DMODEL_DIR", "KICAD9_3DMODEL_DIR", "KISYS3DMOD"):
    env[key] = str(ROOT / "reviewed-models")
version = subprocess.check_output(["kicad-cli", "version"], text=True).strip()
exports = []
for name, fmt, flags in [
    ("fc-substrate", "step", ["--board-only"]),
    ("fc-populated", "step", ["--subst-models", "--no-dnp"]),
    ("fc-components", "stl", ["--subst-models", "--no-dnp", "--no-board-body"]),
]:
    path = OUT / f"{name}.{fmt}"
    command = [
        "kicad-cli", "pcb", "export", fmt, "--force", "--user-origin",
        "153.0912x87.1597mm", "--output", str(path), *flags, str(PCB)
    ]
    started = time.monotonic()
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    log = result.stdout + result.stderr
    (OUT / f"{name}-export.log").write_text(log)
    if result.returncode or any(s in log for s in (
        "Could not add 3D model", "File not found:", "Unable to load 3D model"
    )):
        raise SystemExit(f"{name} export failed; inspect its log")
    exports.append({
        "name": name, "command": command,
        "environment": {key: env[key] for key in (
            "KICAD10_3DMODEL_DIR", "KICAD9_3DMODEL_DIR", "KISYS3DMOD"
        )},
        "exit": result.returncode, "seconds": time.monotonic() - started,
        "source_board_sha256": digest(PCB), "bytes": path.stat().st_size,
        "sha256": digest(path), "kicad_version": version,
    })
    print(name, exports[-1]["sha256"], flush=True)

# Retain every ASCII STL facet in its original order; only the container changes.
mesh_path = OUT / "fc-components.stl"
ascii_mesh = mesh_path.read_bytes()
facets, normal, vertices = [], None, []
for line in ascii_mesh.decode("ascii").splitlines():
    tokens = line.split()
    if tokens[:2] == ["facet", "normal"]:
        normal = [float(x) for x in tokens[2:]]
        vertices = []
    elif tokens[:1] == ["vertex"]:
        vertices.extend(float(x) for x in tokens[1:])
    elif tokens[:1] == ["endfacet"]:
        if normal is None or len(vertices) != 9:
            raise SystemExit("Malformed native STL facet")
        facets.append(normal + vertices)
if not facets:
    raise SystemExit("Native STL contains no facets")
header = b"Native KiCad components; binary container; original facet order".ljust(80, b" ")
binary = header + struct.pack("<I", len(facets))
binary += b"".join(struct.pack("<12fH", *facet, 0) for facet in facets)
mesh_path.write_bytes(binary)
quantization = max(
    abs(value - struct.unpack("<f", struct.pack("<f", value))[0])
    for facet in facets for value in facet[3:]
)
points = [facet[index:index+3] for facet in facets for index in (3, 6, 9)]
write_json(OUT / "mesh-transcode.json", {
    "source_board_sha256": digest(PCB),
    "source_sha256": hashlib.sha256(ascii_mesh).hexdigest(),
    "output_sha256": digest(mesh_path),
    "source_bytes": len(ascii_mesh), "output_bytes": len(binary),
    "triangles": len(facets),
    "transform": "none; unit and axis preserved from native KiCad STL export",
    "max_float32_quantization_error_mm": quantization,
    "component_bbox_mm": {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
    },
    "scope": "Format transcoding only; every facet retained in original order. No simplification, body substitution or assumed placement.",
})
write_json(OUT / "export-result.json", exports)
prior["board_sha256"] = digest(PCB)
prior.pop("hardware_commit", None)
prior["working_tree_base_commit"] = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
).strip()
prior["models"] = models
prior["model_entries"] = len(models)
prior["resolved_enabled_entries"] = len(models)
prior["exports"] = {
    path.name: {"bytes": path.stat().st_size, "sha256": digest(path)}
    for path in (OUT / "fc-substrate.step", OUT / "fc-populated.step", mesh_path)
}
write_json(REVIEW, prior)
dimensions = json.loads((OUT / "board-dimensions.json").read_text())
bbox = board.GetBoardEdgesBoundingBox()
dimensions["board_sha256"] = digest(PCB)
dimensions["thickness_mm"] = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
dimensions["edge_bbox_mm"] = {
    key: pcbnew.ToMM(value) for key, value in {
        "x": bbox.GetX(), "y": bbox.GetY(),
        "w": bbox.GetWidth(), "h": bbox.GetHeight()
    }.items()
}
write_json(OUT / "board-dimensions.json", dimensions)
print(json.dumps({"models": len(models), "triangles": len(facets),
                  "board_sha256": digest(PCB), "mesh_sha256": digest(mesh_path)}))

