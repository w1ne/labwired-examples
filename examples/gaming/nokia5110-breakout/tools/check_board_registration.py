#!/usr/bin/python3
"""Verify source-pad and native STEP registration without turning over either PCB.

Requires KiCad's pcbnew module. Reads real native pads and analytic STEP hole
circles, then compares them to the case interface and committed CAD transform.
This is nominal registration evidence, not a physical assembly test.
"""
import hashlib
import json
from pathlib import Path
import re

import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TOL = 0.000001

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def close(a, b):
    assert len(a) == len(b)
    assert all(abs(x-y) <= TOL for x, y in zip(a, b)), (a, b)

def circles(path):
    text = path.read_text()
    assert "SI_UNIT(.MILLI.,.METRE.)" in re.sub(r"\s+", "", text)
    entities = {m[1]: re.sub(r"\s+", "", m[2])
                for m in re.finditer(r"#(\d+)\s*=\s*(.*?);", text, re.S)}
    result = []
    for value in entities.values():
        match = re.match(r"CIRCLE\([^,]+,#(\d+),([0-9.Ee+-]+)\)", value)
        if not match:
            continue
        axis = entities[match[1]]
        point_id = re.findall(r"#(\d+)", axis)[0]
        point = entities[point_id]
        coordinates = re.search(r",\(([^)]+)\)\)", point)[1]
        result.append(([float(x) for x in coordinates.split(",")], float(match[2])))
    return result

def circle_exists(items, point, radius):
    return any(abs(r-radius) <= TOL and
               all(abs(x-y) <= TOL for x,y in zip(p,point))
               for p,r in items)

def pads(board, reference):
    fp = next(f for f in board.GetFootprints() if f.GetReference() == reference)
    return fp, {p.GetNumber(): p for p in fp.Pads()}

def position(pad, origin, offset):
    point = pad.GetPosition()
    return [point.x/1e6-origin[0]+offset[0],
            -(point.y/1e6-origin[1])+offset[1]]

def main():
    interface = json.loads((ROOT/"mechanical-interface.json").read_text())
    cad = ROOT/"mechanical/nokia-breakout-enclosure.kcad.ts"
    source = cad.read_text()
    # These two imports are the only board placements in this package.
    for token in [
        '.scale([1,1,1.6/1.51]).translate(0,0,pcbZ)',
        '.scale([1,1,nucleoT/1.5]).translate(10,23,nucleoZ)',
    ]:
        assert token in source, "native board placement changed; review its transform"
    for line in source.splitlines():
        if "lib.fromSTEP(" in line:
            assert ".reflect(" not in line and ".rotate" not in line, line
    assert 'value:[v[0],-v[1],v[2]]' in source

    carrier_path = ROOT/"electronics/nokia-carrier.kicad_pcb"
    nucleo_path = ROOT/"references/st/MB1136-mechanical-reference.kicad_pcb"
    carrier = k.LoadBoard(str(carrier_path))
    nucleo = k.LoadBoard(str(nucleo_path))
    native_origin = [113.5011,64.0036]
    pairs = []
    for carrier_ref, nucleo_ref in [("J1","CN5"),("J2","CN6"),("J3","CN9")]:
        cfp, cpads = pads(carrier, carrier_ref)
        nfp, npads = pads(nucleo, nucleo_ref)
        assert cfp.GetLayer() == k.B_Cu, "carrier mating headers must be on the bottom"
        assert nfp.GetLayer() == k.F_Cu, "Nucleo sockets must remain on the top"
        assert cpads.keys() == npads.keys()
        for pin in sorted(cpads, key=int):
            cxy = position(cpads[pin], [0,0], [0,0])
            nxy = position(npads[pin], native_origin, [10,23])
            close(cxy,nxy)
            pairs.append({"carrier":f"{carrier_ref}.{pin}","nucleo":f"{nucleo_ref}.{pin}",
                          "world_xy_mm":cxy,"carrier_net":cpads[pin].GetNetname(),
                          "nucleo_native_net":npads[pin].GetNetname()})

    mounts = []
    for name, file, input_t, scale, offset in [
        ("carrier","nokia-carrier.step",1.51,1.6/1.51,[0,0]),
        ("nucleo","nucleo-mb1136-reference.step",1.5,1.59112/1.5,[10,23]),
    ]:
        path = ROOT/"mechanical/inputs"/file
        cs = circles(path)
        for x,y,diameter in interface[name]["mounts"]:
            native_xy = [x-offset[0],y-offset[1]]
            for z in [0,input_t]:
                assert circle_exists(cs,[*native_xy,z],diameter/2), (name,x,y,z)
            mounts.append({"board":name,"axis_world_xy_mm":[x,y],"diameter_mm":diameter})
        close([input_t*scale],[interface[name]["size"][2]])

    anchors = [next(p["world_xy_mm"] for p in pairs if p["nucleo"] == pin)
               for pin in ["CN6.1","CN5.1","CN9.1"]]
    a,b,c = anchors
    signed_area2 = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    assert abs(signed_area2) > 100
    # With +Z held fixed, flipping only the planar registration reverses this
    # sign. A 180-degree X rotation of the bare board also flips its top face.
    witness = {"pins":["CN6.1","CN5.1","CN9.1"],"world_xy_mm":anchors,
               "native_top_normal":[0,0,1],"signed_triple_product_mm2":signed_area2,
               "rejected_editor_y_with_upward_components_mm2":-signed_area2}

    return {
        "schema":"labwired.native-board-registration.v1",
        "ok":True,"scope":"Nominal source pads, native STEP mounting axes, board side and CAD placement.",
        "cad_source_sha256":sha(cad),
        "sources":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in [
            carrier_path,nucleo_path,ROOT/"mechanical/inputs/nokia-carrier.step",
            ROOT/"mechanical/inputs/nucleo-mb1136-reference.step"]],
        "matched_header_contacts":len(pairs),"header_contacts":pairs,
        "matched_mounting_axes":len(mounts),"mounting_axes":mounts,
        "orientation_witness":witness,
        "native_board_transform_determinants":{"carrier":1.6/1.51,"nucleo":1.59112/1.5},
        "world_mounts_match_native_step":True,
        "physical_prototype_tested":False,
    }

if __name__ == "__main__":
    print(json.dumps(main(),indent=2))
