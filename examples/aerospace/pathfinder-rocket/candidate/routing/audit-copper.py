"""Audit exact native copper. Path estimates exclude contact/pad spreading and thermal proof."""
import pcbnew,json,hashlib,math,heapq
from pathlib import Path
from collections import defaultdict,Counter
root=Path(__file__).resolve().parent
b=pcbnew.LoadBoard(str(root/'pathfinder-routed.kicad_pcb'));source=pcbnew.LoadBoard(str(root.parent/'pathfinder-unrouted.kicad_pcb'))
mm=lambda p:(p.x/1e6,p.y/1e6)
def pins(board):
 return {(f.GetReference(),p.GetNumber()):(p.GetNetname(),mm(p.GetPosition()),tuple(p.GetSize()),tuple(p.GetDrillSize()),p.GetOrientationDegrees(),tuple(p.GetLayerSet().Seq()))for f in board.GetFootprints()for p in f.Pads()}
if pins(b)!=pins(source):raise RuntimeError('routing changed a native pad, layer, drill or electrical assignment')
plan=json.loads((root/'plan.json').read_text());rules={n:c for c in plan['net_classes']for n in c['nets']}
tracks=[];vias=[];pads=[]
for f in b.GetFootprints():
 for p in f.Pads():
  pads.append({'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetname(),'point':mm(p.GetPosition()),'size_mm':[v/1e6 for v in p.GetSize()],'angle_deg':p.GetOrientationDegrees(),'drill_mm':[v/1e6 for v in p.GetDrillSize()],'layers':[l for l in (pcbnew.F_Cu,pcbnew.B_Cu)if p.IsOnLayer(l)],'pad':p})
for item in b.GetTracks():
 net=item.GetNetname();r=rules[net]
 if isinstance(item,pcbnew.PCB_VIA):
  v={'net':net,'point':mm(item.GetPosition()),'diameter_mm':item.GetWidth(pcbnew.F_Cu)/1e6,'drill_mm':item.GetDrillValue()/1e6,'locked':item.IsLocked()};vias.append(v)
  if v['diameter_mm']+1e-6<r['via_diameter_mm'] or v['drill_mm']+1e-6<r['via_drill_mm']:raise RuntimeError('Via is below its declared class dimensions')
 else:
  t={'net':net,'a':mm(item.GetStart()),'b':mm(item.GetEnd()),'layer':item.GetLayer(),'width_mm':item.GetWidth()/1e6,'length_mm':item.GetLength()/1e6,'locked':item.IsLocked()};tracks.append(t)
  if t['width_mm']+1e-6<r['track_width_mm']:raise RuntimeError('Track is below its declared class width')
sha=hashlib.sha256((root/'pathfinder-routed.kicad_pcb').read_bytes()).hexdigest()
drc_summary=json.loads((root/'route-drc-summary.json').read_text())
if drc_summary['routedSha256']!=sha or drc_summary['geometricErrors'] or drc_summary['unconnected'] or drc_summary['dimensionViolations']:
 raise RuntimeError('DRC receipt does not accept this exact native board')
via_holes={'pcb_sha256':sha,'kicad_version':pcbnew.Version(),'via_count':len(vias),'holes':[{'x':v['point'][0],'y':v['point'][1],'drill':v['drill_mm'],'net':v['net']}for v in vias]}
(root/'routed-via-holes.json').write_text(json.dumps(via_holes,indent=2)+'\n')
def sub(a,b):return(a[0]-b[0],a[1]-b[1])
def plus(a,b):return(a[0]+b[0],a[1]+b[1])
def mul(a,s):return(a[0]*s,a[1]*s)
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def lerp(t,u):return plus(t['a'],mul(sub(t['b'],t['a']),u))
def project(t,p):
 d=sub(t['b'],t['a']);return max(0.,min(1.,dot(sub(p,t['a']),d)/max(1e-20,dot(d,d))))
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
RHO=1.724e-5;THICKNESS=.07;PLATING=.018
all_paths=[];graph_facts=[]
for net in ['+','GND','N$11','+5V','N$9','+3V3']:
 ts=[dict(t,splits={0.,1.})for t in tracks if t['net']==net];ps=[p for p in pads if p['net']==net];vs=[v for v in vias if v['net']==net]
 g=defaultdict(dict);contacts=[]
 def node(layer,p):return(layer,round(p[0],4),round(p[1],4))
 def edge(a,b,kind,length=0.,width=None,drill=None,ref=None):
  if a==b:return
  if kind in ['track','overlap']:
   nominal=RHO*length/(width*THICKNESS);tol=nominal/.8
  elif kind in ['via','plated-pad']:
   nominal=RHO*1.6/(math.pi*drill*PLATING);tol=nominal*1.1
  else:nominal=tol=0.
  v={'kind':kind,'length_mm':length,'width_mm':width,'drill_mm':drill,'ref':ref,'nominal_ohm':nominal,'width_tolerance_ohm':tol}
  if b not in g[a] or g[a][b]['width_tolerance_ohm']>tol:g[a][b]=v;g[b][a]=v
 for i,t in enumerate(ts):
  for u in ts[i+1:]:
   if t['layer']!=u['layer']:continue
   dt,du=sub(t['b'],t['a']),sub(u['b'],u['a']);den=cross(dt,du)
   if abs(den)>1e-12:
    q=sub(u['a'],t['a']);a,bp=cross(q,du)/den,cross(q,dt)/den
    if -1e-9<=a<=1+1e-9 and -1e-9<=bp<=1+1e-9:
     a=max(0,min(1,a));bp=max(0,min(1,bp));t['splits'].add(a);u['splits'].add(bp);contacts.append((t,a,u,bp,0.));continue
   choices=[]
   for a in [0.,1.]:
    p=lerp(t,a);bp=project(u,p);choices.append((dist(p,lerp(u,bp)),a,bp))
   for bp in [0.,1.]:
    p=lerp(u,bp);a=project(t,p);choices.append((dist(p,lerp(t,a)),a,bp))
   for gap,a,bp in choices:
    if gap<=.00011:
     t['splits'].add(a);u['splits'].add(bp);contacts.append((t,a,u,bp,gap))
 for t in ts:
  for p in ps:
   if t['layer']not in p['layers']:continue
   candidates={0.,1.,project(t,p['point'])}
   for at in candidates:
    xy=lerp(t,at)
    if p['pad'].HitTest(pcbnew.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6))):
     t['splits'].add(at);edge(node(t['layer'],xy),('pad',p['ref'],p['pin'],t['layer']),'pad-contact',ref=p['ref']+'.'+p['pin'])
  for v in vs:
   at=project(t,v['point']);xy=lerp(t,at)
   if dist(xy,v['point'])<=v['diameter_mm']/2+1e-6:
    t['splits'].add(at);edge(node(t['layer'],xy),node(t['layer'],v['point']),'via-contact')
 for t,a,u,bp,gap in contacts:edge(node(t['layer'],lerp(t,a)),node(u['layer'],lerp(u,bp)),'overlap',length=gap,width=min(t['width_mm'],u['width_mm']))
 for t in ts:
  ss=sorted(t['splits'])
  for x,y in zip(ss,ss[1:]):edge(node(t['layer'],lerp(t,x)),node(t['layer'],lerp(t,y)),'track',length=t['length_mm']*(y-x),width=t['width_mm'])
 for v in vs:edge(node(pcbnew.F_Cu,v['point']),node(pcbnew.B_Cu,v['point']),'via',drill=v['drill_mm'])
 for p in ps:
  if len(p['layers'])==2 and min(p['drill_mm'])>0:edge(('pad',p['ref'],p['pin'],pcbnew.F_Cu),('pad',p['ref'],p['pin'],pcbnew.B_Cu),'plated-pad',drill=min(p['drill_mm']),ref=p['ref']+'.'+p['pin'])
 queries={'+':[('J7','1','J2','1',2.9),('J7','1','J5','1',1.532567)],'GND':[('Q1','2','J7','2',2.9),('J5','2','J7','2',1.532567),('J5','4','J7','2',1.0)],'N$11':[('J2','2','Q1','3',2.9)],'+5V':[('J5','3','A1','18',1.0),('J5','3','A1','40',1.0),('J5','3','Q3','2',1.0)],'N$9':[('Q3','3','J3','1',1.0)],'+3V3':[('A1','20','J1','1',.25),('A1','20','U1','1',.25)]}[net]
 for ar,ap,br,bp,current in queries:
  start=('pad',ar,ap,pcbnew.F_Cu);end=('pad',br,bp,pcbnew.F_Cu);seen={start:0.};prev={};heap=[(0.,0,start)];seq=0
  while heap:
   cost,_,n=heapq.heappop(heap)
   if cost>seen[n]+1e-18:continue
   if n==end:break
   for nxt,e in g[n].items():
    nc=cost+e['width_tolerance_ohm']
    if nc+1e-18<seen.get(nxt,math.inf):seq+=1;seen[nxt]=nc;prev[nxt]=(n,e);heapq.heappush(heap,(nc,seq,nxt))
  if end not in seen:raise RuntimeError(str((net,ar,ap,br,bp,'path graph incomplete; do not invent a result')))
  path=[];n=end
  while n!=start:old,e=prev[n];path.append({**e,'from':old,'to':n});n=old
  path.reverse();nom=sum(e['nominal_ohm']for e in path);tol=sum(e['width_tolerance_ohm']for e in path)
  row={'net':net,'from':ar+'.'+ap,'to':br+'.'+bp,'track_length_mm':sum(e['length_mm']for e in path if e['kind']in ['track','overlap']),'minimum_track_width_mm':min(e['width_mm']for e in path if e['width_mm']),'vias':sum(e['kind']=='via'for e in path),'plated_pad_transitions':sum(e['kind']=='plated-pad'for e in path),'nominal_copper_ohm':nom,'width_tolerance_copper_ohm':tol,'single_path_scenario_a':current,'single_path_drop_v':tol*current,'single_path_loss_w':tol*current**2,'five_amp_path_drop_v':tol*5 if net in ['+','GND']else None,'path':path};all_paths.append(row)
 graph_facts.append({'net':net,'nodes':len(g),'edges':sum(map(len,g.values()))//2,'track_count':len(ts),'via_count':len(vs)})
summary={'pcb_sha256':sha,'unrouted_source_sha256':hashlib.sha256((root.parent/'pathfinder-unrouted.kicad_pcb').read_bytes()).hexdigest(),'plan_sha256':hashlib.sha256((root/'plan.json').read_bytes()).hexdigest(),'rule_file_sha256':{ext:hashlib.sha256((root/('rules.'+ext)).read_bytes()).hexdigest()for ext in ['kicad_pro','kicad_dru']},'drc_summary_sha256':hashlib.sha256((root/'route-drc-summary.json').read_bytes()).hexdigest(),'local_drc_exit':drc_summary['drcExit'],'local_drc_warning_counts':drc_summary['warnings'],'local_drc_exit_reason':str(sum(drc_summary['warnings'].values()))+' warnings; zero errors and zero unconnected items; see the exact DRC summary','local_drc_schematic_parity_checked':False,'kicad_version':pcbnew.Version(),'native_pads_identical_to_unrouted_source':True,'track_count':len(tracks),'via_count':len(vias),'all_declared_dimension_minima_pass':True,'track_nets':{net:{'track_count':sum(t['net']==net for t in tracks),'total_track_mm':sum(t['length_mm']for t in tracks if t['net']==net),'minimum_width_mm':min(t['width_mm']for t in tracks if t['net']==net),'via_drills_mm':sorted(set(v['drill_mm']for v in vias if v['net']==net))}for net in sorted(set(t['net']for t in tracks))},'assumptions':{'copper_resistivity_ohm_mm_at_20C':RHO,'copper_thickness_mm_nominal_not_guaranteed_minimum':THICKNESS,'minimum_width_fraction':.8,'via_plating_mm_assumed_average':PLATING,'nominal_board_thickness_mm':1.6,'maximum_thickness_factor_used_for_via_resistance':1.1},'limitations':['Centerline path resistance is a geometry estimate, not an electrothermal simulation or measured voltage drop.','Each scenario applies the stated current to one path. Concurrent branches can share copper; their full current distribution and temperature are not solved.','Pad spreading, solder/contact resistance, source/load leads, MOSFET channel/package, cable and connector resistance are excluded.','The 0.25 A 3V3 row is illustrative only; startup/SD/current demand and regulator thermal margin are unmeasured.','All PCB/via/terminal current, voltage sag, peak camera current and thermal qualification remain open.'],'graph_facts':graph_facts,'paths':all_paths,'power_pads':[{k:v for k,v in p.items()if k!='pad'}for p in pads if p['net']in ['+','GND','N$11','+5V','N$9'] and p['ref']in ['J7','J5','J2','Q1','Q3','J3']]}
(root/'actual-copper-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'sha256':sha,'tracks':len(tracks),'vias':len(vias),'paths':[{k:v for k,v in p.items()if k!='path'}for p in all_paths]},indent=2))
