#!/usr/bin/env python3
"""Reject revision drift or tracked source edits before a physical image build."""
from pathlib import Path
import json,subprocess,sys
manifest=json.loads((Path(__file__).parent/'dependencies.json').read_text())
cube,iolinki,master=map(Path,sys.argv[1:])
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
def verify(path,entry):
    assert git(path,'rev-parse','HEAD')==entry['revision'],f'{path}: revision mismatch'
    subprocess.run(['git','-C',str(path),'diff','--quiet','HEAD','--','.'],check=True)
verify(cube,manifest['STM32CubeL4'])
verify(cube/'Drivers/STM32L4xx_HAL_Driver',manifest['STM32L4xx_HAL_Driver'])
verify(cube/'Drivers/CMSIS/Device/ST/STM32L4xx',manifest['CMSIS_Device_STM32L4'])
verify(iolinki,manifest['iolinki'])
repo=Path(git(master,'rev-parse','--show-toplevel'))
entry=manifest['iolinki-master'];assert git(repo,'rev-parse','HEAD')==entry['revision']
assert git(repo,'rev-parse','HEAD:'+entry['path'])==entry['tree']
subprocess.run(['git','-C',str(repo),'diff','--quiet','HEAD','--',entry['path']],check=True)
print('Verified CubeL4, HAL, CMSIS, iolinki, and vendored master source pins')
