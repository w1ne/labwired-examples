"""Create deterministic, planar visual copper meshes from extracted native routing.

Track widths, pad sizes, hole diameters and positions remain at source dimensions.
Ground fills remain available in routing.json but are not rendered in this overlay.
"""
from pathlib import Path
import json, math, argparse
from collections import defaultdict

parser=argparse.ArgumentParser()
parser.add_argument('--work-dir',type=Path,default=Path(__file__).resolve().parent)
ROOT=parser.parse_args().work_dir.resolve()
data=json.loads((ROOT/'routing.json').read_text())
groups=defaultdict(lambda:{'positions':[],'normals':[],'indices':[],'primitives':0})

def rounded_rect(w,h,r,steps=8):
    r=max(0,min(r,w/2,h/2));points=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for i in range(steps+1):
            a=math.radians(start+i*90/steps);p=(cx+r*math.cos(a),cy+r*math.sin(a))
            if not points or math.dist(points[-1],p)>1e-9:points.append(p)
    if math.dist(points[0],points[-1])<1e-9:points.pop()
    return points

def circle(r,n=40):return [(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n)) for i in range(n)]

def add_polygon(points,at,angle,z,layer,net,hole=0,kind='pad'):
    """Fan fill, or radial annulus for convex copper pads with circular drill."""
    g=groups[(layer,int(net))];g['primitives']+=1
    # Sorting the convex contour by polar angle yields a valid fan/annulus.
    pts=sorted(points,key=lambda p:math.atan2(p[1],p[0]));n=len(pts)
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle));verts=[]
    for x,y in pts:verts.append([at[0]+x*c-y*s,at[1]+x*s+y*c,z])
    triangles=[]
    if hole>0:
        for x,y in pts:
            a=math.atan2(y,x);xx,yy=hole/2*math.cos(a),hole/2*math.sin(a)
            verts.append([at[0]+xx*c-yy*s,at[1]+xx*s+yy*c,z])
        for i in range(n):
            j=(i+1)%n;triangles.extend([(i,j,n+i),(j,n+j,n+i)])
    else:
        verts.append([at[0],at[1],z])
        triangles.extend((n,i,(i+1)%n)for i in range(n))
    offset=len(g['positions'])//3
    for p in verts:g['positions'].extend(round(v,6) for v in p)
    normal=[0,0,1 if layer=='F.Cu' else -1]
    for _ in verts:g['normals'].extend(normal)
    for tri in triangles:
        if layer=='B.Cu':tri=tri[::-1]
        g['indices'].extend(offset+i for i in tri)

for seg in data['tracks']:
    a,b=seg['start'],seg['end'];length=math.dist(a,b)
    if length<1e-8:continue
    # Capsule gives round trace endcaps using the original trace width.
    width=seg['width'];angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
    add_polygon(rounded_rect(length+width,width,width/2),[(a[0]+b[0])/2,(a[1]+b[1])/2],angle,seg['start_xyz'][2],seg['layer'],seg['net'],kind='track')

for p in data['pads']:
    if p['type']=='np_thru_hole':continue
    w,h=p['size'];shape=p['shape']
    if shape=='circle':outline=circle(w/2)
    else:
        r=min(w,h)/2 if shape=='oval' else min(w,h)*p.get('roundrect_ratio',0.25) if shape=='roundrect' else 0
        outline=rounded_rect(w,h,r)
    layers=p['layers']
    for layer in ('F.Cu','B.Cu'):
        if '*.Cu' not in layers and layer not in layers:continue
        add_polygon(outline,p['at'],p['rotation'],15.025 if layer=='F.Cu' else 13.375,layer,p['net'],p['drill'])

for via in data['vias']:
    for layer in ('F.Cu','B.Cu'):
        add_polygon(circle(via['diameter']/2),via['at'],0,15.03 if layer=='F.Cu' else 13.37,layer,via['net'],via['drill'],kind='via')

meshes=[]
for (layer,net),g in sorted(groups.items()):
    meshes.append({'name':f'copper-{layer}-net{net}','layer':layer,'net':net,'net_name':data['nets'].get(str(net),''),'color':'#c8aa58' if layer=='F.Cu' else '#bc944b',**g})
result={'schema':'labwired.copper-mesh.v1','source_sha256':data['source_sha256'],'coordinates':data['frame'],
        'rendering':{'copper_z_offset_mm':0.02,'hole_resolution':40,'track_width_scale':1,'pad_size_scale':1,'ground_fill_rendered':False,'highlight_net':12,'highlight_meaning':'Selected physical PB6 / RIGHT connection; not a current or timing measurement'},'meshes':meshes}
(ROOT/'copper-mesh.json').write_text(json.dumps(result,separators=(',',':')))
print(json.dumps({'groups':len(meshes),'vertices':sum(len(m['positions'])//3 for m in meshes),'triangles':sum(len(m['indices'])//3 for m in meshes),'file_bytes':(ROOT/'copper-mesh.json').stat().st_size}))
