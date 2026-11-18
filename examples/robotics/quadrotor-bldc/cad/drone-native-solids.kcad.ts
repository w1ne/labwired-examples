// LabWired x KernelCAD: OpenFrame-5F mechanical integration model, mm.
// Frame: unmodified OpenDrone rev2.2 STEP, pinned by commit and SHA-256 in
// mechanical-evidence.json. OpenFrame hardware is CERN-OHL-S-2.0.
// This is an assembly/clearance model, not a flight or strength simulation.
// The motor bodies, propeller blade profiles and soft mounts are ENVELOPES:
// they are not vendor manufacturing geometry. Props retain the
// published 129.7 mm sweep diameter, three blades, 6 mm hub and 5 mm bore.
meta({name:'labwired-quad-openframe-5f',
  title:'LabWired quadrotor — populated ESC and repaired FC',
  description:'Pinned 226 mm OpenFrame-5F frame, four independently posed rotor joints, all 378 native ESC and repaired FC STEP solids as individually fixed assembly parts, plus nominal tri-blade envelopes. Native source datums are corrected; exact full-assembly interference review remains required.'});

const rotor1 = param('rotor1Angle',0,{min:-2160,max:2160,label:'M1 rear-right angle (deg)'});
const rotor2 = param('rotor2Angle',0,{min:-2160,max:2160,label:'M2 front-right angle (deg)'});
const rotor3 = param('rotor3Angle',0,{min:-2160,max:2160,label:'M3 rear-left angle (deg)'});
const rotor4 = param('rotor4Angle',0,{min:-2160,max:2160,label:'M4 front-left angle (deg)'});

// Onshape part exports already share the assembly frame. +Z is up, -Y is
// forward (camera). Actual motor centres are NOT a square-X arrangement.
const motorX = 89;
const motorY = 69.534420756;
const propRadius = 64.85;
const stackY = -12.75;
const armFile = 'https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Arm.step';
const standoffFile = 'https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Standoff-M3-F-F-20-OD5.step';
const origin=(x:number,y:number,z:number)=>({kind:'vec3' as const,value:[x,y,z] as [number,number,number]});
const rig=assembly('labwired-quad-bldc');

const baseShape = await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Base-Bot.step");
const base = rig.part('frame-bottom',baseShape.finish('paint-matte',{color:'#24282c'}));
const partRefs:any = {'frame-bottom':base};
function attach(name:string,shape:any,point:[number,number,number],finish='paint-matte',color='#24282c',parentName='frame-bottom'){
  const parent=partRefs[parentName];
  const p=rig.part(name,shape.finish(finish,{color}));
  parent.connector(name,{type:'frame',origin:origin(...point)});
  p.connector('seat',{type:'frame',origin:origin(...point)});
  rig.mate(name+'-mount',parentName+'.'+name,name+'.seat','fastened');
  partRefs[name]=p;
  return p;
}
attach('frame-cross',await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Cross.step"),[0,0,0]);
attach('frame-middle',await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Base-Top.step"),[0,0,6],'paint-matte','#24282c','frame-cross');
attach('camera-side-left',await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Standoff-L.step"),[13.75,-58,0],'anodized','#d6a528');
attach('camera-side-right',await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Standoff-R.step"),[-13.75,-58,0],'anodized','#d6a528');

// A fresh imported handle for each instance avoids shared-handle transforms.
attach('arm-rear-right',await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Arm.step"),[23,17.96956941,0]);
attach('arm-front-right',(await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Arm.step")).rotateX(180).translate(0,0,6),[23,-17.96956941,0]);
attach('arm-rear-left',(await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Arm.step")).rotateY(180).translate(0,0,6),[-23,17.96956941,0]);
attach('arm-front-left',(await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Arm.step")).rotateZ(180),[-23,-17.96956941,0]);
for(const [name,dx,dy,x,y] of [
  ['rear-left',0,0,-10.25,69.5],['rear-right',20.5,0,10.25,69.5],
  ['middle-left',-2.5,-45.5,-12.75,24],['middle-right',23,-45.5,12.75,24]
] as [string,number,number,number,number][]){
  attach('standoff-'+name,(await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Standoff-M3-F-F-20-OD5.step")).translate(dx,dy,0),[x,y,9],'anodized-black','#24282c','frame-middle');
}

attach('frame-top',await lib.fromSTEP("https://raw.githubusercontent.com/OpenDrone-hw/OpenFrame-5F/71aacb91c09e2970edd459390a4b79e5c61dfd39/releases/rev2.2/step/Top.step"),[-10.25,69.5,29],'paint-matte','#24282c','standoff-rear-left');

// Stack support rings are nominal soft-mount ENVELOPES. Their heights are
// assembly assumptions, not measured compressed grommet dimensions.
// Six-millimetre OD rings clear all imported native components. The prior
// 7 mm OD upper ring intersected a component by 0.0863 mm3. Native STEP
// verification receipts preserve the failure and eight-ring clearance check.
for(const [index,x,y] of [[1,-15.25,-28],[2,15.25,-28],[3,-15.25,2.5],[4,15.25,2.5]]){
  const ring=cylinder(5.4,3).holes('top',{positions:[{u:0,v:0}],diameter:4,depth:'through'}).translate(x,y,9);
  attach('esc-grommet-'+index+'-ENVELOPE',ring,[x,y,9],'rubber','#363a3f','frame-middle');
}

// Board geometry comes from the exact populated native KiCad STEP; solid 213 is
// the PCB substrate. Holes measured at 30.5 mm pitch, 4 mm diameter.
// Candidate stack raised by 2 mm: substrate bottom z14.4, native components
// descend to z11.32, nominally 2.32 mm above the middle frame top z9.
// This envelope separation is not a qualified clearance or assembly proof.
const escStep = "https://raw.githubusercontent.com/w1ne/labwired-examples/100aec12c272423e484b20db36caa796d21adea4/examples/robotics/quadrotor-bldc/hardware/esc-4in1/fabrication-review/esc-board-populated.step";
const escShape = await lib.fromSTEP(escStep,{solid:213});
attach('esc-board',escShape.translate(-75.63257,34.6,14.4),[-15.25,-28,14.4],'paint-matte','#14735b','esc-grommet-1-ENVELOPE');
for(const [index,x,y] of [[1,-15.25,-28],[2,15.25,-28],[3,-15.25,2.5],[4,15.25,2.5]]){
  const ring=cylinder(6.07,3).holes('top',{positions:[{u:0,v:0}],diameter:4,depth:'through'}).translate(x,y,15.93);
  attach('fc-grommet-'+index+'-ENVELOPE',ring,[x,y,15.93],'rubber','#363a3f','esc-board');
}
// Every component solid is retained at its native export pose. The fixed
// relationships express the populated PCB assembly, not a solder strength claim.
const escNativeCenters:[number,number,number,number][] = [[0,79.5200005,-48.9300003,2.45],[1,81.420002,-40.9300003,2.45],[2,69.7899971,-48.9300003,2.45],[3,75.9949989,-62.5750008,2.45],[4,71.6899986,-44.9300003,2.45],[5,79.5200005,-36.9300003,2.45],[6,65.9750023,-44.9250011,2.45],[7,66.8650017,-32.2799997,2.195],[8,83.2999992,-52.9250011,2.45],[9,67.875,-40.9250011,2.45],[10,61.1550026,-50.9500008,2.195],[11,71.6899986,-56.9300003,2.45],[12,69.7899971,-56.9300003,2.45],[13,67.875,-52.8999996,2.45],[14,90.0600014,-43.6300011,2.195],[15,84.454998,-32.2249994,2.195],[16,81.420002,-52.9050007,2.45],[17,61.2400017,-56.7800007,2.195],[18,61.2700005,-43.7250004,2.195],[19,81.420002,-44.9300003,2.45],[20,85.2000008,-56.9499989,2.45],[21,81.420002,-36.9300003,2.45],[22,65.9750023,-40.9250011,2.45],[23,67.875,-56.9250011,2.45],[24,67.875,-44.9250011,2.45],[25,67.875,-48.9250011,2.45],[26,71.6899986,-52.9050007,2.45],[27,79.5200005,-56.9300003,2.45],[28,90.0399971,-37.8500004,2.195],[29,65.9750023,-36.9250011,2.45],[30,83.2999992,-44.9499989,2.45],[31,83.2999992,-40.9499989,2.45],[32,71.4700012,-62.8699989,1.95],[33,61.2800026,-37.8050003,2.195],[34,81.420002,-56.9300003,2.45],[35,71.6899986,-48.9300003,2.45],[36,85.2000008,-36.9499989,2.45],[37,65.9750023,-56.9250011,2.45],[38,83.2999992,-48.9499989,2.45],[39,85.2000008,-40.9499989,2.45],[40,83.2999992,-36.9499989,2.45],[41,78.1199989,-62.5699997,2.45],[42,79.5200005,-40.9300003,2.45],[43,69.7899971,-52.9050007,2.45],[44,81.420002,-48.9300003,2.45],[45,80.170002,-62.5650005,2.45],[46,85.2000008,-48.9499989,2.45],[47,85.2000008,-52.9250011,2.45],[48,83.2999992,-56.9499989,2.45],[49,69.7899971,-40.9300003,2.45],[50,85.2000008,-44.9499989,2.45],[51,71.6899986,-40.9300003,2.45],[52,67.6199989,-62.8774986,1.95],[53,65.9750023,-48.9250011,2.45],[54,79.5200005,-44.9300003,2.45],[55,69.7899971,-36.9300003,2.45],[56,71.6899986,-36.9300003,2.45],[57,79.5200005,-52.9050007,2.45],[58,69.7899971,-44.9300003,2.45],[59,82.295002,-62.5600014,2.45],[60,90.0499992,-56.6749992,2.195],[61,65.9750023,-52.8999996,2.45],[62,67.875,-36.9250011,2.45],[63,90.0699997,-50.9699993,2.195],[64,82.4500008,-53.4300003,-0.235],[65,84.2799377,-49.8300018,-0.67],[66,76.4599342,-48.6599369,-0.235],[67,78.5099983,-42.4000645,-0.235],[68,76.3699989,-57.4571629,-0.52],[69,76.5200005,-39.6099987,-0.235],[70,74.7400017,-43.6000652,-0.27],[71,72.0100021,-54.0698605,-0.27],[72,81.0900002,-36.4799995,-0.27],[73,67.3799362,-46.9497986,-0.37],[74,67.2100029,-53.5799999,-0.27],[75,82.510067,-44.380064,-0.235],[76,74.8500023,-49.1798611,-0.235],[77,83.9000015,-52.6300011,-0.37],[78,76.4900017,-41.3500004,-0.235],[79,67.3099365,-37.2900009,-0.37],[80,76.5099983,-40.1900005,-0.235],[81,81.0299377,-45.5299358,-0.27],[82,71.3400002,-44.4000645,-0.27],[83,87.3400612,-41.0300636,-0.235],[84,78.4499359,-51.4499989,-0.235],[85,74.8100014,-52.9899998,-0.27],[86,72.5600014,-44.420063,-0.27],[87,87.3400612,-41.6200638,-0.235],[88,76.4699364,-47.4899349,-0.27],[89,71.0300026,-48.1197968,-0.27],[90,84.1599998,-53.4400005,-0.235],[91,68.7599373,-36.4899998,-0.235],[92,85.6600647,-43.5800629,-0.37],[93,70.25,-54.0498619,-0.27],[94,87.0400009,-52.3199997,-0.235],[95,66.8650017,-32.2799997,-0.665],[96,65.37994,-36.460001,-0.235],[97,91.8800011,-37.8500004,-0.665],[98,79.1599998,-55.9871616,-0.595],[99,82.2700653,-43.5800629,-0.37],[100,69.0699387,-46.9497986,-0.37],[101,65.6799393,-46.9497986,-0.37],[102,69.0800018,-58.0400009,-0.27],[103,80.4499359,-45.5199356,-0.27],[104,76.5300026,-36.9899998,-0.27],[105,80.9399986,-57.2671623,-0.27],[106,74.7400017,-42.4300632,-0.27],[107,71.6299973,-50.8098717,-0.505],[108,63.9299355,-40.4399986,-0.235],[109,66.1599388,-42.789999,-0.27],[110,74.829998,-50.3398609,-0.235],[111,63.9299355,-39.8400002,-0.235],[112,71.4099998,-54.0598602,-0.27],[113,78.6499367,-45.4999352,-0.27],[114,76.3350029,-55.1471615,-0.52],[115,74.7700005,-40.1000652,-0.27],[116,74.8100014,-53.5799999,-0.27],[117,76.3500023,-56.3071613,-0.52],[118,72.829998,-48.129797,-0.235],[119,68.829937,-46.1497974,-0.235],[120,85.1100655,-38.0800648,-0.27],[121,84.3399963,-40.7800636,-0.67],[122,63.9299355,-39.25,-0.235],[123,70.7599983,-44.4000645,-0.27],[124,80.3100014,-42.4100628,-0.27],[125,76.4299355,-50.3999348,-0.235],[126,65.4499359,-46.1197968,-0.235],[127,67.0,-49.7497978,-0.67],[128,78.7099991,-36.4500008,-0.27],[129,79.1178932,-61.7113228,-0.665],[130,85.4650002,-60.1000004,-0.665],[131,73.1500015,-57.3724995,-0.27],[132,76.5,-40.7699986,-0.27],[133,87.3400612,-40.4300652,-0.235],[134,72.6300011,-54.0798607,-0.27],[135,59.4249992,-37.7749996,-0.665],[136,80.9199982,-54.6271629,-0.235],[137,64.5900002,-52.8299999,-0.235],[138,74.8400002,-49.759861,-0.27],[139,87.2800026,-49.4800014,-0.235],[140,70.1800003,-44.3900642,-0.27],[141,79.8699341,-45.5199356,-0.27],[142,63.9999352,-48.9097958,-0.235],[143,71.329998,-57.1199989,-0.595],[144,66.9300003,-40.0900002,-0.67],[145,91.8600006,-50.9699993,-0.665],[146,72.1378937,-61.6988201,-0.665],[147,73.2200012,-54.0798607,-0.27],[148,75.6300011,-54.2600002,-0.235],[149,79.7099991,-39.7199898,-0.505],[150,76.5300026,-37.5799999,-0.27],[151,80.5100021,-36.4699993,-0.27],[152,65.8150005,-60.1350002,-0.665],[153,91.8800011,-43.6324997,-0.665],[154,79.2699356,-45.5099354,-0.27],[155,76.5300026,-38.4400005,-0.27],[156,68.999939,-37.2900009,-0.37],[157,59.4549999,-56.8099995,-0.665],[158,66.2299385,-52.4497967,-0.27],[159,74.75,-41.2600651,-0.235],[160,84.4500008,-32.2249994,-0.665],[161,74.8199997,-50.9198608,-0.235],[162,59.4549999,-50.9799995,-0.665],[163,69.3100014,-55.2900009,-0.27],[164,75.0999985,-34.5799999,-0.27],[165,75.5699997,-30.4499998,-1.6],[166,76.4799995,-46.6499996,-0.27],[167,74.8100014,-52.0898609,-0.27],[168,74.7400017,-43.0100651,-0.27],[169,76.4599342,-48.0799351,-0.27],[170,79.3199997,-36.7099991,-0.27],[171,78.1199989,-36.4500008,-0.27],[172,91.829998,-56.6800003,-0.665],[173,65.1299973,-55.4099998,-0.37],[174,70.8300018,-55.5600014,-0.37],[175,74.7800026,-39.5200653,-0.235],[176,76.4499359,-49.2399349,-0.235],[177,71.9399986,-44.4100647,-0.27],[178,84.2200661,-44.3900642,-0.235],[179,85.0499992,-47.1299992,-0.27],[180,67.1199379,-46.1397972,-0.235],[181,78.0599365,-45.4999352,-0.27],[182,85.8900642,-44.4100628,-0.235],[183,76.5200005,-39.0300007,-0.27],[184,65.6099396,-37.2900009,-0.37],[185,67.5,-54.960001,-0.53],[186,73.1500015,-44.420063,-0.27],[187,71.5599976,-41.1500778,-0.505],[188,74.7599983,-40.6800632,-0.235],[189,64.5900002,-52.2300014,-0.235],[190,65.1100006,-54.4700012,-0.37],[191,67.0499382,-36.4800014,-0.235],[192,74.75,-41.8400631,-0.27],[193,87.6300011,-52.3199997,-0.235],[194,79.9099998,-36.7199993,-0.27],[195,76.4399376,-49.8199368,-0.27],[196,72.6299973,-55.5499992,-0.37],[197,82.2099991,-52.6300011,-0.37],[198,72.7599983,-38.4700012,-0.235],[199,85.5999985,-52.6300011,-0.37],[200,76.4799995,-46.0599995,-0.27],[201,69.4199982,-56.75,-0.27],[202,83.9600677,-43.5800629,-0.37],[203,80.2499352,-51.4599991,-0.27],[204,72.3500023,-58.5500011,-0.27],[205,77.0399971,-54.2474995,-0.27],[206,59.3950005,-43.7449989,-0.665],[207,70.9600029,-38.460001,-0.27],[208,70.8300018,-54.0598602,-0.27],[209,85.829998,-53.460001,-0.235],[210,79.6499329,-48.7699242,-0.505],[211,74.8199997,-51.4998608,-0.27],[212,70.6699982,-58.5800018,-0.37]];
for(const [index,x,y,z] of escNativeCenters){
  const name="esc-native-solid-"+String(index).padStart(3,"0");
  attach(name,(await lib.fromSTEP(escStep,{solid:index})).translate(-75.63257,34.6,14.4),
    [x+(-75.63257),y+(34.6),z+(14.4)],"paint-matte","#363b40","esc-board");
}

// Repaired native OpenFC-Lite board, immutable PCB SHA3216b761288ee06f.
// Declared nominal thickness 1.0 mm. KiCad exports the substrate z0..0.9378;
// outer copper/mask and package stand-offs retain the source export convention.
// Four open 4 mm mounting cutouts on 30.5 mm centres, real scalloped outline.
// Export origin is mounting-pattern centre (153.0912,87.1597) in native PCB mm.
const fcStep = "https://raw.githubusercontent.com/w1ne/labwired-examples/100aec12c272423e484b20db36caa796d21adea4/examples/robotics/quadrotor-bldc/hardware/flight-controller-openfc-lite-rev2-lw1/mechanical-review/fc-populated.step";
const fcShape = await lib.fromSTEP(fcStep,{solid:163});
attach('fc-board-native',fcShape.translate(0,stackY,22),[-12.5,-28,22],'paint-matte','#18575e','fc-grommet-1-ENVELOPE');
// Every component solid is retained at its native export pose. The fixed
// relationships express the populated PCB assembly, not a solder strength claim.
const fcNativeCenters:[number,number,number,number][] = [[0,7.0788002,3.8297,1.4128],[1,-0.3212,-6.1503,1.1728],[2,6.3487999,2.1497,1.1728],[3,-9.2511997,-15.1002998,1.2728],[4,5.9088001,-0.1703,1.2728],[5,8.5288,-3.0303,1.1728],[6,-0.9812,-6.1603,1.1378],[7,0.0087998,0.0596998,1.4278],[8,7.7788,2.1497,1.1728],[9,-6.1512001,3.4597,1.1378],[10,-10.0361996,15.4696999,1.2728],[11,8.0362999,-1.6653,1.1378],[12,-2.9912,-6.5903001,1.2728],[13,7.9862998,-6.3102999,1.1378],[14,-7.6011999,-15.0002999,1.1378],[15,-8.3811998,15.4896998,1.1378],[16,-6.1311998,2.4797,1.2733],[17,-6.1312001,-3.5803,1.1378],[18,-6.1411998,-1.0503,1.1378],[19,-6.1411998,-0.4103,1.1728],[20,-1.6112,-6.1603,1.1378],[21,-3.0411999,-7.9403,1.5228],[22,6.3787999,-4.1003,1.2728],[23,-7.0670879,-7.0402999,1.2903],[24,-5.7749259,-8.2040262,1.1378],[25,-6.1411998,4.2196999,1.1728],[26,6.3863001,-1.7703,1.2728],[27,-6.1411998,0.2297,1.1728],[28,-6.3411999,-4.4703002,1.2728],[29,8.0288,-4.1103001,1.1378],[30,6.3137999,-6.4102998,1.2728],[31,-6.1411998,0.8597,1.1728],[32,-6.1312001,-1.6903,1.1378],[33,-6.1312001,-2.9803001,1.1728],[34,-6.1411998,1.4897,1.1378],[35,-2.9912,-5.6903,1.2728],[36,7.4487998,-0.1828,1.4328],[37,7.6487999,1.3997,1.2728],[38,-6.1312001,-2.3303,1.1728],[39,-6.2837,9.0146999,-0.2],[40,-2.7812001,-7.0602999,-0.16],[41,-2.7812001,-5.9603,-0.16],[42,-2.7812001,-4.8603001,-0.16],[43,-2.7812001,-3.7603,-0.16],[44,-2.7812001,-2.6603,-0.16],[45,-2.7812001,-1.5603,-0.16],[46,-2.7812001,-0.4603,-0.16],[47,-2.7812001,0.6397,-0.16],[48,-2.7812001,1.7397,-0.16],[49,-10.3812004,-0.5102999,-0.735],[50,-10.3812004,-0.5103002,-1.1105],[51,-2.2612,-14.5977998,-1.565],[52,4.2488,0.5597,-0.235],[53,-7.3812001,9.7846999,-0.485],[54,3.1188,0.9097,-0.2],[55,6.6888,-14.5877995,-1.565],[56,6.9087999,-8.8302999,-0.235],[57,9.1087999,-8.5602999,-0.23],[58,14.6287999,-7.7902999,-0.2],[59,7.5488002,14.4897003,-1.565],[60,2.5588,5.6097,-0.235],[61,3.1288,1.6097,-0.2],[62,6.5388,-9.8702998,-0.2],[63,-0.9112,-2.6502999,-0.2],[64,2.8588001,3.9997,-0.235],[65,-10.1111999,-15.5802999,-1.085],[66,1.1188,5.6197,-0.235],[67,-1.7612,4.4596999,-0.235],[68,7.3687999,-6.3602998,-0.2],[69,-9.7612,9.5647001,-1.085],[70,10.0387998,-0.4603,-0.2],[71,-10.1012001,-9.8702998,-0.2],[72,0.9588,3.3497001,-0.3595],[73,13.7559443,-9.9802999,-0.235],[74,-7.9211998,-12.0803003,-0.71],[75,-0.8812,4.3397001,-0.335],[76,6.8988001,-7.7503002,-0.275],[77,7.2418187,-8.0815282,-0.4355],[78,7.2542458,-8.0815287,-0.4355],[79,7.2696836,-8.0815282,-0.4355],[80,7.2855148,-8.0815282,-0.4355],[81,7.3022161,-8.0815282,-0.4355],[82,7.2419145,-8.0524917,-0.4355],[83,7.2542832,-8.049871,-0.4355],[84,7.2670565,-8.049871,-0.4355],[85,7.2789385,-8.0467968,-0.4355],[86,7.2926056,-8.0524917,-0.4355],[87,7.3084369,-8.0524917,-0.4355],[88,7.3251381,-8.0524917,-0.4355],[89,7.1804874,-8.0651393,-0.4355],[90,-12.0711999,-12.4403,-0.235],[91,8.0888,-6.3602998,-0.235],[92,5.0288,1.1197,-0.235],[93,-0.9212,-1.9403,-0.235],[94,-6.2837,10.4246998,-0.2],[95,-10.1511998,12.9496999,-0.86],[96,10.0488,-3.5103,-0.2],[97,-7.6112001,13.1947002,-0.71],[98,6.6563001,-6.3503001,-0.2],[99,0.3088,4.8697,-0.2],[100,7.2188001,-9.8603001,-0.2],[101,-0.9212,-3.4103,-0.235],[102,4.5188,4.6696999,-0.2],[103,1.1488,-4.8503001,-0.235],[104,11.9488001,-9.9802999,-0.86],[105,3.1288,2.2896999,-0.2],[106,3.5888,4.6896999,-0.3355],[107,-7.7412,-15.1703,-0.485],[108,8.5087996,-8.0003002,-0.335],[109,-0.9112,-1.1703,-0.235],[110,15.0733004,-2.1203001,-1.31],[111,15.2482996,-2.1203001,-1.785],[112,16.8733006,0.6297,-2.133],[113,16.8733006,-0.8703,-2.133],[114,16.8733006,-3.3702999,-2.133],[115,16.8733006,-4.8703001,-2.133],[116,16.7733002,-1.3703001,-2.133],[117,16.7733002,-1.8703,-2.133],[118,16.7733002,-2.3702999,-2.133],[119,16.7733002,-2.8702999,-2.133],[120,16.8733006,0.6297,-1.437],[121,16.8733006,-0.8703,-1.437],[122,16.8733006,-3.3702999,-1.437],[123,16.8733006,-4.8703001,-1.437],[124,16.7733002,-1.3703001,-1.437],[125,16.7733002,-1.8703,-1.437],[126,16.7733002,-2.3702999,-1.437],[127,16.7733002,-2.8702999,-1.437],[128,11.3692799,-2.3702999,-0.275],[129,11.3692799,-2.8702999,-0.275],[130,11.3692799,-3.3702999,-0.275],[131,11.3692799,-3.8702999,-0.275],[132,11.3692799,-4.3703001,-0.275],[133,11.3692799,-4.6203001,-0.275],[134,11.3692799,-5.1203001,-0.275],[135,11.3692799,-5.3703001,-0.275],[136,11.3692799,-1.8703,-0.275],[137,11.3692799,-1.3703,-0.275],[138,11.3692799,-0.8703,-0.275],[139,11.3692799,-0.3703,-0.275],[140,11.3692799,0.1297,-0.275],[141,11.3692799,0.3797,-0.275],[142,11.3692799,0.8797,-0.275],[143,11.3692799,1.1297,-0.275],[144,3.1188,0.1997,-0.2],[145,1.5988,4.8697,-0.235],[146,0.7413,8.8497,-0.495],[147,7.9688001,-9.8902998,-0.235],[148,2.4687999,8.9096999,-0.235],[149,14.5812998,7.1296999,-1.565],[150,13.8888001,-7.7902999,-0.2],[151,8.9787998,-9.865304,-0.275],[152,7.4788003,7.2396998,-0.715],[153,-10.3211999,-12.1503,-0.86],[154,5.7988,-9.8702998,-0.2],[155,-1.2262,-0.0453,-0.2],[156,13.1287999,-7.7803001,-0.2],[157,-11.7912002,10.4696999,-0.235],[158,-0.9212,-4.1202999,-0.2],[159,7.4288001,9.1796999,-0.715],[160,-1.1212001,14.5896997,-1.565],[161,-8.2112,-9.8903003,-0.2],[162,-1.1212,8.8697004,-0.335]];
// Source STEP details belong to their purchased connector assembly. USB
// contact tips/tails and shell are fixed to its plastic body (110); microSD
// contacts/shell are fixed to its body (49). Every original solid and pose is
// retained. This declares assembly parentage, not solder/bearing strength.
const fcSolidName=(index:number)=>"fc-native-solid-"+String(index).padStart(3,"0");
const fcHousingOrder=(index:number)=>index===49?-2:index===110?-1:index;
for(const [index,x,y,z] of fcNativeCenters.slice().sort((a,b)=>fcHousingOrder(a[0])-fcHousingOrder(b[0]))){
  const parent=index>=111&&index<=143?fcSolidName(110):
    ((index>=40&&index<=48)||index===50)?fcSolidName(49):"fc-board-native";
  attach(fcSolidName(index),(await lib.fromSTEP(fcStep,{solid:index})).translate(0,-12.75,22),
    [x,y-12.75,z+22],"paint-matte","#3a4044",parent);
}

// Nominal blades for visual sweep checks only. The clipping cylinder fixes
// the maximum radius; these straight sections are not a Gemfan airfoil.
function nominalProp(){
  let p=cylinder(6,7);
  for(const a of [0,120,240]){
    const blade=path().moveTo(5,-3).lineTo(17,-8).lineTo(38,-10)
      .lineTo(58,-7).lineTo(65,-1).lineTo(62,3).lineTo(38,8)
      .lineTo(15,7).lineTo(5,3).close().extrude(1.6).translate(0,0,2.2).rotateZ(a);
    p=p.union(blade);
  }
  return p.intersect(cylinder(6,propRadius)).subtract(cylinder(8,2.5).translate(0,0,-1));
}
const motorRows:[string,number,number,any,string][]=[
  ['rear-right',motorX,motorY,rotor1,'#e66f35'],
  ['front-right',motorX,-motorY,rotor2,'#e66f35'],
  ['rear-left',-motorX,motorY,rotor3,'#427daf'],
  ['front-left',-motorX,-motorY,rotor4,'#427daf']
];
for(const [name,x,y,angle,color] of motorRows){
  // Motor ENVELOPE: 28 mm OD, 3 mm mounting foot and 15 mm bell.
  // Exact stator, magnets, bearings, thread engagement and mass are absent.
  const foot=attach('motor-base-'+name+'-ENVELOPE',cylinder(3,14).translate(x,y,6),[x,y,6],'anodized-black','#24282c','arm-'+name);
  const bellShape=cylinder(15,14).union(cylinder(12,2.5).translate(0,0,15)).translate(x,y,9.3).finish('anodized-black');
  const bell=rig.part('rotor-'+name+'-ENVELOPE',bellShape);
  foot.connector('axis',{type:'axis',origin:origin(x,y,9.3),axis:[0,0,1]});
  bell.connector('axis',{type:'axis',origin:origin(x,y,9.3),axis:[0,0,1]});
  rig.mate('prop-shaft-'+name,'motor-base-'+name+'-ENVELOPE.axis','rotor-'+name+'-ENVELOPE.axis','revolute',{pose:angle,limitsDeg:[-2160,2160]});
  const prop=rig.part('prop-'+name+'-ENVELOPE',nominalProp().translate(x,y,25.3).finish('polycarbonate',{color}));
  bell.connector('prop-seat',{type:'frame',origin:origin(x,y,25.3)});
  prop.connector('prop-seat',{type:'frame',origin:origin(x,y,25.3)});
  rig.mate('prop-nut-'+name,'rotor-'+name+'-ENVELOPE.prop-seat','prop-'+name+'-ENVELOPE.prop-seat','fastened');
}
animationView({name:'Four rotor joint demonstration — visual only',fps:24,tracks:[
  {param:'rotor1Angle',keys:[{atMs:0,value:0},{atMs:300,value:0},{atMs:2600,value:2160},{atMs:3200,value:2160}]},
  {param:'rotor2Angle',keys:[{atMs:0,value:0},{atMs:300,value:0},{atMs:2600,value:-1800},{atMs:3200,value:-1800}]},
  {param:'rotor3Angle',keys:[{atMs:0,value:0},{atMs:300,value:0},{atMs:2600,value:-1440},{atMs:3200,value:-1440}]},
  {param:'rotor4Angle',keys:[{atMs:0,value:0},{atMs:300,value:0},{atMs:2600,value:1080},{atMs:3200,value:1080}]}
]});
return rig.model();
