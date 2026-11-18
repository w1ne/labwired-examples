import {evaluateAndBuildScript} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/cli/commands/evaluate.ts";
import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {disposeModelShapes} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/warm/releaseShapes.ts";
import {makeCompound} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/node_modules/replicad/dist/replicad.js";
import {makeNativeMemberTranslation} from "./native-member-translation.mts";
import {readFileSync,writeFileSync} from "node:fs";
import {createHash} from "node:crypto";
const root="/data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path";
const {evaluation,model}=await evaluateAndBuildScript({file:root+"/native-sweep-control-fixture.kcad.ts"});
if(!model)throw new Error(JSON.stringify(evaluation.diagnostics));
const results:any[]=[];
const owned:OcctBackend[]=[];const own=(x:OcctBackend)=>{owned.push(x);return x;};
function cube(x:number,y:number,z:number,w=1){const raw=own(OcctBackend.box(w,w,w));return own(raw.located(Transform.translation(x,y,z)));}
try{
 const source=cube(0,0,0);
 const proof=makeNativeMemberTranslation(source,[0,0,1],100);
 try{
  for(const [name,obstacle,expected] of [
   ["moving-away-from-exact-face-contact",cube(0,0,-1),true],
   ["later-collision-above-start",cube(0,0,50),false],
   ["real-initial-penetration",cube(.5,.5,.5),false],
   ["fully-enclosed-obstacle",cube(.25,.25,.25,.2),false],
  ] as const){const result=proof.check(obstacle);results.push({case:name,expected:expected?"clear":"blocked",passed:result.clear===expected,result});}
  const original=OcctBackend.prototype.intersectionVolume;
  try{
   OcctBackend.prototype.intersectionVolume=function(){return NaN;};
   let message="";try{proof.check(cube(0,0,50));}catch(error){message=error instanceof Error?error.message:String(error);}
   results.push({case:"unknown-native-measurement",expected:"closed-failure",passed:message==="unknown native bounding sweep intersection",message});
  }finally{OcctBackend.prototype.intersectionVolume=original;}
 }finally{proof.dispose();}
 const other=cube(3,0,0);
 const separated=own(new OcctBackend(makeCompound([source.getReplicadShape().clone(),other.getReplicadShape().clone()]) as any));
 const refined=makeNativeMemberTranslation(separated,[0,0,1],100);
 try{
  const result=refined.check(cube(1.5,0,50));
  results.push({case:"two-original-solids-refine-empty-space",expected:"clear",passed:result.clear&&result.basis==="conservative-axial-slab-refinement",result});
  const collision=refined.check(cube(3,0,50));
  results.push({case:"second-original-solid-later-collision",expected:"blocked",passed:!collision.clear,result:collision});
 }finally{refined.dispose();}
 const sha=(path:string)=>createHash("sha256").update(readFileSync(path)).digest("hex");
 const receipt={schemaVersion:1,helperSha256:sha(root+"/native-member-translation.mts"),linearHelperSha256:sha(root+"/native-linear-sweep.mts"),allControlsPassed:results.every(x=>x.passed),results};
 writeFileSync(root+"/pico-native-member-controls.json",JSON.stringify(receipt,null,2));
 console.log(JSON.stringify({allControlsPassed:receipt.allControlsPassed,results:results.map(({case:name,expected,passed})=>({case:name,expected,passed}))}));
 if(!receipt.allControlsPassed)process.exitCode=1;
}finally{for(const s of owned.reverse())s.dispose();disposeModelShapes(model);}
