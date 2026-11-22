// Conservative axial assembly-path check for the final Pathfinder bench carrier.
// Preconditions: remove both bulkheads and the radial panel switch; disconnect external leads.
// The moving R18.4 envelope bounds the carrier, populated PCB, battery, converter and service volumes.
// This tests geometric translation only. It does not prove cable retention, tolerances or loads.
const a=assembly('carrier-bore-path');
const shell=cylinder(250,19.8).subtract(cylinder(250.4,19).translate(0,0,-.2)).translate(0,0,230);
const bore=a.part('coupler',shell.color('#6e7983'));
const cassette=a.part('conservative-cassette-envelope',cylinder(242,18.4).translate(0,0,234).color('#51846a'));
bore.connector('axis',{type:'frame',origin:{kind:'vec3',value:[0,0,355]}});
cassette.connector('axis',{type:'frame',origin:{kind:'vec3',value:[0,0,355]}});
a.mate('location','coupler.axis','conservative-cassette-envelope.axis','fastened');
return a.solvedModel({});