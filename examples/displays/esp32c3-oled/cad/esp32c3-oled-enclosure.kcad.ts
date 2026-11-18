// ESP32-C3 OLED enclosure. Units: mm. Z up.
// World frame: native KiCad STEP X=editorX, Y=-editorY, populated side +Z.
// Carrier underside is Z=8. Purchased components retain physical handedness.
// Source dimensions and limitations: cad/mechanical-interface.json.
// Base/lid derive from the hosted enclosure-lid-with-screw-bosses cookbook.
// Purchased PCBA solids are clearance models, not fabrication models.
// No antenna, battery, or radio operation is included.
const output = param("output", "assembly", {choices:["assembly","base-print","lid-print"], label:"Output"}).value;
const wall = 2.5, floorT = 2.5, bodyH = 27.5, lidT = 2;
const boardZ = 8.0, boardT = 1.6;
const pcbTop = boardZ + boardT;
const displayFront = bodyH - 2.3;
const displayBack = displayFront - 1.6;
const mounts = [[4,4],[66,4],[4,41],[66,41]];
const lidMounts = [[-3.5,-3.5],[73.5,-3.5],[73.5,48.5],[-3.5,48.5]];
const oledMounts = [[37.54,35.71],[61.67,35.71],[37.54,9.04],[61.67,9.04]];
const nutDriverDiameter=5.7,nutDriverLength=60;
// Dimensions below retain the electrical editor coordinates. These constructors
// convert each primitive once into native world X=editorX, Y=-editorY, Z up.
// Boolean inputs are mutable feature references; never reflect their shared roots later.
function brick(w,h,d,x,y,z){return box(w,h,d).translate(x,-y-h,z);}
function rounded(w,h,r,z,x,y){return extrudeRoundedRect(w,h,r,z).translate(x,-y,0);}
function hex(af,h,x,y,z){
  const r=af/Math.sqrt(3);
  const pts=Array.from({length:6},(_,i)=>[r*Math.cos((30+60*i)*Math.PI/180),r*Math.sin((30+60*i)*Math.PI/180)]);
  return extrudePolygon(pts,h).translate(x,-y,z);
}
function bore(d,h,x,y,z){return cylinder(h,d/2).translate(x,-y,z);}
function frame(part,name,p){part.connector(name,{type:"frame",origin:{kind:"vec3",value:[p[0],-p[1],p[2]]},normal:[0,0,1]});}
let base=rounded(88,63,5,bodyH,35,22.5)
 .subtract(rounded(83,58,2.5,bodyH,35,22.5).translate(0,0,floorT));
// Eight flush underside screws retain purchased standoffs.
// 90-degree countersinks print without pocket roofs.
for(const [x,y] of [...mounts,...lidMounts]){
 base=base.subtract(bore(2.9,floorT+1,x,y,-0.5));
 const sink=path().moveTo(0,0).lineTo(3.1,0).lineTo(1.45,1.65).lineTo(0,1.65).close().revolve().translate(x,-y,0);
 base=base.subtract(sink);
}
// Open-top USB notch permits vertical board removal after the lid is removed.
const usbCut=extrudeRoundedRect(18,16,1.5,15,{axis:"x"}).translate(-12,-22.5,24.5);
base=base.subtract(usbCut).color("#35495d");
let lid=rounded(88,63,5,lidT,35,22.5).translate(0,0,bodyH);
const windowCut=extrudeRoundedRect(22.744,11.864,0.6,4).translate(49.605,-18.849,bodyH-1);
lid=lid.subtract(windowCut);
for(const [x,y] of lidMounts) lid=lid.subtract(bore(2.9,lidT+2,x,y,bodyH-1));
const glassNearSupports=[];
for(const [x,y] of oledMounts){
 // The two glass-near mounts use an open U section. The 0.85 mm arms
 // and back retain the original wall thickness; no bridge faces the glass.
 let support;
 if(y<20){
  support=brick(4,3,2.3,x-2,y-2,displayFront)
   .subtract(brick(2.3,3,2.5,x-1.15,y-1.15,displayFront-0.1));
  glassNearSupports.push(support);
 }else support=bore(4,2.3,x,y,displayFront);
 lid=lid.union(support);
 lid=lid.subtract(bore(2.3,7,x,y,displayFront-1));
}
// Three registration tabs; 0.30 mm lateral clearance to the base inner wall.
lid=lid.union(brick(16,1.5,1.2,27,-6.2,bodyH-1.2));
lid=lid.union(brick(16,1.5,1.2,27,49.7,bodyH-1.2));
lid=lid.union(brick(1.5,16,1.2,74.7,14.5,bodyH-1.2));
lid=lid.color("#e7ecef");
if(output==="base-print"){
 const a=assembly("oled-base-print");a.part("base",base,{material:"petg"});
 dfmSpec({process:"fdm",buildDirection:"+z",nozzleMm:0.4,minWall:0.8,maxBridgeMm:10,maxOverhangDeg:45});
 return a.model();
}
if(output==="lid-print"){
 const printLid=lid.rotateX(180).translate(0,0,bodyH+lidT);
 const a=assembly("oled-lid-print");a.part("lid",printLid,{material:"petg"});
 dfmSpec({process:"fdm",buildDirection:"+z",nozzleMm:0.4,minWall:0.8,maxBridgeMm:10,maxOverhangDeg:45});
 return a.model();
}
// Carrier geometry follows the native PCB interface. Component shapes are
// conservative mounting envelopes; native electronics are separate deliverables.
// Native board-only STEP contains a 1.51 mm substrate. The explicit Z scale
// is the finished 1.60 mm stack clearance envelope; XY and all holes are unchanged.
// Keep the native XY orientation and +Z populated side. The native substrate
// starts at Z=0; only its qualified positive Z scale and installation height change.
const carrier=(await lib.fromSTEP("./inputs/47111971a61f.step")).scale([1,1,1.6/1.51]).translate(0,0,boardZ);
// Independent native pad-centre gauges. Their coordinates are read from the
// KiCad PCB and checked against the imported BREP, not derived from the placement helpers.
for(const [name,x,y] of [["J2.1",2.88,-30.12],["J2.2",5.42,-30.12],["J3.7",2.88,-14.88]]){
 const gauge=cylinder(boardT+0.2,0.2).translate(x,y,boardZ-0.1);
 require("native-carrier-registration-"+name,clearance(carrier,gauge).between(0.199,0.201));
}
let pcba=carrier;
for(const y of [14.88,30.12]){
 // Samtec HSS-107-G-2 + BHS-107-G-A, 3.18 mm nominal insertion.
 let stack=brick(17.78,2.54,9.77,1.61,y-1.27,pcbTop);
 for(let i=0;i<7;i++){
  const x=2.88+2.54*i;
  stack=stack.union(bore(0.51,3.18,x,y,pcbTop-3.18));
 }
 pcba=pcba.union(stack);
}
const moduleBottom=boardZ+11.37,moduleTop=moduleBottom+1.6;
let controller=rounded(21,17.8,1,1.6,10.5,22.5).translate(0,0,moduleBottom);
const shield=brick(10.35,12.45,2.0,6.8,16.25,moduleTop);
controller=controller.union(shield);
for(const y of [15.1,24.0]) controller=controller.union(brick(2.5,4.303,1.7,17.7,y,moduleTop));
controller=controller.union(bore(2.6,1.3,18.3,22.5,moduleTop));
const usbOuter=extrudeRoundedRect(9,3.21,1.2,7.35,{axis:"x"}).translate(-1.4855,-22.5,moduleTop+1.605);
const usbInner=extrudeRoundedRect(8.3,2.51,0.9,6.5,{axis:"x"}).translate(-1.6,-22.5,moduleTop+1.605);
const usb=usbOuter.subtract(usbInner);
// Native header-centred alignment places the PCB centre 0.0635 mm left of nominal.
controller=controller.union(usb).translate(-0.0635,0,0);
pcba=pcba.union(controller);
// Carrier JST SH receptacle envelope and tail-side solder clearance.
pcba=pcba.union(brick(4.25,6.4,3.0,26.875,21.8,pcbTop));
pcba=pcba.color("#327955");
// Exact Adafruit outline, including tabs. Eagle arcs use +90 degree bulges;
// reflection into this top-view frame reverses their bulge sign.
const b=-Math.tan(Math.PI/8);
let op=path().moveTo(35,9.04).lineTo(35,35.71)
 .bulgeArc(37.54,38.25,b).bulgeArc(40.08,35.71,b)
 .lineTo(40.08,33.17).lineTo(59.13,33.17).lineTo(59.13,35.71)
 .bulgeArc(61.67,38.25,b).bulgeArc(64.21,35.71,b)
 .lineTo(64.21,9.04).bulgeArc(61.67,6.5,b)
 .lineTo(37.54,6.5).bulgeArc(35,9.04,b).close();
// The outline was authored in editor coordinates; convert it before adding holes or glass.
let oled=op.extrude(1.6).reflect("xz").translate(0,0,displayBack);
for(const [x,y]of oledMounts)oled=oled.subtract(bore(2.5,4,x,y,displayBack-1));
const glass=brick(26.7,19.26,1.8,36.255,11.317,displayFront);
// Separate physical display face for the generic LabWired framebuffer binding.
const activeSurface=brick(21.744,10.864,0.02,38.733,13.417,displayFront+1.78);
oled=oled.union(glass).subtract(brick(21.744,10.864,0.021,38.733,13.417,displayFront+1.78));
// 3.2 mm rear-envelope bound, with mount clearances. This is a clearance
// reservation, not a claim that the electronics form a solid rectangular block.
let rear=brick(29.21,24,3.2,35,10.5,displayBack-3.2);
for(const [x,y]of oledMounts)rear=rear.subtract(bore(6,5,x,y,displayBack-4));
oled=oled.union(rear).color("#15282a");
// With the lid removed, use Wera 2069 05118120001 (4 mm hex, Ø5.7 x 60 mm blade).
// The socket engages 1.4 mm of the 1.6 mm nut, leaving 0.2 mm to the PCB.
// The Ø6 electronics reservation is not a fabricated case bore. Check a
// positive 0.10 mm minimum tool clearance; nominal radial margin is 0.15 mm.
for(let i=0;i<oledMounts.length;i++){
 const [x,y]=oledMounts[i];const tool=bore(nutDriverDiameter,nutDriverLength,x,y,displayBack-0.2-nutDriverLength);
 require("M2-driver-rear-clearance-"+i,clearance(tool,oled).gte(0.10));
}
require("pcb-outside-envelope",bbox(carrier).within({x:[69.99,70.01],y:[44.99,45.01],z:[1.59,1.61]}));
require("oled-glass-to-lid-gap",clearance(glass,lid).gte(0.5));
for(let i=0;i<glassNearSupports.length;i++)
 require("oled-glass-to-open-support-"+i,clearance(glass,glassNearSupports[i]).gte(1.0));
require("controller-to-lid-gap",clearance(controller,lid).gte(0.5));
require("pcb-assembly-to-oled-assembly-gap",clearance(pcba,oled).gte(0.5));
require("pcb-assembly-to-lid-gap",clearance(pcba,lid).gte(0.5));
// Plug overmold clearance: 16 x 8 mm, ending at the receptacle front.
const plugSweep=brick(22,16,8,-23.549,14.5,moduleTop+1.605-4);
require("usb-plug-access-to-base",clearance(plugSweep,base).gte(0.5));
require("usb-plug-access-to-lid",clearance(plugSweep,lid).gte(0.5));
const arm=assembly("esp32c3-oled-enclosure");
const bp=arm.part("base",base,{material:"petg"});
const lp=arm.part("lid",lid,{material:"petg"});
const cp=arm.part("carrier-pcba-envelope",pcba,{density:1850});
const dp=arm.part("oled-pcba-envelope",oled,{density:1850});
const sp=arm.part("oled-display-surface",activeSurface.color("#061012"),{density:2500});
frame(dp,"active-surface",[49.605,18.849,displayFront+1.78]);frame(sp,"glass-seat",[49.605,18.849,displayFront+1.78]);
arm.mate("active-surface","oled-pcba-envelope.active-surface","oled-display-surface.glass-seat","fastened");
frame(bp,"lid-seat",[35,-7.75,bodyH]);frame(lp,"base-seat",[35,-7.75,bodyH]);
arm.mate("lid-seat","base.lid-seat","lid.base-seat","fastened");

frame(lp,"display-seat",[37.54,34.01,displayFront]);frame(dp,"lid-seat",[37.54,34.01,displayFront]);
arm.mate("display-seat","lid.display-seat","oled-pcba-envelope.lid-seat","fastened");
async function s25(length){return await lib.part({family:"socket-head-cap-screw",thread:"M2.5",lengthMm:length,detail:"envelope"});}
async function n25(){return await lib.part({family:"hex-nut",thread:"M2.5",detail:"envelope"});}
async function s2(){return await lib.part({family:"socket-head-cap-screw",thread:"M2",lengthMm:8,detail:"envelope"});}
async function n2(){return await lib.part({family:"hex-nut",thread:"M2",detail:"envelope"});}
function fastener(name,shape,parent,pitch,at,length=8,axis=[0,0,1],standard="ISO4762"){
 const part=arm.part(name,shape);
 frame(parent,name,at);frame(part,"seat",at);
 arm.mate(name+"-mate",parent.name+"."+name,name+".seat","fastened",{
 fastener:{part:name,axis:axis,pitchMm:pitch,threadLengthMm:length,standard:standard,
 tool:{kind:"cylinder",lengthMm:40,diameterMm:4,label:"straight hex driver"}}});
 return part;
}
function nut(name,shape,parent,at){
 const part=arm.part(name,shape);frame(parent,name,at);frame(part,"seat",at);
 arm.mate(name+"-mate",parent.name+"."+name,name+".seat","fastened",{fastener:{part:name,axis:[0,0,-1],pitchMm:0.4,threadLengthMm:2.1,standard:"DIN934",tool:{kind:"cylinder",lengthMm:nutDriverLength,diameterMm:nutDriverDiameter,label:"Wera 2069 05118120001, 4 mm hex, 5.7 mm blade"}}});return part;
}
function spacer(name,height,x,y,z,parent){
 // Accu HHTPS female/female metal spacer. Major-diameter clearance envelope:
 // thread engagement is specified by the purchased M2.5 part and mate metadata,
 // not by interference of smooth minor/major-diameter cylinders.
 let s=hex(5,height,0,0,0);
 if(height===5) s=s.subtract(bore(2.5,height+0.2,0,0,-0.1));
 else s=s.subtract(bore(2.5,8.1,0,0,-0.1)).subtract(bore(2.5,8.1,0,0,height-8));
 const part=arm.part(name,s.translate(x,-y,z).color("#b9bdc2"),{density:8500});
 frame(parent,name,[x+2,y,z]);frame(part,"seat",[x+2,y,z]);
 arm.mate(name+"-seat",parent.name+"."+name,name+".seat","fastened");
 return part;
}
function lowerScrew(name,x,y){
 // Accu SSK-M2.5-5-A2: 90 deg head max OD5.88; length5 includes head.
 const s=path().moveTo(0,0).lineTo(2.94,0).lineTo(1.25,1.69).lineTo(1.25,5).lineTo(0,5).close().revolve()
  .subtract(hex(1.5,1.0,0,0,-0.001)).translate(x,-y,0.16).color("#b9bdc2");
 return fastener(name,s,bp,0.45,[x,y,0.16],5,[0,0,-1],"ISO10642");
}
for(let i=0;i<mounts.length;i++){
 const [x,y]=mounts[i];
 const w=arm.part("carrier-washer-"+i,bore(6.5,0.5,x,y,2.5).subtract(bore(2.7,1,x,y,2.25)),{material:"nylon"});
 frame(bp,"washer-"+i,[x+2,y,2.5]);frame(w,"seat",[x+2,y,2.5]);
 arm.mate("washer-"+i,"base.washer-"+i,w.name+".seat","fastened");
 const st=spacer("carrier-standoff-"+i,5,x,y,3.0,w);
 if(i===0){
  frame(st,"board-seat",[x+2,y,boardZ]);frame(cp,"base-seat",[x+2,y,boardZ]);
  arm.mate("carrier-seat",st.name+".board-seat","carrier-pcba-envelope.base-seat","fastened");
 }
 fastener("carrier-screw-"+i,(await s25(4)).translate(x,-y,pcbTop),cp,0.45,[x,y,pcbTop],4);
 lowerScrew("carrier-lower-screw-"+i,x,y);
}
for(let i=0;i<lidMounts.length;i++){
 const [x,y]=lidMounts[i];
 spacer("lid-standoff-"+i,25,x,y,floorT,bp);
 fastener("lid-screw-"+i,(await s25(8)).translate(x,-y,bodyH+lidT),lp,0.45,[x,y,bodyH+lidT],8);
 lowerScrew("lid-lower-screw-"+i,x,y);
}
for(let i=0;i<oledMounts.length;i++){
 const [x,y]=oledMounts[i];
 fastener("display-screw-"+i,(await s2()).translate(x,-y,bodyH+lidT),lp,0.4,[x,y,bodyH+lidT]);
 nut("display-nut-"+i,(await n2()).translate(x,-y,displayBack-1.6),dp,[x+1.7,y,displayBack]);
}
return arm.solvedModel({}, {validate:"warn"});
