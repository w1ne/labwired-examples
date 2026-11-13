// LabWired A1 mini live firmware twin — original parametric geometry.
// Reference: Bambu Lab A1 mini official 180 mm build volume and cantilever layout.
// Not OEM geometry. Belts, rails, motors, cables and service parts are nominal visual references.
// World mm: +X right, +Y rear, +Z up. +print Y moves the bed toward -Y.
const Xmm = param('Xmm', 0, { min: 0, max: 180, unit: 'mm', step: 1, label: 'Toolhead X' });
const Ymm = param('Ymm', 0, { min: 0, max: 180, unit: 'mm', step: 1, label: 'Print Y' });
const Zmm = param('Zmm', 0, { min: 0, max: 180, unit: 'mm', step: 1, label: 'Nozzle height' });
const Edeg = param('Edeg', 0, { min: -3600, max: 3600, unit: 'deg', label: 'Extruder shaft' });
const pcbWidth = param('pcbWidth', 88.5, { min: 60, max: 100, unit: 'mm', label: 'PCB reserve width' });
const pcbDepth = param('pcbDepth', 120, { min: 40, max: 180, unit: 'mm', label: 'PCB reserve depth' });

const A = assembly('a1-mini-reference');
const WHITE='#d4d8db', DARK='#262b30', SILVER='#aeb6bd', BLACK='#12171b';
const GREEN='#33c26f', TUBE='#f4f7f8', CABLE='#25292d', GOLD='#9e8758';
function rr(w:number,d:number,r:number,h:number,x:number,y:number,z:number){return extrudeRoundedRect(w,d,r,h).translate(x,y,z);}
function frame(p:any,n:string,o:number[]){p.connector(n,{type:'frame',origin:{kind:'vec3',value:o}});}
function fixed(name:string,shape:any,parent:any,point:number[],material='abs',overlay=false){
  const p=A.part(name,shape,{material,overlay});
  frame(parent,'fix-'+name,point);frame(p,'mount',point);
  A.mate('fix-'+name,parent.name+'.fix-'+name,name+'.mount','fastened');
  return p;
}
function axis(p:any,n:string,o:number[],v:number[]){p.connector(n,{type:'axis',origin:{kind:'vec3',value:o},axis:v});}

// Two merged rounded pedestal forms reproduce the asymmetric A1 mini base.
let body=rr(210,258,15,34,-45,0,8).union(rr(118,276,14,40,107,4,8));
body=body.subtract(rr(100,220,8,29,107,4,9));
for(let i=0;i<12;i++) body=body.subtract(extrudeRoundedRect(3.4,15,1.7,18,{axis:'x'}).translate(150,-64+i*9,28));
body=body.subtract(extrudeRoundedRect(12,7,1.2,18,{axis:'x'}).translate(150,62,29));
const podShape=rr(76,64,7,14,0,0,0).rotate([1,0,0],55).translate(91,-129,27);
body=body.subtract(rr(77,65,7,30,0,0,-0.1).rotate([1,0,0],55).translate(91,-129,27));
for(const sx of [-1,1])for(const sy of [-1,1]) body=body.union(cylinder(8.3,3.6).subtract(cylinder(9,1.6).translate(0,0,-0.2)).translate(pcbWidth.divide(2).subtract(4).multiply(sx).add(107),pcbDepth.divide(2).subtract(4).multiply(sy).add(1),8.9));
const base=A.part('base',body.color(WHITE),{material:'abs'});
const bottom=fixed('base-bottom',rr(304,252,12,3,8,0,5).color(DARK),base,[100,4,8]);
for(const [i,x,y] of [[0,-126,-104],[1,-126,104],[2,142,-104],[3,142,104]])
  fixed('foot-'+i,rr(20,24,5,5,x,y,0).color(BLACK),bottom,[x,y,5]);

// PCB is an explicit dimensioned reserve, not an imported OEM motherboard.
let pcb=box(pcbWidth,pcbDepth,1.6,true).translate(107,1,18);
for(const sx of [-1,1])for(const sy of [-1,1]) pcb=pcb.subtract(cylinder(4,1.6).translate(pcbWidth.divide(2).subtract(4).multiply(sx).add(107),pcbDepth.divide(2).subtract(4).multiply(sy).add(1),16));
const pcbRef=fixed('controller-pcb-reserve',pcb.color('#176a51'),base,[71.5,-57,17.2]);
fixed('controller-module',box(34,24,7,true).translate(98,0,22.3).color(BLACK),pcbRef,[98,0,18.8]);
for(let i=0;i<4;i++) fixed('driver-module-'+i,box(14,19,5,true).translate(76+i*19,22,21.3).color('#334551'),pcbRef,[76+i*19,22,18.8]);

// Angled 2.4-inch-class display pod with a simple status UI.
const pod=fixed('display-pod',podShape.color(WHITE),base,[91,-114,32]);
const glass=fixed('display-glass',rr(64,48,3,1.3,0,0,14.05).rotate([1,0,0],55).translate(91,-129,27).color(BLACK),pod,[91,-140,28]);
fixed('display-progress',rr(46,2,0.8,0.3,0,-12,15.4).rotate([1,0,0],55).translate(91,-129,27).color(GREEN),glass,[91,-148,24], 'abs',true);
fixed('display-hotend',rr(18,5,1,0.3,-19,0,15.5).rotate([1,0,0],55).translate(91,-129,27).color('#ff8b3d'),glass,[78,-139,29], 'abs',true);
fixed('display-bed',rr(18,5,1,0.3,3,0,15.5).rotate([1,0,0],55).translate(91,-129,27).color('#66b9ff'),glass,[101,-139,29], 'abs',true);
fixed('display-job',rr(41,4,1,0.3,-20,-7,15.5).rotate([1,0,0],55).translate(91,-129,27).color('#dfe7ec'),glass,[91,-144,26], 'abs',true);

// Y rail cradle and two polished shafts.
const cradle=fixed('y-guide',rr(106,242,9,9,-40,1,42).subtract(cylinder(230,5.1).alongAxis([0,1,0]).translate(-69,-114,55)).subtract(cylinder(230,5.1).alongAxis([0,1,0]).translate(-11,-114,55)).color(WHITE),base,[-40,1,42]);
let yRail:any;
for(const x of [-69,-11]){
  const railRef=fixed('y-rail-'+x,cylinder(226,5).alongAxis([0,1,0]).translate(x,-112,55).color(SILVER),cradle,[x,1,50],'mild-steel');
  if(x===-69)yRail=railRef;
}
fixed('y-belt',box(6,229,1.5,true).translate(-40,0,52).color(BLACK),cradle,[-40,0,51.5]);
let yCar=rr(76,49,6,9,-40,70,57).union(rr(160,18,4,4,-40,70,65));
yCar=yCar.subtract(cylinder(52,5.3).alongAxis([0,1,0]).translate(-69,44,55))
  .subtract(cylinder(52,5.3).alongAxis([0,1,0]).translate(-11,44,55));
const bedCar=A.part('bed-carriage',yCar.color(DARK),{material:'aluminum-6061'});
axis(yRail,'slide',[-69,70,55],[0,-1,0]);axis(bedCar,'slide',[-69,70,55],[0,-1,0]);
A.mate('axis-y','y-rail--69.slide','bed-carriage.slide','prismatic',{pose:Ymm,limitsMm:[0,180]});
const heatbed=fixed('heatbed',rr(182,182,4,2.35,-40,70,69).color('#42474b'),bedCar,[-40,70,69],'aluminum-6061');
fixed('pei-build-sheet',rr(180,180,3,0.65,-40,70,71.35).color(GOLD),heatbed,[-40,70,72],'mild-steel');
fixed('plate-handle',rr(36,16,4,1.5,-40,-29,70.35).color(DARK),heatbed,[-40,-16,71.4]);
let plateMarks=rr(174,1.1,0.5,0.18,-40,70,72.02).union(rr(1.1,174,0.5,0.18,-40,70,72.02));
for(const off of [-60,-30,30,60]){
  plateMarks=plateMarks.union(rr(168,0.45,0.2,0.12,-40,70+off,72.04));
  plateMarks=plateMarks.union(rr(0.45,168,0.2,0.12,-40+off,70,72.04));
}
fixed('plate-reference-grid',plateMarks.color('#665a3d'),heatbed,[-40,70,72.05],'abs',true);

// Right-hand vertical column, exposed rail, rear leadscrew and top cap.
let col=rr(48,58,6,308,130,45,48);
col=col.subtract(box(15,9,294).translate(122.5,13,56)).union(rr(22,16,3,10,143,76,50)).subtract(cylinder(12,4.3).translate(144,80,49));
const column=fixed('z-column',col.color(SILVER),base,[130,45,48],'aluminum-6061');
const zRail=fixed('z-rail',box(12,5,292).translate(124,17,58).color('#7d858d'),column,[130,20,60],'mild-steel');
for(let i=0;i<8;i++) fixed('z-rail-bolt-'+i,cylinder(1.5,2.5).alongAxis([0,-1,0]).translate(130,16.7,70+i*37).color(DARK),zRail,[130,16.7,70+i*37],'mild-steel');
fixed('z-leadscrew',threadedRod({spec:'M8',length:282,cosmetic:true}).translate(144,80,60).color(SILVER),column,[144,80,60],'mild-steel');
fixed('column-cap',rr(50,60,6,9,130,45,356).color(DARK),column,[130,45,356]);

// External spool holder silhouette for the standalone A1 mini configuration.
// Its support block seats on the column's right face above the maximum Z-carriage envelope.
let holderShape=box(20,20,16,true).translate(164,60,347)
  .union(box(18,60,16,true).translate(174,90,347))
  .union(cylinder(82,6).alongAxis([1,0,0]).translate(174,110,347))
  .union(cylinder(5,9).alongAxis([1,0,0]).translate(252,110,347));
fixed('spool-holder',holderShape.color(WHITE),column,[154,60,347]);

// Z carriage is a U bracket around the column. Sliding bearing clearance is explicit.
let gantry=rr(70,80,8,58,130,38,99).subtract(rr(48.6,58.6,6,62,130,45,97));
gantry=gantry.union(rr(296,27,4,27,-18,8,112)).subtract(rr(48.6,58.6,6,62,130,45,97)).subtract(box(14,12,62).translate(123,11,97)).subtract(cylinder(64,4.6).translate(144,80,96));
const xGantry=A.part('x-gantry',gantry.color(WHITE),{material:'aluminum-6061'});
axis(column,'slide',[130,17,126],[0,0,1]);axis(xGantry,'slide',[130,17,126],[0,0,1]);
A.mate('axis-z','z-column.slide','x-gantry.slide','prismatic',{pose:Zmm,limitsMm:[0,180]});
let railShape=box(288,4.5,12).translate(-166,-10.1,119.5);
for(let i=0;i<7;i++) railShape=railShape.subtract(cylinder(5,2.4).alongAxis([0,1,0]).translate(-124+i*37,-10.2,125));
const xRail=fixed('x-rail',railShape.color(SILVER),xGantry,[-10,-7,125],'mild-steel');
fixed('x-belt',box(235,2,6).translate(-141,21.7,122).color(BLACK),xGantry,[-10,19,125]);
const xEndCap=fixed('x-end-cap',rr(13,36,4,38,-172.5,8,106).color(DARK),xGantry,[-166,8,125]);
for(let i=0;i<7;i++) fixed('x-rail-bolt-'+i,cylinder(1.3,2.2).alongAxis([0,1,0]).translate(-124+i*37,-10.1,125).color(DARK),xRail,[-124+i*37,-7,125],'mild-steel');

// Purge wiper and waste chute seat on the outer face of the X end cap.
let wiperShape=rr(24,24,4,13,-191,14,100)
  .union(rr(10,15,2,22,-184,10,109))
  .union(rr(14,4,1,5,-186,3,116))
  .union(rr(20,18,3,8,-199,24,92));
fixed('purge-wiper',wiperShape.color(DARK),xEndCap,[-179,14,110]);

// Filament hub seats on the right face of the Z carriage without shared volume.
let hubShape=rr(36,32,5,46,183,22,139)
  .union(cylinder(7,5).alongAxis([0,-1,0]).translate(183,6,164))
  .union(rr(12,4,1,0.6,183,5,149));
fixed('filament-hub',hubShape.color(WHITE),xGantry,[165,22,150]);

// Toolhead is centred at x=-130 at home. All visible details follow axis-x.
let head=rr(53,45,7,73,-130,-13,93);
head=head.subtract(cylinder(47,14.1).alongAxis([0,1,0]).translate(-130,-37,130)).subtract(box(56,45,30).translate(-158,-12.1,110)).subtract(rr(35.2,25.2,3,28.2,-130,14,141.9)).subtract(cylinder(8,5.2).alongAxis([0,-1,0]).translate(-130,6,151));
head=head.union(box(42,3.6,18,true).translate(-130,-12.2,125));
const toolhead=A.part('toolhead',head.color(WHITE),{material:'abs'});
axis(xRail,'slide',[-130,-7,125],[1,0,0]);axis(toolhead,'slide',[-130,-7,125],[1,0,0]);
A.mate('axis-x','x-rail.slide','toolhead.slide','prismatic',{pose:Xmm,limitsMm:[0,180]});
const fan=fixed('toolhead-fan',cylinder(5,13.8).alongAxis([0,1,0]).translate(-130,-34,130).color(DARK),toolhead,[-130,-29,130]);
let fanRotor=cylinder(1.5,4).alongAxis([0,-1,0]).translate(-130,-34,130);
for(let i=0;i<5;i++) fanRotor=fanRotor.union(box(2.8,0.9,9,true).translate(0,0,6.5).rotate([0,1,0],i*72).translate(-130,-34.45,130));
fixed('fan-rotor',fanRotor.color('#d4b570'),fan,[-130,-34.5,130]);
const sock=fixed('hotend-sock',rr(21,20,3,15,-130,-20,78).color(BLACK),toolhead,[-130,-20,92]);
fixed('nozzle',cylinder(6,3).translate(-130,-20,72).color('#bc975a'),sock,[-130,-20,78],'mild-steel');
fixed('cooling-duct-left',rr(19,37,5,10,-150,-20,83).color(DARK),toolhead,[-150,-20,92]);
fixed('cooling-duct-right',rr(19,37,5,10,-110,-20,83).color(DARK),toolhead,[-110,-20,92]);
const entry=fixed('filament-entry',cylinder(18,7.5).translate(-130,-9,166).union(cylinder(4,8.5).translate(-130,-9,184)).color(WHITE),toolhead,[-130,-9,166]);
fixed('filament-collet',cylinder(4,6.5).translate(-130,-9,188).color(BLACK),entry,[-130,-9,188]);
fixed('toolhead-status-led',rr(12,2,0.8,0.5,-130,-36.2,150).color(GREEN),toolhead,[-130,-36,150],'abs',true);
const extruder=fixed('extruder-motor',rr(35,25,3,28,-130,14,142).subtract(cylinder(8,5.2).alongAxis([0,-1,0]).translate(-130,6,151)).color(DARK),toolhead,[-130,12,152],'mild-steel');
const drive=A.part('extruder-shaft',cylinder(5,5).alongAxis([0,-1,0]).translate(-130,5,151).color('#bc975a'),{material:'mild-steel'});
axis(extruder,'shaft',[-130,4,151],[0,1,0]);axis(drive,'shaft',[-130,4,151],[0,1,0]);
A.mate('axis-e','extruder-motor.shaft','extruder-shaft.shaft','revolute',{pose:Edeg,limitsDeg:[-3600,3600]});
A.mechanicalJoint('extruder-drive',{mate:'axis-e',actuator:'extruder-motor',shaft:'extruder-shaft',supports:['extruder-motor'],output:'extruder-shaft'});

// Rear PTFE guide loop. The tube is tangent to the column at one end and then stays
// behind the complete motion envelope. It is a rigid visual proxy, not a flexible-body model.
const tubeProfile=path().circle(0,0,2.2);
const ptfeRail:[number,number,number][]=[[150,76.2,78],[160,92,105],[110,112,205],[30,122,250],[-40,114,230],[-70,105,195]];
fixed('ptfe-guide-loop',tubeProfile.sweep(ptfeRail,{spine:'smooth',frenet:true}).color(TUBE),column,[150,74,78],'abs',true);

// Camera body seats on the front face of the X beam and remains outside toolhead travel.
let cameraShape=rr(18,14,3,13,110,-12.5,138)
  .union(cylinder(3,3.2).alongAxis([0,-1,0]).translate(110,-19.5,145));
fixed('monitoring-camera',cameraShape.color(DARK),xGantry,[110,-5.5,138]);

// Live motion is supplied by LabWired's counted STEP/DIR telemetry.
// This saved CAD revision contains no prerecorded movement. X/Y/Z are authored
// Cartesian translations and E is shaft rotation. The runtime does not claim
// motor torque, belt elasticity, backlash, thermal behavior or deposition.


setRenderEnvironment({preset:'studio',intensity:1.05,rotation:24});
setCameraTarget(10,15,170);
setCameraDistance(520);

// Official published envelope is 347 x 315 x 365 mm including accessories and motion clearance.
// This reference uses nominal visible geometry; no OEM tolerance, load, torque, thermal or deposition claim.
return A.solvedModel({}, {contacts:[
  {parts:['base','base-bottom'],maxVolumeMm3:100,maxThicknessMm:0.1}
]});