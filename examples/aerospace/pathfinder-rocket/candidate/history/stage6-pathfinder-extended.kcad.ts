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

// ---- Launch pad: base plate + 1.5 m 1010 rail (20 x 20 mm) at 180 deg, grounded root
const pad = rk.part('launch-pad-rail', box(300, 300, 10, true).translate(-37, 0, -165)
  .union(box(20, 20, 1510, true).translate(-37, 0, 595)).color('#8a9199'), { material: 'aluminum' });
// ---- Airframe: 42 mm spiral-wound kraft-phenolic tubes, 400 mm booster + 220 mm payload
const lower = rk.part('lower-body-tube', tube(400, R, RI).color('#e9e4da'), { density: 1000 });

// ---- Avionics bay: 250 mm coupler (fits the tube ID), 20 mm switch band, two bulkheads
let coupler = tube(250, 19.8, CRI).translate(0, 0, 230);
coupler = coupler.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));           // arm-switch port
for (const deg of [60,180,300]) coupler=coupler.subtract(radial(4,1,18.5).translate(0,0,410).rotateZ(deg));
const bay = rk.part('avionics-coupler', coupler.color('#d9cdb4'), { density: 1000 });
fasten('coupler', lower, bay, [0, 19.8, 370]);
let band = tube(20, R, RI).translate(0, 0, 400);
band = band.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));
for (const deg of [60, 180, 300]) band = band.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg)); // 3 x 2 mm static ports
const switchBand = rk.part('switch-band', band.color('#1f2a44'), { density: 1000 });
fasten('switch-band', bay, switchBand, [0, 20.2, 410]);
const upper = rk.part('upper-body-tube', tube(220, R, RI).translate(0, 0, 420).color('#e9e4da'), { density: 1000 });
fasten('upper-tube', bay, upper, [0, 19.8, 450]);
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
const envelopes=[["pcb-c_bulk",-12.275,-3.725,455.525,464.075,13,"datasheet"],["pcb-c_5v",1.425,8.575,444.175,453.825,5.5,"datasheet"],["pcb-c_3v3",3.575,8.425,456.125,462.875,5.5,"datasheet"],["pcb-c_dec",10.675,13.725,452.925,460.075,7,"estimated"],["pcb-r_vbat_hi",-9.755,-8.245,414.495,417.505,0.55,"datasheet"],["pcb-r_vbat_lo",-6.755,-5.245,414.495,417.505,0.55,"datasheet"],["pcb-baro",-13.75,4.8,351.86,377.81,7.0,"datasheet"],["pcb-imu",-13.75,4.6,323.81,350.36,7.0,"datasheet"],["pcb-r_scl",-3.755,-2.245,414.495,417.505,0.55,"datasheet"],["pcb-r_sda",-0.755,0.755,414.495,417.505,0.55,"datasheet"],["pcb-sd",-13.75,12.2,294.56,322.31,5.9,"datasheet"],["pcb-pyro_term",-8.775,-0.725,423.0,431.65,9.15,"datasheet"],["pcb-q_pyro",9.775,13.225,461.245,465.155,1.25,"datasheet"],["pcb-r_pyro_g",2.245,3.755,414.495,417.505,0.55,"datasheet"],["pcb-r_pyro_pd",5.245,6.755,414.495,417.505,0.55,"datasheet"],["pcb-r_cont_hi",8.245,9.755,414.495,417.505,0.55,"datasheet"],["pcb-r_cont_lo",-9.755,-8.245,418.995,422.005,0.55,"datasheet"],["pcb-d_pyro",-3.275,0.275,445.475,452.525,10,"assumption"],["pcb-buzzer",-3.6,8.95,379.31,391.86,10.299999999999999,"datasheet"],["pcb-q_buzz",-11.725,-8.275,465.545,469.455,1.25,"datasheet"],["pcb-r_buzz_g",-6.755,-5.245,418.995,422.005,0.55,"datasheet"],["pcb-r_buzz_pd",-3.755,-2.245,418.995,422.005,0.55,"datasheet"],["pcb-d_buzz",-13.275,-10.725,421.115,430.885,8.12,"estimated"],["pcb-led_status",-12.985,-6.515,448.26,454.74,9.85,"datasheet"],["pcb-r_led",-0.755,0.755,418.995,422.005,0.55,"datasheet"],["pcb-cam",10.0775,13.9225,384.395,395.605,10.16,"estimated"],["pcb-q_cam",9.775,13.225,466.245,470.155,1.25,"datasheet"],["pcb-r_cam_pu",2.245,3.755,418.995,422.005,0.55,"datasheet"],["pcb-q_cam_drv",-5.425,-1.975,465.545,469.455,1.1,"datasheet"],["pcb-r_cam_b",5.245,6.755,418.995,422.005,0.55,"datasheet"],["pcb-q_rec",0.865,4.315,465.545,469.455,1.1,"datasheet"],["pcb-r_rec_b",8.245,9.755,418.995,422.005,0.55,"datasheet"],["pcb-uart",-13.9225,-10.0775,384.395,395.605,10.16,"estimated"],["pcb-boost_harness",-7.525,7.525,394.0,402.65,9.15,"datasheet"],["pcb-arm_harness",10.0775,13.9225,397.67,408.33,10.16,"estimated"],["pcb-battery_harness",0.725,8.775,423.0,431.65,9.15,"datasheet"]];
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

// ---- Recovery: Kevlar shock cord on the forward eyebolt, 450 mm nylon chute above it
const cord = rk.part('shock-cord-bundle', cylinder(10, 12).translate(0, 0, 493).color('#f5f5f5'), { density: 400 });
fasten('cord', bhFwd, cord, [0, 0, 493]);
const chute = rk.part('parachute-450mm', cylinder(60, 19.5).translate(0, 0, 503).color('#ffb300'), { density: 300 });
cord.connector('chute-slide', { type: 'axis', origin: { kind: 'vec3', value: [0, 0, 503] }, axis: [0, 0, 1] });
chute.connector('slide', { type: 'axis', origin: { kind: 'vec3', value: [0, 0, 503] }, axis: [0, 0, 1] });
rk.mate('chute-ejection', 'shock-cord-bundle.chute-slide', 'parachute-450mm.slide', 'prismatic', { pose: chuteMm, limitsMm: [0, 300] });

// ---- Nose cone: tangent ogive 160 mm, printed PETG, 1.6 mm wall, 40 mm shoulder
const L = 160, rho = (R * R + L * L) / (2 * R);
let outerPts = [];
for (let i = 0; i <= 24; i++) {
  const x = (L * i) / 24;                      // distance from the tip
  outerPts.push([Math.max(Math.sqrt(rho * rho - (L - x) * (L - x)) + R - rho, 0), 800 - x]);
}
let po = path().moveTo(0, 800);
for (const [r, z] of outerPts.slice(1)) po = po.lineTo(r, z);
po = po.lineTo(RI, 640).lineTo(RI, 600).lineTo(0, 600).close();
let pin = path().moveTo(0, 599).lineTo(RI - 1.6, 599).lineTo(RI - 1.6, 640);
for (const [r, z] of outerPts.slice(1).reverse()) { if (r > 4 && z > 641) pin = pin.lineTo(r - 1.6, z); }
pin = pin.lineTo(0, 785).close();
const nose = rk.part('ogive-nose-cone', po.revolve().subtract(pin.revolve()).color('#f05a28'), { material: 'petg' });
upper.connector('nose-slide', { type: 'axis', origin: { kind: 'vec3', value: [0, 19.6, 620] }, axis: [0, 0, 1] });
nose.connector('slide', { type: 'axis', origin: { kind: 'vec3', value: [0, 19.6, 620] }, axis: [0, 0, 1] });
rk.mate('nose-separation', 'upper-body-tube.nose-slide', 'ogive-nose-cone.slide', 'prismatic', { pose: noseSepMm, limitsMm: [0, 300] });

// ---- Fins: 3 x trapezoid, 3 mm birch ply — root 90, tip 45, span 40, sweep 40
for (let i = 0; i < 3; i++) {
  const fin = path().moveTo(R, 5).lineTo(R, 95).lineTo(R + 40, 55).lineTo(R + 40, 10).close()
    .extrude(3).rotateX(90).translate(0, 1.5, 0).rotateZ(i * 120);
  const f = rk.part('fin-' + (i + 1), fin.color('#1f2a44'), { density: 680 });
  fasten('fin-' + (i + 1), lower, f, polar(R + 0.3, i * 120, 50));
}

// ---- Motor mount: 24 mm tube on two centering rings, screw-on retainer, motor
const rings = [];
for (const [n, z] of [['centering-ring-aft', 8], ['centering-ring-fwd', 100]]) {
  const ring = rk.part(n, tube(4, RI, 13).translate(0, 0, z).color('#b08a5a'), { density: 680 });
  fasten(n, lower, ring, [0, 19.8, z + 2]);
  rings.push(ring);
}
const mmt = rk.part('motor-mount-tube', tube(110, 13, 12.1).color('#c9b48a'), { density: 1000 });
fasten('motor-mount', rings[0], mmt, [0, 13, 10]);
const retainer = rk.part('motor-retainer', tube(8, 15, 12.1).translate(0, 0, -8).color('#3a3f45'), { material: 'aluminum' });
fasten('retainer', mmt, retainer, [0, 12.5, 0]);
// 24 mm F-class motor, 62 g loaded (stand-in solid, density gives the mass)
const motor = rk.part('motor-24mm-F-class', cylinder(95, 12).translate(0, 0, -4).color('#5b4a3a'), { density: 1450 });
fasten('motor', mmt, motor, [0, 12.05, 45]);

// ---- Camera pod at 60 deg (between fins 1 and 2); lens looks aft along the body
const podA = 60, pr = R + 15;
let pod = cylinder(56, 15).translate(0, 0, 290)
  .union(path().moveTo(0, 345).lineTo(15, 345).lineTo(0, 392).close().revolve())
  .subtract(cylinder(55, 13.8).translate(0, 0, 292))
  .subtract(cylinder(2.8, 5).translate(0, 0, 289.6));
const [px, py] = polar(pr, podA, 0);
const podPart = rk.part('camera-pod-fairing', pod.translate(px, py, 0).color('#1f2a44'), { material: 'petg' });
fasten('camera-pod', lower, podPart, polar(R + 0.5, podA, 320));
const cam = rk.part('action-camera-19mm', box(19, 19, 22, true).translate(0, 0, 315)
  .union(cylinder(14.5, 4.5).translate(0, 0, 290.5)).translate(px, py, 0).color('#111111'), { density: 1500 });
fasten('camera', podPart, cam, [px + 9.5, py, 315]);

// ---- Rail buttons (1010 size) at 180 deg, between fins 2 and 3; the aft button rides the rail
const buttons = {};
for (const [n, z] of [['rail-button-aft', 40], ['rail-button-fwd', 330]]) {
  buttons[n] = rk.part(n, radial(6, 4, R).translate(0, 0, z).rotateZ(180).color('#333333'), { material: 'nylon' });
  fasten(n, lower, buttons[n], polar(R + 0.2, 180, z));
}
pad.connector('rail', { type: 'axis', origin: { kind: 'vec3', value: [-27.2, 0, 40] }, axis: [0, 0, 1] });
buttons['rail-button-aft'].connector('slide', { type: 'axis', origin: { kind: 'vec3', value: [-27.2, 0, 40] }, axis: [0, 0, 1] });
rk.mate('launch-rail', 'launch-pad-rail.rail', 'rail-button-aft.slide', 'prismatic', { pose: altMm, limitsMm: [0, 2000] });

return rk.solvedModel({});