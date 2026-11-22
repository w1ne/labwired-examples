// Pathfinder extended avionics BENCH CANDIDATE, derived from K_DmeiaD revision 2.
// No flight, thermal/current, mass, stability or manufacturing qualification.
// All original functional parts remain in the diagram. The 1.5-ohm load is external bench equipment.
// See fit-envelope.json for exact PCB identity, source grades, tolerance/installation allowances and open gates.
// Static geometry; original flight playback and mass/stability claims do not apply.
const altMm=0,noseSepMm=0,chuteMm=0;
const R = 21, RI = 20, CRI = 19.0;                // body OD/ID radius, coupler ID radius
const rk = assembly('Pathfinder extended avionics bench candidate');

function tube(h, ro, ri) {
  return cylinder(h, ro).subtract(cylinder(h + 0.4, ri).translate(0, 0, -0.2));
}
function fasten(name, parent, child, pos) {
  parent.connector('at_' + name, { type: 'frame', origin: { kind: 'vec3', value: pos } });
  child.connector('mount', { type: 'frame', origin: { kind: 'vec3', value: pos } });
  rk.mate(name, parent.name + '.at_' + name, child.name + '.mount', 'fastened');
}
function radial(h, r, x0) { return cylinder(h, r).rotateY(90).translate(x0, 0, 0); } // axis along +X
function polar(r, deg, z) { const a = (deg * Math.PI) / 180; return [Math.cos(a) * r, Math.sin(a) * r, z]; }

// ---- Airframe: 42 mm spiral-wound kraft-phenolic tubes, 400 mm booster + 220 mm payload

// ---- Avionics bay: 250 mm coupler (fits the tube ID), 20 mm switch band, two bulkheads
let coupler = tube(250, 19.8, CRI).translate(0, 0, 230);
coupler = coupler.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));           // arm-switch port
for (const deg of [60,180,300]) coupler=coupler.subtract(radial(4,1,18.5).translate(0,0,410).rotateZ(deg));
const bay = rk.part('avionics-coupler', coupler.color('#d9cdb4'), { density: 1000 });
let band = tube(20, R, RI).translate(0, 0, 400);
band = band.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));
for (const deg of [60, 180, 300]) band = band.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg)); // 3 x 2 mm static ports
const switchBand = rk.part('switch-band', band.color('#1f2a44'), { density: 1000 });
fasten('switch-band', bay, switchBand, [0, 20.2, 410]);
const bhAft = rk.part('bulkhead-aft', cylinder(4, CRI).translate(0, 0, 230).union(cylinder(10.1, 3).translate(0, 0, 220)).color('#b08a5a'), { density: 680 });
fasten('bulkhead-aft', bay, bhAft, [0, 19, 232]);
const bhFwd = rk.part('bulkhead-fwd', cylinder(4, CRI).translate(0, 0, 476).union(cylinder(13.1, 3).translate(0, 0, 479.9)).color('#b08a5a'), { density: 680 });
fasten('bulkhead-fwd', bay, bhFwd, [0, 19, 478]);

// 250 mm coupler leaves 110 mm between the aft-eyelet envelope and the unchanged motor-mount end.
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
const drillHoles=[[-10.585,241.275,0.8],[-10.585,243.815,0.8],[-10.585,246.355,0.8],[-10.585,248.895,0.8],[-10.585,251.435,0.8],[-10.585,253.975,0.8],[-10.585,256.515,0.8],[-10.585,259.055,0.8],[-10.585,261.595,0.8],[-10.585,264.135,0.8],[-10.585,266.675,0.8],[-10.585,269.215,0.8],[-10.585,271.755,0.8],[-10.585,274.295,0.8],[-10.585,276.835,0.8],[-10.585,279.375,0.8],[-10.585,281.915,0.8],[-10.585,284.455,0.8],[-10.585,286.995,0.8],[-10.585,289.535,0.8],[4.655,289.535,0.8],[4.655,286.995,0.8],[4.655,284.455,0.8],[4.655,281.915,0.8],[4.655,279.375,0.8],[4.655,276.835,0.8],[4.655,274.295,0.8],[4.655,271.755,0.8],[4.655,269.215,0.8],[4.655,266.675,0.8],[4.655,264.135,0.8],[4.655,261.595,0.8],[4.655,259.055,0.8],[4.655,256.515,0.8],[4.655,253.975,0.8],[4.655,251.435,0.8],[4.655,248.895,0.8],[4.655,246.355,0.8],[4.655,243.815,0.8],[4.655,241.275,0.8],[-6.811051,285.775,0.8],[-4.271051,285.775,0.8],[-1.731051,285.775,0.8],[0.808949,285.775,0.8],[-9.75,459.8,0.8],[-6.25,459.8,0.8],[12.2,459.0,0.8],[12.2,454.0,0.8],[-10.825,357.215,1],[-10.825,359.755,1],[-10.825,362.295,1],[-10.825,364.835,1],[-10.825,367.375,1],[-10.825,369.915,1],[-10.825,372.455,1],[-10.925,330.735,1],[-10.925,333.275,1],[-10.925,335.815,1],[-10.925,338.355,1],[-10.925,340.895,1],[-10.925,343.435,1],[1.775,343.435,1],[1.775,340.895,1],[1.775,338.355,1],[1.775,335.815,1],[1.775,333.275,1],[1.775,330.735,1],[-10.935,319.495,1],[-8.395,319.495,1],[-5.855,319.495,1],[-3.315,319.495,1],[-0.775,319.495,1],[1.765,319.495,1],[4.305,319.495,1],[6.845,319.495,1],[9.385,319.495,1],[-6.5,426.625,1.2],[-3.0,426.625,1.2],[-1.125,385.585,1],[6.475,385.585,1],[-12.0,429.81,0.8],[-12.0,422.19,0.8],[-9.75,452.775,0.9],[-9.75,450.235,0.9],[12.1275,386.19,1],[12.1275,388.73,1],[12.1275,391.27,1],[12.1275,393.81,1],[-11.8725,386.19,1],[-11.8725,388.73,1],[-11.8725,391.27,1],[-11.8725,393.81,1],[-5.25,397.625,1.2],[-1.75,397.625,1.2],[1.75,397.625,1.2],[5.25,397.625,1.2],[12.1275,401.73,1],[12.1275,404.27,1],[3.0,426.625,1.2],[6.5,426.625,1.2],[-5.25,411.5,2.4],[-1.75,411.5,2.4],[1.75,411.5,2.4],[5.25,411.5,2.4],[-6.5,440.5,2.4],[-3.0,440.5,2.4],[3.0,440.5,2.4],[6.5,440.5,2.4]];
let substrate=box(31.5,1.6,235,true).translate(0,-.8,355);
for(const [x,z,d]of drillHoles)substrate=substrate.subtract(cylinder(2,d/2).rotateX(-90).translate(x,-1.8,z));
const pcb=rk.part('flight-computer-pcb',substrate.color('#1a6b3a'),{density:1850});
fasten('pcb',sled,pcb,[15.3,-1.6,355]);
// Manufacturer-STEP bounding volume. The exact vendor import is retained in the companion source.
const solderPins=[[-10.585,241.275],[-10.585,243.815],[-10.585,246.355],[-10.585,248.895],[-10.585,251.435],[-10.585,253.975],[-10.585,256.515],[-10.585,259.055],[-10.585,261.595],[-10.585,264.135],[-10.585,266.675],[-10.585,269.215],[-10.585,271.755],[-10.585,274.295],[-10.585,276.835],[-10.585,279.375],[-10.585,281.915],[-10.585,284.455],[-10.585,286.995],[-10.585,289.535],[4.655,289.535],[4.655,286.995],[4.655,284.455],[4.655,281.915],[4.655,279.375],[4.655,276.835],[4.655,274.295],[4.655,271.755],[4.655,269.215],[4.655,266.675],[4.655,264.135],[4.655,261.595],[4.655,259.055],[4.655,256.515],[4.655,253.975],[4.655,251.435],[4.655,248.895],[4.655,246.355],[4.655,243.815],[4.655,241.275]];
let mcuVolume=box(52.806999206543,20.778999328613253,5.301439750202199,true).translate(26.4034996032715,10.389499664306626,.5992801248989005).rotateZ(-90).rotateX(-90).translate(-13.36650000,4.451439750202199,239.87800000);
for(const [index,x]of [[0,-10.58500000],[1,4.65500000]]){
 let spacer=box(2.54,2.96,50.8,true).translate(x,1.48,265.40500000);
 for(const [px,pz]of solderPins)if(Math.abs(px-x)<.01)spacer=spacer.union(cylinder(7.7,.25).rotateX(-90).translate(px,-3.1,pz));
 mcuVolume=mcuVolume.union(spacer);
}
const blackpill=rk.part('pcb-mcu',mcuVolume.color('#316a3b'));
fasten('pcb-mcu',pcb,blackpill,[-9.68500000,0,242.54500000]);
const tailReservations={"pcb-c_bulk":[[-9.75,459.8,0.6000000000000001],[-6.25,459.8,0.6000000000000001]],"pcb-c_dec":[[12.2,459.0,0.6000000000000001],[12.2,454.0,0.6000000000000001]],"pcb-baro":[[-10.825,357.215,0.65],[-10.825,359.755,0.65],[-10.825,362.295,0.65],[-10.825,364.835,0.65],[-10.825,367.375,0.65],[-10.825,369.915,0.65],[-10.825,372.455,0.65]],"pcb-imu":[[-10.925,330.735,0.65],[-10.925,333.275,0.65],[-10.925,335.815,0.65],[-10.925,338.355,0.65],[-10.925,340.895,0.65],[-10.925,343.435,0.65],[1.775,343.435,0.65],[1.775,340.895,0.65],[1.775,338.355,0.65],[1.775,335.815,0.65],[1.775,333.275,0.65],[1.775,330.735,0.65]],"pcb-sd":[[-10.935,319.495,0.65],[-8.395,319.495,0.65],[-5.855,319.495,0.65],[-3.315,319.495,0.65],[-0.775,319.495,0.65],[1.765,319.495,0.65],[4.305,319.495,0.65],[6.845,319.495,0.65],[9.385,319.495,0.65]],"pcb-pyro_term":[[-6.5,426.625,0.9],[-3.0,426.625,0.9]],"pcb-buzzer":[[-1.125,385.585,0.65],[6.475,385.585,0.65]],"pcb-d_buzz":[[-12.0,429.81,0.6000000000000001],[-12.0,422.19,0.6000000000000001]],"pcb-led_status":[[-9.75,452.775,0.65],[-9.75,450.235,0.65]],"pcb-cam":[[12.1275,386.19,0.65],[12.1275,388.73,0.65],[12.1275,391.27,0.65],[12.1275,393.81,0.65]],"pcb-uart":[[-11.8725,386.19,0.65],[-11.8725,388.73,0.65],[-11.8725,391.27,0.65],[-11.8725,393.81,0.65]],"pcb-boost_harness":[[-5.25,397.625,0.9],[-1.75,397.625,0.9],[1.75,397.625,0.9],[5.25,397.625,0.9]],"pcb-arm_harness":[[12.1275,401.73,0.65],[12.1275,404.27,0.65]],"pcb-battery_harness":[[3.0,426.625,0.9],[6.5,426.625,0.9]]};
const envelopes=[["pcb-c_bulk",-12.275,-3.725,455.525,464.075,13,"datasheet"],["pcb-c_5v",1.425,8.575,444.175,453.825,5.5,"datasheet"],["pcb-c_3v3",3.575,8.425,456.125,462.875,5.5,"datasheet"],["pcb-c_dec",10.675,13.725,452.925,460.075,7,"estimated"],["pcb-r_vbat_hi",-9.755,-8.245,414.495,417.505,0.55,"datasheet"],["pcb-r_vbat_lo",-6.755,-5.245,414.495,417.505,0.55,"datasheet"],["pcb-baro",-13.75,4.8,351.86,377.81,7.0,"datasheet"],["pcb-imu",-13.75,4.6,323.81,350.36,7.0,"datasheet"],["pcb-r_scl",-3.755,-2.245,414.495,417.505,0.55,"datasheet"],["pcb-r_sda",-0.755,0.755,414.495,417.505,0.55,"datasheet"],["pcb-sd",-13.75,12.2,294.56,322.31,5.9,"datasheet"],["pcb-pyro_term",-8.775,-0.725,423.0,431.65,9.15,"datasheet"],["pcb-q_pyro",9.775,13.225,461.245,465.155,1.25,"datasheet"],["pcb-r_pyro_g",2.245,3.755,414.495,417.505,0.55,"datasheet"],["pcb-r_pyro_pd",5.245,6.755,414.495,417.505,0.55,"datasheet"],["pcb-r_cont_hi",8.245,9.755,414.495,417.505,0.55,"datasheet"],["pcb-r_cont_lo",-9.755,-8.245,419.495,422.505,0.55,"datasheet"],["pcb-d_pyro",-3.275,0.275,445.475,452.525,10,"assumption"],["pcb-buzzer",-3.6,8.95,379.31,391.86,10.299999999999999,"datasheet"],["pcb-q_buzz",-11.725,-8.275,465.545,469.455,1.25,"datasheet"],["pcb-r_buzz_g",-6.755,-5.245,419.495,422.505,0.55,"datasheet"],["pcb-r_buzz_pd",-3.755,-2.245,419.495,422.505,0.55,"datasheet"],["pcb-d_buzz",-13.275,-10.725,421.115,430.885,8.12,"estimated"],["pcb-led_status",-12.985,-6.515,448.26,454.74,9.85,"datasheet"],["pcb-r_led",-0.755,0.755,419.495,422.505,0.55,"datasheet"],["pcb-cam",10.0775,13.9225,384.395,395.605,10.16,"estimated"],["pcb-q_cam",9.775,13.225,466.245,470.155,1.25,"datasheet"],["pcb-r_cam_pu",2.245,3.755,419.495,422.505,0.55,"datasheet"],["pcb-q_cam_drv",-5.425,-1.975,465.545,469.455,1.1,"datasheet"],["pcb-r_cam_b",5.245,6.755,419.495,422.505,0.55,"datasheet"],["pcb-q_rec",0.865,4.315,465.545,469.455,1.1,"datasheet"],["pcb-r_rec_b",8.245,9.755,419.495,422.505,0.55,"datasheet"],["pcb-uart",-13.9225,-10.0775,384.395,395.605,10.16,"estimated"],["pcb-boost_harness",-7.525,7.525,394.0,402.65,9.15,"datasheet"],["pcb-arm_harness",10.0775,13.9225,397.67,408.33,10.16,"estimated"],["pcb-battery_harness",0.725,8.775,423.0,431.65,9.15,"datasheet"]];
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
// Conservative U3V70x primary-STEP bounds include all disconnected vendor sub-solids.
const boost=rk.part('boost-pololu-u3v70f5',box(15.24,5.4848,40.64,true).translate(0,-7.2424,283.32).color('#386599'));
fasten('boost',sled,boost,[0,-4.5,266]);
// Reserved installation space, not exact wire solids or a mass claim.
// Primary Pololu22AWG wire is1.6mm nominal OD; reserve1.8mm and verify supplied wire.
// The8nativeEdge.Cuts holes are2.4mm diameter; a2.2mm protected-wire envelope passes each.
const wirePorts=[[-5.25,411.5],[-1.75,411.5],[1.75,411.5],[5.25,411.5],[-6.5,440.5],[-3.0,440.5],[3.0,440.5],[6.5,440.5]];
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
// Arm switch: key switch through band + coupler port, flange on the outer skin
const armSwitch = rk.part('arm-switch', radial(4.7, 3, 16.5).union(radial(1.6, 4.2, 21.05)).translate(0, 0, 410).color('#d32f2f'), { density: 1500 });
fasten('arm-switch', switchBand, armSwitch, [21.2, 0, 410]);


return rk.solvedModel({});