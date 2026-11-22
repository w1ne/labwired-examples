#!/usr/bin/env python3
"""Prepare one explicit project-load response fixture from an authorized readback.

Does not create a share, change publication or perform any network/browser action.
The source/diagram hashes must be the accepted candidate, and the saved CAS hash
must be new. Metadata is retained; diagram_json is the API loader's documented shape.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
here=Path(__file__).resolve().parent
input_path=Path(sys.argv[1]).resolve()
check=subprocess.run([sys.executable,str(here/'check-project-readback.py'),str(input_path)],capture_output=True,text=True)
if check.returncode: raise SystemExit(check.stdout+check.stderr)
x=json.loads(input_path.read_text()); response=x.get('structuredContent',x)
p=response['project']
row=dict(p)
row['diagram_json']=json.dumps(row.pop('diagram'),separators=(',',':'),ensure_ascii=False)
fixture={**response,'project':row}
raw=(json.dumps(fixture,indent=2,ensure_ascii=False)+'\n').encode()
out=input_path.parent/'browser-project-response-fixture.json';out.write_bytes(raw)
receipt={'kind':'authorized-readback-project-load-fixture','savedProjectId':p['id'],
 'savedContentHash':p['content_hash'],'sourceReadbackPath':str(input_path),
 'sourceReadbackSha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),
 'fixturePath':str(out),'fixtureSha256':hashlib.sha256(raw).hexdigest(),
 'overrides':[{'method':'GET','url':'https://api.labwired.com/v1/projects/'+p['id'],
  'replacement':'authorized fresh project readback; parsed diagram reserialized as diagram_json'}],
 'signedInProjectFetchObserved':False,'projectPublicationChanged':False,
 'runtimeOrFirmwareOverrides':[]}
out.with_name('browser-project-fixture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
