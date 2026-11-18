#!/usr/bin/env python3
"""Fetch only public, pinned source dependencies. Never reset a changed checkout."""
from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parent;out=root/'.deps';out.mkdir(exist_ok=True)
manifest=json.loads((root/'dependencies.json').read_text())
def run(*args,cwd=None):subprocess.run(args,cwd=cwd,check=True)
def checkout(name,entry,sparse=None):
    dest=out/name
    if not dest.exists():
        run('git','clone','--filter=blob:none','--no-checkout',entry['url'],str(dest))
        if sparse:run('git','sparse-checkout','set','--skip-checks',*sparse,cwd=dest)
        run('git','checkout','--detach',entry['revision'],cwd=dest)
    else:
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=dest,text=True).strip()
        if actual!=entry['revision']:raise SystemExit(f'{dest}: wrong revision {actual}; preserve it and choose a separate dependency directory')
        run('git','diff','--quiet',cwd=dest)
    return dest
cube=checkout('STM32CubeL4',manifest['STM32CubeL4'],['Drivers/CMSIS/Include','Drivers/CMSIS/Device/ST/STM32L4xx','Drivers/STM32L4xx_HAL_Driver','Projects/NUCLEO-L476RG/Templates'])
run('git','submodule','update','--init','Drivers/STM32L4xx_HAL_Driver','Drivers/CMSIS/Device/ST/STM32L4xx',cwd=cube)
checkout('iolinki',manifest['iolinki'])
checkout('labwired-core',manifest['iolinki-master'],['third_party/iolinki-master'])
print('Public dependencies fetched at exact recorded revisions')
