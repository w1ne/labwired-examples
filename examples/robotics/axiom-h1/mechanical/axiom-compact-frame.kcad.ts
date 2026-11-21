// AXIOM H1 - compact fore-aft clearance-joint revision candidate, preserving the original source separately.
// Dimensional CAD in mm. Servos/encoders and thermal paths are envelopes, not purchased parts.
// Kinematic reference only. Geometry review does not prove torque, power or gravity stability.
const robot = assembly('AXIOM H1');
const P = {}, G = {}, M = {}, mates = [];
const materialWhite='#E6EEF4', dark='#202C36', cyan='#20DBEA';
function add(name,shape,material='abs'){
 G[name]=shape; M[name]=material; return shape;
}
function cube(x,y,z,sx,sy,sz,color=materialWhite){
 return box(sx,sy,sz,true).translate(x,y,z).color(color);
}
function ball(x,y,z,r,color=dark){
 return sphere(r).translate(x,y,z).color(color);
}
function tubeDown(x,y,zTop,h,r,color=materialWhite){
 return cylinder(h,r).translate(x,y,zTop-h).color(color);
}
function connector(part,name,point,type='axis',axis=[1,0,0]){
 P[part].connector(name,{type,origin:{kind:'vec3',value:point},...(type==='axis'?{axis}:{})});
}
function axisCylinder(r,lo,hi,p,axis) {
 return cylinder(hi-lo,r).alongAxis(axis).translate(p[0]+axis[0]*lo,p[1]+axis[1]*lo,p[2]+axis[2]*lo);
}
function revolute(name,a,b,p,axis,limits){
 const radii={neck_pitch:6,shoulder_roll:35,elbow:40,wrist:30,hip_roll:41,knee:56,ankle:18};
 const key=Object.keys(radii).find(k=>name===k||name.endsWith('_'+k));
 if (key) {
  const R=radii[key], C=(r,lo,hi)=>axisCylinder(r,lo,hi,p,axis);
  const fork=union(C(R,-9,-5),C(R,5,9));
  const pin=union(C(2,-9.2,9.2),C(3.2,-11.8,-8.8),C(3.2,8.8,11.8));
  // Real disjoint axial ranges: tongue +/-4.5, cheeks 5..9.
  // The parent pocket clears the full circular tongue for every angle.
  G[a]=G[a].union(fork).subtract(C(R+.75,-4.75,4.75)).subtract(C(2.2,-100,100)).union(pin);
  // Clear the original shell from the fork's swept circular envelope.
  G[b]=G[b].subtract(C(R+.25,-2000,-4.75)).subtract(C(R+.25,4.75,2000))
   .union(C(R+.5,-4.5,4.5)).subtract(C(2.2,-100,100));
  const spec={origin:p,axis,clearanceRadius:2.2};
  mates.push({name,a,b,p,axis,limits,parent:spec,child:spec});
 } else mates.push({name,a,b,p,axis,limits});
}
function fastened(name,a,b,p){
 mates.push({name,a,b,p,fixed:true});
}
// White armor shells separated by small service gaps in the straight standing pose.
// Fore-aft bearing brackets separate limb workspaces without widening the shoulders.
add('pelvis',union(cube(0,0,480,180,112,80),cube(78.75,80,480,22.5,60,20),cube(-78.75,-80,480,22.5,60,20)));
add('torso',union(cube(0,0,631,225,124,222),cube(101.25,-87.5,700,22.5,75,20),cube(-101.25,-117.5,700,22.5,135,20)));
fastened('torso_mount','pelvis','torso',[0,0,520]);
add('chest_panel',cube(0,-65,650,145,6,110,dark));
fastened('chest_panel_mount','torso','chest_panel',[0,-62,650]);
add('chest_status_light',ball(0,-73,688,5,cyan));
fastened('chest_led_mount','chest_panel','chest_status_light',[0,-68,688]);
add('neck_yaw',cylinder(7,15).translate(0,0,742).color(dark));
revolute('neck_yaw','torso','neck_yaw',[0,0,742],[0,0,1],[-60,60]);
add('neck_pitch',ball(0,0,816,57,materialWhite).subtract(cube(0,-106,816,200,100,200)));
revolute('neck_pitch','neck_yaw','neck_pitch',[0,0,754],[1,0,0],[-25,30]);
add('head_visor',cube(0,-60,820,100,8,29,'#101D26'));
fastened('visor_mount','neck_pitch','head_visor',[0,-56,820]);
for(const s of [-1,1]){
 const name=(s>0?'left':'right')+'_eye';
 add(name,ball(s*22,-68,821,4,cyan));
 fastened(name+'_mount','head_visor',name,[s*22,-64,821]);
}
// Axial channels: shoulders (pitch+roll), elbows, wrists, and grippers.
for(const side of ['left','right']){
 const sign=side==='left'?1:-1;
 const ay=side==='left'?-115:-175,ly=sign*100;
 const sph=side+'_shoulder_pitch',shr=side+'_shoulder_roll';
 const elbow=side+'_elbow',wrist=side+'_wrist',grip=side+'_gripper';
 const xP=sign*130.5,x=sign*167.5;
 add(sph,union(ball(xP,ay,690,18,dark),cube(sign*113.5,ay,690,2,18,8,dark)));
 revolute(sph,'torso',sph,[sign*112.5,ay,690],[1,0,0],[-95,90]);
 add(shr,union(tubeDown(x,ay,690,150,19),ball(x,ay,675,18,materialWhite)).color(materialWhite));
 revolute(shr,sph,shr,[sign*148.5,ay,690],[0,1,0],sign===1?[-70,80]:[-80,70]);
 add(elbow,union(ball(x,ay,520,20,dark),tubeDown(x,ay,519,119,14)).color(materialWhite));
 revolute(elbow,shr,elbow,[x,ay,540],[1,0,0],[-5,125]);
 add(wrist,cube(x,ay,365,40,51,70,dark));
 revolute(wrist,elbow,wrist,[x,ay,400],[1,0,0],[-70,70]);
 add(grip,union(tubeDown(x-sign*9,ay,330,50,8),ball(x-sign*9,ay,322,8)).color(materialWhite));
 revolute(grip,wrist,grip,[x-sign*9,ay,330],[0,0,sign],[0,35]);
 const hp=side+'_hip_pitch',hr=side+'_hip_roll';
 const knee=side+'_knee',ankle=side+'_ankle';
 const lx=sign*123;
 add(hp,ball(sign*108,ly,480,18,dark));
 revolute(hp,'pelvis',hp,[sign*90,ly,480],[1,0,0],[-85,80]);
 add(hr,tubeDown(lx,ly,462,192,23).color(materialWhite));
 revolute(hr,hp,hr,[sign*135,ly,462],[0,1,0],[-40,40]);
 add(knee,union(ball(lx,ly,249,21,dark),tubeDown(lx,ly,242,162,29)).color(materialWhite));
 revolute(knee,hr,knee,[lx,ly,270],[1,0,0],[-5,115]);
 add(ankle,union(ball(lx,ly,62,17,dark),cube(lx,ly-38,25,128,230,50,dark)).color(dark));
 revolute(ankle,knee,ankle,[lx,ly,65],[1,0,0],[-35,35]);
 // The shins belong to the knee output, and are one continuous solid.
 // Shins intentionally sit between the knee and ankle service gaps.
}
for (const name of Object.keys(G)) P[name]=robot.part(name,G[name],{material:M[name]});
for (const m of mates) {
 if (m.parent) {
  for (const [part,suffix,c] of [[m.a,'_parent',m.parent],[m.b,'_child',m.child]]) {
   P[part].connector(m.name+suffix,{type:'axis',origin:{kind:'vec3',value:c.origin},axis:c.axis,jointClearanceRadius:c.clearanceRadius});
  }
 } else {
  connector(m.a,m.name+'_parent',m.p,m.fixed?'frame':'axis',m.axis);
  connector(m.b,m.name+'_child',m.p,m.fixed?'frame':'axis',m.axis);
 }
 robot.mate(m.name,m.a+'.'+m.name+'_parent',m.b+'.'+m.name+'_child',m.fixed?'fastened':'revolute',m.fixed?{}:{limitsDeg:m.limits});
}
return robot.model();