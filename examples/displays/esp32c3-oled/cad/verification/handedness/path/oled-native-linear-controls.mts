import {evaluateAndBuildScript} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/cli/commands/evaluate.ts";
import {isSceneBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/sceneBackend.ts";
import {analysisBodyOf} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {disposeModelShapes} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/warm/releaseShapes.ts";
import {writeFileSync} from "node:fs";
const file="/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/esp32c3-oled-enclosure.kcad.ts";

import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {makeNativeLinearSweep} from "./native-linear-sweep.mts";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
const {evaluation,model}=await evaluateAndBuildScript({file});
if(!model)throw new Error(JSON.stringify(evaluation.diagnostics));
const results:any[]=[];
try{
 const scene=[model.rootShape,...model.shapes.values()].filter(isSceneBackend).find(s=>s.assemblyName==="esp32c3-oled-enclosure")!;
 const native=new Map(scene.parts.map(p=>[p.name,analysisBodyOf(p.shape).located(p.worldTransform)]));
 const source=native.get("carrier-pcba-envelope")!;
 const removed=new Set(["lid","oled-pcba-envelope","oled-display-surface",...[0,1,2,3].flatMap(i=>["display-screw-"+i,"display-nut-"+i,"lid-screw-"+i,"carrier-screw-"+i])]);
 try{
  const proof=makeNativeLinearSweep(source,[0,0,1],100);
  try{
   const actualPairs=[...native].filter(([n])=>n!=="carrier-pcba-envelope"&&!removed.has(n)).map(([part,shape])=>({part,...proof.check(shape)}));
   results.push({case:"actual-PCBA-with-all-pins-upward-positive",expected:"clear",passed:actualPairs.every(p=>p.clear),proof:proof.report,pairs:actualPairs});
   const cap=OcctBackend.box(70,45,1).translate(0,0,35);
   try{const result=proof.check(cap);results.push({case:"later-cap-above-rest-PCBA",expected:"blocked",initialBounds:source.boundingBox(),obstacleBounds:cap.boundingBox(),passed:!result.clear,result});}finally{cap.dispose();}
   const original=OcctBackend.prototype.intersectionVolume;
   try{OcctBackend.prototype.intersectionVolume=function(){return NaN;};let message="";try{proof.check(native.get("carrier-standoff-0")!);}catch(error){message=error instanceof Error?error.message:String(error);}results.push({case:"unknown-native-linear-measurement",expected:"closed-failure",passed:message==="unknown swept slab intersection",message});}finally{OcctBackend.prototype.intersectionVolume=original;}
  }finally{proof.dispose();}
  const wrong=makeNativeLinearSweep(source,[0,0,-1],100);
  try{const result=wrong.check(native.get("base")!);results.push({case:"PCBA-through-floor-wrong-direction",expected:"blocked",passed:!result.clear,result});}finally{wrong.dispose();}
 }finally{for(const b of native.values())b.dispose();}
 const receipt={sourceSha256:createHash("sha256").update(readFileSync(file)).digest("hex"),helperSha256:createHash("sha256").update(readFileSync("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/native-linear-sweep.mts")).digest("hex"),allControlsPassed:results.every(r=>r.passed),results};
 writeFileSync("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-native-linear-controls.json",JSON.stringify(receipt,null,2));
 console.log(JSON.stringify({allControlsPassed:receipt.allControlsPassed,results:results.map(r=>({case:r.case,passed:r.passed,message:r.message,result:r.result,blockers:r.pairs?.filter((p:any)=>!p.clear)}))}));
}finally{disposeModelShapes(model);}
