// Pathfinder mechanical prototype candidate, derived from K_DmeiaD revision 2.
// Static geometry only. Historical mass, flight animation and stability claims do not apply.
// PCB identity and source grades are recorded in candidate/fit-envelope.json.
// 1.5-ohm load is a simulation/bench load; this model is not a flight qualification.
const altMm = 0, noseSepMm = 0, chuteMm = 0;
const R = 21, RI = 20, CRI = 19.0;                // body OD/ID radius, coupler ID radius
const rk = assembly('Pathfinder extended avionics prototype');

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

// ---- 240 mm coupler: 39.6 mm OD, 38 mm ID, 0.2 mm radial fit inside the existing 40 mm tube ID
let coupler = tube(240, 19.8, CRI).translate(0, 0, 240);
coupler = coupler.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));           // arm-switch port
for (const deg of [60, 180, 300]) coupler = coupler.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg));
const bay = rk.part('avionics-coupler', coupler.color('#d9cdb4'), { density: 1000 });
fasten('coupler', lower, bay, [0, 19.8, 370]);
let band = tube(20, R, RI).translate(0, 0, 400);
band = band.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));
for (const deg of [60, 180, 300]) band = band.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg)); // 3 x 2 mm static ports
const switchBand = rk.part('switch-band', band.color('#1f2a44'), { density: 1000 });
fasten('switch-band', bay, switchBand, [0, 20.2, 410]);
const upper = rk.part('upper-body-tube', tube(220, R, RI).translate(0, 0, 420).color('#e9e4da'), { density: 1000 });
fasten('upper-tube', bay, upper, [0, 19.8, 450]);
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
const weactShape = await lib.fromSTEP(weactSource);
// Installation: 40 round 0.5 mm solder pins and two 2.96 mm insulating spacer strips.
const blackpill=rk.part('pcb-mcu',weactShape.rotateZ(-90).rotateX(-90).translate(-12.61650000,4.451439750202199,251.87800000),{density:1800});
const solderPins=[[-9.835,253.275,0.8],[-9.835,255.815,0.8],[-9.835,258.355,0.8],[-9.835,260.895,0.8],[-9.835,263.435,0.8],[-9.835,265.975,0.8],[-9.835,268.515,0.8],[-9.835,271.055,0.8],[-9.835,273.595,0.8],[-9.835,276.135,0.8],[-9.835,278.675,0.8],[-9.835,281.215,0.8],[-9.835,283.755,0.8],[-9.835,286.295,0.8],[-9.835,288.835,0.8],[-9.835,291.375,0.8],[-9.835,293.915,0.8],[-9.835,296.455,0.8],[-9.835,298.995,0.8],[-9.835,301.535,0.8],[5.405,301.535,0.8],[5.405,298.995,0.8],[5.405,296.455,0.8],[5.405,293.915,0.8],[5.405,291.375,0.8],[5.405,288.835,0.8],[5.405,286.295,0.8],[5.405,283.755,0.8],[5.405,281.215,0.8],[5.405,278.675,0.8],[5.405,276.135,0.8],[5.405,273.595,0.8],[5.405,271.055,0.8],[5.405,268.515,0.8],[5.405,265.975,0.8],[5.405,263.435,0.8],[5.405,260.895,0.8],[5.405,258.355,0.8],[5.405,255.815,0.8],[5.405,253.275,0.8]];
const mcuSupports=[];
for (const [index,x] of [[0,-9.83500000],[1,5.40500000]]) {
  let spacer=box(2.54,2.96,50.8,true).translate(x,1.48,277.40500000);
  for (const [px,pz] of solderPins) if (Math.abs(px-x)<0.01) spacer=spacer.union(cylinder(7.7,0.25).rotateX(-90).translate(px,-3.1,pz));
  const support=rk.part('mcu-pin-spacer-'+index,spacer.color('#222222'),{density:1500});
  fasten('mcu-support-'+index,pcb,support,[x+0.9,0,254.54500000]);
  mcuSupports.push(support);
}
fasten('pcb-mcu',mcuSupports[0],blackpill,[-8.93500000,2.96,254.54500000]);
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
