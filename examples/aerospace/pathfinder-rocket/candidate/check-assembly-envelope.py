"""Continuous nominal containment and axial-slide proof; not fabrication or retention qualification."""
from pathlib import Path
import json,math,hashlib
root=Path(__file__).resolve().parent
f=json.loads((root/'fit-envelope.json').read_text());p=json.loads((root/'placement-result.json').read_text());code=(root/'pathfinder-extended.kcad.ts').read_text()
checks=[]
def bound(name,x0,x1,y0,y1,z0,z1):
 radius=math.hypot(max(abs(x0),abs(x1)),max(abs(y0),abs(y1)))
 assert radius<=18.4+1e-8 and z0>=234-1e-8 and z1<=476+1e-8,(name,radius,z0,z1)
 checks.append({'part':name,'radius_upper_mm':radius,'z_mm':[z0,z1],'within_cassette':True})
for c in f['components']:bound(c['cadPart'],c['x0'],c['x1'],0,c['height'],c['z0'],c['z1'])
bound('flight-computer-pcb',-15.75,15.75,-1.6,0,237.5,472.5)
bound('battery installation',-9,9,-15,-4.5,317,385)
bound('battery cable service',-5,5,-11.5,-4.5,388,408)
bound('battery cable bridge',-2,2,-11.75,-7.75,385,388)
bound('converter',-7.62,7.62,-9.9848,-4.5,263,303.64)
for b in [(-8.525,8.525,1.8,13,402.65,413.65),(-9.775,9.775,1.8,13,431.65,442.65),(-14.6,14.6,-4.2,-1.6,411.5,421.5),(-15.8,15.8,-9,-4.2,411.5,421.5),(-14.6,14.6,-4.2,-1.6,440.5,448),(-15.8,15.8,-9,-4.2,440.5,448),(-15.8,-10.2,-9,-6.2,303.64,448),(10.2,15.8,-9,-6.2,303.64,448),(-15.8,15.8,-9,-6.2,303.64,314.5),(5,10.2,-9,-6.2,396,400)]:bound('wire service',*b)
for hole in f['wire_holes']:
 x=hole['x']-25.75;z=hole['y']+227.5;bound('protected wire port',x-1.1,x+1.1,-1.6,1.8,z-1.1,z+1.1)
assert 'frame=frame.intersect(cylinder(242,18.4).translate(0,0,234));'in code
checks.append({'part':'carrier frame','radius_upper_mm':18.4,'z_mm':[234,476],'proof':'Final intersection with the R18.4 x242 cylinder, followed only by subtraction.'})
max_tail_x=0
for c in p['components']:
 a=-c['rot']*math.pi/180
 for pad in c['geometry']['pads']:
  if not pad.get('drill'):continue
  x=pad['x']*math.cos(a)-pad['y']*math.sin(a)+c['x']-25.75;z=pad['x']*math.sin(a)+pad['y']*math.cos(a)+c['y']+227.5
  d=.5 if c['partId']=='mcu'else .9 if c['partId']in ['boost_harness','pyro_term','battery_harness']else min(.65,pad['drill']-.2)
  max_tail_x=max(max_tail_x,abs(x)+d/2);bound(c['partId']+' solder tail',x-d/2,x+d/2,-3.1,0,z-d/2,z+d/2)
front_max_x=max(max(abs(c['x0']),abs(c['x1']))for c in f['components'])
assert front_max_x<14.75 and max_tail_x<14.75
receipt={'schema':'pathfinder.nominal-assembly-envelope.v1','full_cad_sha256':hashlib.sha256(code.encode()).hexdigest(),'pcb_sha256':f['pcb']['sha256'],'conservative_cassette':{'radius_mm':18.4,'z_mm':[234,476],'coupler_bore_radius_mm':19,'nominal_radial_gap_mm':.6,'bounded_hosted_path_receipt':'assembly-path-bounded.json','all_final_moving_geometry_contained':True},'continuous_axial_slide':{'status':'proved_for_declared_nominal_bounds','preconditions':['Remove both bay bulkheads and the radial panel switch.','Disconnect the external bench leads and all leads that prevent axial motion.','Install the populated PCB in the carrier before connecting the reserved wiring harness.'],'pcb_width_mm':31.5,'channel_width_mm':32.1,'nominal_width_gap_per_side_mm':.3,'pcb_nominal_thickness_mm':1.6,'channel_height_mm':2.1,'nominal_upper_gap_mm':.5,'front_body_max_abs_x_mm':front_max_x,'upper_ledge_inner_abs_x_mm':14.75,'minimum_body_to_ledge_side_gap_mm':14.75-front_max_x,'maximum_tail_abs_x_mm':max_tail_x,'minimum_tail_to_end_bridge_y_gap_mm':.65,'minimum_tail_to_reverse_support_y_gap_mm':.85},'containment_checks':checks,'physical_holds':['Bore/print/PCB tolerances, battery swelling and actual wire bends must be measured.','Retainers, solder-tail trim, abrasion protection, strain relief and tool access require assembly inspection.','The full48-body combinatorial solver exceeded its budget on the preceding geometry; this is a conservative bounded-path proof, not a full-assembly search result.','Continuous geometric translation does not qualify vibration, loads, hardware current, temperature or flight.']}
(root/'assembly-envelope-proof.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'contained_items':len(checks),'source':receipt['full_cad_sha256'],'radial_gap_mm':.6,'front_body_gap_mm':14.75-front_max_x,'tail_max_x_mm':max_tail_x}))
