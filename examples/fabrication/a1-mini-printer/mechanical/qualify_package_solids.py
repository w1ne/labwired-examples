#!/usr/bin/env python3
"""Qualify package solids against primary drawings; retain KiCad source provenance.
Run with cadquery-ocp==8.0.1.1.0. Does not certify the physical parts or fabrication.
"""
from pathlib import Path
import hashlib,json,shutil,re
from OCP.STEPControl import STEPControl_Reader,STEPControl_Writer,STEPControl_AsIs
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE,TopAbs_SOLID
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Common
from OCP.gp import gp_Pnt
D=Path(__file__).resolve().parent
M=D/'models';M.mkdir(exist_ok=True)
Q=Path('/usr/share/kicad/3dmodels/Package_DFN_QFN.3dshapes/QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm.step')
T=Path('/usr/share/kicad/3dmodels/Package_SO.3dshapes/SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm.step')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 r=STEPControl_Reader();assert str(r.ReadFile(str(p))).endswith('RetDone');r.TransferRoots();return r.OneShape()
def bbox(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s,b)
 return tuple(b.CornerMin().Coord())+tuple(b.CornerMax().Coord())
def rounded(b):return [round(x,7) for x in b]
def bottoms(s):
 out=[];e=TopExp_Explorer(s,TopAbs_FACE)
 while e.More():
  f=TopoDS.Face(e.Current());b=bbox(f)
  if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(b[5]-b[2])<1e-5 and abs(b[2])<1e-5:out.append(b)
  e.Next()
 return out
q=load(Q);before=bottoms(q)
ep=[b for b in before if b[0]<0<b[3] and b[1]<0<b[4]]
assert len(ep)==1 and abs(ep[0][3]-ep[0][0]-3.15)<1e-6
# Existing model uses 0.4mm contact heels. Allegro ET drawing p19 gives 0.55mm.
for a in [-1.5,-1.0,-.5,0,.5,1.0,1.5]:
 for x,y,w,h in [(-2.15,a-.125,.20,.25),(1.95,a-.125,.20,.25),(a-.125,-2.15,.25,.20),(a-.125,1.95,.25,.20)]:
  q=BRepAlgoAPI_Fuse(q,BRepPrimAPI_MakeBox(gp_Pnt(x,y,0),w,h,.03).Shape()).Shape()
assert BRepCheck_Analyzer(q).IsValid()
qp=M/'A4988SETTR-T_ET_drawing-checked.step'
w=STEPControl_Writer();w.Transfer(q,STEPControl_AsIs);assert str(w.Write(str(qp))).endswith('RetDone')
# Preserve the source license and special ECAD exception in the derivative.
license_block=re.search(r'/\*.*?\*/',Q.read_text(),re.S).group()
txt=qp.read_text();qp.write_text(txt.replace('HEADER;','HEADER;\n'+license_block+'\n/* Modified 2026-11-21: extend contact heels to0.55mm per Allegro ET drawing. */',1))
q=load(qp);after=bottoms(q)
contacts=[b for b in after if not(b[0]<0<b[3] and b[1]<0<b[4])]
# Boolean splits coplanar faces, so check disconnected metal islands below body standoff.
slice=BRepAlgoAPI_Common(q,BRepPrimAPI_MakeBox(gp_Pnt(-3,-3,-.1),6,6,.119).Shape()).Shape()
e=TopExp_Explorer(slice,TopAbs_SOLID);islands=[]
while e.More():islands.append(bbox(e.Current()));e.Next()
pins=[b for b in islands if not(b[0]<0<b[3] and b[1]<0<b[4])]
assert len(pins)==28
for b in pins:
 sizes=sorted([b[3]-b[0],b[4]-b[1]])
 assert abs(sizes[0]-.25)<1e-6 and abs(sizes[1]-.55)<1e-6
qb=bbox(q);assert abs(qb[3]-qb[0]-5)<1e-6 and abs(qb[4]-qb[1]-5)<1e-6 and .8<=qb[5]-qb[2]<=1.0
tp=M/'LMR36520ADDAR_DDA0008B_drawing-checked.step';shutil.copy2(T,tp)
t=load(tp);tb=bbox(t);ts=bottoms(t);tep=[b for b in ts if b[0]<0<b[3] and b[1]<0<b[4]]
assert len(tep)==1
teps=[tep[0][3]-tep[0][0],tep[0][4]-tep[0][1]]
assert 2.11<=teps[0]<=2.71 and 2.8<=teps[1]<=3.4
assert 5.8<=tb[3]-tb[0]<=6.2 and 4.8<=tb[4]-tb[1]<=5.0 and tb[5]-tb[2]<=1.7
tpins=[b for b in ts if abs((b[0]+b[3])/2)>2.4]
assert len(tpins)==8
ys=sorted(set(round((b[1]+b[4])/2,6) for b in tpins))
assert len(ys)==4 and all(abs(ys[i+1]-ys[i]-1.27)<1e-6 for i in range(3))
for b in tpins:assert .31<=b[4]-b[1]<=.51
res={'tool':'OpenCascade cadquery-ocp 8.0.1.1.0','method':'BRep solid and face geometry, not STEP filename or Cartesian control points','scope':'declared package-body/contact dimensions and pin count; not supplier certification or physical sample inspection','models':{
 'A4988SETTR-T':{'source':str(Q),'source_sha256':sha(Q),'path':str(qp),'sha256':sha(qp),'drawing':'https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf','page':19,'source_ep_mm':[3.15,3.15],'modified_heel_length_mm':{'before':.4,'after':.55},'bbox_mm':rounded(qb),'contact_count':28,'contact_width_mm':.25,'pitch_mm':.5,'ep_mm':[3.15,3.15],'valid_solid':BRepCheck_Analyzer(q).IsValid(),'pass':True},
 'LMR36520ADDAR':{'source':str(T),'source_sha256':sha(T),'path':str(tp),'sha256':sha(tp),'drawing':'https://www.ti.com/lit/ds/symlink/lmr36520.pdf','package_drawing':'DDA0008B 4214849/B 09/2025','bbox_mm':rounded(tb),'contact_count':8,'pitch_mm':1.27,'ep_mm':[round(x,6) for x in teps],'ep_allowed_mm':[[2.11,2.71],[2.8,3.4]],'valid_solid':BRepCheck_Analyzer(t).IsValid(),'pass':True}},
 'qualified_instances':{'U10':'A4988SETTR-T','U11':'A4988SETTR-T','U12':'A4988SETTR-T','U13':'A4988SETTR-T','U20':'LMR36520ADDAR'}}
(D/'package-solid-qualification.json').write_text(json.dumps(res,indent=2))
print(json.dumps({'models':{k:{kk:vv for kk,vv in v.items() if kk in ['path','sha256','bbox_mm','ep_mm','contact_count','pass']} for k,v in res['models'].items()},'qualified_instances':res['qualified_instances']},indent=2))
