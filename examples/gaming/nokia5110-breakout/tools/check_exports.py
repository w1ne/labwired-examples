#!/usr/bin/env python3
"""Check the released print meshes and the five-loop window cutting DXF."""
import collections
import hashlib
import json
import math
from pathlib import Path
import struct
ROOT = Path(__file__).resolve().parents[1]
WELD_MM = 0.00001

def mesh(path, expected_size):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count, f"{path.name}: incomplete binary STL"
    edges = collections.defaultdict(list)
    parent = list(range(count))
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    volume = 0.0
    degenerate = 0
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        vertices = [values[3:6], values[6:9], values[9:12]]
        for point in vertices:
            for axis in range(3):
                lo[axis] = min(lo[axis], point[axis])
                hi[axis] = max(hi[axis], point[axis])
        a, b, c = vertices
        cross = (b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0])
        volume += sum(a[i] * cross[i] for i in range(3)) / 6
        points = [tuple(round(v / WELD_MM) for v in point) for point in vertices]
        degenerate += len(set(points)) != 3
        for i in range(3):
            edges[tuple(sorted((points[i], points[(i+1) % 3])))].append(index)
    non_manifold = sum(len(uses) != 2 for uses in edges.values())
    for uses in edges.values():
        for index in uses[1:]:
            parent[root(index)] = root(uses[0])
    components = len({root(i) for i in range(count)})
    size = [hi[i] - lo[i] for i in range(3)]
    assert not non_manifold, f"{path.name}: {non_manifold} boundary/non-manifold edges"
    assert not degenerate, f"{path.name}: {degenerate} collapsed triangles at {WELD_MM} mm"
    assert components == 1, f"{path.name}: {components} disconnected components"
    assert volume > 0, f"{path.name}: nonpositive oriented volume"
    assert all(abs(a-b) < 0.0001 for a,b in zip(size,expected_size)), (path.name,size)
    return {"file":path.name,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),
            "triangles":count,"edge_connected_components":components,
            "boundary_or_nonmanifold_edges":non_manifold,
            "collapsed_triangles_at_weld_tolerance":degenerate,"vertex_weld_tolerance_mm":WELD_MM,
            "bounds_mm":{"min":lo,"max":hi},"size_mm":size,"signed_volume_mm3":volume}

def window(path):
    data = path.read_bytes()
    lines = data.decode("ascii").splitlines()
    assert len(lines) % 2 == 0
    pairs = [(int(lines[i].strip()),lines[i+1].strip()) for i in range(0,len(lines),2)]
    unit_index = pairs.index((9,"$INSUNITS"))
    assert pairs[unit_index+1] == (70,"4"), "DXF units must be millimetres"
    loops = []
    i = 0
    while i < len(pairs):
        if pairs[i] != (0,"LWPOLYLINE"):
            i += 1
            continue
        i += 1
        group = []
        while i < len(pairs) and pairs[i][0] != 0:
            group.append(pairs[i])
            i += 1
        assert (70,"1") in group, "cut loop is open"
        vertices = []
        for code,value in group:
            if code == 10: vertices.append({"x":float(value),"y":None,"bulge":0.0})
            elif code == 20: vertices[-1]["y"] = float(value)
            elif code == 42: vertices[-1]["bulge"] = float(value)
        loops.append(vertices)
    assert len(loops) == 5, "exactly one perimeter and four holes are required"
    perimeter = next(loop for loop in loops if len(loop) == 8)
    assert {(v["x"],v["y"]) for v in perimeter} == {(2,0),(56,0),(58,2),(58,56),(56,58),(2,58),(0,56),(0,2)}
    assert sum(abs(v["bulge"]-(math.sqrt(2)-1)) < 1e-7 for v in perimeter) == 4
    centers = []
    for loop in loops:
        if loop is perimeter: continue
        assert len(loop) == 2 and all(abs(v["bulge"]-1) < 1e-7 for v in loop)
        diameter = math.hypot(loop[1]["x"]-loop[0]["x"],loop[1]["y"]-loop[0]["y"])
        assert abs(diameter-2.9) < 1e-7
        centers.append([(loop[0]["x"]+loop[1]["x"])/2,(loop[0]["y"]+loop[1]["y"])/2])
    assert sorted(centers) == [[4,4],[4,54],[54,4],[54,54]], centers
    return {"file":path.name,"sha256":hashlib.sha256(data).hexdigest(),"units":"mm",
            "closed_cut_loops":5,"outer_size_mm":[58,58],"outer_radius_mm":2,
            "hole_diameter_mm":2.9,"hole_centers_mm":sorted(centers),"duplicate_cut_paths":0}

if __name__ == "__main__":
    print(json.dumps({
        "schema":"labwired.export-file-checks.v1",
        "scope":"Native output-file geometry and mesh topology; no printed or physical qualification.",
        "print_meshes":[mesh(ROOT/"mechanical"/name,size) for name,size in [
            ("nokia-base.stl",[122,104,64]),("nokia-lid.stl",[122,104,17]),
            ("nokia-lcd-clamp.stl",[5.9,36,2]),("nokia-sensor-clamp.stl",[5.9,20,2])]],
        "window_dxf":window(ROOT/"mechanical/nokia-window.dxf"),
    },indent=2))
