#!/usr/bin/env python3
"""Verify pinned Git dependencies or the complete archive's byte manifest."""
from pathlib import Path
import json,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'source'))
from verify_export import verify_export
root=Path(__file__).resolve().parent
if len(sys.argv)!=3:raise SystemExit('Usage: verify-deps.py CUBE_DIR UDSLIB_DIR')
paths=dict(zip(['CUBE','UDSLIB'],map(Path,sys.argv[1:])))
if verify_export(root,paths):raise SystemExit(0)
config=json.loads((root/'source/config.json').read_text())
for pin in config['sourcePins']:
    path=paths[pin['root']]/pin.get('subPath','')
    actual=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
    if actual!=pin['revision']:raise RuntimeError('Dependency revision differs: '+pin['name'])
    subprocess.run(['git','-C',str(path),'diff','--quiet','HEAD','--','.'],check=True)
print('Verified pinned CubeH5, HAL, CMSIS and UDS source trees')
