# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Attach the manufacturer's 49 board-only 4.7uF caps to a KiCad schematic.

C2, C3, C6 are the correctly sourced 3 original 4.7uF capacitors.
Make a root-sheet 7x7 supplementary bank with the same capacitor, +BATT
and GND symbols; then attach each of the other 49 board footprints by UUID.

Invariant: PCB copper nets, tracks, pad positions, vias, zones and component
footprints remain byte-for-byte identical. No silicon or schematic pin guess.
Only an EXTRA schematic circuit matching already-routed +BATT/GND pads is added.
"""
import csv, difflib, pathlib, re, shutil, uuid
D=pathlib.Path(__file__).resolve().parents[1]
P=D/'validation'/'candidate'
P.mkdir(parents=True,exist_ok=True)
for n in ['4in1.kicad_pro','4in1.kicad_dru','ESC.kicad_sch','components.kicad_sym','sym-lib-table','fp-lib-table']:
    shutil.copy2(D/n,P/n)
for n in ['KiCad-Library','4in1ESC-30x30.pretty','4in1ESC-30x30.3dshapes']:
    link=P/n
    if not link.exists():
        link.symlink_to(pathlib.Path('../..')/n)
sch=(D/'4in1.kicad_sch').read_text()
pcb=(D/'4in1.kicad_pcb').read_text()
map_rows=list(csv.DictReader((D/'board-only-caps.csv').open()))
assert len(map_rows)==49
assert {x['new_reference'] for x in map_rows}=={'C'+str(i) for i in range(501,550)}
root_id=re.search(r'^\(kicad_sch .*?\(uuid "([^"]+)"\)',sch).group(1)
def end(s,start):
    assert s[start]=='('
    depth=0; q=False; esc=False
    for i in range(start,len(s)):
        c=s[i]
        if q:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':q=False
        elif c=='"':q=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
    raise RuntimeError('Invalid S-expression')
templates={}
for m in re.finditer(r'\(symbol\s+\(lib_id "',sch):
    b=sch[m.start():end(sch,m.start())]
    mr=re.search(r'\(property "Reference" "([^"]+)"',b)
    if mr and mr.group(1) in ('C2','#PWR05','#PWR06'):
        templates[mr.group(1)]=b
assert len(templates)==3
def token(ref,origin_uuid):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,f'LabWired-OpenESC-2026-11-10/{ref}/{origin_uuid}'))
def translated(template,old_ref,new_ref,dx,dy):
    out=template
    # Sheet instance reference and visible symbol reference.
    out=out.replace(f'(property "Reference" "{old_ref}"',f'(property "Reference" "{new_ref}"')
    out=out.replace(f'(reference "{old_ref}")',f'(reference "{new_ref}")')
    assert new_ref in out
    # All UUIDs belonging to this placed symbol, including pin UUIDs.
    out=re.sub(r'\(uuid "([^"]+)"\)',lambda m:f'(uuid "{token(new_ref,m.group(1))}")',out)
    # KiCad hidden fields at (0 0) have no positioned geometry and must stay 0,0.
    def shift(m):
        x=float(m.group(1));y=float(m.group(2));r=m.group(3)
        if abs(x)<1e-12 and abs(y)<1e-12:return m.group(0)
        return f'(at {x+dx:.4f} {y+dy:.4f} {r})'
    out=re.sub(r'\(at (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)\)',shift,out)
    return out
add=[]
wires=[]
ids={}
for idx,n in enumerate(range(501,550)):
    col=idx%7;row=idx//7
    xx=53.34+col*38.10
    yy=180.34+row*15.24
    dx=xx-78.74;dy=yy-67.31
    ref='C'+str(n)
    # The exact C2 topology has a 1.27mm wire from each capacitor pin to the
    # matching +BATT/GND power label; copies MUST include both wires.
    for suffix,y1,y2 in [('batt',yy-5.08,yy-3.81),('gnd',yy+3.81,yy+5.08)]:
        wires.append('(wire (pts (xy {:.4f} {:.4f}) (xy {:.4f} {:.4f})) (stroke (width 0) (type default)) (uuid "{}"))'.format(
            xx,y1,xx,y2,token(ref+suffix,'C2 original connection')))
    for orig,ref_out in [('C2',ref),('#PWR05',f'#PWR{1000+n}'),('#PWR06',f'#PWR{2000+n}')]:
        text=translated(templates[orig],orig,ref_out,dx,dy)
        if orig=='C2':
            # The copied schematic template carried empty distributor fields.
            # The 49 vendor PCB-only footprints have no such fields, and
            # empty distributor fields have no sourcing meaning.
            for field in ['Farnell','Mouser','Digi-Key','Cost']:
                mark=f'(property "{field}" ""'
                at=text.index(mark)
                text=text[:at]+text[end(text,at):]
        add.append(text)
        if orig=='C2':
            ids[ref]=re.search(r'^\(symbol .*?\(uuid "([^"]+)"\)',text).group(1)
            assert text.count('(pin "1"')==1 and text.count('(pin "2"')==1
            assert f'(reference "{ref}")' in text
# Place the appended symbols before the closing root S-expression.
assert sch[-2:]=='))'
extra='\n\n; LabWired-reviewed fully-specified 49-unit bulk capacitor bank\n'+'\n\n'.join(add)+'\n'
# KiCad may not support comments in schematics; only add symbols.
extra='\n\n'+'\n\n'.join(add+wires)+'\n'
sch_updated=sch[:-1]+extra+')'
(P/'4in1.kicad_sch').write_text(sch_updated)
# The existing footprints already contain real (+BATT,GND) pads, manufacturer
# sourcing and positions. Only assign schematic paths to these 49 footprints.
# Keep the PCB-specific reference metadata aligned to the copied schematic,
# including the 47 footprints that lacked manufacturer + MPN properties.
src_pcb_cap=None
for m in re.finditer(r'(?m)^\t\(footprint "',pcb):
    at=m.start()+1
    z=pcb[at:end(pcb,at)]
    if '(property "Reference" "C2"' in z:
        src_pcb_cap=z
        break
assert src_pcb_cap
prop_templates={}
for name in ['Manufacturer','MPN']:
    pos=src_pcb_cap.index(f'(property "{name}" "')
    prop_templates[name]=src_pcb_cap[pos:end(src_pcb_cap,pos)]
    assert 'CCTC' in prop_templates.get('Manufacturer','') or name!='Manufacturer'
    assert 'TCC1206X7R475K500HT' in prop_templates.get('MPN','') or name!='MPN'
edit=[]
missing_manufacturer=0
missing_mpn=0
for m in re.finditer(r'(?m)^\t\(footprint "',pcb):
    start=m.start()+1; stop=end(pcb,start);b=pcb[start:stop]
    mr=re.search(r'\(property "Reference" "([^"]+)"',b)
    if not mr:continue
    ref=mr.group(1)
    if ref not in ids:continue
    assert '(path "' not in b,ref
    assert '\t\t(sheetname "/")' in b
    assert '(net "+BATT")' in b and '(net "GND")' in b,ref
    assert '(property "LCSC" "C380366"' in b
    new_b=b
    for name in ['Manufacturer','MPN']:
        fstart=f'(property "{name}" "'
        existing=re.search(re.escape(fstart)+r'([^"]*)"',new_b)
        if not existing:
            prop=prop_templates[name]
            prop=re.sub(r'\(uuid "([^"]+)"\)',
                lambda mm:'(uuid "'+token(ref+'-'+name,mm.group(1))+'")',prop)
            # Place real sourcing metadata alongside existing PCB fields.
            new_b=new_b.replace('\t\t(property ki_fp_filters',
                '\t\t'+prop+'\n\t\t(property ki_fp_filters',1)
            if name=='Manufacturer':missing_manufacturer+=1
            else:missing_mpn+=1
        else:
            required={'Manufacturer':'CCTC','MPN':'TCC1206X7R475K500HT'}[name]
            assert existing.group(1)==required,(ref,name,existing.group(1))
    new_b=new_b.replace('\t\t(sheetname "/")',
        '\t\t(path "/'+ids[ref]+'")\n\t\t(units (unit (name "A") (pins "1" "2")))\n\t\t(sheetname "/")',1)
    edit.append((start,stop,new_b,ref))
assert len(edit)==49,len(edit)
assert missing_manufacturer==47 and missing_mpn==47,(missing_manufacturer,missing_mpn)
result=pcb
for start,stop,text,ref in sorted(edit,reverse=True):
    result=result[:start]+text+result[stop:]
delta=[v for v in difflib.unified_diff(pcb.splitlines(),result.splitlines())
       if v.startswith(('+','-')) and not v.startswith(('+++','---'))]
assert delta and all(v.startswith('+') for v in delta)
print('SUPPLIER_FIELDS_RESTORED',missing_manufacturer,missing_mpn)
(P/'4in1.kicad_pcb').write_text(result)
print('SCHEMATIC',len(add),'NEW SYMBOLS',len(wires),'NEW WIRES',len(sch_updated),'BYTES','ROOT_UUID',root_id)
print('PCB PATHS',len(edit),'NEW',len(result)-len(pcb),'BYTES')
print('UNIQUE REFERENCES',len(ids))
print('C501_UUID',ids['C501'])
