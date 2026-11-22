"""Re-run KiCad DRC on the exact final native file without rewriting the board.
The earlier router log remains a separate observation. Requires KiCad 10.0.8.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,re,subprocess
import pcbnew
root=Path(__file__).resolve().parent
pcb=root/'pathfinder-routed.kicad_pcb'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
inputs=[pcb,root/'pathfinder-routed.kicad_pro',root/'pathfinder-routed.kicad_dru']
before={p.name:sha(p) for p in inputs}
for ext in ['kicad_pro','kicad_dru']:
 if (root/('pathfinder-routed.'+ext)).read_bytes()!=(root/('rules.'+ext)).read_bytes():
  raise RuntimeError('Final native rules differ from the retained generated rules')
result=subprocess.run(['kicad-cli','pcb','drc','--format','json','--exit-code-violations','--output',str(root/'identity-corrected-drc.json'),str(pcb)],capture_output=True,text=True)
drc=json.loads((root/'identity-corrected-drc.json').read_text())
if before!={p.name:sha(p) for p in inputs}:raise RuntimeError('DRC changed the source PCB or rules')
board=pcbnew.LoadBoard(str(pcb));plan=json.loads((root/'plan.json').read_text())
classes={net:entry for entry in plan['net_classes'] for net in entry['nets']}
dimensions=[]
for item in board.GetTracks():
 rule=classes[item.GetNetname()]
 actual={'diameter':pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)),'drill':pcbnew.ToMM(item.GetDrillValue())} if isinstance(item,pcbnew.PCB_VIA) else {'width':pcbnew.ToMM(item.GetWidth())}
 minimum={'diameter':rule['via_diameter_mm'],'drill':rule['via_drill_mm']} if isinstance(item,pcbnew.PCB_VIA) else {'width':rule['track_width_mm']}
 if any(actual[key]+1e-6<value for key,value in minimum.items()):dimensions.append({'net':item.GetNetname(),'actual':actual,'minimum':minimum})
identity=json.loads((root/'native-identity-correction.json').read_text())
summary={'schema':'pathfinder.final-native-drc.v1','scope':'Independent final-file DRC after identity-only correction; retained router log is not a routing acceptance claim.',
 'sourceSha256':sha(root/'protected-source.kicad_pcb'),'unroutedSourceSha256':sha(root.parent/'pathfinder-unrouted.kicad_pcb'),
 'routedSha256':sha(pcb),'routingRunRoutedSha256':identity['source_pcb_sha256'],'identityCorrection':'native-identity-correction.json',
 'planSha256':sha(root/'plan.json'),'ruleFileSha256':{p.name:before[p.name] for p in inputs[1:]},'rulesUnchangedByDrc':True,'kicadVersion':pcbnew.Version(),
 'routerSummary':re.findall(r'final score:[^\n]+',(root/'route.log.txt').read_text()),'drcExit':result.returncode,
 'geometricErrors':[item for item in drc['violations'] if item['severity']=='error'],'unconnected':drc['unconnected_items'],
 'warnings':dict(Counter(item['type'] for item in drc['violations'] if item['severity']!='error')),'dimensionViolations':dimensions,
 'trackCount':sum(not isinstance(item,pcbnew.PCB_VIA) for item in board.GetTracks()),'viaCount':sum(isinstance(item,pcbnew.PCB_VIA) for item in board.GetTracks()),
 'schematicParityChecked':False}
(root/'route-drc-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
if result.returncode not in (0,5) or summary['geometricErrors'] or summary['unconnected'] or dimensions:
 raise RuntimeError('Final native DRC or dimension gate rejected; receipt retained')
