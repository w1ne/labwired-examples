#!/usr/bin/env python3
"""Project passive Studio observations into the unchanged nominal oracle input.

Input receipt is from the actual browser run, not the staged payload. Required keys:
 scopeId, epoch, projectId, contentHash, loadedProjectHash, projectReadbackPassed,
 eventsPath, captureOverflow, captureErrors, statusAfterPause, finalWorldHealth,
 assets [{name, sha256, ...}], deployedBuildCommit, qualificationPath,
 qualificationSha256. The harness must retain actual response bytes/hashes.
 No trajectory or motor value is synthesized. No simulation is performed.
"""
import hashlib,json,sys
from pathlib import Path
here=Path(__file__).resolve().parent
receipt_path=Path(sys.argv[1]).resolve()
r=json.loads(receipt_path.read_text())
wanted=json.loads((here/'staged-promotion-receipt.json').read_text())
expected_elf={
 'ctrl1.elf':'240155b860d41d759596edef458e2fe47096835dca7a0ff39a3bac4dc44eb32e',
 'ctrl2.elf':'1f9d80b4242e7e105bb38d588f6556e3c746ad49d35ed462ab3623c98ea405fc',
 'ctrl3.elf':'f3023e937128803b3e5ef08c8b56f6773d6e0752359e15dd113764486bacd0ff',
 'ctrl4.elf':'8db11d2019889f06439719c4eff6aa1f1f2328cfd64bf3100f6778fc56b09819',
 'fc.elf':'b9f18c4e44c808762b83deeea77b2c5988c384f0a55acda47b1391a305406620'}
# The normal deployment optimizes WASM. Accept only the actual shipped engine
# after all seven unchanged native scenarios qualify those exact response bytes.
qualification_path=(receipt_path.parent/r['qualificationPath']).resolve()
qualification_bytes=qualification_path.read_bytes()
assert hashlib.sha256(qualification_bytes).hexdigest()==r['qualificationSha256'], 'Native qualification receipt changed'
qualified=json.loads(qualification_bytes)
assert qualified['kind']=='deployed-engine-native-flight-qualification' and qualified['nativeOraclePassed'], 'Actual deployed engine is not qualified'
assert qualified['expectedDeployedCommit']==r['deployedBuildCommit'], 'Browser and qualified deployment differ'
assert qualified['oracleSha256']=='2cdbc99ff9467743b9ceff4e9857276b2aef9e2128512f3a02c26c9ac8f32ae0', 'Qualification used a different oracle'
assert qualified['adapterSha256']=='33a6eacc83065d950406cbc883e5dc4a56662956c20e2a1c753bff440f6ec6b2', 'Qualification used a different native replay adapter'
assert qualified['qualifiedSourceBaselineAppCommit']=='3157a536da36051d5b1eec9a7c5dff6a720833b6', 'Qualification changed the accepted runtime baseline'
assert hashlib.sha256(json.dumps(qualified['runtimeSourceSha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest()=='9944d448273fc900a40e0f4e404c9cee8a65de231dc612d34411808c74a59e9a', 'Qualified runtime source identities differ'
expected_tags={'nominal','nominal-fine','fault-button','fault-inverter','fault-overcurrent','fault-undervoltage','fault-stall'}
assert len(qualified['scenarios'])==7 and {e['tag'] for e in qualified['scenarios']}==expected_tags, 'Native qualification is incomplete'
expected_assets=None
for scenario in qualified['scenarios']:
 assert scenario['passed'] and scenario['nativeExit']==0 and scenario['oracleExit']==0, 'Native qualification contains a failure'
 for relative,identity in scenario['files'].items():
  artifact=(qualification_path.parent/relative).read_bytes()
  assert len(artifact)==identity['size'] and hashlib.sha256(artifact).hexdigest()==identity['sha256'], 'Qualified native evidence changed: '+relative
 tag=scenario['tag']
 source=json.loads((qualification_path.parent/tag/(tag+'-result.json')).read_text())
 oracle=json.loads((qualification_path.parent/tag/(tag+'-oracle.json')).read_text())
 assert oracle['passed'] and all(oracle['checks'].values()), 'Independent native oracle did not pass'
 assert source['deployedBuildCommit']==r['deployedBuildCommit'] and source['coreCommit']==wanted['coreCommit'], 'Native source commit differs'
 current_assets={a['name']:a['sha256'] for a in source['assets']}
 if expected_assets is None:expected_assets=current_assets
 assert current_assets==expected_assets, 'Native scenarios used different executable bytes'
assert all(expected_assets.get(k)==v for k,v in expected_elf.items()), 'Native qualification changed the accepted firmware'
assert set(expected_assets)==set(expected_elf)|{'candidate-wasm.wasm','candidate-wasm.mjs'}, 'Unexpected native qualification asset set'
assets={a['name']:a['sha256'] for a in r['assets']}
assert all(assets.get(k)==v for k,v in expected_assets.items()), 'Browser executable bytes do not match accepted assets'
assert r['projectId']==wanted['projectId'] and r['contentHash']==r['loadedProjectHash'], 'Wrong loaded project revision'
assert r['projectReadbackPassed'] and r['contentHash']!=wanted['expectedContentHash'], 'Candidate readback is unproven'
assert r['captureOverflow']==0 and not r['captureErrors'], 'Capture lost observations'
assert r['statusAfterPause']=='paused', 'Final UI pause was not observed'
world=r['finalWorldHealth']
assert set(world['nodes'])=={'ctrl1','ctrl2','ctrl3','ctrl4','fc'}, 'Wrong native World node set'
assert min(world['nodes'].values())>=1_200_000_000, 'Not every 80 MHz native MCU reached 15 seconds'
events_path=receipt_path.parent/r['eventsPath']
events=[json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
scope_events=[e for e in events if e.get('scopeId')==r['scopeId']]
assert scope_events and scope_events[0]['sequence']==1, 'Capture missed the start of this runtime scope'
assert scope_events[0]['type'] in ('source','lifecycle'), 'Initial runtime event is missing'
assert all(e['schema']=='labwired.flight-observation/v1' for e in scope_events)
assert all(b['sequence']==a['sequence']+1 for a,b in zip(scope_events,scope_events[1:])), 'Observation sequence gap'
selected=[e for e in scope_events if e.get('epoch')==r['epoch']]
assert selected, 'Selected scope/epoch has no events'
first_body=next((e for e in selected if e['type']=='body'),None)
assert first_body and 0 <= first_body['observation']['timeNs'] <= 30_000_000, 'Capture did not start near native zero'
initial_events=[e for e in scope_events if e['sequence']<first_body['sequence']]
assert any(e['type']=='lifecycle' for e in initial_events), 'Initial lifecycle was not captured'
assert {e['sourcePartId'] for e in initial_events if e['type']=='source'}=={'ctrl1','ctrl2','ctrl3','ctrl4','fc'}, 'Initial native source registrations are incomplete'
assert not any(e['type'] in ('invalid','reset') for e in selected), 'Runtime invalidation/reset in selected flight'
body_rows=[]; motors={}; final=None; ended=False
source_ids={e['sourcePartId']:e['sourceIdentity'] for e in initial_events if e['type']=='source'}
for e in selected:
 if e['type']=='source':
  assert not e.get('replaced'), 'Runtime source replacement within accepted flight'
  source_ids[e['sourcePartId']]=e['sourceIdentity']
 elif e['type']=='motors':
  assert source_ids.get(e['sourcePartId'])==e['sourceIdentity'], 'Unregistered native source identity'
  for component,m in e['observations'].items():
   assert m['clockHz']==80_000_000 and m['sourcePartId']==e['sourcePartId'], 'Wrong clock/owner'
   assert abs(m['timeNs']-m['cycles']/m['clockHz']*1e9)<.001, 'Non-native observation time'
   motors[(m['sourcePartId'],component)]={'owner':m['sourcePartId'],'id':component,
    'speed_rpm':m['speedRpm'],'control_state':m['controlState'],'faults':m['faults'],
    'cycles':m['cycles'],'clockHz':m['clockHz'],'timeNs':m['timeNs'],'sourceIdentity':e['sourceIdentity']}
 elif e['type']=='body' and not ended:
  observation=e['observation']
  assert observation['pendingTimeNs']==0, 'Incomplete body integration at observation'
  assert len(motors)==4, 'Body observation lacks all four native motors'
  body_rows.append({'seconds':observation['timeNs']/1e9,'body':observation,'motors':list(motors.values())})
  ended=observation['timeNs']>=15_000_000_000
 elif e['type']=='lifecycle' and e.get('status')=='paused':
  final=e['diagnostics']
assert set(source_ids)=={'ctrl1','ctrl2','ctrl3','ctrl4','fc'}, 'Five native source identities were not captured'
assert ended and final is not None, 'No complete 15-second flight with final paused diagnostics'
assert body_rows[-1]['seconds']<=15.03, 'Observer stop is too late to preserve the 15-second horizon'
result={'kind':'continuous-studio-production-runtime-passive-observations',
 'projectId':r['projectId'],'contentHash':r['contentHash'],'duration':15,
 'stopped':'duration','seconds':body_rows[-1]['seconds'],'errors':[],
 'faultInjected':False,'final':final,'assets':r['assets'],
 'sourceReceipt':str(receipt_path),'observationScopeId':r['scopeId'],'observationEpoch':r['epoch'],
 'projectTransport':r.get('projectTransport','unspecified'),
 'deployedBuildCommit':r['deployedBuildCommit'],'nativeQualificationSha256':r['qualificationSha256'],
 'rawCaptureEventCount':len(events),'capturedEpochs':sorted({e['epoch'] for e in scope_events}),
 'retainedOtherEpochInvalidations':[e for e in scope_events if e['epoch']!=r['epoch'] and e['type']=='invalid']}
assert result['projectTransport'] in ('real-signed-in-project-read','authorized-readback-project-load-fixture'), 'Project transport must be explicit'
out=receipt_path.parent/'browser-nominal-result.json'
out.write_text(json.dumps(result,indent=2)+'\n')
out.with_name('browser-nominal.ndjson').write_text(''.join(json.dumps(row,separators=(',',':'))+'\n' for row in body_rows))
print(out)
