// LabWired x KernelCAD: OpenFrame-5F mechanical integration model, mm.
// Frame: unmodified OpenDrone rev2.2 STEP, pinned by commit and SHA-256 in
// mechanical-evidence.json. OpenFrame hardware is CERN-OHL-S-2.0.
// This is an assembly/clearance model, not a flight or strength simulation.
// The motor bodies, propeller blade profiles and FC are marked ENVELOPE:
// they are not EMAX/Gemfan/OpenFC manufacturing geometry. Props retain the
// published 129.7 mm sweep diameter, three blades, 6 mm hub and 5 mm bore.
meta({name:'labwired-quad-openframe-5f',
  title:'LabWired quadrotor — populated ESC assembly candidate',
  description:'Pinned 226 mm OpenFrame-5F frame, four independently posed rotor joints, real ESC substrate plus native KiCad component mesh and nominal tri-blade envelopes. Candidate stack lifted 2 mm; imported mesh is visual geometry, not BREP clearance proof.'});

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

// Board geometry comes from the example's native KiCad export; solid 5 is
// the PCB substrate. Holes measured at 30.5 mm pitch, 4 mm diameter.
// Candidate stack raised by 2 mm: substrate bottom z14.4, native components
// descend to z11.32, nominally 2.32 mm above the middle frame top z9.
// This envelope separation is not a qualified clearance or assembly proof.
const escShape = await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/c108ed0/examples/robotics/quadrotor-bldc/hardware/esc-4in1/fabrication-review/esc-board-preview.step",{solid:5});
attach('esc-board',escShape.translate(-75.63257,34.6,14.4),[-15.25,-28,14.4],'paint-matte','#14735b','esc-grommet-1-ENVELOPE');
for(const [index,x,y] of [[1,-15.25,-28],[2,15.25,-28],[3,-15.25,2.5],[4,15.25,2.5]]){
  const ring=cylinder(6.07,3).holes('top',{positions:[{u:0,v:0}],diameter:4,depth:'through'}).translate(x,y,15.93);
  attach('fc-grommet-'+index+'-ENVELOPE',ring,[x,y,15.93],'rubber','#363a3f','esc-board');
}
// Native KiCad GLB component geometry, with its PCB mesh excluded. Converted
// from glTF metres/Y-up to CAD millimetres/Z-up; 213 refs, 56072 triangles.
// Color is uniform after STL conversion. Shape source and SHA are in receipts.
// Both mate frames use substrate top at its centre, not the empty screw bore.
// Moving both frames together leaves the authored component placement unchanged.

// FC ENVELOPE: 40 x 40 x 1.6 mm, four 4 mm holes on 30.5 mm centres.
// Component heights, connector overhang and soft-mount compression are unverified.
let fc=box(40,40,1.6).translate(-20,stackY-20,22);
for(const x of [-15.25,15.25])for(const y of [stackY-15.25,stackY+15.25]){
  fc=fc.subtract(cylinder(3.6,2).translate(x,y,21));
}
attach('fc-board-ENVELOPE',fc,[-15.25,-28,22],'paint-matte','#18575e','fc-grommet-1-ENVELOPE');

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

