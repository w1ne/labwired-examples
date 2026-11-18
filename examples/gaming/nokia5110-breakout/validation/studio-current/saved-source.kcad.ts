// Nokia 5110 Breakout enclosure, revision B. Millimetres; native STEP XY; Z upwards.
// Authoring coordinates below follow the PCB editor (+Y down). The named
// conversion reflects only constructed geometry into native +Y up. Imported
// boards retain their top face at +Z; they are never reflected or turned over.
// Native carrier and ST MB1136 bare-board geometry are retained. Other purchased
// components are identified drawing/envelope models, not vendor STEP replicas.
// Physical prototype measurements remain required; see mechanical-interface.json.
const output=param("output","assembly",{choices:["assembly","base-print","lid-print","lcd-clamp-print","sensor-clamp-print","window"]}).value;
const floorT=3,bodyH=64,lidT=2,pcbZ=23,pcbT=1.6,pcbTop=24.6;
const nucleoZ=10,nucleoT=1.59112,nucleoTop=11.59112;
const lcdZ=57,lcdT=1.6,sensorZ=51,sensorT=1.6;
const socketH=8.51; // Editable fit parameter; measure the purchased Nucleo socket.
const mounts=[[5,5],[85,5],[5,61],[85,61]];
const nucleoMounts=[[20.87,4.93],[69.13,6.2],[53.89,57]];
const lidMounts=[[-11.5,-26.5],[101.5,-26.5],[101.5,67.5],[-11.5,67.5]];
const windowMounts=[[-7,0],[43,0],[-7,50],[43,50]];
const lcdClampAxes=[[-7.3,15],[-7.3,35],[43.3,15],[43.3,35]];
const sensorClampAxes=[[48.45,19],[48.45,31],[99.55,19],[99.55,31]];
function bore(d,h,x,y,z){return cylinder(h,d/2).translate(x,y,z);}
function rounded(w,h,r,d,x,y,z){return extrudeRoundedRect(w,h,r,d).translate(x,y,z);}
function hex(af,h,x,y,z,theta=30){
 const r=af/Math.sqrt(3);
 return extrudePolygon(Array.from({length:6},(_,i)=>[r*Math.cos((theta+60*i)*Math.PI/180),r*Math.sin((theta+60*i)*Math.PI/180)]),h).translate(x,y,z);
}
// Shape transforms mutate: convert once at registration, then reuse that shape.
function editorToWorld(shape){return shape.reflect("xz");}
function frame(p,n,v){p.connector(n,{type:"frame",origin:{kind:"vec3",value:[v[0],-v[1],v[2]]},normal:[0,0,1]});}
let base=rounded(122,104,5,bodyH,45,20.5,0).subtract(rounded(117,99,2.5,bodyH,45,20.5,floorT));
// Four metal standoffs use flush underside M2.5 x6 countersunk screws.
for(const[x,y]of mounts){
 base=base.subtract(bore(2.9,4,x,y,-.5));
 const sink=path().moveTo(0,0).lineTo(3.1,0).lineTo(1.45,1.65).lineTo(0,1.65).close().revolve().translate(x,y,0);
 base=base.subtract(sink);
}
// Nucleo boss footprints avoid the adjacent CN5 pad row. Hex flats face Y.
for(const[x,y]of nucleoMounts){
 base=base.union(rounded(7,6,2,nucleoZ-floorT,x,y,floorT));
 base=base.subtract(bore(2.3,nucleoZ+1,x,y,-.5)).subtract(hex(4.4,4.1,x,y,0,0));
}
// Lid nuts are captured BELOW a 1 mm roof, with an inward side loading slot.
for(const[x,y]of lidMounts){
 base=base.union(bore(8.4,bodyH-floorT,x,y,floorT));
 base=base.subtract(bore(2.9,7,x,y,57.5)).subtract(hex(5.3,2.2,x,y,60.8));
 const sx=x<45?x:x-7;
 base=base.subtract(box(7,5.3,2.2).translate(sx,y-2.65,60.8));
}
// Mini-B receptacle stays on the intact ST-LINK portion. Unplug before disassembly.
base=base.subtract(box(18,10,10).translate(48.065,-35,9));
// Two integral cable-tie bridges retain the LCD and sonar service loops.
for(const x of[32,47]){
 let bridge=box(8,6,5).translate(x,62,3).subtract(box(4,8,2.2).translate(x+2,61,3));
 base=base.union(bridge);
}
base=base.color("#374c60");
let lid=rounded(122,104,5,lidT,45,20.5,bodyH);
for(const[x,y]of lidMounts)lid=lid.subtract(bore(2.9,4,x,y,63));
// Generous rectangular apertures avoid invented module hole/transducer centres.
lid=lid.subtract(rounded(47,47,1,4,18,25,63));
lid=lid.subtract(rounded(46.5,21,1,4,74,25,63));
for(const[x,y]of windowMounts){
 lid=lid.union(bore(8,4,x,y,60));
 lid=lid.subtract(bore(2.9,7,x,y,59.5)).subtract(hex(5.3,2.5,x,y,60));
}
// Front lips and vertical rails hold module PCB edges, not glass or transducers.
for(const [x,ys,z]of[[-7.3,[15,35],58.6],[43.3,[15,35],58.6],[48.45,[19,31],52.6],[99.55,[19,31],52.6]]){
 const isLcd=z>55,first=isLcd?7:15,length=isLcd?36:20;
 // LCD right rail points outward +X; sensor left rail points outward -X.
 const side=(x===-7.3||x===48.45)?-1:1;
 const edge=isLcd?(side<0?-4.5:40.5):(side<0?51.25:96.75);
 const inner=edge+side*.3, bx=side<0?inner-5:inner;
 let rail=box(5,length,bodyH-z).translate(bx,first,z);
 // 0.3 mm side clearance; 0.9 mm lip gives 0.6 mm nominal edge capture.
 rail=rail.union(box(.9,length,1.4).translate(side<0?inner:inner-.9,first,z));
 for(const y of ys){
  rail=rail.subtract(bore(2.3,bodyH-z+1,x,y,z-.5));
  const roof=isLcd?60:55.8;
  rail=rail.subtract(hex(4.3,roof-z,x,y,z));
 }
 lid=lid.union(rail);
}
// Join adjacent rails; no unprintable 0.15 mm crevice remains between them.
lid=lid.union(box(.15,20,5.4).translate(45.8,15,58.6));
// Positive end stops allow 0.3 mm longitudinal clearance and avoid the headers.
for(const y of[-.5,47.8])lid=lid.union(box(4,2.7,8.5).translate(0,y,55.5));
for(const y of[12,35.3])lid=lid.union(box(4,2.7,15).translate(54,y,49));
// Registration tabs have 0.3 mm lateral clearance inside the base walls.
lid=lid.union(box(1.5,16,1.2).translate(-13.2,47,62.8));
lid=lid.union(box(16,1.5,1.2).translate(72,68.2,62.8));
lid=lid.union(box(1.5,16,1.2).translate(101.7,45,62.8)).color("#dce5e8");
let window=rounded(58,58,2,2,18,25,66);
for(const[x,y]of windowMounts)window=window.subtract(bore(2.9,4,x,y,65));
window=window.material({name:"clear cast PMMA",baseColor:"#e6f4f8",opacity:.25,roughness:.1,ior:1.49});
function clamp(isLcd,side){
 const edge=isLcd?(side<0?-4.5:40.5):(side<0?51.25:96.75);
 const inner=edge+side*.3,bx=side<0?inner-5:inner, y=isLcd?7:15, len=isLcd?36:20,z=isLcd?55:49;
 const x=isLcd?(side<0?-7.3:43.3):(side<0?48.45:99.55),ys=isLcd?[15,35]:[19,31];
 let s=box(5,len,2).translate(bx,y,z).union(box(.9,len,2).translate(side<0?inner:inner-.9,y,z));
 for(const py of ys)s=s.subtract(bore(2.3,3,x,py,z-.5));
 return s.color("#7895a5");
}
const lcdClamps=[clamp(true,-1),clamp(true,1)];
const sensorClamps=[clamp(false,-1),clamp(false,1)];
if(output!=="assembly"){
 const print=assembly("nokia-"+output);
 if(output==="base-print")print.part("base",editorToWorld(base),{material:"petg"});
 if(output==="lid-print")print.part("lid",editorToWorld(lid).rotateX(180).translate(0,-41,66),{material:"petg"});
 if(output==="lcd-clamp-print")print.part("lcd-clamp",editorToWorld(lcdClamps[0]).translate(9.8,43,-55),{material:"petg"});
 if(output==="sensor-clamp-print")print.part("sensor-clamp",editorToWorld(sensorClamps[0]).translate(-45.95,35,-49),{material:"petg"});
 if(output==="window")print.part("window",editorToWorld(window).translate(11,54,-66),{density:1180});
 if(output!=="window")dfmSpec({process:"fdm",buildDirection:"+z",nozzleMm:.4,minWall:.8,maxBridgeMm:6,maxOverhangDeg:45});
 return print.model();
}
const carrier=(await lib.fromSTEP("./inputs/9a7142507be4.step")).scale([1,1,1.6/1.51]).translate(0,0,pcbZ).color("#266a50");
const nucleo=(await lib.fromSTEP("./inputs/23632172f33c.step")).scale([1,1,nucleoT/1.5]).translate(10,23,nucleoZ).color("#204d76");
const a=assembly("nokia-breakout-device");
const bp=a.part("base",editorToWorld(base),{material:"petg"});
function fixed(name,shape,parent,seat,density=1850,nativeCoordinates=false){
 const p=a.part(name,nativeCoordinates?shape:editorToWorld(shape),{density});frame(parent,name,seat);frame(p,"seat",seat);
 a.mate(name+"-fixed",parent.name+"."+name,name+".seat","fastened");return p;
}
function screwShape(d,l){
 const hd=d===2?3.8:4.5, hh=d===2?2:2.5,drive=d===2?1.5:2;
 return bore(hd,hh,0,0,0).union(bore(d,l,0,0,-l)).subtract(hex(drive,1.2,0,0,hh-1.1)).color("#b9bec5");
}
function screw(name,d,l,x,y,z,parent,up=false){
 let shape=screwShape(d,l);if(up)shape=shape.rotateX(180);
 // Standard screws use only proper rotations and translations. Threads retain
 // the ISO right-hand contract; the model uses symmetric fit envelopes.
 const p=a.part(name,shape.translate(x,-y,z),{density:7900});
 frame(parent,name,[x,y,z]);frame(p,"seat",[x,y,z]);
 a.mate(name+"-mate",parent.name+"."+name,name+".seat","fastened",{fastener:{part:name,axis:up?[0,0,-1]:[0,0,1],pitchMm:d===2?.4:.45,threadLengthMm:l,standard:"ISO4762",tool:{kind:"cylinder",lengthMm:40,diameterMm:d===2?3:4,label:"straight hex key"}}});return p;
}
function nut(name,d,x,y,z,parent,theta=30){
 const af=d===2?4:5,h=d===2?1.6:2;
 return fixed(name,hex(af,h,x,y,z,theta).subtract(bore(d,h+.2,x,y,z-.1)).color("#b9bec5"),parent,[x+af*.4,y,z+h],7900);
}
const lp=fixed("lid",lid,bp,[45,-30.25,64],1270);
const wp=fixed("lcd-window",window,lp,[-9,0,66],1180);
const np=fixed("nucleo-native-pcb",nucleo,bp,[20.87+2.5,4.93,10],1850,true);
const cp=a.part("carrier-native-pcb",carrier,{density:1850});
for(let i=0;i<nucleoMounts.length;i++){
 const[x,y]=nucleoMounts[i];nut("nucleo-nut-"+i,2,x,y,2.5,bp,0);
 screw("nucleo-screw-"+i,2,10,x,y,nucleoTop,np);
}
for(let i=0;i<mounts.length;i++){
 const[x,y]=mounts[i];
 // Wurth 970200144: AF4, length20, through M2.5. Drawing-derived envelope.
 const st=fixed("carrier-standoff-"+i,hex(4,20,x,y,3).subtract(bore(2.5,20.2,x,y,2.9)).color("#b9bec5"),bp,[x+1.8,y,3],8500);
 if(i===0){frame(st,"carrier-seat",[x+1.8,y,23]);frame(cp,"seat",[x+1.8,y,23]);a.mate("carrier-seat",st.name+".carrier-seat",cp.name+".seat","fastened");}
 screw("carrier-screw-"+i,2.5,5,x,y,pcbTop,cp);
 // ISO10642 envelope; overall length includes head, flush top lies at Z0.16.
 let cs=path().moveTo(0,0).lineTo(2.94,0).lineTo(1.25,1.69).lineTo(1.25,6).lineTo(0,6).close().revolve().subtract(hex(1.5,1,0,0,-.001)).translate(x,-y,.16).color("#b9bec5");
 const p=a.part("standoff-lower-screw-"+i,cs,{density:7900});
 frame(bp,p.name,[x,y,.16]);frame(p,"seat",[x,y,.16]);
 a.mate(p.name+"-mate","base."+p.name,p.name+".seat","fastened",{fastener:{part:p.name,axis:[0,0,-1],pitchMm:.45,threadLengthMm:6,standard:"ISO10642",tool:{kind:"cylinder",lengthMm:40,diameterMm:3,label:"underside hex key"}}});
}
for(let i=0;i<lidMounts.length;i++){
 const[x,y]=lidMounts[i];nut("lid-nut-"+i,2.5,x,y,61, bp);screw("lid-screw-"+i,2.5,8,x,y,66,lp);
}
for(let i=0;i<windowMounts.length;i++){
 const[x,y]=windowMounts[i];nut("window-nut-"+i,2.5,x,y,60.5,lp);screw("window-screw-"+i,2.5,8,x,y,68,wp);
}
const lcp=lcdClamps.map((s,i)=>a.part("lcd-clamp-"+i,editorToWorld(s),{material:"petg"}));
const scp=sensorClamps.map((s,i)=>a.part("sensor-clamp-"+i,editorToWorld(s),{material:"petg"}));
for(let i=0;i<lcdClampAxes.length;i++){
 const[x,y]=lcdClampAxes[i];nut("lcd-clamp-nut-"+i,2,x,y,58.4,lp);screw("lcd-clamp-screw-"+i,2,8,x,y,55,lcp[Math.floor(i/2)],true);
}
for(let i=0;i<sensorClampAxes.length;i++){
 const[x,y]=sensorClampAxes[i];nut("sensor-clamp-nut-"+i,2,x,y,54.2,lp);screw("sensor-clamp-screw-"+i,2,8,x,y,49,scp[Math.floor(i/2)],true);
}
// Exact Samtec TSW pin pitch/post/body/tail dimensions; simplified plastic/pin union.
function tsw(n,x,y,stepY,bodyBottom,down){
 let s=box(2.54,n*2.54,2.54).translate(x-1.27,Math.min(y,y+stepY*(n-1))-1.27,bodyBottom);
 for(let i=0;i<n;i++){
  const pz=down?bodyBottom-5.842:bodyBottom-2.54;
  s=s.union(box(.635,.635,10.922).translate(x-.3175,y+stepY*i-.3175,pz));
 }
 return s.color("#25292c");
}
for(const[n,x,y,dy,name]of[[10,69.13,32.616,-2.54,"J1-CN5"],[8,20.87,18.9,2.54,"J2-CN6"],[8,69.13,54.46,-2.54,"J3-CN9"]]){
 fixed(name,tsw(n,x,y,dy,20.46,true),cp,[x+.9,y,23],2200);
}
// ST archive does not identify socket MPN/height. These envelopes are adjustable
// and require physical measurement; holes preserve the inserted header clearance.
for(const[n,x,y,dy,name]of[[10,69.13,32.616,-2.54,"CN5-socket"],[8,20.87,18.9,2.54,"CN6-socket"],[8,69.13,54.46,-2.54,"CN9-socket"],[6,20.87,41.76,2.54,"CN8-socket"]]){
 let s=box(2.54,n*2.54,socketH).translate(x-1.27,Math.min(y,y+dy*(n-1))-1.27,nucleoTop);
 for(let i=0;i<n;i++)s=s.subtract(bore(1,6.21,x,y+dy*i,nucleoTop+socketH-6.2)).union(bore(.64,2.74,x,y+dy*i,nucleoTop-2.64));
 fixed(name,s.color("#292d31"),np,[x+.9,y,nucleoTop],2200);
}
for(const x of[13.25,74.21]){
 let s=box(5.08,48.26,2.54).translate(x-1.27,7.47,nucleoTop);
 for(let i=0;i<19;i++)for(const dx of[0,2.54])s=s.union(box(.635,.635,11.54).translate(x+dx-.3175,8.74+2.54*i-.3175,nucleoTop-3));
 fixed("morpho-"+Math.round(x*100),s.color("#2a2d30"),np,[x,10,nucleoTop],2200);
}
fixed("J4-LCD-header",tsw(8,45,16,2.54,pcbTop,false),cp,[45.9,16,pcbTop],2200);
fixed("J5-sonar-header",tsw(4,45,47,2.54,pcbTop,false),cp,[45.9,47,pcbTop],2200);
for(const[name,x,y,w,h,t]of[["R1-10k",56,54,1.6,.8,.45],["R2-18k",61,54,1.6,.8,.45],["C1-100n",38,21.08,1.6,.8,.8],["C2-100n",38,47,1.6,.8,.8],["C3-10u",38,43,2,1.25,1.25]]){
 fixed(name,box(w,h,t).translate(x-w/2,y-h/2,pcbTop).color(name[0]==="R"?"#303135":"#bda27a"),cp,[x,y,pcbTop],3100);
}
// Nucleo accessory envelopes use original footprint locations. They are not
// vendor solid models; the USB opening reserves a larger measured-plug envelope.
const usbShell=box(10,10,4.5).translate(52.065,-24, nucleoTop).subtract(box(7.8,8,2.8).translate(53.165,-24.1,nucleoTop+.7)).color("#aeb7be");
fixed("mini-b-receptacle-envelope",usbShell,np,[57.065,-16,nucleoTop],4500);
for(const[x,name,col]of[[36.745,"USER-button","#236daa"],[53.255,"RESET-button","#272b30"]]){
 let b=box(6,6,3).translate(x-3,3.2,nucleoTop).union(bore(3.5,1.5,x,6.2,nucleoTop+3));
 fixed(name,b.color(col),np,[x,6.2,nucleoTop],2200);
}
// Joy-IT revision2 envelope:45x45x14 including specified rear header. PCB
// thickness/glass/row offset are stated fit assumptions, not manufacturer CAD.
let lcd=box(45,45,lcdT).translate(-4.5,2.5,lcdZ);
let rearHeader=box(20.32,2.54,2.54).translate(7.84,3.23,54.46);
for(let i=0;i<8;i++)rearHeader=rearHeader.union(box(.635,.635,10.922).translate(9.11+2.54*i-.3175,4.5-.3175,48.618));
lcd=lcd.union(rearHeader).union(box(40,34,4.018).translate(-2,9,lcdZ+lcdT).subtract(box(36,26,.31).translate(0,13,62.318))).color("#35647b");
const lcdp=fixed("joy-it-rev2-module-envelope",lcd,lp,[-4.2,25,58.6],1900);
for(let i=0;i<2;i++){const v=[i===0?-4.2:40.2,25,57];frame(lcdp,"clamp-"+i,v);frame(lcp[i],"seat",v);a.mate("lcd-clamp-seat-"+i,lcdp.name+".clamp-"+i,lcp[i].name+".seat","fastened");}
fixed("lcd-glass-view-envelope",box(35.8,25.8,.2).translate(.1,13.1,62.318).color("#a8b6a0"),lcdp,[18,26,62.318],2500);
// Adafruit3942:45.5x20x15.5 excluding header. Transducer centres and rear
// parts are visual envelopes only; aperture clears the entire published face.
let sonar=box(45.5,20,sensorT).translate(51.25,15,sensorZ);
sonar=sonar.union(box(10.16,2.54,2.54).translate(68.92,33.73,48.46));
for(let i=0;i<4;i++)sonar=sonar.union(box(.635,9,.635).translate(70.19+2.54*i-.3175,34,49.413));
sonar=sonar.union(box(26,10,2).translate(61,20,49)).color("#235d88");
const sp=fixed("adafruit3942-pcb-envelope",sonar,lp,[51.55,25,52.6],1900);
for(let i=0;i<2;i++){const v=[i===0?51.55:96.45,25,51];frame(sp,"clamp-"+i,v);frame(scp[i],"seat",v);a.mate("sensor-clamp-seat-"+i,sp.name+".clamp-"+i,scp[i].name+".seat","fastened");}
for(let i=0;i<2;i++){
 const x=60.5+27*i;
 let can=bore(16,13.9,x,25,52.6).subtract(bore(13.4,1,x,25,65.7));
 const p=fixed("sonar-transducer-"+i,can.color("#b7c0c5"),sp,[x,25,52.6],2600);
 fixed("sonar-face-"+i,bore(13.2,.1,x,25,65.7).color("#575c62"),p,[x,25,65.7],1800);
}
// The nonuniform Z transform converts circular holes to BSplines. The current
// bbox predicate uses their conservative control hull. Final XY dimensions are
// checked with the exact re-imported STEP bounds in validation, not this hull.
require("carrier-finished-thickness",bbox(carrier).within({z:[1.59,1.61]}));
require("nucleo-native-finished-size",bbox(nucleo).within({x:[69.99,70.01],y:[82.49,82.51],z:[1.58,1.60]}));
require("lcd-to-window-clearance",clearance(lcd,window).gte(3));
require("lcd-to-carrier-clearance",clearance(lcd,carrier).gte(20));
require("sonar-to-carrier-clearance",clearance(sonar,carrier).gte(20));
const plug=box(16,24,8).translate(49.065,-45,10);
require("usb-plug-base-clearance",clearance(editorToWorld(plug),base).gte(.9));
require("carrier-to-case-clearance",clearance(carrier,base).gte(3));
return a.solvedModel({}, {validate:"warn"});
