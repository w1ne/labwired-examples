#!/usr/bin/python3
"""Route this carrier's KiCad netlist using a clearance-aware two-layer grid.

KiCad DRC remains the authority. This generator is an example build utility,
not a new LabWired API or simulator. Tracks0.25mm, vias0.6/0.3mm, clearance0.2mm.
"""
import pcbnew as p
import numpy as np
from pathlib import Path
import json,math,heapq,time
ROOT=Path(__file__).resolve().parent
board=p.LoadBoard(str(ROOT/'handheld-carrier-unrouted.kicad_pcb'))
layout=json.loads((ROOT/'carrier-layout.json').read_text())
G=.2;NX=391;NY=661
grid=np.zeros((2,NY,NX),dtype=np.int16)
ys,xs=np.mgrid[:NY,:NX];xx=xs*G;yy=ys*G
inside=np.zeros((NY,NX),bool)
outline=layout['outline']
for (x1,y1),(x2,y2) in zip(outline,outline[1:]+outline[:1]):
    if y1==y2:continue
    inside^=((y1>yy)!=(y2>yy)) & (xx<(x2-x1)*(yy-y1)/(y2-y1)+x1)
# Keep routing centers0.75mm from the outline, including concave corners.
safe=inside.copy()
for dy in range(-4,5):
    for dx in range(-4,5):
        if dx*dx+dy*dy>16:continue
        safe &= np.roll(np.roll(inside,dy,0),dx,1)
grid[:,~safe]=-1
def point(x,y):return int(round(x/G)),int(round(y/G))
def mmxy(v):return p.ToMM(v.x),p.ToMM(v.y)
pad_groups={}
for f in board.GetFootprints():
    for pad in f.Pads():
        x,y=mmxy(pad.GetPosition());bb=pad.GetBoundingBox();sx,sy=p.ToMM(bb.GetWidth()),p.ToMM(bb.GetHeight())
        net=pad.GetNetCode();owner=net if net else -2
        if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:owner=-3
        layers=[0,1] if pad.GetAttribute()!=p.PAD_ATTRIB_SMD else ([1] if f.IsFlipped() else [0])
        clearance=.2+.125+.04
        ix0=max(0,int((x-sx/2-clearance)/G));ix1=min(NX-1,int(math.ceil((x+sx/2+clearance)/G)))
        iy0=max(0,int((y-sy/2-clearance)/G));iy1=min(NY-1,int(math.ceil((y+sy/2+clearance)/G)))
        for l in layers:grid[l,iy0:iy1+1,ix0:ix1+1]=owner
        if net:pad_groups.setdefault(net,[]).append({'name':f'{f.GetReference()}.{pad.GetNumber()}','x':x,'y':y,'layers':layers})

def valid(l,x,y,net):return 0<=x<NX and 0<=y<NY and (grid[l,y,x]==0 or grid[l,y,x]==net)
def via_ok(x,y,net):
    for dy in range(-1,2):
        for dx in range(-1,2):
            if not all(valid(l,x+dx,y+dy,net) for l in(0,1)):return False
    return True
def encode(l,x,y):return l*NX*NY+y*NX+x
def decode(k):l,k=divmod(k,NX*NY);y,x=divmod(k,NX);return l,x,y
def astar(a,z,net):
    ax,ay=point(a['x'],a['y']);zx,zy=point(z['x'],z['y'])
    goals={encode(l,zx,zy) for l in z['layers']}
    q=[];dist={};prev={};counter=0
    for l in a['layers']:
        k=encode(l,ax,ay);dist[k]=0;heapq.heappush(q,(abs(ax-zx)+abs(ay-zy),0,k))
    while q:
        _,cost,k=heapq.heappop(q)
        if cost!=dist.get(k):continue
        if k in goals:
            route=[]
            while True:
                route.append(decode(k))
                if k not in prev:break
                k=prev[k]
            return route[::-1]
        l,x,y=decode(k)
        neighbors=[(l,x+1,y,1),(l,x-1,y,1),(l,x,y+1,1),(l,x,y-1,1)]
        if via_ok(x,y,net):neighbors.append((1-l,x,y,15))
        for ll,xx,yy,extra in neighbors:
            if not valid(ll,xx,yy,net):continue
            kk=encode(ll,xx,yy);new=cost+extra
            if new<dist.get(kk,1e30):
                dist[kk]=new;prev[kk]=k;h=abs(xx-zx)+abs(yy-zy)+(0 if ll in z['layers'] else 15)
                heapq.heappush(q,(new+h,new,kk))
        counter+=1
        if counter>700000:break
    return None

def add_track(a,z,l,net):
    if abs(a[0]-z[0])+abs(a[1]-z[1])<1e-7:return
    t=p.PCB_TRACK(board);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu if l==0 else p.B_Cu);t.SetNetCode(net);board.Add(t)
def add_path(path,a,z,net):
    for l,x,y in path:
        for dy in range(-3,4):
            for dx in range(-3,4):
                if dx*dx+dy*dy>9:continue
                if 0<=y+dy<NY and 0<=x+dx<NX and grid[l,y+dy,x+dx]==0:grid[l,y+dy,x+dx]=net
    add_track((a['x'],a['y']),(path[0][1]*G,path[0][2]*G),path[0][0],net)
    start=path[0];last=path[0];direction=None
    for item in path[1:]:
        l,x,y=item;ll,lx,ly=last
        if l!=ll:
            add_track((start[1]*G,start[2]*G),(lx*G,ly*G),ll,net)
            via=p.PCB_VIA(board);via.SetPosition(p.VECTOR2I(p.FromMM(x*G),p.FromMM(y*G)));via.SetWidth(p.F_Cu,p.FromMM(.6));via.SetWidth(p.B_Cu,p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(net);board.Add(via)
            start=item;direction=None
        else:
            d=(x-lx,y-ly)
            if direction is not None and d!=direction:
                add_track((start[1]*G,start[2]*G),(lx*G,ly*G),l,net);start=last
            direction=d
        last=item
    add_track((start[1]*G,start[2]*G),(last[1]*G,last[2]*G),last[0],net)
    add_track((last[1]*G,last[2]*G),(z['x'],z['y']),last[0],net)

# Reserve a short outward fanout for every connected module pin before routing.
# This prevents an earlier net from blocking escape from a later header pin.
for net,pads in pad_groups.items():
    if board.FindNet(net).GetNetname()=='GND':continue
    for a in pads:
        if not a['name'].startswith('A1.') or int(a['name'].split('.')[1])>40:continue
        ox,oy=a['x'],a['y'];ex=27.0 if ox<39 else 52.0
        add_track((ox,oy),(ex,oy),1,net)
        ix0,iy=point(min(ox,ex),oy);ix1,_=point(max(ox,ex),oy)
        for ix in range(ix0,ix1+1):
            for dy in range(-3,4):
                for dx in range(-3,4):
                    if dx*dx+dy*dy<=9 and 0<=iy+dy<NY and 0<=ix+dx<NX and grid[1,iy+dy,ix+dx]==0:grid[1,iy+dy,ix+dx]=net
        a['x']=ex;a['layers']=[1]
done=[];failed=[];t0=time.time()
order=sorted(pad_groups,key=lambda n:(board.FindNet(n).GetNetname()=='GND',-len(pad_groups[n])))
for net in order:
    if board.FindNet(net).GetNetname()=='GND':continue
    pending=pad_groups[net][:];connected=[pending.pop(0)]
    while pending:
        _,i,a=min(((abs(a['x']-z['x'])+abs(a['y']-z['y']),i,a) for i,z in enumerate(pending) for a in connected),key=lambda t:t[0])
        z=pending.pop(i);path=astar(a,z,net)
        label=f'{board.FindNet(net).GetNetname()} {a["name"]}->{z["name"]}'
        if path is None:failed.append(label);print('UNROUTED',label,flush=True)
        else:add_path(path,a,z,net);done.append(label);print('ROUTED',label,len(path),flush=True)
        connected.append(z)
# Ground uses KiCad-filled copper planes. The zone engine applies precise pad,
# track, drill and board-edge clearances; GND does not need grid-routed tracks.
gnd=next(n for n in pad_groups if board.FindNet(n).GetNetname()=='GND')
# Give the ground pin an explicit escape below the dense LCD connector.
# Neighboring signal pads constrain the thermal spokes at this one position.
add_track((58,17),(58,22),0,gnd)
# Stitch the upper module-header ground region to the opposite copper plane.
stitch=p.PCB_VIA(board);stitch.SetPosition(p.VECTOR2I(p.FromMM(40),p.FromMM(6)))
stitch.SetWidth(p.F_Cu,p.FromMM(.6));stitch.SetWidth(p.B_Cu,p.FromMM(.6))
stitch.SetDrill(p.FromMM(.3));stitch.SetViaType(p.VIATYPE_THROUGH)
stitch.SetLayerPair(p.F_Cu,p.B_Cu);stitch.SetNetCode(gnd);board.Add(stitch)
for f in board.GetFootprints():
    if f.GetReference()=='J1':
        for pad in f.Pads():
            if pad.GetNumber()=='2':pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
for layer in (p.F_Cu,p.B_Cu):
    zone=p.ZONE(board);zone.SetLayer(layer);zone.SetNetCode(gnd)
    zone.SetLocalClearance(p.FromMM(.25));zone.SetThermalReliefGap(p.FromMM(.25))
    zone.SetThermalReliefSpokeWidth(p.FromMM(.35));zone.SetMinThickness(p.FromMM(.2))
    zone.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
    poly=zone.Outline();poly.NewOutline()
    for x,y in outline:poly.Append(p.FromMM(x),p.FromMM(y))
    board.Add(zone)
p.ZONE_FILLER(board).Fill(board.Zones())
p.SaveBoard(str(ROOT/'handheld-carrier.kicad_pcb'),board)
out={'routed_connections':len(done),'unrouted_connections':len(failed),'ground_strategy':'KiCad-filled F.Cu and B.Cu planes, 0.25 mm local clearance','failures':failed,'seconds':round(time.time()-t0,2),'track_width_mm':.25,'clearance_mm':.2,'via_diameter_mm':.6,'via_drill_mm':.3,'grid_mm':G,'status':'DRC required'}
(ROOT/'routing-report.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
