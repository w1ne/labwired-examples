const W=I.case.width,H=I.case.height,D=I.case.depth,wall=I.case.wall,seam=I.case.seamZ,gap=I.case.seamGap;
const frontFloor=D-wall;
const F=C.fasteners,S=C.switch;
const pcbTop=I.pcb.center[2]+I.pcb.thickness/2;
const pcbBottom=I.pcb.center[2]-I.pcb.thickness/2;
const selected=param('pressedControl','rest',{choices:['rest','btn-a','btn-b','btn-select','btn-start','btn-up','btn-down','btn-left','btn-right']});
const plungerAdjustment=param('plungerAdjustmentMm','0.0',{choices:['-0.4','-0.2','0.0','0.2','0.4']});
const stroke=param('travelCase','nominal',{choices:['nominal','maximum']});
const selectedId=selected.value;
const travel=stroke.value==='maximum'?S.pretravelMm.maximum:S.pretravelMm.nominal;
const press=selectedId==='rest'?0:S.freeGapMm+travel;
const compression=selectedId==='rest'?0:travel;
const a=assembly('labwired-gameboy-assembly-detail');
function rounded(w,h,r,z,t,x=0,y=0){return extrudeRoundedRect(w,h,r,t).translate(x,y,z);}
function cross(span,bar,z,t,x,y){return extrudeRect(span,bar,t).union(extrudeRect(bar,span,t)).translate(x,y,z);}
function hex(af){const r=af/Math.sqrt(3);let h=path();for(let i=0;i<6;i++){const q=(30+i*60)*Math.PI/180;h=i?h.lineTo(r*Math.cos(q),r*Math.sin(q)):h.moveTo(r*Math.cos(q),r*Math.sin(q));}return h.close();}
function addFixed(name,shape,at,material='abs',parent=rear,parentName='rear-shell',options={}){
  const p=a.part(name,shape,{material});
  parent.connector(name,{type:'frame',origin:{kind:'vec3',value:at}});
  p.connector('mount',{type:'frame',origin:{kind:'vec3',value:at}});
  a.mate(name,`${parentName}.${name}`,`${name}.mount`,'fastened',options);
  return p;
}
// Nut traps load horizontally before installing the carrier. The upper roof takes the clamp load.
function captiveBoss(radius,top,nutTop,holeBottom,slotDirection){
  const af=F.nutAcrossFlatsMm+2*F.nutFlatClearancePerSideMm;
  let b=cylinder(nutTop+0.1-wall,radius).cutout(hex(af),{face:'top',depth:F.nutHeightMm+F.nutAxialClearanceMm+0.1});
  b=b.union(cylinder(top-nutTop+0.05,radius).translate(0,0,nutTop-wall));
  const slot=box(af,radius+0.2,F.nutHeightMm+F.nutAxialClearanceMm,false)
    .translate(-af/2,slotDirection<0?-radius-0.1:-0.1,nutTop-F.nutHeightMm-F.nutAxialClearanceMm-wall);
  return b.subtract(slot).hole({byNormal:'Z',atZ:top-wall+0.05},{u:0,v:0,diameter:F.clearanceHoleDiameterMm,depth:top-holeBottom});
}
let back=rounded(W,H,I.case.radius,0,seam,0,H/2)
  .subtract(rounded(W-2*wall,H-2*wall,I.case.radius-wall,wall,seam+1,0,H/2))
  .subtract(rounded(53.6,65.6,4.3,-0.5,4,0,47));
for(const f of I.caseFasteners){back=back.union(captiveBoss(F.caseBossRadiusMm,seam,F.caseNutTopZ,F.caseBoreBottomZ,f.at[1]>H/2?-1:1).translate(f.at[0],f.at[1],wall-0.05));}
for(const p of I.pcb.mounts){back=back.union(captiveBoss(F.pcbBossRadiusMm,pcbBottom,F.pcbNutTopZ,p.at[1]<H/2?F.pcbBottomBoreBottomZ:F.pcbTopBoreBottomZ,p.at[1]>H/2?-1:1).translate(p.at[0],p.at[1],wall-0.05));}
const usbY=P.moduleCenter[1]+C.module.boardLengthMm/2;
const usb=C.directUsb;
const usbCenterZ=pcbBottom-P.header.bodyHeightMm-C.module.boardThicknessMm-usb.receptacleHeightMm/2;
// This access opening accepts the inspected male overmold. It removes the internal extension.
back=back.subtract(box(usb.openingMm[0],16,usb.openingMm[1],false)
  .translate(-usb.openingMm[0]/2,H-14,usbCenterZ-usb.openingMm[1]/2));
const rear=a.part('rear-shell',back.finish('abs',{color:'#c7c5bc'}),{material:'abs'});

let face=rounded(W,H,I.case.radius,seam+gap,D-seam-gap,0,H/2)
  .subtract(rounded(W-2*wall,H-2*wall,I.case.radius-wall,seam+gap-0.1,frontFloor-seam-gap+0.1,0,H/2));
const lcd=I.display,L=C.displayStack;
face=face.subtract(rounded(lcd.window[0],lcd.window[1],1.1,26,7,lcd.center[0],lcd.center[1]));
for(const f of I.caseFasteners){
  const boss=cylinder(frontFloor-seam+0.1,3.8).hole('top',{u:0,v:0,diameter:2.8,depth:'through'}).translate(f.at[0],f.at[1],seam);
  face=face.union(boss);
  face=face.hole({byNormal:'Z',atZ:D,near:[f.at[0],f.at[1],D]},{at:[f.at[0],f.at[1],D],axis:[0,0,-1],diameter:2.8,depth:D-seam+1,counterbore:{diameter:5.1,depth:D-F.caseHeadSeatZ}});
}
for(const b of I.controls){const x=b.center[0],y=b.center[1];
 if(b.kind==='cross')face=face.subtract(cross(b.span+2*S.dpadOpeningClearancePerSideMm,b.bar+2*S.dpadOpeningClearancePerSideMm,26,8,x,y));
 if(b.kind==='round')face=face.subtract(cylinder(8,(b.diameter+0.6)/2).translate(x,y,26));
 if(b.kind==='pill')face=face.subtract(rounded(b.size[0]+0.6,b.size[1]+0.6,(b.size[1]+0.6)/2,26,8,x,y));
}
const speaker={...I.speaker,center:C.speakerReservation.center};
for(let i=0;i<speaker.slots;i++)face=face.subtract(rounded(1.6,13,0.8,26,8,speaker.center[0]-6+i*3,speaker.center[1]));
for(const side of [-1,1])face=face.union(box(9.2,12,1.9,false).translate(side>0?33.5:-42.7,101,20.5));
const front=addFixed('front-shell',face.finish('abs',{color:'#e0ddd3'}),[38,136,seam+gap/2]);
const cover=rounded(53,65,4,0.2,2,0,47).subtract(rounded(14,2,0.8,-0.1,0.65,0,21));
const coverPart=addFixed('battery-service-cover',cover.finish('abs',{color:'#b9b7af'}),[26.6,47,1.2]);
let bezel=rounded(lcd.bezel[0],lcd.bezel[1],6,30.05,1.5,0,107).subtract(rounded(lcd.window[0],lcd.window[1],1,29.9,3,0,107));
for(const f of I.caseFasteners.filter(f=>f.at[1]>H/2))bezel=bezel.subtract(cylinder(3,F.bezelAccessDiameterMm/2).translate(f.at[0],f.at[1],29.9));
addFixed('display-bezel',bezel.finish('abs',{color:'#44454a'}),[32,107,30.03],'abs',front,'front-shell');
const lcdBoard=addFixed('lcd1-pcb-envelope',rounded(lcd.outline[0],lcd.outline[1],1.4,L.pcbBottomZ,L.pcbThicknessMm,0,107).finish('abs',{color:'#194a36'}),[34.5,107,L.pcbBottomZ-0.1],'abs',front,'front-shell');
const displayFrame=rounded(52.4,40.8,1,L.frameBottomZ,L.frameHeightMm,0,107).subtract(rounded(lcd.activeArea[0]+0.4,lcd.activeArea[1]+0.4,0.3,L.frameBottomZ-0.1,L.frameHeightMm+0.3,0,107));
addFixed('lcd1-frame-envelope',displayFrame.finish('abs',{color:'#171b1b'}),[25.5,107,L.frameBottomZ-0.05],'abs',lcdBoard,'lcd1-pcb-envelope');
addFixed('lcd1-active-glass',rounded(lcd.activeArea[0],lcd.activeArea[1],0.2,L.glassBottomZ,L.glassThicknessMm,0,107).material({baseColor:'#829d58',roughness:0.22}),[0,107,L.glassBottomZ-0.1],'abs',lcdBoard,'lcd1-pcb-envelope');

// Carrier outline uses the shared rounded profile; its KiCad tessellation and exact header pads are recorded in derived-interfaces.json.
let pcb=rounded(I.pcb.width,I.pcb.height,I.pcb.radius,pcbBottom,I.pcb.thickness,I.pcb.center[0],I.pcb.center[1]);
for(const f of I.caseFasteners)pcb=pcb.subtract(cylinder(3,4.3).translate(f.at[0],f.at[1],pcbBottom-0.2));
pcb=pcb.holes({byNormal:'Z',atZ:pcbTop},{positions:I.pcb.mounts.map(p=>({u:p.at[0],v:p.at[1]-I.pcb.center[1]})),diameter:I.pcb.mountHoleDiameter,depth:'through'});
pcb=pcb.holes({byNormal:'Z',atZ:pcbTop},{positions:P.pins.map(p=>({u:p.at[0],v:p.at[1]-I.pcb.center[1]})),diameter:P.header.carrierHoleDiameterMm,depth:'through'});
for(const p of P.j1.pins)pcb=pcb.hole({byNormal:'Z',atZ:pcbTop},{at:[p.at[0],p.at[1],pcbTop],axis:[0,0,-1],diameter:p.drill,depth:'through'});
const carrier=addFixed('main-pcb-envelope',pcb.finish('abs',{color:'#24583c'}),[-29,132,pcbBottom]);

// J1 placement and all eight terminal centers come from the final native PCB export.
const j=P.j1,jlo=j.bodyBoundsCaseMm[0],jhi=j.bodyBoundsCaseMm[1],jc=[(jlo[0]+jhi[0])/2,(jlo[1]+jhi[1])/2];
const jp=j.pins[0],jrY=jp.at[1],jrowCenterX=(j.pins[0].at[0]+j.pins[7].at[0])/2;
let jbody=box(jhi[0]-jlo[0],jhi[1]-jlo[1],j.matedHeightMm,false).translate(jlo[0],jlo[1],pcbTop);
const jtail=box(j.terminalSquareMm,j.terminalSquareMm,j.terminalTailLengthMm+0.1,false)
 .translate(jp.at[0]-j.terminalSquareMm/2,jrY-j.terminalSquareMm/2,pcbTop-j.terminalTailLengthMm)
 .patternLinear({count:8,direction:[1,0,0],spacing:j.pitchMm});
jbody=jbody.union(jtail);
const jpart=addFixed('J1-mated-header-envelope',jbody.finish('abs',{color:'#e3dfd3'}),[jc[0],jc[1],pcbTop],'abs',carrier,'main-pcb-envelope');
const jaccess=C.connectorAccess.J1;
addFixed('J1-wire-exit-reservation',box(jhi[0]-jlo[0],jhi[1]-jlo[1],jaccess.wireExitHeightMm,false).translate(jlo[0],jlo[1],pcbTop+j.matedHeightMm).finish('abs',{color:'#c9a15c'}),[jc[0],jc[1],pcbTop+j.matedHeightMm],'abs',jpart,'J1-mated-header-envelope');
const jsolder=box(16,1.8,jaccess.solderAllowanceMm,false).translate(jrowCenterX-8,jrY-0.9,pcbBottom-jaccess.solderAllowanceMm)
 .holes('top',{positions:j.pins.map(p=>({u:p.at[0]-jrowCenterX,v:0})),diameter:0.8,depth:'through'});
addFixed('J1-solder-envelope',jsolder.finish('steel',{color:'#777d83'}),[jrowCenterX,jrY,pcbBottom],'mild-steel',carrier,'main-pcb-envelope');

// A removable support plate shares the two lower PCB screws; it does not add holes to the PCB.
let support=rounded(78,64,3,S.supportPlateBottomZ,S.supportPlateThicknessMm,0,44);
const jw=jaccess.supportWindowMarginsMm;
support=support.subtract(box(jhi[0]-jlo[0]+2*jw.x,jhi[1]-jlo[1]+jw.lowerY+jw.upperY,S.supportPlateThicknessMm+0.4,false)
 .translate(jlo[0]-jw.x,jlo[1]-jw.lowerY,S.supportPlateBottomZ-0.2));
for(const f of I.caseFasteners.filter(f=>f.at[1]<H/2))support=support.subtract(cylinder(3,4.3).translate(f.at[0],f.at[1],23));
for(const p of I.pcb.mounts.filter(p=>p.at[1]<H/2)){
 support=support.union(cylinder(S.supportPlateBottomZ-pcbTop+0.1,S.supportFootRadiusMm).translate(p.at[0],p.at[1],pcbTop));
 support=support.hole({byNormal:'Z',atZ:24.8},{at:[p.at[0],p.at[1],24.8],axis:[0,0,-1],diameter:2.8,depth:'through'});
}
support=support.subtract(cylinder(3,speaker.diameter/2+0.5).translate(speaker.center[0],speaker.center[1],23));
for(const x of [-38,38])support=support.union(box(1.8,42,8.3,false).translate(x-0.9,32,pcbTop));
for(const b of I.controls.filter(b=>b.kind!=='cross')){
 const height=26.2-S.roundButtonStopTravelMm-24.8;
 support=support.union(cylinder(height+0.1,3.8).translate(b.center[0],b.center[1],24.7));
}
for(const sw of P.switches)support=support.subtract(cylinder(5,S.plungerRadiusMm+S.guideRadialClearanceMm).translate(sw.center[0],sw.center[1],22.8));
const dp=I.controls.find(b=>b.kind==='cross');
support=support.union(cylinder(0.4,1).translate(dp.center[0],dp.center[1],24.7)).union(sphere(0.8).translate(dp.center[0],dp.center[1],S.dpadPivotCenterZ));
const supportPart=addFixed('button-support',support.finish('abs',{color:'#a6a198'}),[-29,16,pcbTop],'abs',carrier,'main-pcb-envelope');

// Purchased switch bodies/actuators are nominal envelopes, not reconstructed switch internals.
for(const sw of P.switches){const x=sw.center[0],y=sw.center[1],c=sw.id===selectedId?compression:0;
 const body=box(6,6,3.4,false).hole('top',{u:0,v:0,diameter:3.6,depth:1}).translate(x-3,y-3,pcbTop);
 const swPart=addFixed(`${sw.reference}-body`,body.finish('abs',{color:'#303238'}),[x,y,pcbTop],'abs',carrier,'main-pcb-envelope');
 addFixed(`${sw.reference}-actuator`,cylinder(0.9,1.75).translate(x,y,pcbTop+3.4-c).finish('abs',{color:'#b4aea1'}),[x,y,pcbTop+3.4-c],'abs',swPart,`${sw.reference}-body`);
}
const tipBottom=pcbTop+S.heightMm+S.freeGapMm-Number(plungerAdjustment.value);
function stem(x,y,top){return cylinder(top-tipBottom-S.plungerRadiusMm+0.1,S.plungerRadiusMm).translate(x,y,tipBottom+S.plungerRadiusMm).union(sphere(S.plungerRadiusMm).translate(x,y,tipBottom+S.plungerRadiusMm));}
for(const b of I.controls){const x=b.center[0],y=b.center[1];let shape;
 if(b.kind==='cross'){
   shape=cross(b.span,b.bar,26.5,5.8,x,y).union(cylinder(S.dpadFlangeThicknessMm,S.dpadFlangeRadiusMm).translate(x,y,S.dpadFlangeBottomZ));
   for(const sw of P.switches.filter(sw=>['btn-up','btn-down','btn-left','btn-right'].includes(sw.id)))shape=shape.union(stem(sw.center[0],sw.center[1],26));
   const s=P.switches.find(sw=>sw.id===selectedId);
   if(s&&['btn-up','btn-down','btn-left','btn-right'].includes(selectedId)){
     const dx=s.center[0]-x,dy=s.center[1]-y;
     const radius=Math.hypot(dx,dy),vertical=S.dpadPivotCenterZ-tipBottom-S.plungerRadiusMm;
     // Solve the sphere-tip descent exactly; pretravel poses are imposed geometry, not spring dynamics.
     const angle=(Math.asin((vertical+press)/Math.hypot(radius,vertical))-Math.atan2(vertical,radius))*180/Math.PI;
     shape=shape.rotate([dy,-dx,0],-angle,[x,y,S.dpadPivotCenterZ]);
   }
 }else if(b.kind==='round'){
   shape=cylinder(5,b.diameter/2).translate(x,y,27.3).union(cylinder(1.2,b.diameter/2+1.5).translate(x,y,26.2)).union(stem(x,y,26.3));
 }else{
   shape=rounded(b.size[0],b.size[1],b.size[1]/2,27.3,4.1,x,y).union(rounded(b.size[0]+1.8,b.size[1]+1.8,(b.size[1]+1.8)/2,26.2,1.2,x,y)).union(stem(x,y,26.3));
 }
 if(b.kind!=='cross'&&b.id===selectedId)shape=shape.translate(0,0,-press);
 addFixed(b.id,shape.finish('abs',{color:b.kind==='round'?'#8c2b52':b.kind==='cross'?'#242830':'#6a6b71'}),[x,y,26.2],'abs',supportPart,'button-support');
}

// Nominal Samtec headers: full untrimmed pin envelopes, indexed by the actual carrier pads.
const m=C.module,h=P.header,mx=P.moduleCenter[0],my=P.moduleCenter[1],moduleFront=pcbBottom-h.bodyHeightMm,moduleBack=moduleFront-m.boardThicknessMm;
let moduleBoard=box(m.boardWidthMm,m.boardLengthMm,m.boardThicknessMm,false).translate(mx-m.boardWidthMm/2,my-m.boardLengthMm/2,moduleBack);
moduleBoard=moduleBoard.holes('top',{positions:P.pins.map(p=>({u:p.at[0]-mx,v:p.at[1]-my})),diameter:m.modeledHoleDiameterMm,depth:'through'});
let leftHeader;
for(const side of [-1,1]){
 const row=P.pins.filter(p=>side*p.at[0]>0),rx=row[0].at[0],y0=Math.min(...row.map(p=>p.at[1]))-h.pitchMm/2;
 let header=box(2.54,50.8,h.bodyHeightMm,false).translate(rx-1.27,y0,moduleFront);
 const pins=box(h.pinSquareMm,h.pinSquareMm,h.tailLengthMm+h.bodyHeightMm+h.postLengthMm,false).translate(rx-h.pinSquareMm/2,y0+h.pitchMm/2-h.pinSquareMm/2,moduleFront-h.tailLengthMm).patternLinear({count:20,direction:[0,1,0],spacing:h.pitchMm});
 header=header.union(pins);
 const hp=addFixed(side<0?'A1-header-left':'A1-header-right',header.finish('brass',{color:'#ad934e'}),[rx,my,pcbBottom],'mild-steel',carrier,'main-pcb-envelope');
 if(side<0)leftHeader=hp;
 // Solder strips are maximum row envelopes. Pins occupy their center bores, so these keepouts are separate from installed hardware.
 const solder=box(2.2,50.8,1.1,false).translate(rx-1.1,y0,pcbTop);
 const clear=solder.holes('top',{positions:row.map(p=>({u:0,v:p.at[1]-my})),diameter:1.0,depth:'through'});
 addFixed(side<0?'A1-solder-left-envelope':'A1-solder-right-envelope',clear.finish('steel',{color:'#777d83'}),[rx,my,pcbTop],'mild-steel',carrier,'main-pcb-envelope');
}
const leftRowX=P.pins.find(p=>p.at[0]<0).at[0];
const modulePart=addFixed('A1-pcb-envelope',moduleBoard.finish('abs',{color:'#20252b'}),[leftRowX,my,moduleFront],'abs',leftHeader,'A1-header-left');
addFixed('A1-component-height-envelope',box(10.8,m.boardLengthMm-10,m.componentHeightAllowanceMm,false).translate(mx-5.4,my-m.boardLengthMm/2,moduleBack-m.componentHeightAllowanceMm).finish('abs',{color:'#353a40'}),[mx,my,moduleBack],'abs',modulePart,'A1-pcb-envelope');
// USB receptacle is a provisional envelope: mating datum and connector height require measurement.
const jack=box(usb.receptacleWidthMm,usb.receptacleDepthMm,usb.receptacleHeightMm,false).translate(-usb.receptacleWidthMm/2,usbY-usb.receptacleDepthMm,usbCenterZ-usb.receptacleHeightMm/2);
addFixed('A1-usb-receptacle-envelope',jack.finish('steel',{color:'#888e94'}),[0,usbY,usbCenterZ],'mild-steel',modulePart,'A1-pcb-envelope');
const overmold=box(usb.plugOvermoldMm[0],usb.plugOvermoldMm[1],usb.plugOvermoldMm[2],false)
 .translate(-usb.plugOvermoldMm[0]/2,usbY+usb.shoulderBeyondMatingPlaneMm,usbCenterZ-usb.plugOvermoldMm[2]/2)
 .union(cylinder(usb.strainReliefLengthMm,usb.cableDiameterMm/2).rotate([1,0,0],-90).translate(0,usbY+usb.shoulderBeyondMatingPlaneMm+usb.plugOvermoldMm[1]-0.1,usbCenterZ));
addFixed('usb-external-plug-envelope',overmold.finish('abs',{color:'#2b2e33'}),[0,usbY+0.5,usbCenterZ],'abs',modulePart,'A1-pcb-envelope');

// Catalog envelopes preserve the ISO 4762 interfaces used by the fastener audit.
async function fastener(name,x,y,seat,length,nutTop,headParent,headParentName){
 const nut=hex(F.nutAcrossFlatsMm).extrude(F.nutHeightMm).hole({byNormal:'Z'},{u:0,v:0,diameter:2.6,depth:'through'}).translate(x,y,nutTop-F.nutHeightMm);
 addFixed(`${name}-nut`,nut.finish('brass'),[x,y,nutTop],'mild-steel');
 const screw=(await lib.part({family:'socket-head-cap-screw',thread:F.thread,lengthMm:length,detail:'envelope'})).translate(x,y,seat);
 addFixed(`${name}-screw`,screw.finish('steel'),[x,y,seat],'mild-steel',headParent,headParentName,{fastener:{part:`${name}-screw`,axis:[0,0,-1],pitchMm:F.pitchMm}});
}
for(const f of I.caseFasteners)await fastener(f.id,f.at[0],f.at[1],F.caseHeadSeatZ,F.caseScrewLengthMm,F.caseNutTopZ-0.05,front,'front-shell');
for(const p of I.pcb.mounts){const lower=p.at[1]<H/2;await fastener(p.id,p.at[0],p.at[1],lower?24.8:pcbTop,lower?F.pcbBottomScrewLengthMm:F.pcbTopScrewLengthMm,F.pcbNutTopZ-0.05,lower?supportPart:carrier,lower?'button-support':'main-pcb-envelope');}
addFixed('battery-reserved-envelope',rounded(I.battery.size[0],I.battery.size[1],3,I.battery.center[2]-I.battery.size[2]/2,I.battery.size[2],0,47).finish('abs',{color:'#6684a7'}),[0,47,2.5],'abs',coverPart,'battery-service-cover');
addFixed('speaker-reserved-envelope',cylinder(speaker.height,speaker.diameter/2).translate(speaker.center[0],speaker.center[1],speaker.center[2]-speaker.height/2).finish('steel',{color:'#45484a'}),[35,35,27.55],'mild-steel',front,'front-shell');
return a.solvedModel({});
