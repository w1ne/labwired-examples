#!/usr/bin/env python3
"""Prepare exact structured MCP arguments. This script performs no network calls."""
import hashlib, json
from pathlib import Path
BUNDLE=Path('/data/lw-quadrotor-examples-20261122/examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight')
OUT=Path(__file__).resolve().parent
p=json.loads((BUNDLE/'candidate-project.json').read_text())
a=json.loads((BUNDLE/'acceptance.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
source_rows=[{'part_id':'ctrl1','source_code':p['source_code']},*p['firmware']]
actual={r['part_id']:sha(r['source_code'].encode()) for r in source_rows}
expected={k:v['sha256'] for k,v in a['sourceFiles'].items()}
assert actual==expected,(actual,expected)
diagram_hash=sha(json.dumps(p['diagram'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
assert diagram_hash==a['diagramSha256'],diagram_hash
payload={'project_id':p['id'],'expected_content_hash':p['base_content_hash'],
 'source':p['source_code'],'language':p['source_language'],'entry_path':p['source_entry_path'],
 'diagram':p['diagram'],'firmware':[{'part':r['part_id'],'source':r['source_code'],
 'language':r['source_language'],'entry_path':r['source_entry_path']} for r in p['firmware']]}
raw=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()
(OUT/'project-update-args.json').write_bytes(raw)
receipt={'kind':'staged-project-update-not-executed','projectId':p['id'],
 'expectedContentHash':p['base_content_hash'],'payloadSha256':sha(raw),
 'sourceSha256':actual,'diagramSha256':diagram_hash,
 'coreCommit':a['coreCommit'],'wasmSha256':'4c45fb97b6af9e0a93407a7cc20b9e5d95eb769e653938ab8b284ecf6a5925d7',
 'appIntegrationHead':'fdd9d7f68fe7192ac0a6a496c962db170730e0f8',
 'examplesMergedCommit':'792d362ce0c4b827c91c5bfc7ec71acaf1b9cf2a',
 'sourceAndDiagramValidated':True,'savedProjectUpdated':False,
 'requiredBeforeMutation':['deployed app integration confirmed','actual deployed WASM qualified with unchanged oracle','fresh owner project readback matches expectedContentHash'],
 'requiredAfterMutation':['exact five-source and diagram readback','separate hosted serial check','15 native seconds in continuous Studio body/IMU runtime']}
(OUT/'staged-promotion-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
