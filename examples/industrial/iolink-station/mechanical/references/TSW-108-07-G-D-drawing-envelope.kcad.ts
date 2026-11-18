// Drawing-derived nominal clearance envelope for Samtec TSW-108-07-G-D.
// This is not a manufacturer STEP or a fabrication model.
// Primary sources: Samtec TSW catalog and print revision DS,
// mechanical/references/samtec-tsw-model-provenance.json.
// KiCad model datum: pad 1 centre (0,0), finished board top Z=0.
// Pin 2 is (+2.54,0); pin 3 is (0,-2.54); populated side is +Z.
// Post 5.84, insulator reference 2.54, tail 2.54; total 10.92 mm.
// Use the drawing's 5.08 mm reference body width as a nominal clearance bound.
// Chamfers, moulded scallops and pin tips are conservatively filled.
const pins=[];
for(let row=0;row<8;row++)for(let col=0;col<2;col++)
 pins.push(box(0.635,0.635,10.92).translate(2.54*col-0.3175,-2.54*row-0.3175,-2.54));
const body=box(5.08,20.32,2.54).translate(-1.27,-19.05,0);
const envelope=body.union(...pins).color("#303438");
require("tsw-nominal-external-envelope",bbox(envelope).within({x:[5.079,5.081],y:[20.319,20.321],z:[10.919,10.921]}));
const a=assembly("TSW-108-07-G-D-drawing-envelope");
a.part("TSW-108-07-G-D",envelope);
return a.model();
