// SPDX-License-Identifier: MIT
// UDS bench mounting fixture. Millimetres. Board copper source is pinned.
// Nucleo is a board-envelope fit reference; component/connector fit remains
// a physical prototype check. The carrier is the exact populated KiCad STEP.
meta({name:'h563-uds-bench-a',title:'STM32H563 UDS bench fixture A'});
const boardLength=param('nucleoLength',133.34,{min:133.34,max:133.34});
const boardWidth=param('nucleoWidth',70,{min:70,max:70});
const boardThickness=param('nucleoPcbThickness',1.6,{min:1.4,max:1.8});
const clearance=param('nucleoEdgeClearance',0.35,{min:0.2,max:0.6});
const plateThickness=3;
let plate=box(222,90,plateThickness).fillet(2,{parallel:[0,0,1]});
// M3 carrier bosses, 7 mm stand-off above plate and 52 x 32 mm hole pattern.
for(const [x,y] of [[156,29],[208,29],[156,61],[208,61]]){
  plate=plate.union(cylinder(7,3.3).holes('top',{positions:[{u:0,v:0}],diameter:3,depth:7,thread:{pitch:0.5},name:'M3'}).translate(x,y,3));
}

// Holeless cradle derived from KernelCAD holeless-board-cradle recipe.
// Ends stay open for USB and Ethernet. The 8 mm under-board gap clears the header tails.
const boardX=8,boardY=10,boardZ=11;
let rail=box(boardLength.add(clearance.multiply(2)).add(4.4),2.2,10.8)
  .translate(clearance.multiply(-1).add(boardX-2.2),clearance.multiply(-1).add(boardY-2.2),3);
rail=rail.union(box(boardLength.add(clearance.multiply(2)).add(4.4),2.2,10.8)
  .translate(clearance.multiply(-1).add(boardX-2.2),boardWidth.add(clearance).add(boardY),3));
for(const x of [18,123]){
 for(const y of [boardY-1,boardWidth.add(boardY-1)]){
   rail=rail.union(box(7,2,boardZ-3).translate(x,y,3));
   rail=rail.union(box(7,2,1.2).translate(x,y,boardThickness.add(boardZ)));
 }
}
// Four corner end-stops prevent longitudinal sliding; centre port regions stay open.
for(const x of [clearance.multiply(-1).add(boardX-2.2),boardLength.add(clearance).add(boardX)]){
 for(const y of [boardY,boardWidth.add(boardY-4)]){
  rail=rail.union(box(2.2,4,10.8).translate(x,y,3));
 }
}
// Slotted tie-down points retain the harness and keep connector loads off solder tails.
for(const x of [145,216]){
 plate=plate.subtract(box(2,12,5).translate(x,39,-1));
}
plate=plate.union(rail);

return plate;
