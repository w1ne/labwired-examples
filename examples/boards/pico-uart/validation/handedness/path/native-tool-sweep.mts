
import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {validBody} from "./native-axisymmetric-sweep.mts";
type V=[number,number,number];
export function makeNativeToolSweep(bounds:{min:V;max:V},spec:{axis:V;tool:any},distance:number){
 const tool=spec.tool;
 if(tool?.kind!=="cylinder"||!Number.isFinite(tool.diameterMm)||tool.diameterMm<=0||!Number.isFinite(tool.lengthMm)||tool.lengthMm<=0||!Number.isFinite(distance)||distance<=0)throw new Error("unsupported native tool sweep");
 const axis=spec.axis;const length=Math.hypot(...axis);if(length!==1)throw new Error("tool axis must be normalized");
 const center=bounds.min.map((x,i)=>(x+bounds.max[i])/2) as V;
 const dot=(a:V,b:V)=>a.reduce((n,x,i)=>n+x*b[i],0);
 const maxProjection=axis.reduce((n,x,i)=>n+x*(x>=0?bounds.max[i]:bounds.min[i]),0);
 const head=center.map((x,i)=>x+axis[i]*(maxProjection-dot(center,axis))) as V;
 const helper:V=Math.abs(axis[0])<.9?[1,0,0]:[0,1,0];let u=helper.map((x,i)=>x-dot(helper,axis)*axis[i]) as V;const ul=Math.hypot(...u);u=u.map(x=>x/ul) as V;
 const v:V=[axis[1]*u[2]-axis[2]*u[1],axis[2]*u[0]-axis[0]*u[2],axis[0]*u[1]-axis[1]*u[0]];
 const frame=Transform.fromColumnMajor([...u,0,...v,0,...axis,0,...head,1]);
 const original=OcctBackend.cylinder(tool.lengthMm+distance,tool.diameterMm/2);
 const body=original.located(frame);original.dispose();
 if(!validBody(body)){body.dispose();throw new Error("invalid native tool BREP");}
 return{
  report:{basis:"exact-declared-cylinder-tool-swept-BREP",tool,axis,headMm:head,toolTranslationDistanceMm:distance,totalAxialExtentMm:tool.lengthMm+distance},
  check(obstacle:OcctBackend){const volumeMm3=body.intersectionVolume(obstacle);if(!Number.isFinite(volumeMm3)||volumeMm3<0)throw new Error("unknown native tool intersection");return{clear:volumeMm3===0,volumeMm3};},
  dispose(){body.dispose();}
 };
}
