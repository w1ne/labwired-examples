// Doom desktop enclosure, revision A. All dimensions in millimetres.
// Native routed carrier STEP; factory DevKit DXF outline; MRB3205 drawing geometry.
// Purchased component envelopes are explicitly nominal, not vendor STEP models.
// The 12 mm DevKit component allowance and LCD rear allowance are keep-out checks.
// Cable dress, printed tolerances and physical hardware remain qualification steps.
const output=param("output","assembly",{choices:["assembly","base-print","lid-print","ribbon-spacer-print"]}).value;
const floorT=2.5,bodyH=63.5,lidT=2,boardZ=10,boardT=1.6,pcbTop=11.6;
// KiCad's editor uses +Y down; a populated STEP uses world Y=-editorY and +Z.
// Manual envelopes are dimensioned below in the editor frame, then converted
// once at every geometry, connector and requirement boundary. Native geometry
// keeps its component-side +Z. No populated vendor model is reflected.
const worldShapes=new Map();
function world(shape){if(!worldShapes.has(shape))worldShapes.set(shape,shape.reflect("xz"));return worldShapes.get(shape);}
function worldPoint(v){return[v[0],-v[1],v[2]];}
const mounts=[[4,4],[76,4],[4,96],[76,96]];
const lidMounts=[[-3,-3],[83,-3],[-3,103],[83,103]];
const lcdX=11.2,lcdY=4.635,lcdFront=59.5,lcdBack=57.9;
// Dimensions are back-view on the vendor drawing; mirror X for this front-view frame.
const lcdMounts=[[lcdX+3.40,lcdY+3],[lcdX+54.18,lcdY+3],[lcdX+3.40,lcdY+87.65],[lcdX+54.18,lcdY+87.65]];
function rounded(w,h,r,z,x,y){return extrudeRoundedRect(w,h,r,z).translate(x,y,0);}
function bore(d,h,x,y,z){return cylinder(h,d/2).translate(x,y,z);}
function hex(af,h,x,y,z){const r=af/Math.sqrt(3);return extrudePolygon(Array.from({length:6},(_,i)=>[r*Math.cos((30+60*i)*Math.PI/180),r*Math.sin((30+60*i)*Math.PI/180)]),h).translate(x,y,z);}
function frame(p,n,v){p.connector(n,{type:"frame",origin:{kind:"vec3",value:worldPoint(v)},normal:[0,0,1]});}
let base=rounded(100,120,5,bodyH,40,50).subtract(rounded(95,115,2.5,bodyH,40,50).translate(0,0,floorT));
for(const[x,y]of mounts){
 base=base.subtract(bore(2.9,floorT+1,x,y,-.5));
 const sink=path().moveTo(0,0).lineTo(3.1,0).lineTo(1.45,1.65).lineTo(0,1.65).close().revolve().translate(x,y,0);
 base=base.subtract(sink);
}
// Captive M3 nuts slide in from inside the empty base, before the PCB is fitted.
for(const[x,y]of lidMounts){
 base=base.union(bore(10,bodyH-floorT,x,y,floorT));
 base=base.subtract(hex(5.8,3,x,y,bodyH-6));
 base=base.subtract(bore(3.4,11,x,y,bodyH-10));
 const inward=y<50?y:y-9;
 base=base.subtract(box(5.8,9,3).translate(x-2.9,inward,bodyH-6));
}
// USB opening keeps the rear wall closed above the cable. The45-degree roof
// leaves a6 mm bridge, within the declared FDM process. The plug allowance is
//28 mm wide x16 mm high; it is a design allowance, not a vendor plug STEP.
const usbOpening=extrudePolygon([[-15,0],[15,0],[15,18],[3,30],[-3,30],[-15,18]],18).rotateX(90).translate(36.83,117.2,16);
base=base.subtract(usbOpening).color("#293f50");
let lid=rounded(100,120,5,lidT,40,50).translate(0,0,bodyH);
for(const[x,y]of lidMounts)lid=lid.subtract(bore(3.4,lidT+2,x,y,bodyH-1));
for(const[x,y]of lcdMounts)lid=lid.subtract(bore(2.9,lidT+2,x,y,bodyH-1));
// Full glass recess gives 0.9 mm nominal axial gap above the touch surface.
lid=lid.subtract(box(55.24,77.9,2).translate(lcdX+.99,lcdY+6.42,bodyH-1));
lid=lid.subtract(rounded(49.6,65.8,.5,4,lcdX+28.84,lcdY+42.62).translate(0,0,bodyH-1));
// Registration tabs have 0.3 mm nominal lateral clearance.
lid=lid.union(box(1.5,20,1.2).translate(-7.2,40,bodyH-1.2));
lid=lid.union(box(1.5,20,1.2).translate(85.7,40,bodyH-1.2));
lid=lid.union(box(20,1.5,1.2).translate(30,-7.2,bodyH-1.2)).color("#d8e1e5");
// MRB3205 rear header has7.0 mm nominal exposed pins. IDSD accepts5.59..6.22
// mm insertion. This1.1 mm spacer sets nominal insertion to5.9 mm. Verify the
// actual pin length and printed thickness before mating; it must not bottom out.
const ribbonSpacerT=1.1; // Editable measured stack dimension; nominal exposed pin7.0 minus insertion5.9.
const ribbonSpacerPrint=box(45,6,ribbonSpacerT).subtract(box(42,3.6,ribbonSpacerT+.2).translate(1.5,1.2,-.1));
require("ribbon-depth-stop-height",bbox(ribbonSpacerPrint).within({z:[.78,1.41]}));
const ribbonSpacer=ribbonSpacerPrint.translate(17.5,lcdY-.33,lcdBack-2.54-ribbonSpacerT);
if(output!=="assembly"){
 const a=assembly("doom-"+output);
 a.part(output,world(output==="base-print"?base:output==="lid-print"?lid.rotateX(180).translate(0,100,bodyH+lidT):ribbonSpacerPrint),{material:"petg"});
 dfmSpec({process:"fdm",buildDirection:"+z",nozzleMm:.4,minWall:1,maxBridgeMm:10,maxOverhangDeg:45});
 return a.model();
}
// KiCad exports the 1.51 mm laminate core; scale only Z to finished 1.60 mm.
// Temporary editor-frame reflection is reversed by world(pcba). Thus the
// imported PCB reaches the assembly with native Y and native component-side Z.
const carrier=(await lib.fromSTEP("./inputs/doom-carrier-board.step")).scale([1,1,1.6/1.51]).translate(0,0,boardZ).reflect("xz");
// Batch independent physical bodies; retain one final PCBA, not every union prefix.
const carrierComponents=[];
for(const x of[25.4,48.26]){
 // Samtec SSW-122-01-G-S: 2.41 REF width; 56.39 +/-0.25 length.
 let socket=box(2.41,56.39,8.51).translate(x-1.205,37.135,pcbTop);
 const sockets=[],tails=[];
 for(let i=0;i<22;i++){
  const y=38.66+2.54*i;
  sockets.push(bore(1,6.3,x,y,pcbTop+2.31));
  tails.push(bore(.64,2.74,x,y,pcbTop-2.64));
 }
 socket=socket.subtract(...sockets).union(...tails);
 carrierComponents.push(socket);
}
let displayHeader=box(43.18,5.08,2.54).translate(18.41,8.19,pcbTop);
const displayPins=[];
for(let i=0;i<17;i++)for(const y of[9.46,12])displayPins.push(box(.635,.635,10.922).translate(19.68+2.54*i-.3175,y-.3175,pcbTop-2.54));
displayHeader=displayHeader.union(...displayPins);
carrierComponents.push(displayHeader);
const resistorPositions=[["R1", 53.34, 46.28], ["R2", 53.34, 48.82], ["R3", 20.32, 69.14], ["R4", 20.32, 46.28], ["R5", 20.32, 48.82], ["R6", 20.32, 51.36], ["R7", 20.32, 53.9], ["R8", 20.32, 66.6], ["R9", 20.32, 74.22], ["R10", 20.32, 76.76], ["R11", 20.32, 79.3], ["R12", 20.32, 81.84], ["R13", 20.32, 84.38], ["R14", 20.32, 86.92], ["R15", 20.32, 56.44], ["R16", 20.32, 58.98], ["R17", 20.32, 61.52], ["R18", 20.32, 64.06], ["R19", 53.34, 81.84], ["R20", 53.34, 61.52], ["R21", 53.34, 58.98], ["R22", 67.0, 40.0], ["R23", 67.0, 44.0], ["R24", 67.0, 48.0], ["R25", 67.0, 52.0]];
for(const[,x,y]of resistorPositions)carrierComponents.push(box(1.6,.8,.55).translate(x-.8,y-.4,pcbTop));
const capacitorPositions=[["C1", 65.0, 28.0], ["C2", 65.0, 32.0]];
// TDK C2012 bodies: maximum manufacturer tolerance 2.2 x1.45 x1.45 mm.
for(const[,x,y]of capacitorPositions)carrierComponents.push(box(2.2,1.45,1.45).translate(x-1.1,y-.725,pcbTop));
const pcba=carrier.union(...carrierComponents).color("#285f49");
// Espressif v1.0 DXF exact outline: 25.4 x62.865, not the rounded PDF label62.74.
const devkitBottom=pcbTop+8.51+2.54,devkitTop=devkitBottom+1.6;
let devkit=rounded(25.4,62.865,.5,1.6,36.83,68.5275).translate(0,0,devkitBottom);
const devkitBores=[],devkitHeaders=[];
for(const x of[25.4,48.26]){
 const header=box(2.54,55.88,2.54).translate(x-1.27,37.39,pcbTop+8.51);
 const pins=[];
 for(let i=0;i<22;i++){
  const y=38.66+2.54*i;
  devkitBores.push(bore(.95,2,x,y,devkitBottom-.2));
  pins.push(box(.635,.635,10.922).translate(x-.3175,y-.3175,pcbTop+8.51-5.842));
 }
 devkitHeaders.push(header.union(...pins));
}
devkit=devkit.subtract(...devkitBores).union(...devkitHeaders).color("#303a40");
const devkitAllowance=box(25.4,62.865,12).translate(24.13,37.095,devkitTop);
let lcd=box(57.6,90.73,1.6).translate(lcdX,lcdY,lcdBack);
for(const[x,y]of lcdMounts)lcd=lcd.subtract(bore(3.4,2,x,y,lcdBack-.2));
// Adhesive, LCD and touch are the drawing's0.5 +2.4 +1.2 mm stack.
lcd=lcd.union(box(54.64,77.3,4.1).translate(lcdX+1.29,lcdY+6.72,lcdFront));
let lcdHeader=box(43.18,5.08,2.54).translate(18.41,lcdY+.13,lcdBack-2.54);
const lcdPins=[];
for(let i=0;i<17;i++)for(const y of[lcdY+1.4,lcdY+3.94])lcdPins.push(box(.635,.635,9.54).translate(19.68+2.54*i-.3175,y-.3175,lcdBack-9.54));
lcdHeader=lcdHeader.union(...lcdPins);
lcd=lcd.union(lcdHeader).color("#173f4b");
// Reserved rear electronics volume is checked, not presented as a manufactured part.
let lcdRearAllowance=box(57.6,90.73,9.54).translate(lcdX,lcdY,lcdBack-9.54);
for(const[x,y]of lcdMounts)lcdRearAllowance=lcdRearAllowance.subtract(bore(12,10,x,y,lcdBack-9.8));
// Samtec IDSD double-row length is17*2.54+1.50=44.68 mm. The+0.48
// formula is for single-row IDSS and does not apply to this cable.
function idsd(y,z,down){
 let shape=box(44.68,5.08,9.27).translate(17.66,y-2.54,down?z-9.27:z);
 const sockets=[];
 for(let i=0;i<17;i++)for(const row of[-1.27,1.27])sockets.push(box(.95,.95,6.3).translate(19.68+2.54*i-.475,y+row-.475,down?z-6.2:z-.1));
 return shape.subtract(...sockets).color("#343a3e");
}
const cableLow=idsd(10.73,pcbTop+2.54,false);
const cableHigh=idsd(lcdY+2.67,lcdBack-2.54-ribbonSpacerT,true);
require("lower-ribbon-connector-to-base",clearance(world(cableLow),world(base)).gte(.5));
require("upper-ribbon-connector-to-base",clearance(world(cableHigh),world(base)).gte(.5));
require("ribbon-connectors-to-devkit-reserve",clearance(world(cableHigh),world(devkitAllowance)).gte(2));
const usbPlugAllowance=box(28,30,16).translate(22.83,99.96,16.5);
require("carrier-to-lid",clearance(world(pcba),world(lid)).gte(1));
require("devkit-height-reserve-to-display",clearance(world(devkitAllowance),world(lcdRearAllowance)).gte(2));
require("devkit-to-base",clearance(world(devkit),world(base)).gte(.5));
require("display-to-base",clearance(world(lcd),world(base)).gte(.5));
require("usb-plug-access",clearance(world(usbPlugAllowance),world(base)).gte(.5));
require("touch-glass-to-lid",clearance(world(lcd),world(lid)).gte(.3));
const a=assembly("esp32s3-doom-desktop");
function part(name,shape,options){return a.part(name,world(shape),options);}
const bp=part("base",base,{material:"petg"});
const lp=part("lid",lid,{material:"petg"});
const cp=part("carrier-pcba",pcba,{density:1850});
const dp=part("esp32s3-devkitc-v1-outline-and-headers",devkit,{density:1850});
// Registration witnesses refer to real native F.Cu pad centres, not a visual guess.
frame(cp,"native-J1-1",[25.4,38.66,pcbTop]);
frame(cp,"native-J1-2",[25.4,41.2,pcbTop]);
frame(cp,"native-J2-1",[48.26,38.66,pcbTop]);
const sp=part("mrb3205-drawing-envelope",lcd,{density:2000});
function fixed(n,parent,child,v){frame(parent,n,v);frame(child,"seat-"+n,v);a.mate(n,parent.name+"."+n,child.name+".seat-"+n,"fastened");}
fixed("lid-seat",bp,lp,[40,-8.75,bodyH]);
const cableLowPart=part("idsd-carrier-end-envelope",cableLow,{density:1600});
const cableHighPart=part("idsd-display-end-envelope",cableHigh,{density:1600});
fixed("ribbon-carrier-seat",cp,cableLowPart,[20.68,10.73,pcbTop+2.54]);
const cableSpacerPart=part("display-ribbon-depth-spacer",ribbonSpacer,{material:"petg"});
fixed("ribbon-depth-spacer-seat",sp,cableSpacerPart,[20.68,lcdY+4.94,lcdBack-2.54]);
fixed("ribbon-display-seat",cableSpacerPart,cableHighPart,[20.68,lcdY+4.94,lcdBack-2.54-ribbonSpacerT]);
frame(cp,"devkit-seat",[26.4,38.66,pcbTop+8.51]);frame(dp,"socket-seat",[26.4,38.66,pcbTop+8.51]);
a.mate("devkit-sockets","carrier-pcba.devkit-seat",dp.name+".socket-seat","fastened",{fit:{kind:"press",part:dp.name,axis:[0,0,1]}});
async function screw(thread,l){return await lib.part({family:"socket-head-cap-screw",thread,lengthMm:l,detail:"envelope"});}
function fastener(n,s,parent,v,l,thread,axis=[0,0,1],standard="ISO4762"){
 // Standard fasteners keep their catalog handedness; only their location changes.
 const p=a.part(n,s.translate(0,-2*v[1],0));frame(parent,n,v);frame(p,"seat",v);
 a.mate(n+"-mate",parent.name+"."+n,n+".seat","fastened",{fastener:{part:n,axis,pitchMm:thread==="M3"?.5:.45,threadLengthMm:l,standard,tool:{kind:"cylinder",lengthMm:45,diameterMm:thread==="M3"?5:4,label:"straight hex driver"}}});return p;
}
for(let i=0;i<mounts.length;i++){
 const[x,y]=mounts[i];
 const w=part("carrier-washer-"+i,bore(6.5,.5,x,y,floorT).subtract(bore(2.7,1,x,y,2.25)),{material:"nylon"});fixed("washer-"+i,bp,w,[x+2,y,floorT]);
 const st=part("carrier-standoff-"+i,hex(5,7,x,y,3).subtract(bore(2.5,7.2,x,y,2.9)),{density:8500});fixed("standoff-"+i,w,st,[x+2,y,3]);
 if(i===0)fixed("carrier-seat",st,cp,[x+2,y,boardZ]);
 fastener("carrier-upper-screw-"+i,(await screw("M2.5",5)).translate(x,y,pcbTop),cp,[x,y,pcbTop],5,"M2.5");
 const lower=path().moveTo(0,0).lineTo(2.94,0).lineTo(1.25,1.69).lineTo(1.25,5).lineTo(0,5).close().revolve().subtract(hex(1.5,1,0,0,-.001)).translate(x,y,.16);
 fastener("carrier-lower-screw-"+i,lower,bp,[x,y,.16],5,"M2.5",[0,0,-1],"ISO10642");
}
for(let i=0;i<lidMounts.length;i++){
 const[x,y]=lidMounts[i];
 const n=part("lid-nut-"+i,hex(5.5,2.4,x,y,bodyH-6).subtract(bore(3,3,x,y,bodyH-6.2)),{density:7850});fixed("captive-nut-"+i,bp,n,[x+2,y,bodyH-6]);
 fastener("lid-screw-"+i,(await screw("M3",10)).translate(x,y,bodyH+lidT),lp,[x,y,bodyH+lidT],10,"M3");
}
for(let i=0;i<lcdMounts.length;i++){
 const[x,y]=lcdMounts[i];
 const st=part("display-spacer-"+i,bore(5,4,x,y,lcdFront).subtract(bore(2.7,4.2,x,y,lcdFront-.1)),{material:"nylon"});fixed("display-spacer-seat-"+i,lp,st,[x+2,y,bodyH]);
 if(i===0)fixed("display-seat",st,sp,[x+2,y,lcdFront]);
 const w=part("display-washer-"+i,bore(6.5,.5,x,y,lcdBack-.5).subtract(bore(2.7,1,x,y,lcdBack-.75)),{material:"nylon"});fixed("display-washer-seat-"+i,sp,w,[x+2,y,lcdBack]);
 const n=part("display-nut-"+i,hex(5,2,x,y,lcdBack-2.5).subtract(bore(2.5,2.4,x,y,lcdBack-2.7)),{density:7850});fixed("display-nut-seat-"+i,w,n,[x+2,y,lcdBack-.5]);
 fastener("display-screw-"+i,(await screw("M2.5",12)).translate(x,y,bodyH+lidT),lp,[x,y,bodyH+lidT],12,"M2.5");
}
return a.solvedModel({}, {validate:"warn"});
