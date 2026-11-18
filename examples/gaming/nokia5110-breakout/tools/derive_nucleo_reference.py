#!/usr/bin/python3
"""Derive the purchased Nucleo bare-board fit reference from pinned ST native CAD.

Requires KiCad 10 CLI and its pcbnew Python module. Outputs a reviewable derivative
under build/ by default. It does not overwrite the package's checked-in reference.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

import pcbnew as k

PACKAGE = Path(__file__).resolve().parents[1]
ARCHIVE_SHA256 = "66e2aa6a1ca58e787ea1717c0736a1853777f93a20a95e4d2e0273dc234eb52d"
MEMBER = "MB1136C/Altium_Designer/MB1136.PcbDoc"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE / "build/nucleo-reference")
    args = parser.parse_args()
    archive = PACKAGE / "references/st/mb1136_bdp.zip"
    if sha(archive) != ARCHIVE_SHA256:
        raise SystemExit("ST archive hash differs from the reviewed source")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    imported = output / "MB1136-imported.kicad_pcb"
    report = output / "altium-import.json"
    with tempfile.TemporaryDirectory(prefix="nokia-st-native-") as temp:
        source = Path(temp) / "MB1136.PcbDoc"
        with zipfile.ZipFile(archive) as bundle:
            source.write_bytes(bundle.read(MEMBER))
        subprocess.run([
            "kicad-cli", "pcb", "import", "--format", "altium",
            "--output", str(imported), "--report-format", "json",
            "--report-file", str(report), str(source),
        ], check=True)

    board = k.LoadBoard(str(imported))
    changes = []
    count = 0
    point = lambda x, y: k.VECTOR2I(k.FromMM(x), k.FromMM(y))
    for shape in list(board.GetDrawings()):
        if type(shape).__name__ != "PCB_SHAPE":
            continue
        if shape.GetLayer() == k.Edge_Cuts:
            board.Remove(shape)
        if board.GetLayerName(shape.GetLayer()) != "Mechanical 1":
            continue
        if shape.GetShape() == k.SHAPE_T_SEGMENT and shape.GetStart() == shape.GetEnd():
            changes.append({"repair": "remove zero-length source edge",
                            "at_mm": [shape.GetStart().x / 1e6, shape.GetStart().y / 1e6]})
            continue
        clone = shape.Duplicate()
        if clone.GetShape() == k.SHAPE_T_SEGMENT:
            start = clone.GetStart()
            if abs(start.x / 1e6 - 161.9711) < 0.00001 and abs(start.y / 1e6 - 144.5036) < 0.00001:
                clone.SetStart(point(162.0011, 144.5036))
                changes.append({"repair": "close 0.030 mm contour gap",
                                "from_mm": [161.9711, 144.5036],
                                "to_mm": [162.0011, 144.5036]})
        clone.SetLayer(k.Edge_Cuts)
        clone.SetWidth(k.FromMM(0.05))
        board.Add(clone)
        count += 1
    if len(changes) != 2 or count != 29:
        raise SystemExit(f"ST contour differs from the reviewed source: {count} edges, {changes}")
    derivative = output / "MB1136-mechanical-reference.kicad_pcb"
    k.SaveBoard(str(derivative), board)
    step = output / "nucleo-mb1136-reference.step"
    subprocess.run([
        "kicad-cli", "pcb", "export", "step", "--force", "--no-components",
        "--user-origin", "113.5011x64.0036mm", "--output", str(step), str(derivative),
    ], check=True)
    receipt = {
        "source_archive_sha256": ARCHIVE_SHA256, "source_member": MEMBER,
        "finished_contour_layer": "Mechanical 1", "edge_count": count,
        "repairs": changes, "derived_board_sha256": sha(derivative),
        "step_sha256": sha(step), "step_origin_mm": [113.5011, 64.0036],
        "scope": "Purchased ST module bare-board mechanical reference; do not fabricate from this derivative.",
        "note": "KiCad-generated identifiers and STEP timestamps may change on replay; compare geometry and dimensions.",
    }
    (output / "derivation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
