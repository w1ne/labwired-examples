#!/usr/bin/env python3
"""Apply source-backed A1 package models and GCT revA2 mounting coordinates.
Preserves every signal pad and net. Only J20 SH/NPTH positions change.
Do not run over an input file. Refill zones and run unchanged-rule DRC afterward.
"""
from pathlib import Path
import argparse,json,hashlib
import pcbnew
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--models-dir',default=str(Path(__file__).resolve().parent/'models'));p.add_argument('--model-prefix');p.add_argument('--footprint-output');a=p.parse_args()
src=Path(a.input).resolve();dst=Path(a.output).resolve();assert src!=dst
b=pcbnew.LoadBoard(str(src));fps={f.GetReference():f for f in b.GetFootprints()}
j=fps['J20'];assert abs(j.GetOrientationDegrees())<1e-8
def pad_record(p):
 return {'uuid':p.m_Uuid.AsString(),'number':p.GetNumber(),'net':p.GetNetname(),'xy_mm':[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],'size_mm':[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)],'drill_mm':[pcbnew.ToMM(p.GetDrillSize().x),pcbnew.ToMM(p.GetDrillSize().y)]}
before=[pad_record(p) for f in b.GetFootprints() for p in f.Pads()]
signal=[pad_record(p) for p in j.Pads() if p.GetNumber() not in ['', 'SH']]
ys={round(p['xy_mm'][1],6) for p in signal};assert len(ys)==1
signal_y=ys.pop();signal_length=signal[0]['size_mm'][1];assert abs(signal_length-1.15)<1e-7
lower=signal_y+signal_length/2+4.00
upper=lower-3.925;peg=lower-3.30
changes=[]
for pad in j.Pads():
 n=pad.GetNumber();pos=pad.GetPosition();old=pcbnew.ToMM(pos.y)
 if n=='SH':new=upper if old<signal_y+2 else lower
 elif n=='' and pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:new=peg
 else:continue
 assert abs(new-old)<.11
 pad.SetPosition(pcbnew.VECTOR2I(pos.x,pcbnew.FromMM(new)))
 changes.append({'pad':n or 'NPTH','x_mm':pcbnew.ToMM(pos.x),'before_y_mm':old,'after_y_mm':new,'delta_y_mm':round(new-old,9)})
assert len(changes)==6
j.SetValue('USB4216-03-A')
j.SetFPIDAsString('LabWired_GCT:USB4216-03-A')
j.SetLibDescription('GCT USB4216-03-A; primary drawing revA2 2025-07-28; dimensioned SMT/peg interface; source evidence in mechanical qualification.')
# Replace inherited USB4110 outline graphics with dimensioned USB4216 body/courtyard.
removed_graphics=list(j.GraphicalItems())
for item in removed_graphics:
 if item.GetLayer() in [pcbnew.F_Fab,pcbnew.F_CrtYd,pcbnew.F_SilkS]:j.Remove(item)
cx=pcbnew.ToMM(j.GetPosition().x);front=lower+2.10;back=front-6.50
def rectangle(layer,x0,y0,x1,y1,width):
 sh=pcbnew.PCB_SHAPE(j);sh.SetShape(pcbnew.SHAPE_T_RECT);sh.SetLayer(layer);sh.SetWidth(pcbnew.FromMM(width));sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x0),pcbnew.FromMM(y0)));sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x1),pcbnew.FromMM(y1)));j.Add(sh)
rectangle(pcbnew.F_Fab,cx-4.47,back,cx+4.47,front,.10)
rectangle(pcbnew.F_CrtYd,cx-5.82,signal_y-.575-.25,cx+5.82,front+.25,.05)
for x in [cx-4.60,cx+4.60]:
 sh=pcbnew.PCB_SHAPE(j);sh.SetShape(pcbnew.SHAPE_T_SEGMENT);sh.SetLayer(pcbnew.F_SilkS);sh.SetWidth(pcbnew.FromMM(.12));sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(upper+.9)));sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(lower-1.0)));j.Add(sh)
# All copper and non-J20 footprint geometry must remain identical apart from the six declared y positions.
after=[pad_record(p) for f in b.GetFootprints() for p in f.Pads()]
changed_ids={x['uuid'] for x in before if x not in after}
assert len(changed_ids)<=6
assert signal==[pad_record(p) for p in j.Pads() if p.GetNumber() not in ['', 'SH']]
names={'U10':'A4988SETTR-T_ET_drawing-checked.step','U11':'A4988SETTR-T_ET_drawing-checked.step','U12':'A4988SETTR-T_ET_drawing-checked.step','U13':'A4988SETTR-T_ET_drawing-checked.step','U20':'LMR36520ADDAR_DDA0008B_drawing-checked.step','J20':'USB4216-03-A_A2_drawing-clearance.step'}
models={}
for ref,name in names.items():
 model_path=Path(a.models_dir)/name;assert model_path.is_file(),model_path
 f=fps[ref];f.Models().clear();m=pcbnew.FP_3DMODEL()
 m.m_Filename=(a.model_prefix.rstrip('/')+'/'+name) if a.model_prefix else str(model_path.resolve())
 m.m_Scale.x=m.m_Scale.y=m.m_Scale.z=1
 f.Add3DModel(m)
 models[ref]={'path':m.m_Filename,'sha256':hashlib.sha256(model_path.read_bytes()).hexdigest()}
dst.parent.mkdir(parents=True,exist_ok=True);pcbnew.SaveBoard(str(dst),b)
if a.footprint_output:
 lib=Path(a.footprint_output);lib.mkdir(parents=True,exist_ok=True)
 pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib),j)
report={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output':str(dst),'output_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'pad_changes':changes,'signal_pad_records_unchanged':True,'models':models,'primary_drawing':'GCT USB4216 revA2 28July2025 p1 recommended PCB layout','datum':{'unchanged_signal_center_y_mm':signal_y,'lower_shell_center_y_mm':lower,'upper_shell_center_y_mm':upper,'peg_center_y_mm':peg,'body_front_y_mm':lower+2.10},'required_next':'refill copper zones and run original project DRC'}
dst.with_suffix('.mechanical-patch.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

