// LabWired x KernelCAD / drone propulsion concept
// Dimensions in mm. Four independent ESC/motor channels are represented mechanically;
// LabWired firmware-in-loop proof currently covers one 24V six-step BLDC channel.
meta({name:'labwired-quad-bldc-rig',license:'CC0-1.0',title:'LabWired x KernelCAD — Quad BLDC propulsion rig',
  description:'Parametric quadrotor with four revolute propeller shafts, ESC board and landing skids. Motor control comes from LabWired firmware-in-loop.'});
const spinCW = param('rotorCW',0,{min:-2160,max:2160,label:'CW rotor angle'});
const spinCCW = param('rotorCCW',0,{min:-2160,max:2160,label:'CCW rotor angle'});
const armReach = 205;
const motorR = 23;
const chassisZ = 55;
const corners:[string,number,number,number][]=[
 ['front-left',145,-145,45],['front-right',145,145,135],
 ['rear-left',-145,-145,315],['rear-right',-145,145,225]];
// Carbon/metal frame: central sealed electronics bay + four diagonal arms.
let chassis = box(148,132,24,true).translate(0,0,68);
for(const [name,x,y,angle] of corners){
  const beam=box(armReach+7,20,15).translate(-7,-10,chassisZ).rotateZ(Math.atan2(y,x)*180/Math.PI);
  const stator=cylinder(28,motorR).translate(x,y,57);
  chassis=chassis.union(beam).union(stator);
}
// Landing skids are part of the monocoque concept geometry.
for(const side of [-1,1]){
  chassis=chassis.union(box(14,165,10).translate(side*53-7,-82.5,0));
  for(const yy of [-60,60]){
    chassis=chassis.union(box(12,12,56).translate(side*53-6,yy-6,0));
  }
}
// Mounting bosses rise from the top deck, supporting a separate removable ESC board.
for(const [x,y] of [[-27,-18],[27,-18],[-27,18],[27,18]]){
  chassis=chassis.union(cylinder(11,3.6).translate(x,y,80));
}
chassis=chassis.finish('anodized-black');
// ESC controller card and voltage/current telemetry electronics, concept-level positions.
// Not a validated transistor/PCB layout; electronics truth is held in LabWired.
const pcb=box(68,48,1.6).translate(-34,-24,91).finish('paint-matte',{color:'#136c5d'});
function propBlade(){
  return path().moveTo(0,-9).lineTo(18,-17).lineTo(47,-16)
    .lineTo(80,-10).lineTo(111,-5).lineTo(116,0)
    .lineTo(88,7).lineTo(46,13).lineTo(16,13).lineTo(0,8)
    .close().extrude(4);
}
const rig=assembly('labwired-quad-bldc');
const frame=rig.part('carbon-monocoque',chassis,{material:'aluminum-6061'});
const esc=rig.part('esc-controller-board',pcb,{material:'abs'});
const origin=(x:number,y:number,z:number)=>({kind:'vec3' as const,value:[x,y,z] as [number,number,number]});
frame.connector('esc-seat',{type:'frame',origin:origin(27,18,91)});
esc.connector('esc-seat',{type:'frame',origin:origin(27,18,91)});
rig.mate('esc-board-bolts','carbon-monocoque.esc-seat','esc-controller-board.esc-seat','fastened');
for(const [name,x,y] of corners){
  // Separate moving bell, shaft cap and twin blade pair: physically a rotor.
  let rotor=cylinder(17,21).union(cylinder(7,12).translate(0,0,14));
  rotor=rotor.union(propBlade().rotateY(4).translate(0,0,19))
    .union(propBlade().rotateZ(180).rotateY(4).translate(0,0,19));
  rotor=rotor.translate(x,y,85).finish('anodized-black');
  const p=rig.part('rotor-'+name,rotor,{material:'abs'});
  frame.connector('shaft-'+name,{type:'axis',origin:origin(x,y,85),axis:[0,0,1]});
  p.connector('shaft-'+name,{type:'axis',origin:origin(x,y,85),axis:[0,0,1]});
  const angle = name==='front-left'||name==='rear-right'?spinCW:spinCCW;
  rig.mate('prop-shaft-'+name,
   'carbon-monocoque.shaft-'+name,
   'rotor-'+name+'.shaft-'+name,'revolute',{pose:angle,limitsDeg:[-2160,2160]});
}
animationView({name:'Spin-up and commanded stop (visual; not a flight dynamics model)',fps:24,
 tracks:[
  {param:'rotorCW',keys:[{atMs:0,value:0},{atMs:300,value:0},{atMs:1850,value:1800},
    {atMs:2600,value:2160},{atMs:3200,value:2160}]},
  {param:'rotorCCW',keys:[{atMs:0,value:0},{atMs:300,value:0},{atMs:1850,value:-1800},
    {atMs:2600,value:-2160},{atMs:3200,value:-2160}]}
 ]});
return rig.model();
