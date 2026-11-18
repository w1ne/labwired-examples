
import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {getOC} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/node_modules/replicad/dist/replicad.js";
import {validBody} from "./native-axisymmetric-sweep.mts";
type V=[number,number,number];
type Bounds={min:V,max:V};
function box(bounds:Bounds){const d=bounds.max.map((v,i)=>v-bounds.min[i]);if(d.some(v=>!Number.isFinite(v)||v<=0))throw new Error("invalid box envelope");const b=OcctBackend.box(d[0],d[1],d[2]);try{return b.located(Transform.translation(...bounds.min));}finally{b.dispose();}}
function combine(parts:OcctBackend[]){if(parts.length===0)throw new Error("empty envelope");let result=parts[0].located(Transform.identity());for(const part of parts.slice(1)){const next=result.union(part);result.dispose();result=next;}return result;}
function levels(source:OcctBackend,k:number,bounds:Bounds){
 const all=[bounds.min[k],bounds.max[k]];
 const faces=(source.getReplicadShape() as any).faces;const oc=getOC() as any;
 try{for(const face of faces){
  if(face.geomType!=="PLANE")continue;
  const n=face.normalAt();try{const normal=[n.x,n.y,n.z];if(normal.some((x,i)=>i!==k&&Math.abs(x)>1e-12))continue;}finally{n.delete();}
  const ad=new oc.BRepAdaptor_Surface_2(face.wrapped,true);let p:any;
  try{p=ad.Value((ad.FirstUParameter()+ad.LastUParameter())/2,(ad.FirstVParameter()+ad.LastVParameter())/2);const value=[p.X(),p.Y(),p.Z()][k];if(Number.isFinite(value)&&value>bounds.min[k]&&value<bounds.max[k])all.push(value);}finally{p?.delete();ad.delete();}
 }}finally{for(const face of faces)face.delete();}
 all.sort((a,b)=>a-b);
 const coarse:number[]=[all[0]];
 for(const value of all.slice(1)){if(value-coarse.at(-1)!>1e-7)coarse.push(value);}
 if(coarse.at(-1)!<bounds.max[k]){if(bounds.max[k]-coarse.at(-1)!<=1e-7&&coarse.length>1)coarse[coarse.length-1]=bounds.max[k];else coarse.push(bounds.max[k]);}
 if(coarse.length>128)throw new Error("native envelope slab budget exceeded");
 return coarse;
}
export function makeNativeLinearSweep(source:OcctBackend,direction:V,distance:number){
 const k=direction.findIndex(x=>x!==0);if(k<0||Math.abs(direction[k])!==1||direction.some((x,i)=>i!==k&&x!==0)||!(distance>0)||!Number.isFinite(distance))throw new Error("only finite cardinal translation envelopes supported");
 const owned:OcctBackend[]=[];const own=(b:OcctBackend)=>{owned.push(b);return b;};
 try{
  const outer=source.boundingBox();const cuts=levels(source,k,outer);
  const candidates:OcctBackend[]=[],swept:OcctBackend[]=[],slabs:any[]=[];
  for(let i=0;i<cuts.length-1;i++){
   const region={min:[...outer.min] as V,max:[...outer.max] as V};region.min[k]=cuts[i];region.max[k]=cuts[i+1];
   const clip=own(box(region));const chunk=own(source.intersect(clip));const volume=chunk.volume();
   if(!Number.isFinite(volume)||volume<0)throw new Error("unknown slab volume");
   if(volume===0){slabs.push({min:cuts[i],max:cuts[i+1],sourceVolumeMm3:0});continue;}
   const components=chunk.solidComponents().map(own);
   for(let j=0;j<components.length;j++){
    const component=components[j];const componentVolume=component.volume();
    if(!Number.isFinite(componentVolume)||componentVolume<=0)throw new Error("unknown slab solid volume");
    const bounds=component.boundingBox();const candidate=own(box(bounds));candidates.push(candidate);
    if(candidates.length>256)throw new Error("native slab component budget exceeded");
    const travel={min:[...bounds.min] as V,max:[...bounds.max] as V};
    if(direction[k]>0)travel.max[k]+=distance;else travel.min[k]-=distance;
    swept.push(own(box(travel)));
    slabs.push({min:cuts[i],max:cuts[i+1],component:j,sourceVolumeMm3:componentVolume,candidateBounds:bounds,sweptBounds:travel});
   }
  }
  const envelope=own(combine(candidates));
  if(!validBody(envelope)||swept.some(b=>!validBody(b)))throw new Error("invalid swept slab envelope");
  const outside=own(source.subtract(envelope));const outsideVolumeMm3=outside.volume();
  if(outsideVolumeMm3!==0)throw new Error("source outside slab envelope: "+outsideVolumeMm3);
  return{
   report:{basis:"conservative-native-BREP-axial-slab-envelope",direction,distanceMm:distance,sourceOutsideEnvelopeVolumeMm3:outsideVolumeMm3,slabs},
   check(obstacle:OcctBackend){const componentVolumesMm3=swept.map(b=>b.intersectionVolume(obstacle));if(componentVolumesMm3.some(v=>!Number.isFinite(v)||v<0))throw new Error("unknown swept slab intersection");return{clear:componentVolumesMm3.every(v=>v===0),componentVolumesMm3};},
   dispose(){for(const b of owned.reverse())b.dispose();}
  };
 }catch(error){for(const b of owned.reverse())b.dispose();throw error;}
}
