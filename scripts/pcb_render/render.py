#!/usr/bin/env python3
"""Generic source-grounded PBR renderer for populated PCB GLB files, Blender 4.x."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--profile",default=None)
    p.add_argument("--engine",choices=["cycles","eevee"],default="cycles")
    p.add_argument("--width",type=int,default=1600)
    p.add_argument("--height",type=int,default=900)
    p.add_argument("--samples",type=int,default=48)
    p.add_argument("--strict",action="store_true",help="Reject anonymous meshes or materials lacking authored roles")
    return p.parse_args(sys.argv[sys.argv.index("--")+1:])
def color(s):
    s=s.lstrip("#")
    if len(s)!=6:raise ValueError("Expected hex color")
    return tuple((v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4) for v in [int(s[i:i+2],16)/255 for i in (0,2,4)])+(1,)
PRESETS={
 "solder_mask":("#0c5636",.02,.33),
 "fr4":("#38442e",.0,.74),
 "epoxy":("#1e2226",.02,.48),
 "ceramic":("#c9bba1",.0,.7),
 "plastic":("#e1ded5",.0,.5),
 "tin":("#c4c9cc",.82,.3),
 "gold":("#d7ab48",.88,.24),
 "copper":("#b97a45",.85,.3),
 "aluminum":("#aeb7c0",.8,.28)}
def semantic(n):
    n=n.lower().replace("_"," ").replace("-"," ")
    for terms,role in [
      (("solder mask","soldermask"),"solder_mask"),
      (("substrate","fr4","dielectric"),"fr4"),
      (("gold","contact","pad"),"gold"),
      (("copper","trace"),"copper"),
      (("tin","solder","leadframe"),"tin"),
      (("ceramic","mlcc"),"ceramic"),
      (("epoxy","chip body","ic body"),"epoxy"),
      (("plastic","housing"),"plastic")]:
        if any(t in n for t in terms):return role
    return None
a=args()
src=Path(a.input).resolve();dst=Path(a.output).resolve()
assert src.is_file() and src.suffix.lower()==".glb"
assert 256<=a.width<=4096 and 256<=a.height<=4096 and 1<=a.samples<=512
profile=json.loads(Path(a.profile).read_text()) if a.profile else {}
rules=profile.get("materials",{})
assert isinstance(rules,dict)
for v in rules.values():assert v in PRESETS,("invalid profile role",v)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
meshes=[o for o in bpy.data.objects if o.type=="MESH"]
assert meshes and all(o.data.polygons for o in meshes),"No populated geometry"
materials=[]
anonymous_meshes=[o.name for o in meshes if o.name.startswith("=>[") or o.name.startswith("Node_") or o.name.startswith("Object_")]
for mat in bpy.data.materials:
    sh=next((n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None) if mat.use_nodes else None
    if not sh:continue
    role=rules.get(mat.name) or semantic(mat.name)
    if role:
        rgb,metal,rough=PRESETS[role]
        sh.inputs["Base Color"].default_value=color(rgb)
    else:
        # Repair the generic KiCad GLB fallback: all metallic=1 and rough=1.
        c=sh.inputs["Base Color"].default_value
        bright=max(c[:3]);contrast=bright-min(c[:3])
        metal=.04 if bright<.28 or contrast>.18 else .7
        rough=.52 if metal<.1 else .34
    sh.inputs["Metallic"].default_value=metal
    sh.inputs["Roughness"].default_value=rough
    if role=="solder_mask" and "Coat Weight" in sh.inputs:sh.inputs["Coat Weight"].default_value=.18
    materials.append({"name":mat.name,"role":role or "source_color_fallback"})
pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
cen=(lo+hi)*.5; ext=hi-lo;d=max(ext)
assert d>1e-5
scene=bpy.context.scene
world=bpy.data.worlds.new("studio")
world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=color("#1a222c")
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.55
scene.world=world
def light(name,direction,power,size):
    bpy.ops.object.light_add(type="AREA",location=cen+d*Vector(direction))
    obj=bpy.context.object;obj.name=name;obj.data.energy=power
    obj.data.shape="DISK";obj.data.size=size*d
    obj.rotation_euler=(cen-obj.location).to_track_quat("-Z","Y").to_euler()
light("key",(-1.2,-1.5,2.3),0.45,2.3)
light("fill",(1.4,-.2,1.8),0.24,1.7)
light("rim",(-.2,1.4,1.3),0.18,1.4)
bpy.ops.mesh.primitive_plane_add(size=d*5,location=(cen.x,cen.y,lo.z-d*.035))
floor=bpy.context.object;floor.name="studio backdrop";floor_mat=bpy.data.materials.new("dark matte studio")
floor_mat.diffuse_color=color("#29323b");floor_mat.use_nodes=True
sh=floor_mat.node_tree.nodes.get("Principled BSDF")
sh.inputs["Base Color"].default_value=color("#29323b")
sh.inputs["Roughness"].default_value=.92
floor.data.materials.append(floor_mat)
bpy.ops.object.camera_add(location=cen+d*Vector((1.8,-1.6,1.8)))
cam=bpy.context.object;cam.rotation_euler=(cen-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=d*1.85
scene.camera=cam
scene.render.engine="CYCLES" if a.engine=="cycles" else "BLENDER_EEVEE"
if a.engine=="cycles":scene.cycles.samples=a.samples;scene.cycles.use_denoising=False
else:scene.eevee.taa_render_samples=a.samples
scene.render.resolution_x=a.width;scene.render.resolution_y=a.height
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.filepath=str(dst);dst.parent.mkdir(parents=True,exist_ok=True)
unknown_materials=[m["name"] for m in materials if m["role"]=="source_color_fallback"]
if a.strict and (unknown_materials or anonymous_meshes):
    raise RuntimeError("Strict photoreal render requires named mesh identity and authored material roles: anonymous meshes=%d; unclassified materials=%s"%(len(anonymous_meshes),unknown_materials))
bpy.ops.render.render(write_still=True)
receipt={"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
"image_sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
"meshes_imported":len(meshes),"materials":materials,"engine":a.engine,"samples":a.samples,
"source_geometry_unchanged":True,"geometry_generated":False,
"missing_components_not_invented":True,
"anonymous_meshes":len(anonymous_meshes),"unclassified_materials":unknown_materials,
"quality_verdict":"review_required" if anonymous_meshes or unknown_materials else "geometry_materials_named",
"photoreal_validated":False}
dst.with_suffix(dst.suffix+".provenance.json").write_text(json.dumps(receipt,indent=2)+"\n")
print("PCB_RENDER_COMPLETE",json.dumps({"output":str(dst),"mesh_count":len(meshes),"material_count":len(materials)}),flush=True)
