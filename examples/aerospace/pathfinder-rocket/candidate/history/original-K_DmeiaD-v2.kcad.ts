// LabWired Pathfinder — 42 mm hobby rocket with electronic apogee deployment
// and a side-mounted action camera. Z is the rocket axis (nose up), mm.
// Original parametric design. Masses come from part materials and densities;
// motor, LiPo, camera and parachute are mass stand-ins, not vendor geometry.
// Rev 2: fin span 55 -> 40 mm. CAD-mass stability 2.55 cal at liftoff, 3.17 cal at burnout
// (Barrowman CP z=213 mm, CG z=320 mm; physics/stability.py). Fin FEA: 30 N tip load, SF 3.3.
setRenderEnvironment({ preset: 'softbox', intensity: 1.2 });
// Flight playback. Altitude comes from physics/flight_sim.py (1-D RK4, ISA, Cd 0.55,
// F-class curve, 450 mm chute, CAD dry mass 288 g). Display only: time x10, altitude 1:200.
// Nose separation and chute ejection start at the firmware's verified deploy time.
const altMm = param('altMm', 0, { min: 0, max: 2000 });
const noseSepMm = param('noseSepMm', 0, { min: 0, max: 300 });
const chuteMm = param('chuteMm', 0, { min: 0, max: 300 });
animationView({
  name: 'flight: boost, coast, apogee deploy, descent (time x10, altitude 1:200)',
  tracks: [
    { param: 'altMm', keys: [
      { atMs: 0, value: 0.0 },
      { atMs: 1, value: 0.0 },
      { atMs: 51, value: 37.5 },
      { atMs: 101, value: 144.8 },
      { atMs: 151, value: 304.7 },
      { atMs: 202, value: 512.5 },
      { atMs: 252, value: 717.8 },
      { atMs: 302, value: 900.3 },
      { atMs: 352, value: 1062.1 },
      { atMs: 403, value: 1207.8 },
      { atMs: 453, value: 1333.1 },
      { atMs: 503, value: 1442.3 },
      { atMs: 553, value: 1536.3 },
      { atMs: 603, value: 1616.0 },
      { atMs: 653, value: 1681.9 },
      { atMs: 703, value: 1734.6 },
      { atMs: 753, value: 1774.4 },
      { atMs: 804, value: 1802.1 },
      { atMs: 854, value: 1816.7 },
      { atMs: 904, value: 1819.0 },
      { atMs: 954, value: 1809.1 },
      { atMs: 1004, value: 1788.9 },
      { atMs: 1054, value: 1775.0 },
      { atMs: 1104, value: 1762.9 },
      { atMs: 1154, value: 1751.0 },
      { atMs: 1554, value: 1656.3 },
      { atMs: 1954, value: 1561.7 },
      { atMs: 2354, value: 1467.2 },
      { atMs: 2754, value: 1372.8 },
      { atMs: 3154, value: 1278.4 },
      { atMs: 3554, value: 1184.1 },
      { atMs: 3954, value: 1090.0 },
      { atMs: 4354, value: 995.9 },
      { atMs: 4754, value: 901.9 },
      { atMs: 5154, value: 807.9 },
      { atMs: 5554, value: 714.1 },
      { atMs: 5954, value: 620.3 },
      { atMs: 6354, value: 526.7 },
      { atMs: 6754, value: 433.1 },
      { atMs: 7154, value: 339.6 },
      { atMs: 7554, value: 246.2 },
      { atMs: 7954, value: 152.9 },
      { atMs: 8354, value: 59.6 },
      { atMs: 8609, value: 0.2 },
      { atMs: 8659, value: 0.0 } ] },
    { param: 'noseSepMm', keys: [ { atMs: 0, value: 0 }, { atMs: 945, value: 0 }, { atMs: 1100, value: 260, ease: 'easeOut' } ] },
    { param: 'chuteMm', keys: [ { atMs: 0, value: 0 }, { atMs: 960, value: 0 }, { atMs: 1160, value: 220, ease: 'easeOut' } ] },
  ],
  fps: 24,
});

const R = 21, RI = 20, CRI = 19.2;                // body OD/ID radius, coupler ID radius
const rk = assembly('LabWired Pathfinder rocket');

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

// ---- Avionics bay: 140 mm coupler (fits the tube ID), 20 mm switch band, two bulkheads
let coupler = tube(140, RI, CRI).translate(0, 0, 340);
coupler = coupler.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));           // arm-switch port
const bay = rk.part('avionics-coupler', coupler.color('#d9cdb4'), { density: 1000 });
fasten('coupler', lower, bay, [0, 19.8, 370]);
let band = tube(20, R, RI).translate(0, 0, 400);
band = band.subtract(radial(4, 3.2, 18.5).translate(0, 0, 410));
for (const deg of [60, 180, 300]) band = band.subtract(radial(4, 1, 18.5).translate(0, 0, 410).rotateZ(deg)); // 3 x 2 mm static ports
const switchBand = rk.part('switch-band', band.color('#1f2a44'), { density: 1000 });
fasten('switch-band', bay, switchBand, [0, 20.2, 410]);
const upper = rk.part('upper-body-tube', tube(220, R, RI).translate(0, 0, 420).color('#e9e4da'), { density: 1000 });
fasten('upper-tube', bay, upper, [0, 19.8, 450]);
const bhAft = rk.part('bulkhead-aft', cylinder(4, CRI).translate(0, 0, 340).union(cylinder(10.1, 3).translate(0, 0, 330)).color('#b08a5a'), { density: 680 });
fasten('bulkhead-aft', bay, bhAft, [0, 19, 342]);
const bhFwd = rk.part('bulkhead-fwd', cylinder(4, CRI).translate(0, 0, 476).union(cylinder(13.1, 3).translate(0, 0, 479.9)).color('#b08a5a'), { density: 680 });
fasten('bulkhead-fwd', bay, bhFwd, [0, 19, 478]);

// Sled spans the bulkheads; PCB on +Y face, 1S LiPo on -Y face
const sled = rk.part('avionics-sled', box(32, 2, 132, true).translate(0, 0, 410).color('#2d2d2d'), { material: 'petg' });
fasten('sled', bhAft, sled, [0, 0, 344]);
const pcb = rk.part('flight-computer-pcb', box(30, 1.6, 90, true).translate(0, 1.8, 410).color('#1a6b3a'), { density: 1850 });
fasten('pcb', sled, pcb, [0, 1.0, 410]);
const comps = [   // name, size [x,y,z], centre — sit on the PCB top face (y = 2.6)
  ['blackpill-stm32f411', [21, 4, 53], [0, 4.6, 426.5], '#14161a'],
  ['bme280-baro', [10, 2.5, 10], [-9, 3.85, 386], '#6b6f75'],
  ['mpu6050-imu', [10, 2.5, 10], [7, 3.85, 388], '#202020'],
  ['microsd-socket', [14, 2, 15], [7, 3.6, 373], '#a0a6ad'],
  ['pyro-terminal', [10, 8, 8], [-9, 6.6, 370], '#2e7d32'],
];
for (const [n, s, c, col] of comps) {
  const comp = rk.part(n, box(s[0], s[1], s[2], true).translate(c[0], c[1], c[2]).color(col), { density: 1800 });
  fasten(n, pcb, comp, c);
}
const lipo = rk.part('lipo-1s-400mah', box(30, 7, 50, true).translate(0, -4.5, 410).color('#3949ab'), { density: 1900 });
fasten('lipo', sled, lipo, [0, -4.5, 410]);
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
