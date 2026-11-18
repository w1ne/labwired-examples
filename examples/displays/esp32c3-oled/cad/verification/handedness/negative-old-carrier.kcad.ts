// Negative control: restore the historical wrong-side carrier rotation.
const carrier=(await lib.fromSTEP("https://raw.githubusercontent.com/w1ne/labwired-examples/308810312b293bacf90d613ae7a6a9119b492a41/examples/displays/esp32c3-oled/cad/inputs/47111971a61f.step")).scale([1,1,1.6/1.51]).rotateX(180).translate(0,0,9.6);
for(const [name,x,y] of [["J2.1",2.88,-30.12],["J2.2",5.42,-30.12],["J3.7",2.88,-14.88]]){
 const gauge=cylinder(1.8,0.2).translate(x,y,7.9);
 require("native-carrier-registration-"+name,clearance(carrier,gauge).between(0.199,0.201));
}
return carrier;
