#!/usr/bin/env python3
"""Independent OCCT fit audit for the A1 reference source.
Imports the native KiCad STEP. Uses KernelCAD-exported enclosure/tray STEP when
provided. Otherwise reconstructs the same explicit source primitives with OCCT;
this fallback is identified in the evidence and is not supplier geometry.
"""
from pathlib import Path
import argparse,hashlib,json,math
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax1,gp_Ax2,gp_Trsf,gp_Vec
D=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--board-step',default=str(D/'a1-populated-fit.step'));ap.add_argument('--source',default=str(D/'a1-native-fit.kcad.ts'));ap.add_argument('--enclosure-step');ap.add_argument('--bottom-step');ap.add_argument('--output',default=str(D/'enclosure-fit.json'));a=ap.parse_args()
def load(p):
 r=STEPControl_Reader();assert str(r.ReadFile(str(p))).endswith('RetDone');r.TransferRoots();return r.OneShape()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def box(x,y,z,w,d,h):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),w,d,h).Shape()
def cyl(x,y,z,r,h,axis=(0,0,1)):return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape()
def union(a,b):return BRepAlgoAPI_Fuse(a,b).Shape()
def cut(a,b):return BRepAlgoAPI_Cut(a,b).Shape()
def rr(w,d,r,h,x,y,z,axis='z'):
 if axis=='z':
  s=box(x-w/2+r,y-d/2,z,w-2*r,d,h)
  s=union(s,box(x-w/2,y-d/2+r,z,w,d-2*r,h))
  for dx in [-w/2+r,w/2-r]:
   for dy in [-d/2+r,d/2-r]:s=union(s,cyl(x+dx,y+dy,z,r,h))
 elif axis=='x':
  s=box(x,y-w/2,z-d/2+r,h,w,d-2*r)
  if w-2*r>1e-9:s=union(s,box(x,y-w/2+r,z-d/2,h,w-2*r,d))
  for dy in [-w/2+r,w/2-r]:
   for dz in [-d/2+r,d/2-r]:s=union(s,cyl(x,y+dy,z+dz,r,h,(1,0,0)))
 else:raise ValueError(axis)
 return s
def transform(s,axis,angle,translate):
 t=gp_Trsf();t.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(*axis)),math.radians(angle));t.SetTranslationPart(gp_Vec(*translate));return BRepBuilderAPI_Transform(s,t,True).Shape()
def bbox(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s,b);return list(b.CornerMin().Coord())+list(b.CornerMax().Coord())
def volume(s):
 g=GProp_GProps();BRepGProp.VolumeProperties_s(s,g);return g.Mass()
def intersection(a,b):return max(0.0,volume(BRepAlgoAPI_Common(a,b).Shape()))
def distance(a,b):
 e=BRepExtrema_DistShapeShape(a,b);e.Perform();assert e.IsDone();return e.Value()
def cylinders(s,radius):
 out=[];e=TopExp_Explorer(s,TopAbs_FACE)
 while e.More():
  f=TopoDS.Face(e.Current());surf=BRepAdaptor_Surface(f)
  if surf.GetType()==GeomAbs_Cylinder:
   c=surf.Cylinder();v=c.Axis().Direction().Coord()
   if abs(c.Radius()-radius)<1e-6 and abs(v[2])>.999999:out.append({'center':list(c.Location().Coord())[:2],'z_range':[bbox(f)[2],bbox(f)[5]]})
  e.Next()
 return out
source=Path(a.source).read_text()
for literal in ['rr(105,220,8,30.1,107,4,7.9)',"extrudeRoundedRect(14,8,1.2,18,{axis:'x'}).translate(150,-14,20.48)",'translate(57,-49,17.205)','cylinder(9.3,3.6)']:
 assert literal in source,('Source changed; update the independent fit audit',literal)
mounts=[[95,-44.5],[95,46.5],[152.5,-44.5],[61.5,46.5]]
method='KernelCAD exported exact BReps'
if a.enclosure_step and a.bottom_step:
 housing=load(a.enclosure_step);tray=load(a.bottom_step)
else:
 method='Independent OCCT reconstruction of the exact primitive parameters in the evaluated KernelCAD source'
 housing=union(rr(210,258,15,34,-45,0,8),rr(118,276,14,40,107,4,8))
 housing=cut(housing,rr(105,220,8,30.1,107,4,7.9))
 for i in range(12):housing=cut(housing,rr(3.4,15,1.7,18,150,-64+i*9,28,'x'))
 housing=cut(housing,rr(14,8,1.2,18,150,-14,20.48,'x'))
 housing=cut(housing,transform(rr(77,65,7,30,0,0,-.1),(1,0,0),55,(91,-129,27)))
 tray=rr(304,252,12,3,8,0,5)
 for x,y in mounts:tray=cut(union(tray,cyl(x,y,7.9,3.6,9.3)),cyl(x,y,4.9,1.6,14))
board=transform(load(a.board_step),(0,0,1),90,(57,-49,17.205))
# Conservative bounding prism contains every PCB/component point throughout a
# straight downward removal. The tray slab stays at or below housing bottom Z = 8 mm.
board_bounds=bbox(board)
board_removal=box(57,-49,-30,100,100,board_bounds[5]+30)
tray_removal=box(-144,-126,-30,304,252,38)
# Reference cable-overmold gauge. Height 6.5 mm is GCT's mating sketch maximum;
# width 12 mm is an explicitly declared design envelope, not a universal USB limit.
plug=box(156.995,-20,20.48-3.25,45,12,6.5)
contacts={
 'pcb_to_housing_overlap_mm3':intersection(board,housing),
 'pcb_to_tray_overlap_mm3':intersection(board,tray),
 'plug_path_to_housing_overlap_mm3':intersection(plug,housing),
 'pcb_downward_removal_bound_overlap_mm3':intersection(board_removal,housing),
 'tray_downward_removal_bound_overlap_mm3':intersection(tray_removal,housing)
}
assert all(v<1e-5 for v in contacts.values()),contacts
board_holes=cylinders(board,1.6);tray_holes=cylinders(tray,1.6)
holes=[]
for center in mounts:
 bs=min(board_holes,key=lambda h:math.dist(center,h['center']))
 ts=min(tray_holes,key=lambda h:math.dist(center,h['center']))
 err=math.dist(bs['center'],ts['center']);assert err<1e-6
 holes.append({'world_center_mm':center,'pcb_center_mm':bs['center'],'tray_center_mm':ts['center'],'coaxial_error_mm':err,'diameter_mm':3.2,'pcb_z_range_mm':bs['z_range'],'tray_z_range_mm':ts['z_range']})
result={'tool':'OpenCascade cadquery-ocp 8.0.1.1.0','scope':'nominal modeled enclosure/board fit and reference plug passage; not physical hardware or OEM qualification','enclosure_geometry_method':method,'source_path':str(a.source),'source_sha256':sha(a.source),'board_step_path':str(a.board_step),'board_step_sha256':sha(a.board_step),'native_step_transform':{'rotation_z_deg':90,'translation_mm':[57,-49,17.205]},'valid_breps':{k:BRepCheck_Analyzer(v).IsValid() for k,v in [('pcb',board),('housing',housing),('tray',tray)]},'pcb_bounds_world_mm':board_bounds,'housing_bounds_mm':bbox(housing),'tray_bounds_mm':bbox(tray),'intersections':contacts,'clearances_mm':{'minimum_pcb_to_housing':distance(board,housing),'minimum_pcb_to_tray':distance(board,tray),'minimum_declared_plug_to_housing':distance(plug,housing),'pcb_outline_to_cavity_sidewall_nominal':2.5,'highest_component_to_roof':38-board_bounds[5]},'mounting_holes':holes,'usb':{'mouth_center_world_mm':[156.995,-14,20.48],'outward_axis':[1,0,0],'reference_plug_envelope_yz_mm':[12,6.5],'opening_yz_mm':[14,8],'reference_plug_width_is_design_assumption':True},'assembly_access':{'direction':[0,0,-1],'method':'Continuous conservative swept bounding prisms for PCB and tray slab; bosses lie inside PCB prism','clear':True},'limitations':['Exact nominal geometry only; component and enclosure manufacturing tolerances are not propagated.','USB spring/latch/forming details and locating-peg depth are nominal because the public drawing does not dimension them.','Cable overmold width 12 mm is the declared reference envelope; all commercial cable housings are not covered.','This checks installation and static fit, not thermal, vibration, screw preload, wire-harness routing or physical printer operation.'],'pass':True}
for key,path in [('enclosure',a.enclosure_step),('tray',a.bottom_step)]:
 if path:result[key+'_step_sha256']=sha(path)
Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

