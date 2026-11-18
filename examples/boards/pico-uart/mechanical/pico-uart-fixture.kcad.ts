// Pico UART fixture, rev A. Millimetres; native KiCad STEP X=editorX, Y=-editorY, Z up.
// Native Raspberry Pi SC0915 model plus specified Samtec header stack.
// Model checks verify nominal fit. Printed tolerances and cable overmolds require bench qualification.
const output=param("output","assembly",{choices:["assembly","base-print","lid-print"]}).value;
const floorT=2.5,bodyH=27.5,lidT=2,boardZ=8,boardT=1.6,pcbTop=9.6;
const mounts=[[4,4],[56,4],[4,66],[56,66]];
const lidMounts=[[-3.5,-3.5],[63.5,-3.5],[63.5,73.5],[-3.5,73.5]];
// Dimensions below retain the electrical editor coordinates. These constructors
// convert each primitive once into native world X=editorX, Y=-editorY, Z up.
// Boolean inputs are mutable feature references; never reflect their shared roots later.
function brick(w,h,d,x,y,z){return box(w,h,d).translate(x,-y-h,z);}
function rounded(w,h,r,z,x,y){return extrudeRoundedRect(w,h,r,z).translate(x,-y,0);}
function bore(d,h,x,y,z){return cylinder(h,d/2).translate(x,-y,z);}
function hex(af,h,x,y,z){
 const r=af/Math.sqrt(3);
 return extrudePolygon(Array.from({length:6},(_,i)=>[r*Math.cos((30+60*i)*Math.PI/180),r*Math.sin((30+60*i)*Math.PI/180)]),h).translate(x,-y,z);
}
function frame(p,n,v){p.connector(n,{type:"frame",origin:{kind:"vec3",value:[v[0],-v[1],v[2]]},normal:[0,0,1]});}
let base=rounded(78,88,5,bodyH,30,35).subtract(rounded(73,83,2.5,bodyH,30,35).translate(0,0,floorT));
// Four carrier and four lid standoffs use flush underside M2.5 screws.
for(const[x,y]of[...mounts,...lidMounts]){
 base=base.subtract(bore(2.9,floorT+1,x,y,-.5));
 const sink=path().moveTo(0,0).lineTo(3.1,0).lineTo(1.45,1.65).lineTo(0,1.65).close().revolve().translate(x,-y,0);
 base=base.subtract(sink);
}
// Open-top notch preserves vertical board removal and accepts a bounded 16 x 8 mm plug.
base=base.subtract(brick(18,20,16,21,-13,17.5)).color("#35495d");
let lid=rounded(78,88,5,lidT,30,35).translate(0,0,bodyH);
for(const[x,y]of lidMounts)lid=lid.subtract(bore(2.9,lidT+2,x,y,bodyH-1));
// Three individual Adafruit954 connector housings exit here. Red5V stays disconnected.
lid=lid.subtract(extrudeRoundedRect(10,14,1,4).translate(10,-17.54,bodyH-1));
for(const x of[5,15])lid=lid.subtract(brick(3.2,7,4,x-1.6,26,bodyH-1));
// Registration tabs, 0.3 mm lateral clearance.
lid=lid.union(brick(1.5,16,1.2,-6.2,27,bodyH-1.2));
lid=lid.union(brick(16,1.5,1.2,22,74.7,bodyH-1.2));
lid=lid.union(brick(1.5,16,1.2,64.7,27,bodyH-1.2)).color("#dde7e9");
if(output==="base-print"){
 const a=assembly("pico-uart-base-print");a.part("base",base,{material:"petg"});
 dfmSpec({process:"fdm",buildDirection:"+z",nozzleMm:.4,minWall:.8,maxBridgeMm:10,maxOverhangDeg:45});
 return a.model();
}
if(output==="lid-print"){
 const a=assembly("pico-uart-lid-print");a.part("lid",lid.rotateX(180).translate(0,0,bodyH+lidT),{material:"petg"});
 dfmSpec({process:"fdm",buildDirection:"+z",nozzleMm:.4,minWall:.8,maxBridgeMm:10,maxOverhangDeg:45});
 return a.model();
}
const carrier=(await lib.fromSTEP("../cad/pico-carrier.step")).scale([1,1,1.6/1.51]).translate(0,0,boardZ);
// Independent native PCB registration: pin1, pin2 and the opposite row.
for(const [name,x,y] of [["J1.1",21.11,-7.37],["J1.2",21.11,-9.91],["J2.1",38.89,-7.37]]){
 const gauge=cylinder(boardT+0.2,0.25).translate(x,y,boardZ-0.1);
 require("native-carrier-registration-"+name,clearance(carrier,gauge).between(0.249,0.251));
}
let pcba=carrier;
for(const x of[21.11,38.89]){
 // Samtec SSW-120-01-G-S drawing-derived nominal envelope, not vendor STEP.
 // Width 2.41 REF; length (20*2.54)+0.51 = 51.31 +/-0.25; height8.51, tail2.64.
 let socket=brick(2.41,51.31,8.51,x-1.205,5.845,pcbTop);
 for(let i=0;i<20;i++){
  const y=7.37+2.54*i;
  socket=socket.subtract(bore(1,6.3,x,y,pcbTop+2.31));
  // Tail envelope is round .64; nominal insertion fit, not spring-contact mechanics.
  socket=socket.union(bore(.64,2.74,x,y,pcbTop-2.64));
 }
 pcba=pcba.union(socket);
}
pcba=pcba.union(brick(2.54,7.62,2.54,8.73,13.73,pcbTop));
for(let i=0;i<3;i++)pcba=pcba.union(brick(.635,.635,10.922,10-.3175,15+2.54*i-.3175,pcbTop-2.54));
pcba=pcba.color("#266c4f");
// Manufacturer STEP's PCB lies in X/Z and is centred at original Y=0.
// A proper Rx(90) rotation maps native +Y to populated world +Z.
// Native pin1=(1.61,0,-49.63) maps to J1.1=(21.11,-7.37); pin40 maps to J2.1.
// USB is at world Y=-4.7; board body spans Y=-57..-6. No vendor reflection is used.
const moduleMidZ=pcbTop+8.51+2.54+.5;
// Preserve every original solid as a separate fixed component. The USB lips
// touch the receptacle shell; combining them into one mesh creates non-manifold edges.
const componentSeats=[[30,31.5,20.65],[30,7.799999,21.65],[30,5,23.83],[30,5,21.44],[33.725,5,22.85],[26.275,5,22.85],[26.5,18,21.65],[30,32,21.65],[24.3,10.800001,21.65],[36,12.6,21.65],[36,16.900002,21.65],[32.9,14.400002,21.65],[32.9,19.400002,21.65],[32.9,16.900002,21.65],[36.400001,24.300001,21.65],[27.7,40.55,21.65],[26.2,25.099999,21.65]];
const componentShapes=[];
const moduleBuild=assembly("pico-with-specified-headers");
let nativePart;
for(let i=0;i<17;i++){
 const shape=(await lib.fromSTEP("../references/raspberry-pi/Pico-R3.step",{solid:i})).rotateX(90).translate(19.5,-57,moduleMidZ).color(i===0?"#287251":i<=6?"#b8bcc0":i===8?"#a8dcb8":"#33393c");
 const name=i===0?"pico-board":"pico-component-"+i;
 const p=moduleBuild.part(name,shape,{density:1850});
 componentShapes.push({name,shape,index:i,inner:p});
 if(i===0)nativePart=p;
}
for(const e of componentShapes){
 if(e.index===0)continue;
 const parent=e.index>=2&&e.index<=5?componentShapes[1].inner:nativePart;
 frame(parent,e.name,componentSeats[e.index]);frame(e.inner,"fixed-seat",componentSeats[e.index]);
 moduleBuild.mate("native-fixed-"+e.name,parent.name+"."+e.name,e.inner.name+".fixed-seat","fastened");
}
for(const x of[21.11,38.89]){
 let header=brick(2.54,50.8,2.54,x-1.27,6.1,pcbTop+8.51);
 for(let i=0;i<20;i++){
  // TSW-120-07-G-S: 5.842 mating post +2.54 insulator +2.54 solder tail.
  header=header.union(brick(.635,.635,10.922,x-.3175,7.37+2.54*i-.3175,pcbTop+8.51-5.842));
 }
 header=header.color("#22262a");
 componentShapes.push({name:"pico-header-"+Math.round(x*100),shape:header,index:-1,x});
 const hp=moduleBuild.part("header-"+Math.round(x*100),header,{density:2200});
 frame(nativePart,"header-"+Math.round(x*100),[x+1,7.37,moduleMidZ-.5]);frame(hp,"seat",[x+1,7.37,moduleMidZ-.5]);
 moduleBuild.mate("soldered-header-"+Math.round(x*100),"pico-board.header-"+Math.round(x*100),hp.name+".seat","fastened");
}
// The vendor board is an exact, multi-solid assembly. Compound preserves its
// separate components; a boolean union would incorrectly demand one fused solid.
const pico=moduleBuild.model().toCompound();
// LED is the asymmetric native witness: its manufacturer body is on the pin1 side.
// The old Rz(180) row swap puts its X centroid at35.7 and fails this bound.
// Z is bounded by the original LED body extent, not its bounding-box midpoint.
// The native body has a nonuniform section, so its mass centroid is not at mid-height.
require("native-pico-led-on-pin1-side",centerOfMass(componentShapes[8].shape).within({x:[24.29,24.31],y:[-10.81,-10.79],z:[21.65,22.25]}));
for(const [name,x,y] of [["pin1",21.11,-7.37],["pin2",21.11,-9.91],["pin40",38.89,-7.37]]){
 const gauge=cylinder(1.2,0.25).translate(x,y,moduleMidZ-0.6);
 require("native-pico-registration-"+name,clearance(componentShapes[0].shape,gauge).between(0.249,0.251));
}

require("native-carrier-size",bbox(carrier).within({x:[59.99,60.01],y:[69.99,70.01],z:[1.59,1.61]}));
require("pico-to-lid",clearance(pico,lid).gte(1));
require("carrier-to-lid",clearance(pcba,lid).gte(1));
const usbPlug=brick(16,30,8,22,-25.3,moduleMidZ+1.615-4);
require("usb-plug-base-access",clearance(usbPlug,base).gte(.5));
require("usb-plug-lid-access",clearance(usbPlug,lid).gte(.5));
const a=assembly("pico-uart-fixture");
const bp=a.part("base",base,{material:"petg"});
const lp=a.part("lid",lid,{material:"petg"});
const cp=a.part("carrier-pcba",pcba,{density:1850});
const picoParts={};
for(const e of componentShapes)picoParts[e.name]=a.part(e.name,e.shape,{density:e.index===-1?2200:1850});
const pp=picoParts["pico-board"];
for(const e of componentShapes){
 if(e.index===0)continue;
 const p=picoParts[e.name],v=e.index===-1?[e.x+1,7.37,moduleMidZ-.5]:componentSeats[e.index];
 const parent=e.index>=2&&e.index<=5?picoParts["pico-component-1"]:pp;
 frame(parent,e.name,v);frame(p,"fixed-seat",v);
 if(e.index===-1&&e.x===21.11) a.mate("fixed-"+e.name,p.name+".fixed-seat",parent.name+"."+e.name,"fastened");
 else a.mate("fixed-"+e.name,parent.name+"."+e.name,p.name+".fixed-seat","fastened");
}
frame(bp,"lid-seat",[30,-7.75,bodyH]);frame(lp,"base-seat",[30,-7.75,bodyH]);
a.mate("lid-seat","base.lid-seat","lid.base-seat","fastened");
frame(cp,"module-seat",[21.11+1,7.37,pcbTop+8.51]);frame(picoParts["pico-header-2111"],"carrier-seat",[21.11+1,7.37,pcbTop+8.51]);
a.mate("pico-sockets","carrier-pcba.module-seat","pico-header-2111.carrier-seat","fastened",{fit:{kind:"press",part:"pico-header-2111",axis:[0,0,1]}});
async function screw(l){return await lib.part({family:"socket-head-cap-screw",thread:"M2.5",lengthMm:l,detail:"envelope"});}
function fastener(n,s,parent,v,l,axis=[0,0,1],standard="ISO4762"){
 const p=a.part(n,s);frame(parent,n,v);frame(p,"seat",v);
 a.mate(n+"-mate",parent.name+"."+n,n+".seat","fastened",{fastener:{part:n,axis,pitchMm:.45,threadLengthMm:l,standard,tool:{kind:"cylinder",lengthMm:40,diameterMm:4,label:"straight hex driver"}}});return p;
}
function spacer(n,h,x,y,z,parent){
 let s=hex(5,h,0,0,0);
 if(h===5)s=s.subtract(bore(2.5,h+.2,0,0,-.1));
 else s=s.subtract(bore(2.5,8.1,0,0,-.1)).subtract(bore(2.5,8.1,0,0,h-8));
 const p=a.part(n,s.translate(x,-y,z).color("#b9bdc2"),{density:8500});
 frame(parent,n,[x+2,y,z]);frame(p,"seat",[x+2,y,z]);a.mate(n+"-seat",parent.name+"."+n,n+".seat","fastened");return p;
}
function lower(n,x,y){
 const s=path().moveTo(0,0).lineTo(2.94,0).lineTo(1.25,1.69).lineTo(1.25,5).lineTo(0,5).close().revolve().subtract(hex(1.5,1,0,0,-.001)).translate(x,-y,.16).color("#b9bdc2");
 return fastener(n,s,bp,[x,y,.16],5,[0,0,-1],"ISO10642");
}
for(let i=0;i<mounts.length;i++){
 const[x,y]=mounts[i];
 const w=a.part("carrier-washer-"+i,bore(6.5,.5,x,y,2.5).subtract(bore(2.7,1,x,y,2.25)),{material:"nylon"});
 frame(bp,"washer-"+i,[x+2,y,2.5]);frame(w,"seat",[x+2,y,2.5]);a.mate("washer-"+i,"base.washer-"+i,w.name+".seat","fastened");
 const st=spacer("carrier-standoff-"+i,5,x,y,3,w);
 if(i===0){frame(st,"board-seat",[x+2,y,boardZ]);frame(cp,"base-seat",[x+2,y,boardZ]);a.mate("carrier-seat",st.name+".board-seat","carrier-pcba.base-seat","fastened");}
 fastener("carrier-screw-"+i,(await screw(4)).translate(x,-y,pcbTop),cp,[x,y,pcbTop],4);
 lower("carrier-lower-screw-"+i,x,y);
}
for(let i=0;i<lidMounts.length;i++){
 const[x,y]=lidMounts[i];spacer("lid-standoff-"+i,25,x,y,floorT,bp);
 fastener("lid-screw-"+i,(await screw(8)).translate(x,-y,bodyH+lidT),lp,[x,y,bodyH+lidT],8);
 lower("lid-lower-screw-"+i,x,y);
}
return a.solvedModel({}, {validate:"warn"});
