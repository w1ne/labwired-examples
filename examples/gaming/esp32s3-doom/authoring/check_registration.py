#!/usr/bin/python3
"""Check native KiCad pads against the evaluated transform path and exported STEP.

Requires KiCad 10 pcbnew. No nominal part is turned over to fit a case.
This verifies model registration; it does not qualify physical hardware.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import pcbnew as k
ROOT = Path(__file__).resolve().parents[1]
TOL = 0.000001

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def close(a, b):
    assert len(a) == len(b)
    assert all(abs(x-y) <= TOL for x,y in zip(a,b)), (a,b)

def circles(path):
    text = path.read_text()
    assert "SI_UNIT(.MILLI.,.METRE.)" in re.sub(r"\s+", "", text)
    entities = {m[1]: re.sub(r"\s+", "", m[2]) for m in re.finditer(r"#(\d+)\s*=\s*(.*?);", text, re.S)}
    result = []
    for value in entities.values():
        match = re.match(r"CIRCLE\([^,]+,#(\d+),([0-9.Ee+-]+)\)", value)
        if not match: continue
        point_id = re.findall(r"#(\d+)", entities[match[1]])[0]
        values = re.search(r",\(([^)]+)\)\)", entities[point_id])[1]
        result.append(([float(x) for x in values.split(",")],float(match[2])))
    assert result
    return result

def circle_exists(items, point, radius):
    return any(abs(r-radius)<=TOL and all(abs(x-y)<=TOL for x,y in zip(p,point)) for p,r in items)

def numeric(value):
    return value["evaluated"] if isinstance(value,dict) else value

def apply(point, transforms):
    p=list(point)
    for t in transforms:
        if t["op"] == "scale": p=[v*numeric(t[axis]) for v,axis in zip(p,["sx","sy","sz"])]
        elif t["op"] == "translate": p=[v+numeric(t["vec"][axis]) for v,axis in zip(p,["x","y","z"])]
        elif t["op"] == "reflect":
            assert t["plane"] in ["xy","xz","yz"]
            i={"xy":2,"xz":1,"yz":0}[t["plane"]];p[i]=-p[i]
        else: raise AssertionError("Unreviewed native transform: "+str(t))
    return p

def verify(capture_path):
    source=ROOT/"mechanical/doom-desktop.kcad.ts"
    board_path=ROOT/"electronics/doom-carrier.kicad_pcb"
    input_step=ROOT/"mechanical/inputs/doom-carrier-board.step"
    output_step=ROOT/"mechanical/doom-desktop-assembly.step"
    capture=json.loads(capture_path.read_text())
    assert capture["sourceSha256"] == sha(source), "stale native transform capture"
    path=capture["nativePath"]
    assert path[0]["kind"]=="importedStep" and path[-1]["kind"]=="boolean"
    transforms=[t for record in path for t in record["transforms"]]
    close([numeric(capture["partAt"][axis]) for axis in ["x","y","z"]],[0,0,0])
    origin=apply([0,0,0],transforms)
    basis=[[v-o for v,o in zip(apply(p,transforms),origin)] for p in [[1,0,0],[0,1,0],[0,0,1]]]
    close(origin,[0,0,10]);close(basis[0],[1,0,0]);close(basis[1],[0,1,0]);close(basis[2],[0,0,1.6/1.51])
    determinant=basis[0][0]*basis[1][1]*basis[2][2]
    assert determinant>0 and basis[2][2]>0
    native_circles=circles(input_step);final_circles=circles(output_step)
    board=k.LoadBoard(str(board_path));fps={f.GetReference():f for f in board.GetFootprints()}
    contacts=[];top=11.6
    for ref in ["J1","J2","J3"]:
        fp=fps[ref];assert fp.GetLayer()==k.F_Cu
        for pad in sorted(fp.Pads(),key=lambda p:int(p.GetNumber())):
            pos=pad.GetPosition();xy=[pos.x/1e6,-pos.y/1e6]
            radius=pad.GetDrillSize().x/2e6
            for z in [0,1.51]: assert circle_exists(native_circles,[*xy,z],radius),(ref,pad.GetNumber(),z)
            close(apply([*xy,1.51],transforms),[*xy,top])
            if ref in ["J1","J2"]:
                # Exported SSW socket bore, tail and real DevKit header bore.
                for z,r in [(20.11,.5),(13.91,.5),(11.6,.32),(8.96,.32),(24.25,.475),(22.65,.475)]:
                    assert circle_exists(final_circles,[*xy,z],r),(ref,pad.GetNumber(),z,r)
            contacts.append({"pad":ref+"."+pad.GetNumber(),"net":pad.GetNetname(),"native_world_xy_mm":xy})
    assert len(contacts)==78
    mounts=[]
    for ref in ["H1","H2","H3","H4"]:
        pad=list(fps[ref].Pads())[0];pos=pad.GetPosition();xy=[pos.x/1e6,-pos.y/1e6]
        for z in [0,1.51]: assert circle_exists(native_circles,[*xy,z],1.45),(ref,z)
        for z,r in [(2.5,1.45),(10,1.25),(11.6,1.25)]:
            assert circle_exists(final_circles,[*xy,z],r),(ref,z,r)
        mounts.append({"pad":ref,"world_xy_mm":xy,"native_hole_diameter_mm":2.9})
    witnesses={w["name"]:w for w in capture["witnesses"]}
    for pad,name in [("J1.1","native-J1-1"),("J1.2","native-J1-2"),("J2.1","native-J2-1")]:
        xy=next(p["native_world_xy_mm"] for p in contacts if p["pad"]==pad)
        close(witnesses[name]["origin"]["value"],[*xy,top]);close(witnesses[name]["normal"],[0,0,1])
    a=witnesses["native-J1-1"]["origin"]["value"];b=witnesses["native-J2-1"]["origin"]["value"];c=witnesses["native-J1-2"]["origin"]["value"]
    triple=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);close([triple],[-58.0644])
    return {"schema":"labwired.native-board-registration.v1","ok":True,
        "scope":"Native pads and STEP holes; evaluated carrier transform chain; exported socket, DevKit bore and mounting geometry.",
        "cad_source_sha256":sha(source),"capture_sha256":sha(capture_path),
        "sources":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in [board_path,input_step,output_step]],
        "native_header_contacts":78,"exported_socket_and_devkit_axes":44,"header_contacts":contacts,
        "mounting_axes":mounts,"native_transform_determinant":determinant,"native_top_normal":[0,0,1],
        "signed_triple_product_mm2":triple,"rejected_mirrored_layout_mm2":-triple,"physical_prototype_tested":False}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,default=ROOT/"validation/native-frame-capture.json");args=p.parse_args()
    print(json.dumps(verify(args.capture),indent=2))
