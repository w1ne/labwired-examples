// Negative control: deliberately reflect the native populated Pico to swap its physical rows.
const board=(await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/753232d92fb76c2ea4e087bd05a3a43d5bc67dbf/examples/boards/pico-uart/references/raspberry-pi/Pico-R3.step",{solid:0})).rotateX(90).translate(19.5,-57,21.15).reflect("yz").translate(60,0,0);
const led=(await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/753232d92fb76c2ea4e087bd05a3a43d5bc67dbf/examples/boards/pico-uart/references/raspberry-pi/Pico-R3.step",{solid:8})).rotateX(90).translate(19.5,-57,21.15).reflect("yz").translate(60,0,0);
for(const [name,x,y] of [["pin1",21.11,-7.37],["pin2",21.11,-9.91],["pin40",38.89,-7.37]]){
 const gauge=cylinder(1.2,0.25).translate(x,y,20.55);
 require("native-pico-registration-"+name,clearance(board,gauge).between(0.249,0.251));
}
require("native-pico-led-on-pin1-side",centerOfMass(led).within({x:[24.29,24.31],y:[-10.81,-10.79],z:[21.65,22.25]}));
return board;
