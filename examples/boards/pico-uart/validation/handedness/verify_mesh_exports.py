#!/usr/bin/env python3
"""Check the actual print exports, independent of the CAD construction script."""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json, struct, zipfile
import xml.etree.ElementTree as ET
def sha(b):return hashlib.sha256(b).hexdigest()
def stl(path,size):
    raw=path.read_bytes();count=struct.unpack_from("<I",raw,80)[0]
    assert len(raw)==84+50*count,(path,"invalid binary STL size")
    edges=Counter();directed=Counter();points=[];volume=0.
    for row in struct.iter_unpack("<12fH",raw[84:]):
        vs=[tuple(row[3+3*i:6+3*i]) for i in range(3)]
        keys=[tuple(round(c,6)for c in p)for p in vs]
        assert len(set(keys))==3,(path,"degenerate face")
        points.extend(vs)
        for a,b in zip(keys,keys[1:]+keys[:1]):edges[tuple(sorted((a,b)))]+=1;directed[(a,b)]+=1
        a,b,c=vs
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    bad=sum(n!=2 for n in edges.values())
    wrong=sum(directed[(a,b)]!=directed[(b,a)]for a,b in edges)
    assert bad==0 and wrong==0,(path,bad,wrong)
    low=[min(p[i]for p in points)for i in range(3)];high=[max(p[i]for p in points)for i in range(3)]
    assert all(abs(high[i]-low[i]-size[i])<.001 for i in range(3)),(path,low,high,size)
    assert abs(low[2])<.001 and volume>0,(path,low,volume)
    return {"sha256":sha(raw),"bytes":len(raw),"binaryStlValid":True,"triangleCount":count,"bounds":{"min":low,"max":high},
        "expectedSize":size,"nonTwoManifoldEdges":bad,"inconsistentOrientedEdges":wrong,"signedVolumeMm3":volume,"vertexWeldToleranceMm":.000001}
def mf(path,stl_count):
    raw=path.read_bytes()
    with zipfile.ZipFile(path)as z:
        assert z.testzip()is None
        models=[n for n in z.namelist()if n.endswith(".model")]
        assert len(models)==1,models
        tree=ET.fromstring(z.read(models[0]))
    assert tree.attrib.get("unit")=="millimeter",tree.attrib
    meshes=tree.findall(".//{*}mesh");assert len(meshes)==1
    vertices=meshes[0].findall("./{*}vertices/{*}vertex");tris=meshes[0].findall("./{*}triangles/{*}triangle")
    assert len(tris)==stl_count,(path,len(tris),stl_count)
    edges=Counter()
    for tri in tris:
        ids=[int(tri.attrib[k])for k in ["v1","v2","v3"]]
        assert len(set(ids))==3 and min(ids)>=0 and max(ids)<len(vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((a,b)))]+=1
    assert all(n==2 for n in edges.values())
    return {"sha256":sha(raw),"bytes":len(raw),"zipValid":True,"unit":"millimeter","vertexCount":len(vertices),
        "triangleCount":len(tris),"nonTwoManifoldEdges":0}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--kind",choices=["oled","pico"],required=True);ap.add_argument("--package",type=Path,required=True)
    args=ap.parse_args();p=args.package
    folder=p/("cad/exports"if args.kind=="oled"else"mechanical")
    prefix="esp32c3-oled"if args.kind=="oled"else"pico-uart"
    dims={"base":[88,63,27.5],"lid":[88,63,4.3]}if args.kind=="oled"else{"base":[78,88,27.5],"lid":[78,88,3.2]}
    result={}
    for part,size in dims.items():
        name=prefix+"-"+part
        result[name+".stl"]=stl(folder/(name+".stl"),size)
        result[name+".3mf"]=mf(folder/(name+".3mf"),result[name+".stl"]["triangleCount"])
    evidence=p/("cad/verification/handedness"if args.kind=="oled"else"validation/handedness")
    (evidence/"mesh-export-check.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"kind":args.kind,"status":"pass","files":{k:{"triangles":v["triangleCount"],"nonTwoManifoldEdges":v["nonTwoManifoldEdges"]}for k,v in result.items()}}))
if __name__=="__main__":main()
