meta({name:'populated-esc-stack-clearance',description:'Exact native populated PCB against nominal upper stack grommet. Geometry clearance only.'});
const rig=assembly('populated-esc-stack-clearance');
const pcb=rig.part('populated-esc',await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/619a61230add2ea3bd3e8a4f9d278a75ad396d04/examples/robotics/quadrotor-bldc/hardware/esc-4in1/fabrication-review/esc-board-populated.step"));
const g=rig.part('upper-grommet',cylinder(6.07,3.5).subtract(cylinder(6.07,2)).translate(60.38257,-62.6,1.53));
pcb.connector('support',{type:'frame',origin:{kind:'vec3',value:[63.38257,-62.6,1.53]}});
g.connector('seat',{type:'frame',origin:{kind:'vec3',value:[63.38257,-62.6,1.53]}});
rig.mate('support-seat','populated-esc.support','upper-grommet.seat','fastened');
return rig.model();