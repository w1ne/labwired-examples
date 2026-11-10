# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Actual physical-footprint BOM, including the 49 PCB-only bus capacitors.

This BOM is taken from KiCad's board rather than the incomplete schematic BOM.
External parts (motors/propellers/FC/battery) are in system-bom.csv.
"""
import csv, collections, os, re
import pcbnew as k
d=os.path.dirname(os.path.abspath(__file__))
b=k.LoadBoard(os.path.join(d,'4in1.kicad_pcb'))
def natural(s):
    m=re.fullmatch(r'([A-Z#]+)([0-9]+)',s)
    return (m.group(1),int(m.group(2))) if m else (s,0)
rows=[]
for fp in sorted(b.GetFootprints(),key=lambda f:natural(f.GetReference())):
    ref=fp.GetReference();value=fp.GetValue()
    props={fld.GetName():fld.GetText() for fld in fp.GetFields()}
    fields={
      'Designator':ref, 'Value':value, 'Footprint':str(fp.GetFPID().GetLibItemName()),
      'LCSC Part #':props.get('LCSC',''),
      'Manufacturer':props.get('Manufacturer',''),
      'Manufacturer Part #':props.get('MPN',''),
      'PCB SMD':('no' if ref.startswith('TP') or ref=='U3' else 'yes'),
      'Population':('NOT POPULATED - board logo' if ref=='U3' else
          ('NOT POPULATED - test pad' if ref.startswith('TP') else 'ASSEMBLE')),
      'Source':('PCB-only bank, see original manufacturer documentation' if ref.startswith('C') and ref[1:].isdigit() and 501<=int(ref[1:])<=549 else 'PCB layout')
    }
    if ref.startswith('C5') and len(ref)==4 and value=='4.7uF':
        # Matched to upstream production notes (same LCSC part C380366).
        assert fields['LCSC Part #']=='C380366'
        fields['Manufacturer']='CCTC'
        fields['Manufacturer Part #']='TCC1206X7R475K500HT'
        fields['Source']='OpenESC rev3.3.1 sourcing note; footprint on actual board'
    rows.append(fields)
assert len(rows)==222
assert len({r['Designator'] for r in rows})==222
with open(os.path.join(d,'fabrication-review','pcb-all-components.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Exactly one BOM row per distinct supplier part: CPL references must all be
# represented without missing or duplicate designators.
group=collections.defaultdict(list)
for row in rows:
    if row['PCB SMD']!='yes':continue
    key=(row['Value'],row['Footprint'],row['LCSC Part #'],row['Manufacturer Part #'])
    group[key].append(row['Designator'])
grouped=[]
for (value,foot,lcsc,mpn),refs in sorted(group.items(),key=lambda kv:(kv[0][2],kv[0][0])):
    grouped.append({'Comment':value,'Designator':', '.join(sorted(refs,key=natural)),
                    'Footprint':foot,'LCSC Part #':lcsc,'MPN':mpn,
                    'Quantity':len(refs),'Status':('needs sourcing' if not lcsc else 'LCSC specified')})
with open(os.path.join(d,'fabrication-review','pcba-bom-grouped.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(grouped[0]));w.writeheader();w.writerows(grouped)
assert sum(len(v) for v in group.values()) == 213
assert not any(not r['LCSC Part #'] for r in rows if r['PCB SMD']=='yes')
print('BOARD_FOOTPRINTS',len(rows),'ASSEMBLY_COUNT',sum(len(v) for v in group.values()),
      'GROUPED_LINES',len(grouped),'NO_LCSC',sum(1 for r in rows if r['PCB SMD']=='yes' and not r['LCSC Part #']))
print('COUNTS',collections.Counter(r['Designator'][0] for r in rows))
print('GROUPED top 22')
for x in sorted(grouped,key=lambda r:-r['Quantity'])[:22]:print(x)
