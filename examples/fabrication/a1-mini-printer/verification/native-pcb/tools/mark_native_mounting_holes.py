#!/usr/bin/python3
"""Declare the four unnumbered NPTH mounting holes as board-only metadata."""
import argparse, hashlib, json, re, shutil
from pathlib import Path
import pcbnew
ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--evidence',required=True);args=ap.parse_args()
src,dst=Path(args.input),Path(args.output);assert src.resolve()!=dst.resolve()
raw=src.read_text();board=pcbnew.LoadBoard(str(src));refs={f.GetReference():f for f in board.GetFootprints()};changes=[]
for ref in ['H1','H2','H3','H4']:
 f=refs[ref];pads=list(f.Pads())
 assert f.GetValue()=='M3' and f.GetFPIDAsString()=='MountingHole_3.2mm_M3'
 assert f.GetAttributes()==12 and len(pads)==1
 assert pads[0].GetNumber()=='' and pads[0].GetNetCode()==0 and pads[0].GetAttribute()==pcbnew.PAD_ATTRIB_NPTH
 changes.append({'reference':ref,'footprint_uuid':f.m_Uuid.AsString(),'pad_uuid':pads[0].m_Uuid.AsString(),'attributes_before':12,'attributes_after':28,'reason':'Unnumbered nonplated M3 mounting hole with no electrical terminal'})
def patch(block,reverse=False):
 m=re.search(r'\(property "Reference" "([^"]+)"',block)
 if not m or m.group(1) not in ['H1','H2','H3','H4']:return block
 old='(attr exclude_from_pos_files exclude_from_bom)';new='(attr board_only exclude_from_pos_files exclude_from_bom)'
 if reverse:old,new=new,old
 assert block.count(old)==1,(m.group(1),old)
 return block.replace(old,new)
pattern=r'\n\t\(footprint\b.*?\n\t\)'
blocks=re.findall(pattern,raw,re.S);assert len(blocks)==157
result=re.sub(pattern,lambda m:patch(m.group()),raw,flags=re.S)
restored=re.sub(pattern,lambda m:patch(m.group(),True),result,flags=re.S)
assert restored==raw
assert result.count('(attr board_only exclude_from_pos_files exclude_from_bom)')-raw.count('(attr board_only exclude_from_pos_files exclude_from_bom)')==4
dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(result)
if src.with_suffix('.kicad_pro').is_file():shutil.copy2(src.with_suffix('.kicad_pro'),dst.with_suffix('.kicad_pro'))
sha=lambda d:hashlib.sha256(d).hexdigest()
report={'input_sha256':sha(raw.encode()),'output_sha256':sha(result.encode()),'changes':changes,'reverse_restores_input_bytes':True,'pad_uuids_and_pad_records_unchanged':True,'all_copper_and_net_records_unchanged':True,'geometry_and_rules_unchanged':True,'pass':True}
ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True);(ev/'mounting-hole-board-only.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
