#!/usr/bin/env python3
"""Run the reviewed existing native driver and oracle against downloaded shipped bytes.
Usage: run-shipped-qualification.py APP SHIPPED_DIR HELPER_RECEIPT_DIR EXPECTED_COMMIT FRESH_OUTPUT
This script does not model physics, compile firmware, or alter any test threshold.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess, sys
here=Path(__file__).resolve().parent
app,shipped,helpers=map(lambda p:Path(p).resolve(),sys.argv[1:4])
commit=sys.argv[4];out=Path(sys.argv[5]).resolve()
archive=Path('/data/lw-quadrotor-examples-20261122/examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight')
archive_commit='cbb23bc84bf5d5f2e3ae1346893c99de14aa18fe'
archive_prefix='examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight/'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(here/'replay-shipped-native-world.mts')=='33a6eacc83065d950406cbc883e5dc4a56662956c20e2a1c753bff440f6ec6b2','Reviewed native replay adapter changed'
manifest=json.loads(subprocess.check_output(['git','show',archive_commit+':'+archive_prefix+'artifacts.json'],cwd=archive))
reader=archive/'capture/analyze-flight.py'
assert sha(reader)==manifest['files']['capture/analyze-flight.py']['sha256'],'Independent oracle changed'
download=json.loads((shipped/'download-receipt.json').read_text())
assert download['buildCommit']==commit,'Wrong intended deployed commit'
for asset in download['assets']:
 fingerprint=re.search(r'\.([0-9a-f]{12})\.(?:js|wasm)$',asset['url'])
 assert fingerprint and fingerprint.group(1)==asset['sha256'][:12],'Deployed asset URL content hash differs'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=app,text=True).strip()==commit,'Wrong app checkout'
assert sha(shipped/'build-manifest.json')==download['manifestSha256'],'Stored deployed manifest changed'
assert json.loads((shipped/'build-manifest.json').read_text())['commit']==commit,'Stored deployed commit changed'
# Pin the accepted plant, clock interpretation and bridge helpers as well as the driver.
baseline_app='3157a536da36051d5b1eec9a7c5dff6a720833b6'
runtime_paths=['packages/playground/src/mechanical/thrustBody.ts', 'packages/playground/src/mechanical/flightObservation.ts', 'packages/playground/src/mechanical/flightShaftLoad.ts', 'packages/playground/src/mechanical/flightRuntime.ts', 'packages/playground/src/mechanical/flightRuntimeSources.ts', 'packages/playground/src/mechanical/flightRuntimeObservation.ts', 'packages/playground/src/mechanical/useFlightRuntime.ts', 'packages/ui/src/wasm/simulator-bridge.ts', 'packages/ui/src/wasm/simulator-bridge-types.ts', 'packages/ui/src/wasm/world-adc-input.ts', 'packages/ui/src/wasm/can-bus-report.ts', 'packages/ui/src/wasm/wifiHostNet.ts', 'packages/ui/src/sim/instructionBreakpoints.ts', 'packages/ui/src/labtools/sourceDebug.ts']
runtime_sources={}
for path in runtime_paths:
 baseline_bytes=subprocess.check_output(['git','show',baseline_app+':'+path],cwd=app)
 assert (app/path).read_bytes()==baseline_bytes,'Qualified runtime source changed: '+path
 runtime_sources[path]=hashlib.sha256(baseline_bytes).hexdigest()
runtime_fingerprint=hashlib.sha256(json.dumps(runtime_sources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert runtime_fingerprint=='9944d448273fc900a40e0f4e404c9cee8a65de231dc612d34411808c74a59e9a','Reviewed runtime source identity changed'
out.mkdir(parents=False,exist_ok=False)
receipt={'kind':'deployed-engine-native-flight-qualification','expectedDeployedCommit':commit,
 'startedAt':datetime.now(timezone.utc).isoformat(),'nativeOraclePassed':False,'browserFlightPassed':False,
 'archiveCommit':archive_commit,'oracleSha256':sha(reader),'adapterSha256':sha(here/'replay-shipped-native-world.mts'),
 'downloadReceiptSha256':sha(shipped/'download-receipt.json'),'helperBuildReceiptSha256':sha(helpers/'helper-build-receipt.json'),
 'scenarioCountRequired':7,'scenarios':[],'modelClockOracleChanges':False,
 'qualifiedSourceBaselineAppCommit':baseline_app,'runtimeSourceManifestSha256':runtime_fingerprint,'runtimeSourceSha256':runtime_sources}
scenarios=[('nominal',15,'Infinity','button',5000),('nominal-fine',15,'Infinity','button',1000),
 *[('fault-'+name,10,'6',kind,5000) for name,kind in [('button','button'),('inverter','inverter_fault'),
 ('overcurrent','overcurrent_fault'),('undervoltage','undervoltage_fault'),('stall','stall')]]]
status=out/'qualification.json'
status.write_text(json.dumps(receipt,indent=2)+'\n')
for tag,duration,fault_time,fault_kind,batch in scenarios:
 scenario=out/tag;scenario.mkdir()
 env=dict(os.environ,LABWIRED_APP=str(app),LABWIRED_SHIPPED_RUNTIME=str(shipped),LABWIRED_REPLAY_HELPERS=str(helpers),LABWIRED_EVIDENCE_OUT=str(scenario))
 command=['node','--import',str(app/'node_modules/tsx/dist/loader.mjs'),str(here/'replay-shipped-native-world.mts'),
  str(duration),fault_time,tag,fault_kind,str(batch)]
 print('Starting '+tag,flush=True)
 with (scenario/'native.log').open('w') as log:
  native=subprocess.run(command,cwd=app,env=env,stdout=log,stderr=subprocess.STDOUT)
 result=scenario/(tag+'-result.json');oracle=scenario/(tag+'-oracle.json')
 oracle_exit=None;report=None
 if native.returncode==0 and result.exists():
  with (scenario/'oracle.log').open('w') as log:
   evaluated=subprocess.run([sys.executable,str(reader),str(result)],stdout=log,stderr=subprocess.STDOUT)
  oracle_exit=evaluated.returncode
  if oracle.exists():report=json.loads(oracle.read_text())
 passed=native.returncode==0 and oracle_exit==0 and bool(report and report.get('passed'))
 entry={'tag':tag,'durationSeconds':duration,'worldRoundsPerPoll':batch,'faultKind':fault_kind if fault_time!='Infinity' else None,
  'command':command,'nativeExit':native.returncode,'oracleExit':oracle_exit,'passed':passed,
  'files':{str(p.relative_to(out)):{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(scenario.iterdir()) if p.is_file()}}
 receipt['scenarios'].append(entry);status.write_text(json.dumps(receipt,indent=2)+'\n')
 print(tag+': '+('PASS' if passed else 'FAIL; remaining cases not run'),flush=True)
 if not passed:break
receipt['nativeOraclePassed']=len(receipt['scenarios'])==len(scenarios) and all(s['passed'] for s in receipt['scenarios'])
receipt['finishedAt']=datetime.now(timezone.utc).isoformat()
status.write_text(json.dumps(receipt,indent=2)+'\n')
sys.exit(0 if receipt['nativeOraclePassed'] else 1)
