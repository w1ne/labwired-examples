#!/usr/bin/env python3
"""Read-only native KiCad proof; requires the exact pinned source and KiCad10 pcbnew."""
from pathlib import Path
import pcbnew,json,hashlib
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--board',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();oldpath=args.source;newpath=args.board;old=pcbnew.LoadBoard(str(oldpath));new=pcbnew.LoadBoard(str(newpath));new.BuildConnectivity()
def pads(b):return {(f.GetReference(),p.m_Uuid.AsString()):(p,f) for f in b.GetFootprints() for p in f.Pads()}
a=pads(old);b=pads(new);assert set(a)<=set(b);added=set(b)-set(a);assert len(added)==4
changed_nets=[];changed_geometry=[]
for k,(p,f) in a.items():
 q,g=b[k]
 if p.GetNetname()!=q.GetNetname():changed_nets.append({'ref':k[0],'pin':q.GetNumber(),'from':p.GetNetname(),'to':q.GetNetname()})
 geom=lambda t:(t.GetPosition().x,t.GetPosition().y,t.GetSize().x,t.GetSize().y,t.GetOrientationDegrees(),int(t.GetShape()),t.GetOffset().x,t.GetOffset().y)
 if geom(p)!=geom(q):changed_geometry.append({'ref':k[0],'pin':q.GetNumber(),'uuid':k[1],'from':geom(p),'to':geom(q)})
assert {(x['ref'],x['pin']) for x in changed_nets}=={('U9','2'),('U9','3')};assert {x['ref'] for x in changed_geometry}=={'U10','J15','J28','J54','C38'}
isolation={}
for ref,pin in [('U9','2'),('U9','3'),('USB1','A8'),('USB1','B8'),('U7','2'),('U15','2')]:
 f=next(f for f in new.GetFootprints() if f.GetReference()==ref);p=next(p for p in f.Pads() if p.GetNumber()==pin);layer=f.GetLayer();shape=p.GetEffectiveShape(layer);contacts=[]
 for t in new.GetTracks():
  if t.IsOnLayer(layer) and shape.Collide(t.GetEffectiveShape(layer)):contacts.append({'type':'track_or_via','uuid':t.m_Uuid.AsString(),'net':t.GetNetname()})
 for g in new.GetFootprints():
  for q in g.Pads():
   if q.m_Uuid==p.m_Uuid or not q.IsOnLayer(layer):continue
   if shape.Collide(q.GetEffectiveShape(layer)):contacts.append({'type':'pad','ref':g.GetReference(),'pin':q.GetNumber(),'net':q.GetNetname()})
 for z in new.Zones():
  if z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer) and z.GetFilledPolysList(layer).Collide(shape):contacts.append({'type':'filled_zone','uuid':z.m_Uuid.AsString(),'net':z.GetNetname()})
 assert not contacts,(ref,pin,contacts);isolation[ref+'.'+pin]={'layer':pcbnew.LSET.Name(layer),'net':p.GetNetname(),'copper_contacts':contacts}
u10=next(f for f in new.GetFootprints() if f.GetReference()=='U10');u10old=next(f for f in old.GetFootprints() if f.GetReference()=='U10');assert u10.GetPosition()==u10old.GetPosition() and u10.GetOrientationDegrees()==u10old.GetOrientationDegrees() and u10.GetLayer()==u10old.GetLayer();u10contacts={p.GetNumber():[q.m_Uuid.AsString() for q in new.GetConnectivity().GetConnectedTracks(p)] for p in u10.Pads()};assert all(u10contacts.values())
proold=json.loads(oldpath.with_suffix('.kicad_pro').read_text());pronew=json.loads(newpath.with_suffix('.kicad_pro').read_text());ex=pronew['erc'].pop('erc_exclusions');assert len(ex)==1;pronew['erc']['erc_exclusions']=[];assert proold==pronew
r={'tool':'KiCad '+pcbnew.GetBuildVersion(),'source_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest(),'corrected_sha256':hashlib.sha256(newpath.read_bytes()).hexdigest(),'original_pad_objects':len(a),'corrected_pad_objects':len(b),'changed_pad_nets':changed_nets,'added_pad_objects':[{'ref':k[0],'pin':b[k][0].GetNumber(),'net':b[k][0].GetNetname(),'uuid':k[1]} for k in sorted(added)],'all_other_pad_nets_unchanged':True,'changed_existing_pad_geometry':changed_geometry,'isolated_nc_pads':isolation,'u10_body_pose_preserved':True,'u10_same_net_track_contacts':u10contacts,'footprints':len(list(new.GetFootprints())),'filled_zones':len(new.Zones()),'project_values_equal_except_one_exact_erc_exclusion':True,'physical_rules_and_erc_severities_identical':True,'remaining_physical_omission':'Card1 DAT1 pad8; no pad added and no parity waiver'}
args.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['changed_existing_pad_geometry','u10_same_net_track_contacts']},indent=2))
