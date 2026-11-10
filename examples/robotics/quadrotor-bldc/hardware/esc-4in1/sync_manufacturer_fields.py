# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Schematic->PCB manufacturer metadata sync. Connectivity/geometry unchanged."""
import difflib, pathlib, re
D=pathlib.Path(__file__).resolve().parent
boardfile=D/'4in1.kicad_pcb'
old=boardfile.read_text()
sch=(D/'fabrication-review/schematic.net').read_text()
def end(s,pos):
    assert s[pos]=='('
    depth=0; quoted=False; escaped=False
    for i in range(pos,len(s)):
        c=s[i]
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
    raise ValueError('malformed KiCad S-expression')
vendor={}
for m in re.finditer(r'(?m)^\t\t\(comp\s*\n\t\t\t\(ref "([^"]+)"\)',sch):
    b=sch[m.start()+2:end(sch,m.start()+2)]
    mf=re.search(r'\(field\s+\(name "Manufacturer"\)\s+"([^"]+)"\)',b)
    if mf:vendor[m.group(1)]=mf.group(1)
updates=[]
for m in re.finditer(r'(?m)^\t\(footprint "',old):
    start=m.start()+1; stop=end(old,start)
    b=old[start:stop]
    mr=re.search(r'(?m)^\t\t\(property "Reference" "([^"]+)"',b)
    if not mr:raise ValueError('missing reference')
    ref=mr.group(1)
    if ref not in vendor:continue
    mp=re.search(r'(?m)^\t\t\(property "Manufacturer" "([^"]*)"',b)
    if mp is None:raise ValueError(f'{ref} has no Manufacturer field')
    got=mp.group(1); desired=vendor[ref]
    if got==desired:continue
    if got:raise ValueError(f'nonempty metadata differs on {ref}: {got} vs {desired}')
    updates.append((start+mp.start(1),start+mp.end(1),desired,ref))
assert len(updates)==154, (len(updates),vendor)
new=old
for s,e,value,ref in sorted(updates,reverse=True):
    assert new[s:e]==''
    new=new[:s]+value+new[e:]
delta=[line for line in difflib.unified_diff(old.splitlines(),new.splitlines(),n=0)
       if line.startswith(('+','-')) and not line.startswith(('+++','---'))]
assert len(delta)==308
assert all(line.lstrip('+-\t').startswith('(property "Manufacturer" ') for line in delta)
assert all('''(property "Manufacturer" "")''' not in new[start:start+100] for start in [])
boardfile.write_text(new)
print('METADATA_SYNC',len(updates),'FOOTPRINTS; no wires, pads, nets, zones, vias, footprint coordinates or design rules modified')
print('MANUFACTURERS',sorted(set(v for _,_,v,_ in updates)))
