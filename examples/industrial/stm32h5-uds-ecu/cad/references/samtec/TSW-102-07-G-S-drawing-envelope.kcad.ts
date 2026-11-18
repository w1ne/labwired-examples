// SPDX-License-Identifier: MIT
// Drawing-derived nominal external-fit envelope for Samtec TSW-102-07-G-S.
// This is not a manufacturer STEP or a fabrication model.
// Samtec TSW print: -07 tail2.54, body2.54REF, post5.84, total10.92mm;
// square pin0.635mm. Chamfers, moulded scallops and tips are conservatively filled.
// KiCad datum: pad1(0,0), pad2(0,-2.54), finished board topZ0, populated+Z.
const body=box(2.54,5.08,2.54).translate(-1.27,-3.81,0);
const pins=[0,-2.54].map(y=>box(.635,.635,10.92).translate(-.3175,y-.3175,-2.54));
const envelope=body.union(...pins).color("#303438");
require("tsw-102-07-envelope",bbox(envelope).within({x:[2.539,2.541],y:[5.079,5.081],z:[10.919,10.921]}));
const a=assembly("TSW-102-07-G-S-drawing-envelope");a.part("TSW-102-07-G-S",envelope);return a.model();
