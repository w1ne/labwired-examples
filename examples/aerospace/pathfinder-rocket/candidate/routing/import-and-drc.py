import hashlib,json,subprocess,pcbnew,re
from pathlib import Path
from collections import Counter
r=Path(__file__).resolve().parent
b=pcbnew.LoadBoard(str(r/'protected-source.kicad_pcb'))
assert pcbnew.ImportSpecctraSES(b,str(r/'strict.ses'))
pcbnew.SaveBoard(str(r/'strict.kicad_pcb'),b)
for ext in ['kicad_pro','kicad_dru']:(r/('strict.'+ext)).write_bytes((r/('rules.'+ext)).read_bytes())
result=subprocess.run(['kicad-cli','pcb','drc','--format','json','--exit-code-violations','--output',str(r/'strict-drc.json'),str(r/'strict.kicad_pcb')],capture_output=True,text=True)
drc=json.loads((r/'strict-drc.json').read_text())
assert (r/'strict.kicad_pro').read_bytes()==(r/'rules.kicad_pro').read_bytes()
plan=json.loads((r/'plan.json').read_text());by_net={n:c for c in plan['net_classes']for n in c['nets']};dim=[]
for t in b.GetTracks():
 rule=by_net[t.GetNetname()]
 if isinstance(t,pcbnew.PCB_VIA):
  actual={'diameter':pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)),'drill':pcbnew.ToMM(t.GetDrillValue())};req={'diameter':rule['via_diameter_mm'],'drill':rule['via_drill_mm']}
 else:actual={'width':pcbnew.ToMM(t.GetWidth())};req={'width':rule['track_width_mm']}
 for k,v in req.items():
  if actual[k]+1e-6<v:dim.append({'net':t.GetNetname(),'actual':actual,'minimum':req})
summary={'sourceSha256':hashlib.sha256((r/'protected-source.kicad_pcb').read_bytes()).hexdigest(),'routedSha256':hashlib.sha256((r/'strict.kicad_pcb').read_bytes()).hexdigest(),'routerSummary':re.findall(r'final score:[^\n]+',(r/'route.log.txt').read_text()),'drcExit':result.returncode,'geometricErrors':[x for x in drc['violations']if x['severity']=='error'],'unconnected':drc['unconnected_items'],'warnings':dict(Counter(x['type'] for x in drc['violations']if x['severity']!='error')),'dimensionViolations':dim,'trackCount':sum(not isinstance(t,pcbnew.PCB_VIA)for t in b.GetTracks()),'viaCount':sum(isinstance(t,pcbnew.PCB_VIA)for t in b.GetTracks())}
(r/'route-drc-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
