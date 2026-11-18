// Samtec HSS-107-G-2 dimensional envelope, not a manufacturer STEP.
// https://suddendocs.samtec.com/catalog_english/ss.pdf
const a=assembly("hss-107-g-2-envelope");
let s=box(2.54,17.78,2.54).translate(-1.27,-1.27,1.90);
for(let i=0;i<7;i++){
 const y=i*2.54;
 s=s.union(cylinder(4.44,0.66).translate(0,y,0));
 s=s.union(cylinder(3.18,0.255).translate(0,y,-3.18));
 s=s.subtract(cylinder(3.68,0.28).translate(0,y,0.76));
}
a.part("hss-107-g-2",s.color("#343434"),{density:1800});
return a.model();
