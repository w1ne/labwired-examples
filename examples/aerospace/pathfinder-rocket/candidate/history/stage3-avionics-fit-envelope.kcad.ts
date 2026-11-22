// Pathfinder mechanical prototype candidate, derived from K_DmeiaD revision 2.
// Static geometry only. Historical mass, flight animation and stability claims do not apply.
// PCB identity and source grades are recorded in candidate/fit-envelope.json.
// 1.5-ohm load is a simulation/bench load; this model is not a flight qualification.
const altMm = 0, noseSepMm = 0, chuteMm = 0;
const R = 21, RI = 20, CRI = 19.0;                // body OD/ID radius, coupler ID radius
const rk = assembly('Pathfinder static avionics fit');

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

// ---- 240 mm coupler: 39.6 mm OD, 38 mm ID, 0.2 mm radial fit inside the existing 40 mm tube ID
let coupler = tube(240, 19.8, CRI).translate(0, 0, 240);
coupler = coupler.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));           // arm-switch port
for (const deg of [60, 180, 300]) coupler = coupler.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg));
const bay = rk.part('avionics-coupler', coupler.color('#d9cdb4'), { density: 1000 });
// Coupler is the fixed root of this static electronics-fit subassembly.
let band = tube(20, R, RI).translate(0, 0, 400);
band = band.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));
for (const deg of [60, 180, 300]) band = band.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg)); // 3 x 2 mm static ports
const switchBand = rk.part('switch-band', band.color('#1f2a44'), { density: 1000 });
fasten('switch-band', bay, switchBand, [0, 20.2, 410]);
const bhAft = rk.part('bulkhead-aft', cylinder(4, CRI).translate(0, 0, 240).union(cylinder(10.1, 3).translate(0, 0, 230)).color('#b08a5a'), { density: 680 });
fasten('bulkhead-aft', bay, bhAft, [0, 19, 242]);
const bhFwd = rk.part('bulkhead-fwd', cylinder(4, CRI).translate(0, 0, 476).union(cylinder(13.1, 3).translate(0, 0, 479.9)).color('#b08a5a'), { density: 680 });
fasten('bulkhead-fwd', bay, bhFwd, [0, 19, 478]);

// Open edge-channel carrier. PCB slides axially after a bulkhead is removed.
// 31.2 mm channel width / 1.8 mm height gives the 31 x 1.6 PCB 0.1 mm clearance per side.
// Open center preserves through-hole lead space; trim leads to <=1.5 mm below PCB.
let frame = box(1,4.5,232,true).translate(16.1,-1.75,360)
  .union(box(1,4.5,232,true).translate(-16.1,-1.75,360));
for (const x of [-15.05,15.05]) {
  frame = frame.union(box(1.1,0.4,232,true).translate(x,-1.9,360));
  frame = frame.union(box(1.1,0.4,232,true).translate(x,0.3,360));
}
for (const z of [245.5,474.5]) frame = frame.union(box(33.2,2,3,true).translate(0,-3,z));
// Two reverse-face ribs support the boost module's bare PCB rear face.
for (const z of [428,463]) frame = frame.union(box(33.2,0.5,2,true).translate(0,-4.25,z));
// Battery and boost end stops lie outside their occupied axial spans.
for (const z of [354,406,423,468]) frame = frame.union(box(33.2,2,2,true).translate(0,-5,z));
// Reserve the retained panel switch stem at z=410 without touching the PCB edge.
frame = frame.subtract(radial(4.3,3.3,16.3).translate(0,0,410));
const sled = rk.part('avionics-sled',frame.color('#343940'),{material:'petg'});
fasten('sled',bhAft,sled,[0,-3,244]);
const mcuHoles=[[-9.835,253.275,0.8],[-9.835,255.815,0.8],[-9.835,258.355,0.8],[-9.835,260.895,0.8],[-9.835,263.435,0.8],[-9.835,265.975,0.8],[-9.835,268.515,0.8],[-9.835,271.055,0.8],[-9.835,273.595,0.8],[-9.835,276.135,0.8],[-9.835,278.675,0.8],[-9.835,281.215,0.8],[-9.835,283.755,0.8],[-9.835,286.295,0.8],[-9.835,288.835,0.8],[-9.835,291.375,0.8],[-9.835,293.915,0.8],[-9.835,296.455,0.8],[-9.835,298.995,0.8],[-9.835,301.535,0.8],[5.405,301.535,0.8],[5.405,298.995,0.8],[5.405,296.455,0.8],[5.405,293.915,0.8],[5.405,291.375,0.8],[5.405,288.835,0.8],[5.405,286.295,0.8],[5.405,283.755,0.8],[5.405,281.215,0.8],[5.405,278.675,0.8],[5.405,276.135,0.8],[5.405,273.595,0.8],[5.405,271.055,0.8],[5.405,268.515,0.8],[5.405,265.975,0.8],[5.405,263.435,0.8],[5.405,260.895,0.8],[5.405,258.355,0.8],[5.405,255.815,0.8],[5.405,253.275,0.8],[-6.061051,297.775,0.8],[-3.521051,297.775,0.8],[-0.981051,297.775,0.8],[1.558949,297.775,0.8]];
let substrate=box(31,1.6,221,true).translate(0,-0.8,360);
for (const [x,z,d] of mcuHoles) substrate=substrate.subtract(cylinder(2,d/2).rotateX(-90).translate(x,-1.8,z));
const pcb=rk.part('flight-computer-pcb',substrate.color('#1a6b3a'),{density:1850});
fasten('pcb',sled,pcb,[0,-0.8,360]);
// Actual manufacturer STEP body: registration is derived from all 44 source holes.
const weactSource = 'https://raw.githubusercontent.com/WeActStudio/WeActStudio.MiniSTM32F4x1/6a7f7d434a9d6361f91590d4cdd16b4a70ce7513/Hardware/MiniF4x1Cx_V31_3D.step';
// Conservative primary-STEP bounding volume for low-memory fit checks.
// The original imported-STEP build remains in pathfinder-extended.kcad.ts.
const weactShape=box(52.806999206543,20.778999328613253,5.301439750202199,true).translate(26.4034996032715,10.389499664306626,0.5992801248989005);
// Installation: 40 round 0.5 mm solder pins and two 2.96 mm insulating spacer strips.
let mcuFitVolume=weactShape.rotateZ(-90).rotateX(-90).translate(-12.61650000,4.451439750202199,251.87800000);
const solderPins=[[-9.835,253.275,0.8],[-9.835,255.815,0.8],[-9.835,258.355,0.8],[-9.835,260.895,0.8],[-9.835,263.435,0.8],[-9.835,265.975,0.8],[-9.835,268.515,0.8],[-9.835,271.055,0.8],[-9.835,273.595,0.8],[-9.835,276.135,0.8],[-9.835,278.675,0.8],[-9.835,281.215,0.8],[-9.835,283.755,0.8],[-9.835,286.295,0.8],[-9.835,288.835,0.8],[-9.835,291.375,0.8],[-9.835,293.915,0.8],[-9.835,296.455,0.8],[-9.835,298.995,0.8],[-9.835,301.535,0.8],[5.405,301.535,0.8],[5.405,298.995,0.8],[5.405,296.455,0.8],[5.405,293.915,0.8],[5.405,291.375,0.8],[5.405,288.835,0.8],[5.405,286.295,0.8],[5.405,283.755,0.8],[5.405,281.215,0.8],[5.405,278.675,0.8],[5.405,276.135,0.8],[5.405,273.595,0.8],[5.405,271.055,0.8],[5.405,268.515,0.8],[5.405,265.975,0.8],[5.405,263.435,0.8],[5.405,260.895,0.8],[5.405,258.355,0.8],[5.405,255.815,0.8],[5.405,253.275,0.8]];

for (const [index,x] of [[0,-9.83500000],[1,5.40500000]]) {
  let spacer=box(2.54,2.96,50.8,true).translate(x,1.48,277.40500000);
  for (const [px,pz] of solderPins) if (Math.abs(px-x)<0.01) spacer=spacer.union(cylinder(7.7,0.25).rotateX(-90).translate(px,-3.1,pz));
  mcuFitVolume=mcuFitVolume.union(spacer);
}
const blackpill=rk.part('pcb-mcu',mcuFitVolume.color('#252930'),{density:1800});
fasten('pcb-mcu',pcb,blackpill,[-8.935,0,254.545]);
// Conservative installed envelopes. Exact source grades are retained in fit-envelope.json.
const envelopes = [["pcb-bat",0.02,3.61,454.43,460.57,10,"assumption"],["pcb-c_bulk",-8.95,-0.4,443.16,451.71,13,"datasheet"],["pcb-c_5v",1.1,4.15,443.16,450.31,7,"estimated"],["pcb-c_3v3",5.65,8.7,443.16,450.31,7,"estimated"],["pcb-c_dec",10.2,13.25,443.16,450.31,7,"estimated"],["pcb-r_vbat_hi",1.05,4.1,388.78,401.09,10.76,"estimated"],["pcb-r_vbat_lo",5.2,8.25,402.83,415.14,10.76,"estimated"],["pcb-baro",-13.0,5.28,367.73,387.28,5.37,"estimated"],["pcb-imu",-13.0,3.06,344.86,366.23,4.4,"estimated"],["pcb-r_scl",9.75,12.8,402.83,415.14,10.76,"estimated"],["pcb-r_sda",-13.0,-9.95,416.64,428.95,10.76,"estimated"],["pcb-sd",-13.0,11.5,306.56,343.36,6.5,"estimated"],["pcb-pyro_term",-13.0,-9.155,430.45,441.66,10.16,"estimated"],["pcb-ematch",-8.45,-5.4,416.64,428.95,10.76,"estimated"],["pcb-q_pyro",-0.42,3.03,462.98,466.89,1.25,"datasheet"],["pcb-r_pyro_g",-3.9,-0.85,416.64,428.95,10.76,"estimated"],["pcb-r_pyro_pd",0.65,3.7,416.64,428.95,10.76,"estimated"],["pcb-r_cont_hi",5.2,8.25,416.64,428.95,10.76,"estimated"],["pcb-r_cont_lo",9.75,12.8,416.64,428.95,10.76,"estimated"],["pcb-d_pyro",-13.0,-9.45,454.43,461.48,10,"assumption"],["pcb-buzzer",-13.0,-0.45,388.78,401.33,12.53,"estimated"],["pcb-q_buzz",5.11,9.9,454.43,459.94,9.8,"estimated"],["pcb-r_buzz_g",5.6,8.65,388.78,401.09,10.76,"estimated"],["pcb-r_buzz_pd",10.15,13.2,388.78,401.09,10.76,"estimated"],["pcb-d_buzz",-13.0,-10.45,443.16,452.93,8.12,"estimated"],["pcb-led_status",-7.95,-1.48,454.43,460.91,14.1,"estimated"],["pcb-r_led",-13.0,-9.95,402.83,415.14,10.76,"estimated"],["pcb-cam",-7.655,-3.81,430.45,441.66,10.16,"estimated"],["pcb-q_cam",4.53,7.98,462.98,466.89,1.25,"datasheet"],["pcb-r_cam_pu",-8.45,-5.4,402.83,415.14,10.76,"estimated"],["pcb-q_cam_drv",-13.0,-8.21,462.98,468.49,9.8,"estimated"],["pcb-r_cam_b",-3.9,-0.85,402.83,415.14,10.76,"estimated"],["pcb-q_rec",-6.71,-1.92,462.98,468.49,9.8,"estimated"],["pcb-r_rec_b",0.65,3.7,402.83,415.14,10.76,"estimated"],["pcb-uart",-2.31,1.535,430.45,441.66,10.16,"estimated"],["pcb-boost_harness",3.035,6.88,430.45,441.66,10.16,"estimated"],["pcb-arm_harness",8.38,12.225,430.45,441.11,10.16,"estimated"]];
for (const [name,x0,x1,z0,z1,h,grade] of envelopes) {
  const center=[(x0+x1)/2,h/2,(z0+z1)/2];
  const color=grade==='datasheet'?'#a8a5a0':grade==='assumption'?'#d98f40':'#536576';
  const body=rk.part(name,box(x1-x0,h,z1-z0,true).translate(center[0],center[1],center[2]).color(color),{density:1500});
  fasten(name,pcb,body,[center[0],0,center[2]]);
}
// Original battery envelope retained; no unselected battery is represented as vendor-qualified.
const lipo=rk.part('lipo-1s-400mah',box(30,7,50,true).translate(0,-7.5,380).color('#3949ab'),{density:1900});
fasten('lipo',sled,lipo,[0,-7.5,380]);
// Reverse-face converter uses the manufacturer's module STEP, with directly soldered harness wires.
const pololuSource='https://www.pololu.com/file/0J1561/step-up-voltage-regulator-u3v70x.step';
const boostShape=await lib.fromSTEP(pololuSource);
const boost=rk.part('boost-pololu-u3v70f5',boostShape.rotateZ(90).rotateX(90).translate(7.62,-4.5,425),{density:1800});
fasten('boost',sled,boost,[0,-4.5,445]);
// Arm switch: key switch through band + coupler port, flange on the outer skin
const armSwitch = rk.part('arm-switch', radial(4.7, 3, 16.5).union(radial(1.6, 4.2, 21.05)).translate(0, 0, 410).color('#d32f2f'), { density: 1500 });
fasten('arm-switch', switchBand, armSwitch, [21.2, 0, 410]);

return rk.solvedModel({});
