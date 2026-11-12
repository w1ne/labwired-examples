meta({name:'populated-esc-stack-clearance',description:'Exact native populated PCB against all eight nominal six-millimetre OD stack rings. Geometry clearance only; no solder or compression acceptance.'});
const rig=assembly('populated-esc-stack-clearance');
const pcb=rig.part('populated-esc',await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/619a61230add2ea3bd3e8a4f9d278a75ad396d04/examples/robotics/quadrotor-bldc/hardware/esc-4in1/fabrication-review/esc-board-populated.step"));
const holes=[[60.38257,-62.6],[90.88257,-62.6],[60.38257,-32.1],[90.88257,-32.1]];
for(let i=0;i<holes.length;i++){
const [x,y]=holes[i];
for(const [side,z,h,contact] of [['lower',-5.4,5.4,0],['upper',1.53,6.07,1.53]] as [string,number,number,number][]){
const name=side+'-grommet-'+(i+1);
const g=rig.part(name,cylinder(h,3).holes('top',{positions:[{u:0,v:0}],diameter:4,depth:'through'}).translate(x,y,z));
const origin={kind:'vec3' as const,value:[x+2.75,y,contact] as [number,number,number]};
pcb.connector(name,{type:'frame',origin});
g.connector('seat',{type:'frame',origin});
rig.mate(name+'-seat','populated-esc.'+name,name+'.seat','fastened');
}}
return rig.model();