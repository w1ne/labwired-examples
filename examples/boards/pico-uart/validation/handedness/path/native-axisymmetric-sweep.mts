
import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {getOC} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/node_modules/replicad/dist/replicad.js";
type V=[number,number,number];
type Segment={z0:number;z1:number;r0:number;r1:number;surface:string};
const dot=(a:V,b:V)=>a.reduce((n,x,i)=>n+x*b[i],0);
const cross=(a:V,b:V):V=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const unit=(a:V):V=>{const l=Math.hypot(...a);if(!Number.isFinite(l)||l===0)throw new Error("invalid axis");return a.map(x=>x/l) as V;};
const mm=(evaluated:number)=>({expression:String(evaluated),unit:"mm",evaluated});
function localFrame(axis:V){const z=unit(axis);const a:V=Math.abs(z[0])<.9?[1,0,0]:[0,1,0];const u=unit(a.map((x,i)=>x-dot(a,z)*z[i]) as V);const v=cross(z,u);return Transform.fromColumnMajor([...u,0,...v,0,...z,0,0,0,0,1]);}
export function validBody(body:OcctBackend){const oc=getOC() as any;const a=new oc.BRepCheck_Analyzer((body.getReplicadShape() as any).wrapped,true,true);try{return a.IsValid_2();}finally{a.delete();}}
function primitive(s:Segment,x:number,y:number):OcctBackend{
 if(!(s.z1>s.z0)||!Number.isFinite(s.z1+s.z0+s.r1+s.r0)||Math.min(s.r0,s.r1)<0||Math.max(s.r0,s.r1)<=0)throw new Error("invalid envelope segment");
 if(s.r0===s.r1){const c=OcctBackend.cylinder(s.z1-s.z0,s.r0);const out=c.located(Transform.translation(x,y,s.z0));c.dispose();return out;}
 const sketch=OcctBackend.fromSketchCommands([{kind:"moveTo",x:mm(0),y:mm(s.z0)},{kind:"lineTo",x:mm(s.r0),y:mm(s.z0)},{kind:"lineTo",x:mm(s.r1),y:mm(s.z1)},{kind:"lineTo",x:mm(0),y:mm(s.z1)},{kind:"close"}] as any);
 try{const b=OcctBackend.revolveFromSketch(sketch);const out=b.located(Transform.translation(x,y,0));b.dispose();return out;}finally{sketch.dispose();}
}
function combine(parts:OcctBackend[]):OcctBackend{
 if(parts.length===0)throw new Error("no analytic envelope candidates");
 let result=parts[0].located(Transform.identity());
 for(const p of parts.slice(1)){const next=result.union(p);result.dispose();result=next;}
 return result;
}
function analyticSegments(local:OcctBackend,x:number,y:number):Segment[]{
 const oc=getOC() as any;const faces=(local.getReplicadShape() as any).faces;const out:Segment[]=[];
 try{for(const face of faces){
  const type=face.geomType;

  if(type!=="CYLINDRE"&&type!=="CONE")continue;
  const ad=new oc.BRepAdaptor_Surface_2(face.wrapped,true);
  let s:any,ax:any,loc:any,dir:any,p0:any,p1:any;
  try{
   s=type==="CYLINDRE"?ad.Cylinder():undefined;
   if(s){ax=s.Axis();loc=ax.Location();dir=ax.Direction();}
   if(s&&(Math.hypot(dir.X(),dir.Y())>1e-12||Math.abs(Math.abs(dir.Z())-1)>1e-12||Math.hypot(loc.X()-x,loc.Y()-y)>1e-9))continue;
   const u=(ad.FirstUParameter()+ad.LastUParameter())/2;
   p0=ad.Value(u,ad.FirstVParameter());p1=ad.Value(u,ad.LastVParameter());
   let z0=p0.Z(),z1=p1.Z();
   let r0=type==="CYLINDRE"?s.Radius():Math.hypot(p0.X()-x,p0.Y()-y),r1=type==="CYLINDRE"?s.Radius():Math.hypot(p1.X()-x,p1.Y()-y);
   if(z0>z1){[z0,z1]=[z1,z0];[r0,r1]=[r1,r0];}
   if(z1>z0)out.push({z0,z1,r0,r1,surface:type});
  }finally{p0?.delete();p1?.delete();dir?.delete();loc?.delete();ax?.delete();s?.delete();ad.delete();}
 }}finally{for(const f of faces)f.delete();}
 return out;
}
export function makeNativeSweep(source:OcctBackend,axis:V,distance:number,nut?:{outerRadius:number;innerRadius:number}){
 if(!Number.isFinite(distance)||distance<=0)throw new Error("invalid travel");
 const frame=localFrame(axis),inverse=frame.inverse();
 const local=source.located(inverse);
 const box=local.boundingBox({exact:true});let x=(box.min[0]+box.max[0])/2,y=(box.min[1]+box.max[1])/2;
 const oc=getOC() as any;const faces=(local.getReplicadShape() as any).faces;
 try{for(const face of faces){if(face.geomType!=="CYLINDRE")continue;const ad=new oc.BRepAdaptor_Surface_2(face.wrapped,true);let cyl:any,ax:any,d:any,p:any;try{cyl=ad.Cylinder();ax=cyl.Axis();d=ax.Direction();p=ax.Location();if(Math.hypot(d.X(),d.Y())<=1e-12){x=p.X();y=p.Y();break;}}finally{p?.delete();d?.delete();ax?.delete();cyl?.delete();ad.delete();}}}finally{for(const f of faces)f.delete();}
 const owned:OcctBackend[]=[local];const own=(b:OcctBackend)=>{owned.push(b);return b;};
 try{
  let segments:Segment[];let rest:OcctBackend;let swept:OcctBackend[];
  if(nut){
   const bores=analyticSegments(local,x,y).filter(s=>s.surface==="CYLINDRE"&&s.r0===nut.innerRadius);
   if(bores.length===0)throw new Error("no exact catalog bore");
   segments=[{z0:Math.min(...bores.map(s=>s.z0)),z1:Math.max(...bores.map(s=>s.z1)),r0:nut.outerRadius+1e-5,r1:nut.outerRadius+1e-5,surface:"catalog-hex-circumradius-plus-conservative-0.00001-mm"}];
   const ring=(extra:number)=>{const outer=own(primitive({...segments[0],z1:segments[0].z1+extra},x,y));const inner=own(primitive({...segments[0],z1:segments[0].z1+extra,r0:nut.innerRadius,r1:nut.innerRadius},x,y));return own(outer.subtract(inner));};
   rest=ring(0);swept=[ring(distance)];
  }else{
   segments=analyticSegments(local,x,y);
   const restComponents=segments.map(s=>own(primitive(s,x,y)));rest=own(combine(restComponents));
   swept=segments.flatMap(s=>{
    if(s.r0===s.r1)return[own(primitive({...s,z1:s.z1+distance},x,y))];
    if(s.r1>s.r0)return[own(primitive(s,x,y)),own(primitive({z0:s.z1,z1:s.z1+distance,r0:s.r1,r1:s.r1,surface:"positive-cap-extrusion"},x,y))];
    return[own(primitive({...s,z0:s.z0+distance,z1:s.z1+distance},x,y)),own(primitive({z0:s.z0,z1:s.z0+distance,r0:s.r0,r1:s.r0,surface:"negative-cap-extrusion"},x,y))];
   });
  }
  if(!validBody(rest)||swept.some(b=>!validBody(b)))throw new Error("invalid envelope BREP");
  const outside=own(local.subtract(rest));const outsideVolumeMm3=outside.volume();
  if(outsideVolumeMm3!==0)throw new Error("source outside conservative envelope: "+outsideVolumeMm3);
  return{
   report:{basis:"conservative-axisymmetric-BREP-envelope",axis,distanceMm:distance,sourceOutsideEnvelopeVolumeMm3:outsideVolumeMm3,segments,localFrameWorld:Array.from((()=>{const a=new Float64Array(16);frame.writeTo(a);return a;})()),restEnvelopeVolumeMm3:rest.volume(),sweptComponentCount:swept.length},
   check(obstacle:OcctBackend){const placed=obstacle.located(inverse);try{const componentVolumesMm3=swept.map(s=>s.intersectionVolume(placed));if(componentVolumesMm3.some(v=>!Number.isFinite(v)||v<0))throw new Error("unknown swept intersection");return{clear:componentVolumesMm3.every(v=>v===0),componentVolumesMm3};}finally{placed.dispose();}},
   dispose(){for(const b of owned.reverse())b.dispose();}
  };
 }catch(error){for(const b of owned.reverse())b.dispose();throw error;}
}
