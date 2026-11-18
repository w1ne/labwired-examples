import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {validBody} from "./native-axisymmetric-sweep.mts";
import {makeNativeLinearSweep} from "./native-linear-sweep.mts";
type V=[number,number,number];
type Bounds={min:V,max:V};
function box(bounds:Bounds){
 const d=bounds.max.map((x,i)=>x-bounds.min[i]);
 if(d.some(x=>!Number.isFinite(x)||x<=0)||bounds.min.some(x=>!Number.isFinite(x)))throw new Error("invalid native bounding envelope");
 const raw=OcctBackend.box(d[0],d[1],d[2]);
 try{return raw.located(Transform.translation(...bounds.min));}finally{raw.dispose();}
}
/** Each original solid is independently enclosed. Zero swept-envelope overlap proves
 * continuous separation; positive overlap refines to the existing axial slab proof.
 * All non-finite, negative, invalid or uncontained results fail closed. */
export function makeNativeMemberTranslation(source:OcctBackend,direction:V,distance:number){
 const k=direction.findIndex(x=>x!==0);
 if(k<0||Math.abs(direction[k])!==1||direction.some((x,i)=>i!==k&&x!==0)||!Number.isFinite(distance)||distance<=0)throw new Error("invalid native member translation");
 if(!validBody(source))throw new Error("invalid native source");
 const sourceVolume=source.volume();
 if(!Number.isFinite(sourceVolume)||sourceVolume<=0)throw new Error("unknown native source volume");
 const bounds=source.boundingBox();
 const rest=box(bounds);
 let sweep:OcctBackend|undefined,slab:ReturnType<typeof makeNativeLinearSweep>|undefined;
 try{
  const outside=source.subtract(rest);
  let outsideVolume:number;
  try{outsideVolume=outside.volume();}finally{outside.dispose();}
  if(outsideVolume!==0)throw new Error("source outside native bounding envelope: "+outsideVolume);
  const travel={min:[...bounds.min] as V,max:[...bounds.max] as V};
  if(direction[k]>0)travel.max[k]+=distance;else travel.min[k]-=distance;
  sweep=box(travel);
  if(!validBody(rest)||!validBody(sweep))throw new Error("invalid native bounding sweep");
  return{
   report:{basis:"per-original-solid-conservative-native-BREP-sweep",direction,distanceMm:distance,sourceVolumeMm3:sourceVolume,sourceBounds:bounds,sourceOutsideBoundingEnvelopeVolumeMm3:outsideVolume,sweptBounds:travel},
   check(obstacle:OcctBackend){
    const boundingEnvelopeIntersectionMm3=sweep!.intersectionVolume(obstacle);
    if(!Number.isFinite(boundingEnvelopeIntersectionMm3)||boundingEnvelopeIntersectionMm3<0)throw new Error("unknown native bounding sweep intersection");
    if(boundingEnvelopeIntersectionMm3===0)return{clear:true,basis:"zero-conservative-bounding-envelope-intersection",boundingEnvelopeIntersectionMm3};
    slab??=makeNativeLinearSweep(source,direction,distance);
    const refined=slab.check(obstacle);
    return{...refined,basis:"conservative-axial-slab-refinement",boundingEnvelopeIntersectionMm3,refinement:slab.report};
   },
   dispose(){slab?.dispose();sweep!.dispose();rest.dispose();}
  };
 }catch(error){slab?.dispose();sweep?.dispose();rest.dispose();throw error;}
}
