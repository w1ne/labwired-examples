meta({name:'native-fc-stack-clearance',description:'Exact exported repaired FC compound against nominal stack rings. Geometry only; solder attachment and compressed mount dimensions are unqualified.'});
const rig=assembly('native-fc-stack-clearance');
const pcb=rig.part('populated-fc',(await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/2c9bef1efcfa6ea9ec8008565b50d32267d782ea/examples/robotics/quadrotor-bldc/hardware/flight-controller-openfc-lite-rev2-lw1/mechanical-review/fc-populated.step")).translate(0,-12.75,22));
for(const [index,x,y] of [[1,-15.25,-28],[2,15.25,-28],[3,-15.25,2.5],[4,15.25,2.5]]){
 const name='fc-grommet-'+index+'-ENVELOPE';
 const g=rig.part(name,cylinder(6.07,3).holes('top',{positions:[{u:0,v:0}],diameter:4,depth:'through'}).translate(x,y,15.93));
 const origin={kind:'vec3' as const,value:[x+(x<0?2.75:-2.75),y,22] as [number,number,number]};
 pcb.connector(name,{type:'frame',origin});g.connector('seat',{type:'frame',origin});
 rig.mate(name+'-seat','populated-fc.'+name,name+'.seat','fastened');
}
return rig.model();
