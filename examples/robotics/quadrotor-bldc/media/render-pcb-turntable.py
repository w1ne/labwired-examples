#!/usr/bin/env python3
"""Render actual populated ESC PCB GLB in a slow 3D orbit (no synthetic parts)."""
import math,os,sys
from pathlib import Path
import bpy
from mathutils import Vector

SRC=Path(__file__).resolve().parents[1]/'hardware/esc-4in1/fabrication-review/esc-board-populated.glb'
OUT=Path(os.environ.get('LABWIRED_PCB_3D_FRAMES','/data/tmp/labwired-quad-3d-frames'))
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
# The glTF source uses a white fallback top solder-mask material (mat_14).
# Restore realistic green solder mask; retain all 214 original mesh objects.
for mat_name, color in [('mat_14',(0.010,0.055,0.025,1)),('mat_16',(0.008,0.052,0.022,1))]:
    m=bpy.data.materials.get(mat_name)
    if m is not None:
        m.diffuse_color=color
        if m.use_nodes:
            shader=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if shader is not None:
                shader.inputs['Base Color'].default_value=color
                shader.inputs['Roughness'].default_value=0.4
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(x) for o in meshes for x in o.bound_box]
mn=Vector((min(v[i] for v in points) for i in range(3)))
mx=Vector((max(v[i] for v in points) for i in range(3)))
center=(mn+mx)/2
extent=mx-mn
print('RENDER SOURCE',SRC,'MESHES',len(meshes),'EXTENTS',list(extent),flush=True)

world=bpy.data.worlds.new('LabWired studio background')
bpy.context.scene.world=world
world.use_nodes=True
bg=world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(0.027,0.043,0.064,1)
bg.inputs['Strength'].default_value=0.8

def area(loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=(center+Vector(loc)))
    o=bpy.context.object; o.data.energy=power; o.data.shape='DISK'; o.data.size=size
    direction=center-o.location; o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
area((0.04,-0.03,0.065),0.4,0.08)
area((-0.04,0.03,0.048),0.25,0.09)
area((0.02,0.04,0.06),0.25,0.08)

bpy.ops.object.camera_add()
cam=bpy.context.object; bpy.context.scene.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=max(extent.x,extent.y)*1.8
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=8
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.view_settings.view_transform='Standard'
scene.view_settings.look='Medium High Contrast'
scene.view_settings.exposure=0
scene.render.filepath=str(OUT/'pcb-turntable-0001.png')
frames=int(sys.argv[-1]) if len(sys.argv)>1 and sys.argv[-1].isdigit() else 1
for i in range(frames):
    phase=i/max(frames-1,1)
    angle=math.radians(30+115*phase)
    # flat PCB lies on XY; camera orbits around its center
    rad=0.095
    cam.location=center+Vector((rad*math.cos(angle),rad*math.sin(angle),0.10-0.016*math.sin(math.pi*phase)))
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/f'pcb-turntable-{i+1:04d}.png')
    bpy.ops.render.render(write_still=True)
    if (i+1)%10==0 or i==0:print('FRAME',i+1,'/',frames,flush=True)
