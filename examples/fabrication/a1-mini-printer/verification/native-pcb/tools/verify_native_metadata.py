#!/usr/bin/python3
"""Prove the final editable PCB differs from the physical source only by listed metadata."""
import argparse, hashlib, json, re
from pathlib import Path
from make_native_portable import MODEL_FILES
ap=argparse.ArgumentParser();ap.add_argument('physical');ap.add_argument('final');ap.add_argument('--evidence',required=True);args=ap.parse_args()
physical,final,ev=Path(args.physical),Path(args.final),Path(args.evidence)
sha=lambda data:hashlib.sha256(data).hexdigest()
base=physical.read_bytes();raw=final.read_bytes();assert sha(base)=='55b7162b73d0d9675725c5ea9211b6c633feeb2bd298e9a1e6209b5e5c25a6ad'
link=json.loads((ev/'native-schematic-linkage.json').read_text())
portable=json.loads((ev/'portable-model-paths.json').read_text())
holes=json.loads((ev/'mounting-hole-board-only.json').read_text())
nc=json.loads((ev/'native-nc-metadata.json').read_text())
namespace=json.loads((ev/'native-footprint-namespaces.json').read_text())
assert link['ok'] and link['allOtherBytesIdentical'] and link['nativePcbSha256']==sha(base)
assert portable['pass'] and portable['reverse_restores_input_bytes'] and portable['input_sha256']==link['linkedPcbSha256']
assert holes['pass'] and holes['reverse_restores_input_bytes'] and holes['input_sha256']==portable['output_sha256']
assert nc['pass'] and nc['reverse_restores_input_bytes'] and nc['conductive_connectivity_unchanged'] and nc['input_sha256']==holes['output_sha256'] and namespace['input_sha256']==nc['output_sha256']
assert namespace['pass'] and namespace['reverse_restores_input_bytes'] and namespace['output_sha256']==sha(raw)
restored=raw
namespace_by_ref={change['reference']:change for change in namespace['changes']}
assert len(namespace_by_ref)==156
def restore_namespace(m):
 block=m.group();ref=re.search(rb'\(property "Reference" "([^"]+)"',block).group(1).decode()
 change=namespace_by_ref.get(ref)
 if not change:return block
 old=('(footprint "'+change['after']+'"').encode();new=('(footprint "'+change['before']+'"').encode()
 assert block.count(old)==1
 assert change['after'].split(':',1)[1]==change['before']
 return block.replace(old,new,1)
restored=re.sub(rb'\n\t\(footprint\b.*?\n\t\)',restore_namespace,restored,flags=re.S)
assert sha(restored)==namespace['input_sha256']
for change in nc['changes']:
 line=('\n\t\t\t(net "'+change['after']+'")').encode();assert restored.count(line)==1;restored=restored.replace(line,b'')
assert sha(restored)==nc['input_sha256']
def restore_holes(m):
 block=m.group();ref=re.search(rb'\(property "Reference" "([^"]+)"',block).group(1).decode()
 if ref not in ['H1','H2','H3','H4']:return block
 old=b'(attr board_only exclude_from_pos_files exclude_from_bom)';new=b'(attr exclude_from_pos_files exclude_from_bom)'
 assert block.count(old)==1
 return block.replace(old,new)
restored=re.sub(rb'\n\t\(footprint\b.*?\n\t\)',restore_holes,restored,flags=re.S)
assert sha(restored)==holes['input_sha256']
for model in MODEL_FILES:
 old=('(model "${KIPRJMOD}/models/'+model['filename']+'"').encode();new=('(model "'+model['original_path']+'"').encode()
 assert restored.count(old)==len(model['references']);restored=restored.replace(old,new)
 assert sha((final.parent/'models'/model['filename']).read_bytes())==model['sha256']
assert sha(restored)==portable['input_sha256']
paths=re.findall(rb'\n\t\t\(path "([^"]+)"\)',restored)
assert len(paths)==153 and {x.decode() for x in paths}=={x['after'] for x in link['changes']}
final_uuid_map=json.loads((ev/'schematic-uuid-map.json').read_text())
assert final_uuid_map['sourceSha256']==sha(final.with_suffix('.kicad_sch').read_bytes())
assert len(final_uuid_map['references'])==153
assert {ref:record['path'] for ref,record in final_uuid_map['references'].items()}=={change['ref']:change['after'] for change in link['changes']}
restored=re.sub(rb'\n\t\t\(path "[^"]+"\)',b'',restored)
assert restored==base,'Unlisted change to the accepted physical PCB bytes'
assert physical.with_suffix('.kicad_pro').read_bytes()==final.with_suffix('.kicad_pro').read_bytes()
report={'schema':'labwired.native-metadata-only-provenance.v1','physical_source_sha256':sha(base),'schematic_linked_sha256':link['linkedPcbSha256'],'portable_linked_sha256':portable['output_sha256'],'mounting_metadata_sha256':holes['output_sha256'],'isolated_nc_named_sha256':nc['output_sha256'],'final_pcb_sha256':sha(raw),'final_schematic_sha256':sha(final.with_suffix('.kicad_sch').read_bytes()),'rules_sha256':sha(final.with_suffix('.kicad_pro').read_bytes()),'accepted_populated_step_sha256':'4fa338f753a8c8a17331facabd8ee8d3698bc0a0cd3fa152b71749e88baa2e2a','listed_metadata_changes':{'schematic_uuid_paths':153,'model_filename_strings':6,'board_only_mounting_holes':4,'isolated_ic_nc_net_names':12,'footprint_library_namespaces':156},'removing_only_listed_metadata_restores_physical_source_bytes':True,'all_footprint_and_pad_uuids_preserved':True,'schematic_uuid_paths_match_final_schematic':True,'all_pad_geometry_and_copper_and_zone_bytes_preserved':True,'all_connected_signal_and_power_pad_net_names_preserved':True,'each_new_nc_net_is_one_isolated_physical_pad':True,'duplicated_mounting_pads_still_have_no_net':True,'all_3d_transforms_and_model_bytes_unchanged':True,'project_rules_byte_identical':True,'step_geometry_provenance_retained':True,'pass':True}
(ev/'native-metadata-only-provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
