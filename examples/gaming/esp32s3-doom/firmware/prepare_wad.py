#!/usr/bin/env python3
"""Recover the exact existing shareware data input from its pinned release image."""
from pathlib import Path
import hashlib,json,urllib.request
root=Path(__file__).resolve().parent
record=json.loads((root/'build-inputs.json').read_text())['wad']
target=root/'source/wad/doom1.wad'
if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==record['sha256']:
    print('Pinned IWAD already present.');raise SystemExit(0)
with urllib.request.urlopen(record['source'],timeout=60) as response:
    image=response.read()
if hashlib.sha256(image).hexdigest()!=record['source_sha256']:
    raise SystemExit('Release image hash does not match the pinned input.')
data=image[record['offset']:record['offset']+record['bytes']]
if len(data)!=record['bytes'] or data[:4]!=b'IWAD' or hashlib.sha256(data).hexdigest()!=record['sha256']:
    raise SystemExit('IWAD content does not match the pinned input.')
target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
print('Prepared pinned shareware IWAD:',len(data),'bytes.')
