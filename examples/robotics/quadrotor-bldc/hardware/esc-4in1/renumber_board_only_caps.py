# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Reference-only KiCad 10 PCB derivative of the OpenESC bulk bank.

The vendor board carries 49 PCB-only 4.7uF capacitors with duplicate
reference designators. Only their Reference property VALUES change.
Unlike a whole-file pcbnew.SaveBoard(), this preserves all zone/track text,
project board metadata, UUIDs, settings and official DRC exclusions.
All resulting changes are checked with a line-level exact invariant.
"""
import csv,difflib,pathlib,re
root=pathlib.Path(__file__).resolve().parent
old=(root/'4in1-upstream-original.kicad_pcb').read_text()
items=list(csv.DictReader((root/'board-only-caps.csv').open()))
assert len(items)==49
def matching_end(s, pos):
    assert s[pos]=='('
    depth=0; string=False; escape=False
    for i in range(pos,len(s)):
        c=s[i]
        if string:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c=='"': string=False
        elif c=='"': string=True
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
    raise ValueError('Unbalanced KiCad footprint at '+str(pos))
matches=[]
for m in re.finditer(r'(?m)^\t\(footprint\s+"',old):
    start=m.start()+1
    end=matching_end(old,start)
    block=old[start:end]
    pos=re.search(r'(?m)^\t\t\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+[-.\d]+)?\)',block)
    ref=re.search(r'(?m)^\t\t\(property "Reference" "([^"]+)"',block)
    if not pos or not ref:raise ValueError('Malformed footprint '+str(start))
    x,y=map(float,pos.groups())
    entry=[z for z in items if z['original_reference']==ref.group(1) and
       abs(float(z['x_mm'])-x)<.001 and abs(float(z['y_mm'])-y)<.001]
    if len(entry)==1:
       if '(path "' in block:raise ValueError('Will not rename schematic-owned '+ref.group(1))
       matches.append((start+ref.start(1),start+ref.end(1),entry[0]))
assert len(matches)==49,(len(matches),len(items))
new=old
for start,end,row in sorted(matches,reverse=True):
    assert new[start:end]==row['original_reference']
    new=new[:start]+row['new_reference']+new[end:]
delta=list(difflib.unified_diff(old.splitlines(),new.splitlines(),n=0))
changed=[line for line in delta if line.startswith(('+','-')) and not line.startswith(('+++','---'))]
assert len(changed)==98
assert all(line.lstrip('+-\t').startswith('(property "Reference" "') for line in changed)
assert new.count('(property "Reference" "C501"')==1
assert len(new)!=len(old)
(root/'4in1.kicad_pcb').write_text(new)
print('CHANGED 49 reference values; all other lines byte-identical')
print('OLD_SIZE',len(old),'NEW_SIZE',len(new))
