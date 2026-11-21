#!/usr/bin/env python3
"""USB4216-03-A reference clearance geometry from GCT drawing revA2.
This is an original drawing-derived model, not a GCT native CAD file.
Dimensioned shell/mating/land interfaces are reproduced. Undimensioned spring,
latch, forming radii and peg depth are nominal visual geometry, not qualified.
Run with cadquery-ocp==8.0.1.1.0.
"""
from pathlib import Path
import json,hashlib,argparse
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs,STEPControl_Reader
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.BRep import BRep_Builder
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopoDS import TopoDS_Compound
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax2
D=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--models-dir',default=str(D/'models'));parser.add_argument('--drawing-pdf');args=parser.parse_args()
M=Path(args.models_dir).resolve();M.mkdir(parents=True,exist_ok=True)
DRAWING_SHA256='af4ebb92b1027c31a55977f4a2b5fa0bdecbb633a31e294a52691f1c7fcff96f'
if args.drawing_pdf:assert hashlib.sha256(Path(args.drawing_pdf).read_bytes()).hexdigest()==DRAWING_SHA256
def box(x,y,z,w,d,h):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),w,d,h).Shape()
def fuse(a,b):return BRepAlgoAPI_Fuse(a,b).Shape()
def bbox(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s,b)
 return tuple(b.CornerMin().Coord())+tuple(b.CornerMax().Coord())
def capsule(width,height,y,length,zcenter=1.68):
 r=height/2;dx=width/2-r
 s=box(-dx,y,zcenter-r,2*dx,length,height)
 for x in [-dx,dx]:s=fuse(s,BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,zcenter),gp_Dir(0,1,0)),r,length).Shape())
 return s
# KiCad model coordinates are +X right, +Y toward PCB interior, +Z above board.
# The footprint origin remains (35,97); signal land center localY=-3.680mm.
front_y=-2.995
shell=capsule(8.94,3.16,front_y,6.50)
shell=BRepAlgoAPI_Cut(shell,capsule(8.34,2.56,front_y-.001,6.502)).Shape()
# Four SMT shell stakes. Width envelope11.14mm; dimensions1.20/0.95mm from bottom view.
stakes=[]
for x0 in [-5.57,4.27]:
 for cy,depth in [(-.895,1.20),(3.030,.95)]:
  foot=box(x0,cy-depth/2,0,1.30,depth,.30)
  riser_x = -4.57 if x0 < 0 else 4.27
  foot=fuse(foot,box(riser_x,cy-depth/2,0,.30,depth,1.30))
  stakes.append(foot);shell=fuse(shell,foot)
# Insulator back wall and tongue. Nominal front setback0.15mm from4.60-4.45.
rear=BRepAlgoAPI_Common(capsule(8.34,2.56,front_y+4.60,1.90),box(-4.18,front_y+4.60,.39,8.36,1.91,2.58)).Shape()
tongue=box(-6.69/2,front_y+.15,1.68-.35,6.69,6.35,.70)
plastic=fuse(rear,tongue)
# Locating pegs: drawing diameter and6.00mm spacing; depth0.50mm is nominal,
# because the primary drawing does not dimension this depth.
for x in [-3,3]:plastic=fuse(plastic,BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,2.405,-.5),gp_Dir(0,0,1)),.245,1.10).Shape())
tails=[]
xs=[-3.325,-3.075,-2.525,-2.275,-1.75,-1.25,-.75,-.25,.25,.75,1.25,1.75,2.275,2.525,3.075,3.325]
for x in xs:tails.append(box(x-.10,3.105,0,.20,.65,.10))
bld=BRep_Builder();shape=TopoDS_Compound();bld.MakeCompound(shape)
for s in [shell,plastic,*tails]:
 assert BRepCheck_Analyzer(s).IsValid()
 bld.Add(shape,s)
assert BRepCheck_Analyzer(shape).IsValid()
out=M/'USB4216-03-A_A2_drawing-clearance.step'
w=STEPControl_Writer();w.Transfer(shape,STEPControl_AsIs);assert str(w.Write(str(out))).endswith('RetDone')
text=out.read_text().replace('HEADER;','HEADER;\n/* Original drawing-derived clearance geometry. GCT USB4216 revA2,28July2025. Not supplier CAD. Springs/latches/peg depth are nominal; shell, mating envelope, mounting interface are dimensioned. */',1)
out.write_text(text)
res={
 'part':'GCT USB4216-03-A','provenance':'original drawing-derived clearance model; not vendor CAD',
 'drawing_url':'https://www.mouser.lt/datasheet/3/1507/1/usb4216.pdf','drawing_revision':'A2,2025-07-28','drawing_sha256':DRAWING_SHA256,
 'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'body_mm':{'width':8.94,'length':6.50,'height':3.16,'standoff':.10,'top_above_pcb':3.26,'front_at_footprint_y':2.995},
 'mating_opening_mm':{'width':8.34,'height':2.56,'tongue_width':6.69,'tongue_thickness':.70},
 'shell_stakes':{'count':4,'overall_width_mm':11.14,'center_pitch_y_mm':3.925,'rear_heel_length_mm':.95,'front_heel_length_mm':1.20},
 'locating_pegs':{'count':2,'diameter_mm':.49,'pitch_mm':6,'nominal_undimensioned_depth_mm':.50},
 'contact_count':16,'contact_width_mm':.20,'bbox_mm':[round(x,7) for x in bbox(shape)],
 'land_pattern':{'shell_x_mm':[-5.095,5.095],'shell_y_mm':[-3.030,.895],'peg_x_mm':[-3,3],'peg_y_mm':-2.405,'signal_y_mm':-3.680,'signal_pad_length_mm':1.15,'layout_tolerance_mm':.05},
 'scope':'dimensioned package, mating envelope, and mounting interface only; undimensioned internal/forming details and peg depth are nominal; no physical sample qualification',
 'valid_brep':BRepCheck_Analyzer(shape).IsValid()
}
(D/'usb4216-solid-qualification.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res,indent=2))

