
import {prepareAssemblyPathInput} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/mcp/tools/checkAssemblyPath.ts";
import {checkAssemblyPathMeshes,nativeInitialContacts} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/runtime/assemblyPath.ts";
import {prepareAssemblyPathScene} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/runtime/assemblyPathScene.ts";
import {evaluateAndBuildScript} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/cli/commands/evaluate.ts";
import {isSceneBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/sceneBackend.ts";
import {analysisBodyOf,OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {disposeModelShapes} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/warm/releaseShapes.ts";
import {resolvePart} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/parts/familyTable.ts";
import {makeCompound} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/node_modules/replicad/dist/replicad.js";
import {TriangleBvh} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/runtime/dfm/meshBvh.ts";
import {assessSequenceStability} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/runtime/assemblyStability.ts";
import {makeNativeSweep} from "./native-axisymmetric-sweep.mts";
import {makeNativeLinearSweep} from "./native-linear-sweep.mts";
import {makeNativeToolSweep} from "./native-tool-sweep.mts";
import {readFileSync,writeFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {execFileSync} from "node:child_process";
type V=[number,number,number];
const runtime="/data/worktrees/kernelcad-collab-project-assets-20261118";
const packageRoot="/data/worktrees/labwired-examples-oled-handedness-20261118";
const file=packageRoot+"/examples/displays/esp32c3-oled/cad/esp32c3-oled-enclosure.kcad.ts";
const asset=packageRoot+"/examples/displays/esp32c3-oled/cad/inputs/47111971a61f.step";
const output="/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-ordered-complete-native-path.json";
const sha=(x:any)=>createHash("sha256").update(x).digest("hex");
const read=(x:string)=>sha(readFileSync(x));
const start=Date.now();
const metadata=await prepareAssemblyPathInput({file,assembly:"esp32c3-oled-enclosure",workBudget:80000000,sequence:false});
if("error" in metadata)throw new Error(metadata.error);
const {evaluation,model}=await evaluateAndBuildScript({file});
if(!model)throw new Error(JSON.stringify(evaluation.diagnostics));
const scene=[model.rootShape,...model.shapes.values()].filter(isSceneBackend).find(s=>s.assemblyName==="esp32c3-oled-enclosure")!;
const arm=model.session.assemblies.get(scene.assemblyName)!;
const prepared=prepareAssemblyPathScene(scene,metadata.options);
const originals=prepared.parts;
const native=new Map(scene.parts.map(p=>[p.name,analysisBodyOf(p.shape).located(p.worldTransform)]));
const byName=new Map(originals.map(p=>[p.name,p]));
const stages:any[]=[];
const evidence:any={
 schemaVersion:1,sourceSha256:read(file),stepAssetSha256:read(asset),sourceFile:file,
 packageCommit:execFileSync("git",["rev-parse","HEAD"],{cwd:packageRoot,encoding:"utf8"}).trim(),
 runtimeCommit:execFileSync("git",["rev-parse","HEAD"],{cwd:runtime,encoding:"utf8"}).trim(),
 runtimeDiffSha256:sha(execFileSync("git",["diff","HEAD"],{cwd:runtime})),
 harnessSha256:read(new URL(import.meta.url).pathname),
 nativeSweepHelperSha256:read("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/native-axisymmetric-sweep.mts"),
 nativeLinearHelperSha256:read("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/native-linear-sweep.mts"),
 nativeToolHelperSha256:read("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/native-tool-sweep.mts"),
 basis:"Exact source solids and original world-space triangle meshes. Continuous triangle translation for rigid modules. Independently validated conservative axisymmetric BREP swept envelopes for declared fasteners, with original driver-envelope checks preserved.",
 limitations:["This receipt does not change the hosted assembly-path tool result.","Native BREP volume checks establish nominal geometric clearance. They do not model friction, thread deformation, torque, cable flex, or hands.","Display glass is retained in its purchased OLED module, not assembled as a separate user part.","The base and lid are held fixtures for the documented phases. Approximate support checks record any additional holds.","Physical print, fit, cable and repeated-assembly qualification is unperformed."],
 sourceParts:originals.map(p=>{const matrix=new Float64Array(16);scene.parts.find(s=>s.name===p.name)!.worldTransform.writeTo(matrix);return{name:p.name,worldMeshSha256:sha(JSON.stringify(p.mesh)),vertices:p.mesh.vertices.length/3,triangles:p.mesh.triangles.length/3,worldTransform:[...matrix]};}),
 derivedFasteners:prepared.options.fasteners,stages,status:"in-progress"
};
const persist=()=>writeFileSync(output,JSON.stringify({...evidence,elapsedMs:Date.now()-start},null,2));
function bounds(mesh:any){const min:V=[Infinity,Infinity,Infinity],max:V=[-Infinity,-Infinity,-Infinity];for(let i=0;i<mesh.vertices.length;i++){const k=i%3;min[k]=Math.min(min[k],mesh.vertices[i]);max[k]=Math.max(max[k],mesh.vertices[i]);}return{min,max};}
function mapFilter(map:any,names:Set<string>){return map?Object.fromEntries(Object.entries(map).filter(([n])=>names.has(n))):undefined;}
function options(remaining:any[],mover:string){const names=new Set(remaining.map(p=>p.name));return{...prepared.options,parts:[mover],sequence:false,disassemblyOrder:false,stability:false,search:false,subassemblies:[],fixtures:undefined,threadedFasteners:prepared.options.threadedFasteners?.filter(n=>names.has(n)),fasteners:mapFilter(prepared.options.fasteners,names),fits:mapFilter(prepared.options.fits,names),tools:mapFilter(prepared.options.tools,names),workBudget:80000000};}
function concat(name:string,members:string[]){const vertices:number[]=[],triangles:number[]=[];const offsets:any[]=[];for(const n of members){const p=byName.get(n)!;const offset=vertices.length/3;offsets.push({part:n,vertexOffset:offset,triangleOffset:triangles.length/3,worldMeshSha256:sha(JSON.stringify(p.mesh))});vertices.push(...p.mesh.vertices);for(const i of p.mesh.triangles)triangles.push(i+offset);}return{part:{name,mesh:{vertices,triangles}},offsets};}
function exactDirection(actual:any,expected:V){return actual?.length===3&&actual.every((x:number,i:number)=>x===expected[i]);}
async function step(label:string,remaining:any[],members:string[],direction:V,kind:"fastener"|"straight",phase:string){
 const t=Date.now(),name=members.length===1?members[0]:label;
 const receipt:any={stage:stages.length+1,phase,label,movingOriginalParts:members,allRemainingOriginalParts:remaining.map(p=>p.name),direction,kind,passed:false};
 stages.push(receipt);persist();
 try{
  if(members.some(n=>!remaining.some(p=>p.name===n)))throw new Error("planned part missing from remaining scene");
  const group=members.length>1?concat(name,members):undefined;
  const numeric=group?[...remaining.filter(p=>!members.includes(p.name)),group.part]:remaining;
  const opts=options(numeric,name);
  if(group){
   receipt.exactMeshConcatenation=group.offsets;
   const compound=new OcctBackend(makeCompound(members.map(n=>native.get(n)!.getReplicadShape().clone())) as any);
   const row=new WeakMap<any,number>();const proofs=prepared.options[nativeInitialContacts]!;
   receipt.nativeInitialCompoundIntersections=[];
   try{for(const other of numeric.filter(p=>p.name!==name)){const volume=compound.intersectionVolume(native.get(other.name)!);if(!Number.isFinite(volume)||volume<0)throw new Error("unknown compound intersection");row.set(other.mesh,volume);receipt.nativeInitialCompoundIntersections.push({obstacle:other.name,volumeMm3:volume});}}finally{compound.dispose();}
   proofs.volumes.set(group.part.mesh,row);
  }
  const meshReport=checkAssemblyPathMeshes(numeric,opts);
  receipt.meshReport=meshReport;
  if(kind==="straight"){
   receipt.passed=meshReport.ok&&meshReport.parts.length===1&&meshReport.parts[0].state.kind==="removable"&&meshReport.parts[0].validDirections.some(d=>exactDirection(d,direction));
   if(!receipt.passed){
    const requested=meshReport.parts[0]?.directions.find(d=>exactDirection(d.direction,direction));
    if(requested&&!requested.clear&&requested.blockingParts.length>0){
     const moving=group?new OcctBackend(makeCompound(members.map(n=>native.get(n)!.getReplicadShape().clone())) as any):native.get(name)!;
     try{
      const proof=makeNativeLinearSweep(moving,direction,100);
      try{receipt.nativeContinuousTranslation={...proof.report,obstacles:remaining.filter(p=>!members.includes(p.name)).map(p=>({part:p.name,...proof.check(native.get(p.name)!)}))};receipt.passed=receipt.nativeContinuousTranslation.obstacles.every((p:any)=>p.clear);}
      finally{proof.dispose();}
     }finally{if(group)moving.dispose();}
    }
   }
  }else{
   const spec=prepared.options.fasteners?.[name];
   if(!spec||!exactDirection(spec.axis,direction))throw new Error("planned fastener axis differs from source mate");
   const raw=meshReport.parts.find(p=>p.part===name)!;
   receipt.toolReachPassed=spec.tool===null||raw.toolReach?.status==="clear";
   if(!receipt.toolReachPassed&&spec.tool?.kind==="cylinder"){
    const toolProof=makeNativeToolSweep(native.get(name)!.boundingBox(),spec as any,100);
    try{receipt.nativeToolSweep={...toolProof.report,obstacles:remaining.filter(p=>p.name!==name).map(p=>({part:p.name,...toolProof.check(native.get(p.name)!)}))};receipt.toolReachPassed=receipt.nativeToolSweep.obstacles.every((p:any)=>p.clear);}
    finally{toolProof.dispose();}
   }
   const stored=arm.__parts().find(p=>p.name===name)!;
   const cat=model.records.find(r=>r.id===stored.originalShape.id)?.metadata?.catalogPart;
   const nut=cat?.family==="hex-nut"?resolvePart({family:cat.family,thread:cat.attributes.thread as string}):undefined;
   const distance=100;
   const proof=makeNativeSweep(native.get(name)!,direction,distance,nut?{outerRadius:nut.acrossFlatsMm/Math.sqrt(3),innerRadius:nut.nominalMm/2}:undefined);
   try{
    receipt.nativeContinuousSweep={...proof.report,obstacles:remaining.filter(p=>p.name!==name).map(p=>({part:p.name,...proof.check(native.get(p.name)!)}))};
   }finally{proof.dispose();}
   const own=bounds(byName.get(name)!.mesh);
   const others=remaining.filter(p=>p.name!==name).map(p=>bounds(p.mesh));
   const shifted={min:own.min.map((x,i)=>x+distance*direction[i]),max:own.max.map((x,i)=>x+distance*direction[i])};
   receipt.finalBounds=shifted;
   receipt.completelyOutsideRemainingBounds=others.every(b=>[0,1,2].some(i=>shifted.max[i]<b.min[i]||shifted.min[i]>b.max[i]));
   receipt.passed=receipt.toolReachPassed&&receipt.completelyOutsideRemainingBounds&&receipt.nativeContinuousSweep.obstacles.every((p:any)=>p.clear);
  }
  receipt.elapsedMs=Date.now()-t;persist();
  console.log(JSON.stringify({stage:receipt.stage,phase,label,passed:receipt.passed,elapsedMs:receipt.elapsedMs,meshState:receipt.meshReport.parts[0]?.state,toolReachPassed:receipt.toolReachPassed,nativeBlockers:receipt.nativeContinuousSweep?.obstacles.filter((x:any)=>!x.clear)}));
  if(!receipt.passed)throw new Error("stage failed: "+label);
  return remaining.filter(p=>!members.includes(p.name));
 }catch(error){receipt.error=error instanceof Error?error.message:String(error);receipt.elapsedMs=Date.now()-t;evidence.status="blocked";persist();throw error;}
}
function stability(phase:string,stageList:any[],parts:any[],fixture:string){
 const build=stageList.slice().reverse().map((s,i)=>({index:i+1,adds:s.movingOriginalParts,direction:s.direction.map((x:number)=>-x),motion:s.kind==="fastener"?"helical":"straight"}));
 const result=assessSequenceStability(build,parts.map(p=>({name:p.name,mesh:p.mesh,bbox:bounds(p.mesh),bvh:new TriangleBvh(p.mesh)})),{gravity:[0,0,-1],fixtures:[fixture],contactToleranceMm:.05});
 return{phase,fixture,buildSteps:build,stamp:result.stamp,findings:result.findings,steps:[...result.steps.entries()]};
}
try{
 persist();console.log(JSON.stringify({phase:"prepared",elapsedMs:Date.now()-start,originalParts:originals.length}));
 let remaining=[...originals];
 for(let i=0;i<4;i++)remaining=await step("remove-lid-screw-"+i,remaining,["lid-screw-"+i],[0,0,1],"fastener","device");
 const lidMembers=["lid","oled-pcba-envelope","oled-display-surface",...[0,1,2,3].flatMap(i=>["display-screw-"+i,"display-nut-"+i])];
 remaining=await step("lid-with-complete-OLED",remaining,lidMembers,[0,0,1],"straight","device");
 for(let i=0;i<4;i++)remaining=await step("remove-carrier-screw-"+i,remaining,["carrier-screw-"+i],[0,0,1],"fastener","device");
 remaining=await step("lift-carrier-PCBA",remaining,["carrier-pcba-envelope"],[0,0,1],"straight","device");
 for(let i=0;i<4;i++)remaining=await step("remove-carrier-lower-screw-"+i,remaining,["carrier-lower-screw-"+i],[0,0,-1],"fastener","device");
 for(let i=0;i<4;i++)remaining=await step("remove-carrier-standoff-"+i,remaining,["carrier-standoff-"+i],[0,0,1],"straight","device");
 for(let i=0;i<4;i++)remaining=await step("remove-carrier-washer-"+i,remaining,["carrier-washer-"+i],[0,0,1],"straight","device");
 for(let i=0;i<4;i++)remaining=await step("remove-lid-lower-screw-"+i,remaining,["lid-lower-screw-"+i],[0,0,-1],"fastener","device");
 for(let i=0;i<4;i++)remaining=await step("remove-lid-standoff-"+i,remaining,["lid-standoff-"+i],[0,0,1],"straight","device");
 if(remaining.length!==1||remaining[0].name!=="base")throw new Error("device coverage incomplete");
 evidence.deviceRemainingFixtures=remaining.map(p=>p.name);
 let bench=originals.filter(p=>lidMembers.includes(p.name));
 for(let i=0;i<4;i++){bench=await step("remove-display-screw-"+i,bench,["display-screw-"+i],[0,0,1],"fastener","lid-bench");bench=await step("remove-display-nut-"+i,bench,["display-nut-"+i],[0,0,-1],"fastener","lid-bench");}
 bench=await step("remove-purchased-OLED-with-glass",bench,["oled-pcba-envelope","oled-display-surface"],[0,0,-1],"straight","lid-bench");
 if(bench.length!==1||bench[0].name!=="lid")throw new Error("lid coverage incomplete");
 evidence.lidRemainingFixtures=bench.map(p=>p.name);
 evidence.stability=[stability("device",stages.filter(s=>s.phase==="device"),originals,"base"),stability("lid-bench",stages.filter(s=>s.phase==="lid-bench"),originals.filter(p=>lidMembers.includes(p.name)),"lid")];
 const source=native.get("lid-screw-0")!;const shifted=source.located(Transform.translation(.2,0,0));const negative=makeNativeSweep(shifted,[0,0,1],100);
 try{evidence.negativeControls=[{case:"upper-screw-shifted-0.2-mm-through-spacer",expected:"blocked",result:negative.check(native.get("lid-standoff-0")!)}];}finally{negative.dispose();shifted.dispose();}
 if(evidence.negativeControls.some((n:any)=>n.result.clear))throw new Error("negative control passed unexpectedly");
 evidence.status="complete-geometric-evidence";
 evidence.hostedAssemblyPathStatus="not-yet-accepted; native swept-envelope refinement is independent evidence";
 persist();console.log(JSON.stringify({status:evidence.status,stages:stages.length,elapsedMs:Date.now()-start,needsHold:evidence.stability.map((s:any)=>({phase:s.phase,parts:s.findings.map((f:any)=>f.part)}))}));
}catch(error){evidence.error=error instanceof Error?error.message:String(error);persist();console.log(JSON.stringify({status:evidence.status,error:evidence.error,elapsedMs:Date.now()-start}));}
finally{for(const shape of native.values())shape.dispose();disposeModelShapes(model);}
