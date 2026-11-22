#!/usr/bin/env python3
"""Check an actual MCP get result against the reviewed candidate. No network calls."""
import hashlib,json,sys
from pathlib import Path
here=Path(__file__).resolve().parent
wanted=json.loads((here/'staged-promotion-receipt.json').read_text())
raw=json.loads(Path(sys.argv[1]).read_text())
x=raw.get('structuredContent',raw)
p=x.get('project',x)
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[{'part_id':'ctrl1','source_code':p.get('source_code','')},*p.get('firmware',[])]
sources={r['part_id']:sha(r['source_code'].encode()) for r in rows}
diagram_sha=sha(json.dumps(p['diagram'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
checks={'projectIdentity':p.get('id')==wanted['projectId'],
 'allFiveSources':sources==wanted['sourceSha256'],
 'diagram':diagram_sha==wanted['diagramSha256'],
 'newContentHash':bool(p.get('content_hash')) and p['content_hash']!=wanted['expectedContentHash']}
receipt={'kind':'saved-project-candidate-readback','passed':all(checks.values()),'checks':checks,
 'contentHash':p.get('content_hash'),'verifiedHash':p.get('verified_hash'),
 'sourceSha256':sources,'diagramSha256':diagram_sha,
 'flightVerifiedByThisReadback':False}
print(json.dumps(receipt,indent=2))
sys.exit(0 if receipt['passed'] else 1)
