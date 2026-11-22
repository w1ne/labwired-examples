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
// The 31.5 x 1.6 x 235 mm PCB slides in a 31.7 x 1.8 mm channel (0.1 mm lateral per side,0.2 mm above the seated PCB).
// End bridges occupy Z234..237 and473..476,Y-5.75..-3.75. PCB occupiesZ237.5..472.5.
// The lowered end bridges leave0.65mm to the maximum trimmed solder-tail depth during axial insertion.
// Trim all through-hole solder tails to <=1.5 mm below the carrier PCB.
let frame=box(1,4.5,242,true).translate(16.35,-1.75,355)
 .union(box(1,4.5,242,true).translate(-16.35,-1.75,355));
for(const x of [-15.3,15.3]){
 frame=frame.union(box(1.1,.4,242,true).translate(x,-1.8,355));
 frame=frame.union(box(1.1,.4,242,true).translate(x,.4,355));
}
for(const z of [235.5,474.5])frame=frame.union(box(33.7,2,3,true).translate(0,-4.75,z));
// Reverse-face converter supports and end stops; bare-board rear surface is at Y=-4.5.
for(const z of [433,468])frame=frame.union(box(33.7,.55,2,true).translate(0,-4.225,z));
for(const z of [429,472])frame=frame.union(box(33.7,2.05,2,true).translate(0,-4.975,z));
// Battery tray: maximum pack17x9.5x66 plus1 mm per axis installation reserve =18x10.5x68.
// Clear opening18.2mm; 0.8mm walls/back,2mm end stops. This is a fit prototype, not vibration acceptance.
frame=frame.union(box(19.8,.8,72,true).translate(0,-15.4,371));
for(const x of [-9.5,9.5])frame=frame.union(box(.8,11.85,72,true).translate(x,-9.875,371));
for(const z of [336,406])frame=frame.union(box(33.7,2.05,2,true).translate(0,-4.975,z))
 .union(box(19.8,11.85,2,true).translate(0,-9.875,z));
// Cable slot in the forward tray stop preserves a 4x4 mm bridge volume.
frame=frame.subtract(box(6,5,2.4,true).translate(0,-9.75,406));
// Trim only outer lower tray corners; the battery reservation is unchanged.
frame=frame.intersect(cylinder(242,18.4).translate(0,0,234));
frame=frame.subtract(radial(4.3,3.3,16.3).translate(0,0,410));
const sled=rk.part('avionics-sled',frame.color('#343940'),{material:'petg'});
fasten('sled',bhAft,sled,[0,-4.75,234]);
const drillHoles=[[-10.585,241.275,0.8],[-10.585,243.815,0.8],[-10.585,246.355,0.8],[-10.585,248.895,0.8],[-10.585,251.435,0.8],[-10.585,253.975,0.8],[-10.585,256.515,0.8],[-10.585,259.055,0.8],[-10.585,261.595,0.8],[-10.585,264.135,0.8],[-10.585,266.675,0.8],[-10.585,269.215,0.8],[-10.585,271.755,0.8],[-10.585,274.295,0.8],[-10.585,276.835,0.8],[-10.585,279.375,0.8],[-10.585,281.915,0.8],[-10.585,284.455,0.8],[-10.585,286.995,0.8],[-10.585,289.535,0.8],[4.655,289.535,0.8],[4.655,286.995,0.8],[4.655,284.455,0.8],[4.655,281.915,0.8],[4.655,279.375,0.8],[4.655,276.835,0.8],[4.655,274.295,0.8],[4.655,271.755,0.8],[4.655,269.215,0.8],[4.655,266.675,0.8],[4.655,264.135,0.8],[4.655,261.595,0.8],[4.655,259.055,0.8],[4.655,256.515,0.8],[4.655,253.975,0.8],[4.655,251.435,0.8],[4.655,248.895,0.8],[4.655,246.355,0.8],[4.655,243.815,0.8],[4.655,241.275,0.8],[-6.811051,285.775,0.8],[-4.271051,285.775,0.8],[-1.731051,285.775,0.8],[0.808949,285.775,0.8],[-10.225,452.715,0.8],[-6.725,452.715,0.8],[-2.175,454.515,0.8],[-2.175,449.515,0.8],[11.975,390.545,0.8],[11.975,380.385,0.8],[10.525,407.095,0.8],[10.525,396.935,0.8],[-10.825,357.215,1],[-10.825,359.755,1],[-10.825,362.295,1],[-10.825,364.835,1],[-10.825,367.375,1],[-10.825,369.915,1],[-10.825,372.455,1],[-10.925,330.735,1],[-10.925,333.275,1],[-10.925,335.815,1],[-10.925,338.355,1],[-10.925,340.895,1],[-10.925,343.435,1],[1.775,343.435,1],[1.775,340.895,1],[1.775,338.355,1],[1.775,335.815,1],[1.775,333.275,1],[1.775,330.735,1],[-12.225,420.905,0.8],[-12.225,410.745,0.8],[-7.675,420.905,0.8],[-7.675,410.745,0.8],[-10.935,319.495,1],[-8.395,319.495,1],[-5.855,319.495,1],[-3.315,319.495,1],[-0.775,319.495,1],[1.765,319.495,1],[4.305,319.495,1],[6.845,319.495,1],[9.385,319.495,1],[-2.825,440.915,1.2],[0.675,440.915,1.2],[-3.125,420.905,0.8],[-3.125,410.745,0.8],[1.425,420.905,0.8],[1.425,410.745,0.8],[5.975,420.905,0.8],[5.975,410.745,0.8],[10.525,420.905,0.8],[10.525,410.745,0.8],[-1.125,385.585,1],[6.475,385.585,1],[-3.025,462.515,0.75],[-3.025,461.245,0.75],[-3.025,459.975,0.75],[-12.225,434.715,0.8],[-12.225,424.555,0.8],[-12.225,407.095,0.8],[-12.225,396.935,0.8],[8.11,432.175,0.8],[8.11,424.555,0.8],[-10.515,463.005,0.9],[-10.515,460.465,0.9],[-7.675,407.095,0.8],[-7.675,396.935,0.8],[-7.15,425.275,1],[-7.15,427.815,1],[-7.15,430.355,1],[-7.15,432.895,1],[-3.125,407.095,0.8],[-3.125,396.935,0.8],[3.265,462.515,0.75],[3.265,461.245,0.75],[3.265,459.975,0.75],[1.425,407.095,0.8],[1.425,396.935,0.8],[9.555,462.515,0.75],[9.555,461.245,0.75],[9.555,459.975,0.75],[5.975,407.095,0.8],[5.975,396.935,0.8],[-1.805,425.275,1],[-1.805,427.815,1],[-1.805,430.355,1],[-1.805,432.895,1],[-10.125,392.085,1.2],[-10.125,388.585,1.2],[-10.125,385.085,1.2],[-10.125,381.585,1.2],[3.54,427.54,1],[3.54,430.08,1],[6.725,440.915,1.2],[10.225,440.915,1.2]];
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
const blackpill=rk.part('pcb-mcu',mcuVolume.color('#316a3b'),{density:1800});
fasten('pcb-mcu',pcb,blackpill,[-9.68500000,0,242.54500000]);
const envelopes=[["pcb-c_bulk",-12.75,-4.2,448.44,456.99,13,"datasheet"],["pcb-c_5v",-13.75,-6.6,437.29,446.94,5.5,"datasheet"],["pcb-c_3v3",5.9,10.75,448.44,455.19,5.5,"datasheet"],["pcb-c_dec",-3.7,-0.65,448.44,455.59,7,"estimated"],["pcb-r_vbat_hi",10.45,13.5,379.31,391.62,10.76,"estimated"],["pcb-r_vbat_lo",9.0,12.05,395.86,408.17,10.76,"estimated"],["pcb-baro",-13.75,4.8,351.86,377.81,7.0,"datasheet"],["pcb-imu",-13.75,4.6,323.81,350.36,7.0,"datasheet"],["pcb-r_scl",-13.75,-10.7,409.67,421.98,10.76,"estimated"],["pcb-r_sda",-9.2,-6.15,409.67,421.98,10.76,"estimated"],["pcb-sd",-13.75,12.2,294.56,322.31,5.9,"datasheet"],["pcb-pyro_term",-5.1,2.95,437.29,445.94,9.15,"datasheet"],["pcb-q_pyro",-13.75,-10.3,466.47,470.38,1.25,"datasheet"],["pcb-r_pyro_g",-4.65,-1.6,409.67,421.98,10.76,"estimated"],["pcb-r_pyro_pd",-0.1,2.95,409.67,421.98,10.76,"estimated"],["pcb-r_cont_hi",4.45,7.5,409.67,421.98,10.76,"estimated"],["pcb-r_cont_lo",9.0,12.05,409.67,421.98,10.76,"estimated"],["pcb-d_pyro",0.85,4.4,448.44,455.49,10,"assumption"],["pcb-buzzer",-3.6,8.95,379.31,391.86,10.299999999999999,"datasheet"],["pcb-q_buzz",-5.78,-0.99,458.49,464.0,9.8,"estimated"],["pcb-r_buzz_g",-13.75,-10.7,423.48,435.79,10.76,"estimated"],["pcb-r_buzz_pd",-13.75,-10.7,395.86,408.17,10.76,"estimated"],["pcb-d_buzz",6.835,9.385,423.48,433.25,8.12,"estimated"],["pcb-led_status",-13.75,-7.28,458.49,464.97,9.85,"datasheet"],["pcb-r_led",-9.2,-6.15,395.86,408.17,10.76,"estimated"],["pcb-cam",-9.2,-5.355,423.48,434.69,10.16,"estimated"],["pcb-q_cam",-8.8,-5.35,466.47,470.38,1.25,"datasheet"],["pcb-r_cam_pu",-4.65,-1.6,395.86,408.17,10.76,"estimated"],["pcb-q_cam_drv",0.51,5.3,458.49,464.0,9.8,"estimated"],["pcb-r_cam_b",-0.1,2.95,395.86,408.17,10.76,"estimated"],["pcb-q_rec",6.8,11.59,458.49,464.0,9.8,"estimated"],["pcb-r_rec_b",4.45,7.5,395.86,408.17,10.76,"estimated"],["pcb-uart",-3.855,-0.01,423.48,434.69,10.16,"estimated"],["pcb-boost_harness",-13.75,-5.1,379.31,394.36,9.15,"datasheet"],["pcb-arm_harness",1.49,5.335,423.48,434.14,10.16,"estimated"],["pcb-battery_harness",4.45,12.5,437.29,445.94,9.15,"datasheet"]];
for(const [name,x0,x1,z0,z1,h,grade]of envelopes){
 const center=[(x0+x1)/2,h/2,(z0+z1)/2];
 const body=rk.part(name,box(x1-x0,h,z1-z0,true).translate(center[0],center[1],center[2])
 .color(grade==='datasheet'?'#a8a5a0':grade==='assumption'?'#d98f40':'#536576'),{density:1500});
 fasten(name,pcb,body,[center[0],0,center[2]]);
}
// Battery body below is an installation volume, not an exact vendor mesh.
// Nominal61x15x7.5 and published positive tolerances5/2/2 => max66x17x9.5 mm.
const lipo=rk.part('battery-tattu-450mah-envelope',box(18,10.5,68,true).translate(0,-9.75,371).color('#3949ab'),{density:1900});
fasten('battery',sled,lipo,[0,-15,371]);
// Connector and cable service reservation:20x10x7mm, separate from the pack body.
// BT2.0 rating9A continuous/15A burst does not qualify the remaining cable/copper path.
const batteryCable=rk.part('battery-pigtail-service-envelope',box(10,7,20,true).translate(0,-8,418).union(box(4,4,3,true).translate(0,-9.75,406.5)).color('#6b78ca'),{density:1000});
fasten('battery-cable',lipo,batteryCable,[0,-9.75,405]);
// Conservative U3V70x primary-STEP bounds include all disconnected vendor sub-solids.
const boost=rk.part('boost-pololu-u3v70f5',box(15.24,5.4848,40.64,true).translate(0,-7.2424,450.32).color('#386599'),{density:1800});
fasten('boost',sled,boost,[0,-4.5,433]);
// Arm switch: key switch through band + coupler port, flange on the outer skin
const armSwitch = rk.part('arm-switch', radial(4.7, 3, 16.5).union(radial(1.6, 4.2, 21.05)).translate(0, 0, 410).color('#d32f2f'), { density: 1500 });
fasten('arm-switch', switchBand, armSwitch, [21.2, 0, 410]);


return rk.solvedModel({});
