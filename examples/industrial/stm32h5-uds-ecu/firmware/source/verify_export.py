#!/usr/bin/env python3
"""Verify every exported dependency byte before building without Git metadata."""
from pathlib import Path
import hashlib,json

def verify_export(root, supplied):
    root=Path(root).resolve()
    config=json.loads((root/'source/config.json').read_text())
    expected={k:(root/v['archivePath']).resolve() for k,v in config['vendors'].items()}
    if set(supplied)!=set(expected):
        raise RuntimeError('Dependency root keys differ')
    if not all(Path(supplied[k]).resolve()==p and not (p/'.git').exists() for k,p in expected.items()):
        return False
    manifest=json.loads((root/'source/vendor-manifest.json').read_text())
    if manifest['sourcePins']!=config['sourcePins']:
        raise RuntimeError('Export source revision records differ')
    listed={}
    for item in manifest['files']:
        rel=Path(item['path'])
        if rel.is_absolute() or '..' in rel.parts or item['path'] in listed:
            raise RuntimeError('Unsafe or duplicate dependency path')
        p=root/rel
        if p.is_symlink() or not p.is_file():
            raise RuntimeError('Missing or linked dependency: '+str(rel))
        if not any(p.is_relative_to(v) for v in expected.values()):
            raise RuntimeError('Dependency escapes declared root')
        data=p.read_bytes()
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise RuntimeError('Dependency byte mismatch: '+str(rel))
        listed[item['path']]=item
    actual={str(p.relative_to(root)) for base in expected.values() for p in base.rglob('*') if p.is_file() or p.is_symlink()}
    if actual!=set(listed):
        raise RuntimeError('Dependency inventory differs: '+repr(sorted(actual.symmetric_difference(listed))[:10]))
    print('Verified '+str(len(listed))+' exported dependency files and exact source revisions')
    return True
