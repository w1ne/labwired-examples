"""Extract visual copper geometry from the exact saved KiCad carrier.

No routing is invented. Coordinates use the revision-3 case frame in mm.
"""
from pathlib import Path
import re, json, math, hashlib, argparse

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[3]/'pcb/handheld-carrier.kicad_pcb')
parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args()
ROOT=args.output_dir.resolve();ROOT.mkdir(parents=True,exist_ok=True)
src=args.source.resolve()
tokens=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',src.read_text())
stack=[]; root=None
for token in tokens:
    if token=='(':
        item=[]
        if stack:stack[-1].append(item)
        stack.append(item)
    elif token==')':
        root=stack.pop()
    else:
        if token.startswith('"'):token=json.loads(token)
        stack[-1].append(token)

def children(x,key):return [c for c in x if isinstance(c,list) and c and c[0]==key]
def child(x,key,default=None):return next(iter(children(x,key)),default)
def vals(x,key,default=None):
    c=child(x,key)
    return c[1:] if c else default
def xy(x):return [float(x[0])-39,140-float(x[1])]
def point(x,key):return xy(vals(x,key))
def fl(v):return [float(x) for x in v]

data={'schema':'labwired.carrier-visual.v1','source':src.name,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
      'frame':{'units':'mm','x':'right','y':'toward top of device','z':'toward front','native_to_case':'x = native_x - 39; y = 140 - native_y','front_surface_z':15.0,'back_surface_z':13.4},
      'nets':{n[1]:n[2] for n in children(root,'net')},'tracks':[],'vias':[],'pads':[],'footprints':[],'outline':[],'zones':[]}
for seg in children(root,'segment'):
    data['tracks'].append({'start':point(seg,'start'),'end':point(seg,'end'),'width':float(vals(seg,'width')[0]),'layer':vals(seg,'layer')[0],'net':int(vals(seg,'net')[0])})
for via in children(root,'via'):
    data['vias'].append({'at':point(via,'at'),'diameter':float(vals(via,'size')[0]),'drill':float(vals(via,'drill')[0]),'layers':vals(via,'layers'),'net':int(vals(via,'net')[0])})
for fp in children(root,'footprint'):
    at=fl(vals(fp,'at')); theta=math.radians(at[2] if len(at)>2 else 0)
    ref=next((p[2] for p in children(fp,'property') if p[1]=='Reference'),'')
    value=next((p[2] for p in children(fp,'property') if p[1]=='Value'),'')
    def fp_xy(v):
        # KiCad rotates footprint-local y-down coordinates anticlockwise.
        x,y=float(v[0]),float(v[1]);c,s=math.cos(theta),math.sin(theta)
        return xy([at[0]+x*c+y*s,at[1]-x*s+y*c])
    pads=[]
    for p in children(fp,'pad'):
        pa=fl(vals(p,'at',[0,0])); net=vals(p,'net',['0',''])
        dr=vals(p,'drill',[0]); drill=float(dr[0]) if dr[0]!='oval' else min(fl(dr[1:]))
        pad={'reference':ref,'number':p[1],'type':p[2],'shape':p[3],'at':fp_xy(pa),'size':fl(vals(p,'size')),'roundrect_ratio':float(vals(p,'roundrect_rratio',[0.25])[0]),
             'rotation':pa[2] if len(pa)>2 else 0,'drill':drill,
             'layers':vals(p,'layers'),'net':int(net[0]),'net_name':net[1] if len(net)>1 else ''}
        data['pads'].append(pad);pads.append(pad)
    # Retain physical symbol bounds and reference; exact body comes from CAD.
    data['footprints'].append({'reference':ref,'value':value,'library_name':fp[1],'at':xy(at),'rotation':at[2] if len(at)>2 else 0,'layer':vals(fp,'layer')[0],'pad_count':len(pads)})
for tag in ('gr_line','gr_arc','gr_rect'):
    for p in children(root,tag):
        if vals(p,'layer',[''])[0]!='Edge.Cuts':continue
        item={'type':tag[3:]}
        for key in ('start','mid','end'):
            if child(p,key):item[key]=point(p,key)
        data['outline'].append(item)
for z in children(root,'zone'):
    polygons=[]
    for p in children(z,'filled_polygon'):
        pts=child(p,'pts',[])
        polygons.append({'layer':vals(p,'layer',vals(z,'layer',['F.Cu']))[0],'points':[xy(pt[1:]) for pt in children(pts,'xy')]})
    data['zones'].append({'net':int(vals(z,'net')[0]),'net_name':vals(z,'net_name',[''])[0],'polygons':polygons})

for track in data['tracks']:
    z=15.02 if track['layer']=='F.Cu' else 13.38
    track['start_xyz']=[*track['start'],z];track['end_xyz']=[*track['end'],z]
for via in data['vias']:
    via['front_xyz']=[*via['at'],15.025];via['back_xyz']=[*via['at'],13.375]
(ROOT/'routing.json').write_text(json.dumps(data,separators=(',',':')))
print(json.dumps({'sha':data['source_sha256'],'counts':{k:len(data[k]) for k in ('tracks','vias','pads','footprints','outline','zones')}},indent=2))
