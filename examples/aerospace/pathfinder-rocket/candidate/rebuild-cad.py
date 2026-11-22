import json, math, pathlib, hashlib, shutil, re
root=pathlib.Path(__file__).resolve().parent
hist=root/'history'; hist.mkdir(exist_ok=True)
source=(hist/'original-K_DmeiaD-v2.kcad.ts').read_text()
(hist/'original-K_DmeiaD-v2.kcad.ts').write_text(source)
j=json.loads((root/'placement-result.json').read_text())
o=j['outline'];cx=(o['minX']+o['maxX'])/2;cy=(o['minY']+o['maxY'])/2
assert j['actual_mm']==[31.5,235]
rows=[];mcu=next(c for c in j['components']if c['partId']=='mcu');assert mcu['rot']==0
for c in j['components']:
 p=c['physical'];b=c['local_courtyard'];a=-c['rot']*math.pi/180
 pts=[(x*math.cos(a)-z*math.sin(a)+c['x']-cx,x*math.sin(a)+z*math.cos(a)+c['y']-cy+355) for x in [b['minX'],b['maxX']]for z in [b['minY'],b['maxY']]]
 x0=min(x for x,z in pts);x1=max(x for x,z in pts);z0=min(z for x,z in pts);z1=max(z for x,z in pts)
 pid=c['partId'];dims=p.get('bbox_mm');basis=p.get('source','');grade=p['status']
 if pid in ['mcu','baro','imu','sd']:h=dims[2]+2.4;basis+='; 2.4 mm installation stand-off reserved'
 elif pid=='led_status':h=dims[2]+1;basis+='; specified 1 mm straight-lead spacer'
 elif pid=='buzzer':h=dims[2]+.6;basis+='; 0.6 mm assembly height allowance, not a vendor tolerance'
 elif grade=='datasheet':h=dims[2]
 elif dims:h=max(dims);basis+='; largest registry axis conservatively used as installed height'
 else:h=10;grade='assumption';basis='10 mm provisional installed height reserve'
 rows.append(dict(partId=pid,ref=c['ref'],cadPart='pcb-'+pid,footprintId=c['footprintId'],x0=round(x0,6),x1=round(x1,6),z0=round(z0,6),z1=round(z1,6),height=h,sourceGrade=grade,heightBasis=basis,radialClearance=19-math.hypot(max(abs(x0),abs(x1)),h)))
assert min(r['radialClearance']for r in rows)>0
mx=mcu['x']-cx;mz=mcu['y']-cy+355
holes=[]; tails={}
for c in j['components']:
 a=-c['rot']*math.pi/180
 for p in c['geometry']['pads']:
  if not p.get('drill'):continue
  x=p['x']*math.cos(a)-p['y']*math.sin(a)+c['x']-cx
  z=p['x']*math.sin(a)+p['y']*math.cos(a)+c['y']-cy+355
  holes.append([round(x,8),round(z,8),p['drill']])
  if c['partId']!='mcu': tails.setdefault('pcb-'+c['partId'],[]).append([round(x,8),round(z,8),.9 if c['partId'] in ['boost_harness','pyro_term','battery_harness'] else min(.65,p['drill']-.2)])
holes += [[h['x']-cx,h['y']-cy+355,h['diameter']]for h in j.get('wireHoles',[])]
via_data=json.loads((root/'routing/routed-via-holes.json').read_text())
assert via_data['pcb_sha256']==hashlib.sha256((root/'routing/pathfinder-routed.kicad_pcb').read_bytes()).hexdigest()
holes += [[v['x']-cx,v['y']-cy+355,v['drill']]for v in via_data['holes']]

mcupins=[[round(mx+p['x'],8),round(mz+p['y'],8)]for p in mcu['geometry']['pads'][:40]]
prefix=source[source.index('const R ='):source.index('// Sled spans')]
prefix=prefix.replace('CRI = 19.2','CRI = 19.0').replace("assembly('LabWired Pathfinder rocket')","assembly('Pathfinder extended avionics bench candidate')")
prefix=prefix.replace('140 mm coupler','250 mm coupler').replace('tube(140, RI, CRI).translate(0, 0, 340)','tube(250, 19.8, CRI).translate(0, 0, 230)')
prefix=prefix.replace("const bay = rk.part","for (const deg of [60,180,300]) coupler=coupler.subtract(radial(4,1,18.5).translate(0,0,410).rotateZ(deg));\nconst bay = rk.part")
prefix=prefix.replace('cylinder(4, CRI).translate(0, 0, 340).union(cylinder(10.1, 3).translate(0, 0, 330))','cylinder(4, CRI).translate(0, 0, 230).union(cylinder(10.1, 3).translate(0, 0, 220))')
prefix=prefix.replace("fasten('bulkhead-aft', bay, bhAft, [0, 19, 342])","fasten('bulkhead-aft', bay, bhAft, [0, 19, 232])")
header='''// Pathfinder extended avionics BENCH CANDIDATE, derived from K_DmeiaD revision 2.
// No flight, thermal/current, mass, stability or manufacturing qualification.
// All original functional parts remain in the diagram. The 1.5-ohm load is external bench equipment.
// See fit-envelope.json for exact PCB identity, source grades, tolerance/installation allowances and open gates.
// Static geometry; original flight playback and mass/stability claims do not apply.
const altMm=0,noseSepMm=0,chuteMm=0;
'''
frame='''// 250 mm coupler leaves 110 mm between the aft-eyelet envelope and the unchanged motor-mount end.
// The 31.5 x 1.6 x 235 mm PCB slides in a 32.1 x 2.1 mm channel (0.3 mm lateral per side,0.5 mm above the nominal seated PCB).
// End bridges occupy Z234..237 and473..476,Y-5.75..-3.75. PCB occupiesZ237.5..472.5.
// The lowered end bridges leave0.65mm to the maximum trimmed solder-tail depth during axial insertion.
// Trim all through-hole solder tails to <=1.5 mm below the carrier PCB.
let frame=box(1,4.9,242,true).translate(16.55,-1.55,355)
 .union(box(1,4.9,242,true).translate(-16.55,-1.55,355));
for(const x of [-15.4,15.4]){
 frame=frame.union(box(1.3,.4,242,true).translate(x,-1.8,355));
 frame=frame.union(box(1.3,.4,242,true).translate(x,.7,355));
}
for(const z of [235.5,474.5])frame=frame.union(box(34.1,2,3,true).translate(0,-4.75,z));
// Reverse-face converter supports and end stops; bare-board rear surface is at Y=-4.5.
for(const z of [266,301])frame=frame.union(box(34.1,.55,2,true).translate(0,-4.225,z));
for(const z of [262,305])frame=frame.union(box(34.1,2.05,2,true).translate(0,-4.975,z));
// Battery tray: maximum pack17x9.5x66 plus1 mm per axis installation reserve =18x10.5x68.
// Clear opening18.2mm; 0.8mm walls/back,2mm end stops. This is a fit prototype, not vibration acceptance.
frame=frame.union(box(19.8,.8,72,true).translate(0,-15.4,351));
for(const x of [-9.5,9.5])frame=frame.union(box(.8,11.85,72,true).translate(x,-9.875,351));
for(const z of [316,386])frame=frame.union(box(34.1,2.05,2,true).translate(0,-4.975,z))
 .union(box(19.8,11.85,2,true).translate(0,-9.875,z));
// Cable slot in the forward tray stop preserves a 4x4 mm bridge volume.
frame=frame.subtract(box(6,5,2.4,true).translate(0,-9.75,386));
// Trim only outer lower tray corners; the battery reservation is unchanged.
frame=frame.intersect(cylinder(242,18.4).translate(0,0,234));
frame=frame.subtract(radial(4.3,3.3,16.3).translate(0,0,410));
const sled=rk.part('avionics-sled',frame.color('#343940'),{material:'petg'});
fasten('sled',bhAft,sled,[0,-4.75,234]);
'''
board='const drillHoles='+json.dumps(holes,separators=(',',':'))+''';
let substrate=box(31.5,1.6,235,true).translate(0,-.8,355);
for(const [x,z,d]of drillHoles)substrate=substrate.subtract(cylinder(2,d/2).rotateX(-90).translate(x,-1.8,z));
const pcb=rk.part('flight-computer-pcb',substrate.color('#1a6b3a'),{density:1850});
fasten('pcb',sled,pcb,[15.3,-1.6,355]);
'''
envelopes='const tailReservations='+json.dumps(tails,separators=(',',':'))+';\nconst envelopes='+json.dumps([[r['cadPart'],r['x0'],r['x1'],r['z0'],r['z1'],r['height'],r['sourceGrade']]for r in rows if r['partId']!='mcu'],separators=(',',':'))+''';
for(const [name,x0,x1,z0,z1,h,grade]of envelopes){
 const center=[(x0+x1)/2,h/2,(z0+z1)/2];
 let occupied=box(x1-x0,h,z1-z0,true).translate(center[0],center[1],center[2]);
 for(const [x,z,d]of(tailReservations[name]||[]))occupied=occupied.union(cylinder(3.1,d/2).rotateX(-90).translate(x,-3.1,z));
 const body=rk.part(name,occupied.color(grade==='datasheet'?'#a8a5a0':grade==='assumption'?'#d98f40':'#536576')); // occupied volume has no asserted physical mass
 fasten(name,pcb,body,[center[0],0,center[2]]);
}
// Battery body below is an installation volume, not an exact vendor mesh.
// Nominal61x15x7.5 and published positive tolerances5/2/2 => max66x17x9.5 mm.
const lipo=rk.part('battery-tattu-450mah-envelope',box(18,10.5,68,true).translate(0,-9.75,351).color('#3949ab'));
fasten('battery',sled,lipo,[0,-15,351]);
// Connector and cable service reservation:20x10x7mm, separate from the pack body.
// BT2.0 rating9A continuous/15A burst does not qualify the remaining cable/copper path.
const batteryCable=rk.part('battery-pigtail-service-envelope',box(10,7,20,true).translate(0,-8,398).union(box(4,4,3,true).translate(0,-9.75,386.5)).color('#6b78ca'));
fasten('battery-cable',lipo,batteryCable,[0,-9.75,385]);
'''
suffix=source[source.index('// Arm switch'):]
bayprefix=prefix
bayprefix=re.sub(r'// ---- Launch pad:.*?// ---- Airframe:', '// ---- Airframe:', bayprefix, flags=re.S)
bayprefix=re.sub(r"^const lower = .*\n",'',bayprefix,flags=re.M)
bayprefix=re.sub(r"^fasten\('coupler'.*\n",'',bayprefix,flags=re.M)
bayprefix=re.sub(r"^const upper = .*\n",'',bayprefix,flags=re.M)
bayprefix=re.sub(r"^fasten\('upper-tube'.*\n",'',bayprefix,flags=re.M)
baysuffix=suffix[:suffix.index('// ----')]+ '\nreturn rk.solvedModel({});\n'
# Exact source STEP assets are kept without fusing new solids into vendor compounds.
for mode in ['vendor-step','bounded']:
 mcuCode=f"const solderPins={json.dumps(mcupins,separators=(',',':'))};\n"
 if mode=='vendor-step':
  mcuCode+="const weactShape=await lib.fromSTEP('https://raw.githubusercontent.com/WeActStudio/WeActStudio.MiniSTM32F4x1/6a7f7d434a9d6361f91590d4cdd16b4a70ce7513/Hardware/MiniF4x1Cx_V31_3D.step');\n"
  mcuCode+=f"const blackpill=rk.part('pcb-mcu',weactShape.rotateZ(-90).rotateX(-90).translate({mx-10.2815:.8f},4.451439750202199,{mz-22.097:.8f}));\nconst supports=[];\n"
 else:
  mcuCode="// Manufacturer-STEP bounding volume. The exact vendor import is retained in the companion source.\n"+mcuCode
  mcuCode+=f"let mcuVolume=box(52.806999206543,20.778999328613253,5.301439750202199,true).translate(26.4034996032715,10.389499664306626,.5992801248989005).rotateZ(-90).rotateX(-90).translate({mx-10.2815:.8f},4.451439750202199,{mz-22.097:.8f});\n"
 mcuCode+=f"for(const [index,x]of [[0,{mx-7.5:.8f}],[1,{mx+7.74:.8f}]]){{\n let spacer=box(2.54,2.96,50.8,true).translate(x,1.48,{mz+3.43:.8f});\n for(const [px,pz]of solderPins)if(Math.abs(px-x)<.01)spacer=spacer.union(cylinder(7.7,.25).rotateX(-90).translate(px,-3.1,pz));\n"
 if mode=='vendor-step':
  mcuCode+=f" const support=rk.part('mcu-pin-spacer-'+index,spacer.color('#222222'),{{density:1500}});\n fasten('mcu-support-'+index,pcb,support,[x+.9,0,{mz-19.43:.8f}]);supports.push(support);\n}}\nfasten('pcb-mcu',supports[0],blackpill,[{mx-6.6:.8f},2.96,{mz-19.43:.8f}]);\n"
 else:
  mcuCode+=f" mcuVolume=mcuVolume.union(spacer);\n}}\nconst blackpill=rk.part('pcb-mcu',mcuVolume.color('#316a3b'));\nfasten('pcb-mcu',pcb,blackpill,[{mx-6.6:.8f},0,{mz-19.43:.8f}]);\n"
 if mode=='vendor-step':
  boostCode="const boostShape=await lib.fromSTEP('https://www.pololu.com/file/0J1561/step-up-voltage-regulator-u3v70x.step');\nconst boost=rk.part('boost-pololu-u3v70f5',boostShape.rotateZ(90).rotateX(90).translate(7.62,-4.5,263));\n"
 else:boostCode="// Conservative U3V70x primary-STEP bounds include all disconnected vendor sub-solids.\nconst boost=rk.part('boost-pololu-u3v70f5',box(15.24,5.4848,40.64,true).translate(0,-7.2424,283.32).color('#386599'));\n"
 boostCode+="fasten('boost',sled,boost,[0,-4.5,266]);\n"
 serviceCode='''// Reserved installation space, not exact wire solids or a mass claim.
// Primary Pololu22AWG wire is1.6mm nominal OD; reserve1.8mm and verify supplied wire.
// The8nativeEdge.Cuts holes are2.4mm diameter; a2.2mm protected-wire envelope passes each.
const wirePorts='''+json.dumps([[h['x']-cx,h['y']-cy+355]for h in j.get('wireHoles',[])],separators=(',',':'))+''';
let wireSpace=box(17.05,11.2,11,true).translate(0,7.4,408.15)
 .union(box(19.55,11.2,11,true).translate(0,7.4,437.15));
for(const [x,z]of wirePorts)wireSpace=wireSpace.union(cylinder(3.4,1.1).rotateX(-90).translate(x,-1.6,z));
for(const [z0,z1]of [[411.5,421.5],[440.5,448]]){
 wireSpace=wireSpace.union(box(29.2,2.6,z1-z0,true).translate(0,-2.9,(z0+z1)/2));
 wireSpace=wireSpace.union(box(31.6,4.8,z1-z0,true).translate(0,-6.6,(z0+z1)/2));
}
// Two underside side corridors reserve three1.8mm conductors per side.
// They pass below the structural bridges and outside the battery tray.
for(const x of [-13,13])wireSpace=wireSpace.union(box(5.6,2.8,144.36,true).translate(x,-7.6,375.82));
// Converter-end and battery-pigtail fan-out volumes meet, without entering,
// the separate purchased-module and connector installation envelopes.
wireSpace=wireSpace.union(box(31.6,2.8,10.86,true).translate(0,-7.6,309.07));
wireSpace=wireSpace.union(box(5.2,2.8,4,true).translate(7.6,-7.6,398));
const harnessSpace=rk.part('power-harness-service-envelope',wireSpace.color('#d58e35'),{});
fasten('harness-space',pcb,harnessSpace,[0,-1.6,417]);
// Conductor entry and driver access are performed with the coupler removed.
// Bend space permits a5.5mm centerline turn; the cable maker gives no minimum
// radius, so bend, abrasion protection, strain relief and thermal limits remain physical checks.
'''
 block=frame+board+mcuCode+envelopes+boostCode+serviceCode
 full=header+prefix+block+suffix;bay=header+bayprefix+block+baysuffix
 fullName='pathfinder-vendor-step.kcad.ts'if mode=='vendor-step'else'pathfinder-extended.kcad.ts'
 bayName='avionics-fit-vendor-step.kcad.ts'if mode=='vendor-step'else'avionics-fit-envelope.kcad.ts'
 (root/fullName).write_text(full.strip());(root/bayName).write_text(bay.strip())
receipt=dict(schema=2,candidate='source-bound-extended-bench-candidate',pcb=dict(outline=o,span_mm=j['actual_mm'],thickness_mm=1.6,topY=0,center=[0,-.8,355],component_count=37,device_part_count=41,unrouted=False,routed_via_count=via_data['via_count'],sha256=via_data['pcb_sha256'],unrouted_input_sha256=hashlib.sha256((root/'pathfinder-unrouted.kicad_pcb').read_bytes()).hexdigest()),enclosure=dict(end_bridge_top_y_mm=-3.75,maximum_solder_tail_y_mm=-3.1,tail_to_end_bridge_gap_mm=.65,airframe_od_mm=42,airframe_id_mm=40,coupler_od_mm=39.6,coupler_id_mm=38,coupler_z=[230,480],carrier_z=[234,476],pcb_z=[237.5,472.5],axial_clearance_to_motor_mount_mm=110),harness=dict(source='https://www.pololu.com/product/2642',gauge_awg=22,nominal_od_mm=1.6,reserved_od_mm=1.8,protected_port_envelope_mm=2.2,port_diameter_mm=2.4,side_channels_mm=[5.6,2.8],bend_centerline_space_mm=5.5,bend_radius_is_assembly_assumption=True,remaining=['Verify actual insulation diameter and bend before closure.','Use abrasion protection and strain relief at every bare FR4 pass-through.','The two external bench-load wires are connected with the bay open; they are not a qualified enclosed flight harness.','Screwdriver access requires the coupler removed; support2poleterminal bodies during tightening.']),wire_holes=j.get('wireHoles',[]),terminal_service_volumes=j.get('serviceVolumes',[]),stackup=j.get('stackup'),components=rows,minimum_component_radial_clearance_mm=min(r['radialClearance']for r in rows),battery=dict(mpn='Tattu TAA4501S75BT2',maximum_pack_xyz_mm=[17,9.5,66],installation_xyz_mm=[18,10.5,68],center=[0,-9.75,351],radialClearance=19-math.hypot(9,15),tray_minimum_radial_clearance_mm=.6,tray_outer_radius_bound_mm=18.4,previous_rectangular_tray_clearance_mm=19-math.hypot(9.9,15.8),service_xyz_mm=[10,7,20],service_center=[0,-8,398],sourceGrade='manufacturer-max-plus-declared-installation-allowance'),boost=dict(mpn='Pololu U3V70F5 #2891',source='https://www.pololu.com/file/0J1561/step-up-voltage-regulator-u3v70x.step',bounds_mm=[[-7.62,-9.9848,263],[7.62,-4.5,303.64]]),limitations=['The PCB channel is32.1x2.1mm for31.5x1.6mm nominal substrate. JLC regular outline tolerance+/-0.2mm and1.6mm thickness+/-10% leave0.4mm total lateral and0.34mm vertical clearance before carrier printing error; measure the actual print and board before assembly.','This is static component-body and installation-volume fit; terminal wire paths, screw-tool access, cable gauge/retention and PCB-current capacity require their separate checks.','Generic small passive/transistor/harness items retain conservative registry envelopes; sourceGrade remains explicit per part.','Offboard1.5ohm bench load is not a flight initiator or an assembled carrier resistor.','Physical voltage sag, peak camera current, thermal/current behavior, vibration, battery swelling and flight dynamics are unqualified.','Routing and independent KiCad DRC are recorded separately against the exact native PCB. Static fit does not imply manufacturing, electrical-current or thermal acceptance.'],cad_sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest()for name in ['pathfinder-extended.kcad.ts','pathfinder-vendor-step.kcad.ts','avionics-fit-envelope.kcad.ts','avionics-fit-vendor-step.kcad.ts']})
drill_review=json.loads((root/'pcb-cad-drill-parity-review.json').read_text())
if drill_review['pcb_sha256']!=receipt['pcb']['sha256'] or drill_review['source_sha256']!=receipt['cad_sources']['pathfinder-extended.kcad.ts']:
 raise RuntimeError('Drill projection review does not match this native PCB and CAD source')
receipt['pcb']['cad_drill_projection']=dict(review='pcb-cad-drill-parity-review.json',shape_count=sum(drill_review['counts'].values()),one_to_one=drill_review['one_to_one'],maximum_center_rounding_mm=.0005,rounded_center_count=len(drill_review['nonzero_over_1e_9_mm']))
receipt['limitations'].append('All 173 cutout and drill shapes map one-to-one. Ten J3/J4/J6 hole centers differ from the native board by at most 0.0005 mm because of coordinate rounding; CAD/native coordinates are not exactly equal.')
(root/'fit-envelope.json').write_text(json.dumps(receipt,indent=2)+'\n')
(root/'placement-result.json').write_text(json.dumps(j,indent=2)+'\n')
(root/'project.input.pending.json').write_text((root/'design-input.json').read_text())
(root/'pathfinder-unrouted.kicad_pcb').write_bytes((root/'pathfinder-unrouted.kicad_pcb').read_bytes())
review=json.loads((hist/'root-battery-current-review-20261122.json').read_text())
review['prior_review_diagram_file_sha256']=review['diagram_file_sha256']
review['diagram_file_sha256']=hashlib.sha256((root/'project.input.pending.json').read_bytes()).hexdigest()
review['fit_envelope_file_sha256']=hashlib.sha256((root/'fit-envelope.json').read_bytes()).hexdigest()
(root/'battery-current-review.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(dict(component_count=37,device_part_count=41,pcb_mm=j['actual_mm'],min_component_radial_clearance=receipt['minimum_component_radial_clearance_mm'],min_battery_tray_radial_clearance=receipt['battery']['tray_minimum_radial_clearance_mm'],source_hashes=receipt['cad_sources']),indent=2))
