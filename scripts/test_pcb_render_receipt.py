"""Validate a source-bound PCB renderer receipt without Blender dependencies."""
import hashlib
import json
import struct
import sys
from pathlib import Path

def verify(image, source, minimum_meshes=1):
    image=Path(image);source=Path(source)
    report=json.loads(image.with_suffix(image.suffix+".provenance.json").read_text())
    assert image.read_bytes()[:8]==b"\x89PNG\r\n\x1a\n"
    width,height=struct.unpack(">II",image.read_bytes()[16:24])
    assert width>=256 and height>=256
    assert report["image_sha256"]==hashlib.sha256(image.read_bytes()).hexdigest()
    assert report["source_sha256"]==hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["meshes_imported"]>=int(minimum_meshes)
    assert report["source_geometry_unchanged"] is True
    assert report["geometry_generated"] is False
    assert report["missing_components_not_invented"] is True
    assert report["photoreal_validated"] is False
    assert report["quality_verdict"] in {"review_required","geometry_materials_named"}
    return {"width":width,"height":height,"meshes":report["meshes_imported"],
            "quality":report["quality_verdict"]}

if __name__=="__main__":
    print(json.dumps(verify(*sys.argv[1:])))
