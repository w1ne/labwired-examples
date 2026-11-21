// AXIOM H1 - original 20-axis humanoid robot mechanical reference.
// Dimensional CAD in mm. Servos/encoders and thermal paths are envelopes, not purchased parts.
// Physical dynamics are independently simulated by examples/axiom-h1/axiom_h1.xml.
const robot = assembly('AXIOM H1');
const P = {};
const materialWhite='#E6EEF4', dark='#202C36', cyan='#20DBEA';
function add(name,shape,material='abs'){
 P[name]=robot.part(name,shape,{material});return P[name];
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
function revolute(name,a,b,p,axis,limits){
 connector(a,name+'_parent',p,'axis',axis);
 connector(b,name+'_child',p,'axis',axis);
 // visual assembly: actual joints and limits are in MuJoCo MJCF
}
function fastened(name,a,b,p){
 connector(a,name+'_parent',p,'frame');
 connector(b,name+'_child',p,'frame');
 // visual assembly: fixed geometry
}
// White armor shells separated by small service gaps in the straight standing pose.
add('pelvis',cube(0,0,480,180,112,80));
add('torso',cube(0,0,631,225,124,222));
fastened('torso_mount','pelvis','torso',[0,0,520]);
add('chest_panel',cube(0,-65,650,145,6,110,dark));
fastened('chest_panel_mount','torso','chest_panel',[0,-62,650]);
add('chest_status_light',ball(0,-73,688,5,cyan));
fastened('chest_led_mount','chest_panel','chest_status_light',[0,-68,688]);
add('neck_yaw',cylinder(12,15).translate(0,0,742).color(dark));
revolute('neck_yaw','torso','neck_yaw',[0,0,742],[0,0,1],[-60,60]);
add('neck_pitch',ball(0,0,814,60,materialWhite));
revolute('neck_pitch','neck_yaw','neck_pitch',[0,0,754],[1,0,0],[-25,30]);
add('head_visor',cube(0,-64,820,100,8,29,'#101D26'));
fastened('visor_mount','neck_pitch','head_visor',[0,-60,820]);
for(const s of [-1,1]){
 const name=(s>0?'left':'right')+'_eye';
 add(name,ball(s*22,-72,821,4,cyan));
 fastened(name+'_mount','head_visor',name,[s*22,-68,821]);
}
// Axial channels: shoulders (pitch+roll), elbows, wrists, and grippers.
for(const side of ['left','right']){
 const sign=side==='left'?1:-1;
 const sph=side+'_shoulder_pitch',shr=side+'_shoulder_roll';
 const elbow=side+'_elbow',wrist=side+'_wrist',grip=side+'_gripper';
 const xP=sign*130.5,x=sign*167.5;
 add(sph,ball(xP,0,690,18,dark));
 revolute(sph,'torso',sph,[sign*112.5,0,690],[1,0,0],[-95,90]);
 add(shr,union(tubeDown(x,0,690,150,19),ball(x,0,675,18,materialWhite)).color(materialWhite));
 revolute(shr,sph,shr,[sign*148.5,0,690],[0,1,0],[-75,75]);
 add(elbow,union(ball(x,0,520,20,dark),tubeDown(x,0,519,119,14)).color(materialWhite));
 revolute(elbow,shr,elbow,[x,0,540],[1,0,0],[-5,125]);
 add(wrist,cube(x,0,365,58,51,70,dark));
 revolute(wrist,elbow,wrist,[x,0,400],[1,0,0],[-70,70]);
 add(grip,union(tubeDown(x-sign*18,0,330,50,8),ball(x-sign*18,0,322,8)).color(materialWhite));
 revolute(grip,wrist,grip,[x-sign*18,0,330],[0,0,sign],[0,35]);
 const hp=side+'_hip_pitch',hr=side+'_hip_roll';
 const knee=side+'_knee',ankle=side+'_ankle';
 const lx=sign*114;
 add(hp,ball(sign*108,0,480,18,dark));
 revolute(hp,'pelvis',hp,[sign*90,0,480],[1,0,0],[-85,80]);
 add(hr,tubeDown(lx,0,462,192,23).color(materialWhite));
 revolute(hr,hp,hr,[sign*126,0,480],[0,1,0],[-40,40]);
 add(knee,union(ball(lx,0,249,21,dark),tubeDown(lx,0,242,162,29)).color(materialWhite));
 revolute(knee,hr,knee,[lx,0,270],[1,0,0],[-5,115]);
 add(ankle,union(ball(lx,0,62,18,dark),cube(lx,-38,25,128,230,50,dark)).color(dark));
 revolute(ankle,knee,ankle,[lx,0,65],[1,0,0],[-35,35]);
 // The shins belong to the knee output, and are one continuous solid.
 // Shins intentionally sit between the knee and ankle service gaps.
}
return robot.model();