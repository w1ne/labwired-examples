# SPDX-License-Identifier: CERN-OHL-S-2.0
"""KiCad native board API: restore unconnected package pads and manufacturer metadata.

Only modifies a DERIVATIVE board. Every expected absent pad is an explicitly
NC schematic pin; the native footprint library has a corresponding pad. Clone
existing identical pads from the same footprint to retain layer/shape and
hand-solder geometry. A complete before/after audit is required before use.
"""
import re, collections, pathlib
import pcbnew as k
D=pathlib.Path(__file__).resolve().parents[1]
board=k.LoadBoard(str(D/'4in1.kicad_pcb'))
refs={f.GetReference():f for f in board.GetFootprints()}
assert len(refs)==222
report=(D/'validation/drc-preserved.txt').read_text()
vendor={}
for m in re.finditer(r'\[footprint_symbol_field_mismatch\]: Field .Manufacturer. differs \(PCB: .*, Schematic: .([^.]*)\)\s+Local override; warning\s+@\([^)]+\): Footprint ([^\n]+)',report):
    pass
# Do not parse vendor fields from the rendered report when names may contain punctuation.
# KiCad's parsed S-expression schematic netlist is the authoritative metadata.
netlist=(D/'fabrication-review/schematic.net').read_text()
def sexpr_end(s,start):
    depth=0; quoted=False; escape=False
    for i in range(start,len(s)):
        c=s[i]
        if quoted:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
    raise ValueError('unterminated S-expression')
for m in re.finditer(r'(?m)^\t\t\(comp\n\t\t\t\(ref "([^"]+)"\)',netlist):
    ref=m.group(1)
    if ref not in refs:continue
    block=netlist[m.start()+2:sexpr_end(netlist,m.start()+2)]
    field=re.search(r'\(field\s+\(name "Manufacturer"\)\s+"([^"]+)"\)',block)
    if field:vendor[ref]=field.group(1)
updated=[]
for ref,value in vendor.items():
    f=refs[ref]
    field=f.GetField('Manufacturer')
    if field and field.GetText()!=value:
        if field.GetText() not in ('',value):raise ValueError(f'{ref} manufacturer conflicting: {field.GetText()} vs {value}')
        field.SetText(value)
        updated.append(ref)
print('MANUFACTURER_REPAIRED',len(updated))
assert len(updated)==154,(len(updated),updated)
missing={
 'U2':['8','23','24'],'U5':['8','23','24'],
 'U7':['8','23','24'],'U9':['23','24'],
 'U6':['5','7'],'U10':['5','7','8']
}
assert sum(map(len,missing.values()))==16
stems={
 'U2':'QFN-28_L4.0-W4.0-P0.40-TL-EP2.4',
 'U5':'QFN-28_L4.0-W4.0-P0.40-TL-EP2.4',
 'U7':'QFN-28_L4.0-W4.0-P0.40-TL-EP2.4',
 'U9':'QFN-28_L4.0-W4.0-P0.40-TL-EP2.4',
 'U6':'QFN-24_L4.0-W4.0-P0.50-TL-EP2.8',
 'U10':'QFN-24_L4.0-W4.0-P0.50-TL-EP2.8'
}
nc_map={
 'U2':{'8':'PA2','23':'PA15','24':'PB3'},
 'U5':{'8':'PA2','23':'PA15','24':'PB3'},
 'U7':{'8':'PA2','23':'PA15','24':'PB3'},
 'U9':{'23':'PA15','24':'PB3'},
 'U6':{'5':'NC','7':'NC'},
 'U10':{'5':'NC','7':'NC','8':'NC'}
}
changes=[]
for ref,nums in missing.items():
    fp=refs[ref]
    lib=k.FootprintLoad(str(D/'4in1ESC-30x30.pretty'),stems[ref])
    assert lib,stems[ref]
    lookup={pad.GetNumber():pad for pad in lib.Pads()}
    # Before adding, existing package geometry must match the library under
    # mirrored local y (KiCad bottom-side placement). Refuse drift.
    seen=set(z.GetNumber() for z in fp.Pads())
    available=sorted(seen-{str(x) for x in range(10,21)},key=lambda s:(len(s),s))
    for pin in ['4','6','9','10','13','18','20','21','22','25','27']:
        if pin in seen and pin in lookup:
            a=fp.FindPadByNumber(pin).GetFPRelativePosition()
            b=lookup[pin].GetFPRelativePosition()
            if abs(k.ToMM(a.x)-k.ToMM(b.x))>.003 or abs(k.ToMM(a.y)+k.ToMM(b.y))>.003:
                raise ValueError(f'Library mismatch for {ref} pin {pin}: {k.ToMM(a.x),k.ToMM(a.y)} vs {k.ToMM(b.x),k.ToMM(b.y)}')
    for num in nums:
        assert fp.FindPadByNumber(num) is None
        libpad=lookup[num]
        libpos=libpad.GetFPRelativePosition()
        # Clone adjacent physical pad on same target footprint to preserve
        # actual copper-layer, mask, shape and local soldermask expansion.
        same_edge=min(
          (p for p in fp.Pads() if p.GetNumber() and p.GetNumber() in lookup),
          key=lambda p:(abs(k.ToMM(p.GetFPRelativePosition().x)-k.ToMM(libpos.x))+
                        abs(k.ToMM(p.GetFPRelativePosition().y)+k.ToMM(libpos.y)))
        )
        cloned=same_edge.Duplicate()
        cloned.SetNumber(num)
        cloned.SetNetCode(0)
        fp.Add(cloned)
        cloned.SetFPRelativePosition(k.VECTOR2I(libpos.x,-libpos.y))
        changes.append((ref,num,nc_map[ref][num],str(fp.GetLayerName()),str(cloned.GetLayerName()),k.ToMM(cloned.GetPosition().x),k.ToMM(cloned.GetPosition().y)))
print('RESTORED_PADS',len(changes))
for c in changes:print('PAD',c)
assert len(changes)==16
assert all(refs[ref].FindPadByNumber(pin) for ref,nums in missing.items() for pin in nums)
before_len=2922
assert len(board.GetTracks())==before_len and board.GetNetCount()==195
out=D/'4in1-candidate.kicad_pcb'
k.SaveBoard(str(out),board)
print('CANDIDATE_SAVED',out,out.stat().st_size)
