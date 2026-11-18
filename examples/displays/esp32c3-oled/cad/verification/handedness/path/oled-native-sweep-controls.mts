import {evaluateAndBuildScript} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/cli/commands/evaluate.ts";
import {isSceneBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/sceneBackend.ts";
import {analysisBodyOf} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {disposeModelShapes} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/warm/releaseShapes.ts";
import {writeFileSync} from "node:fs";
const file="/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/esp32c3-oled-enclosure.kcad.ts";

import {OcctBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {makeNativeSweep} from "./native-axisymmetric-sweep.mts";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
const {evaluation,model}=await evaluateAndBuildScript({file});
if(!model)throw new Error(JSON.stringify(evaluation.diagnostics));
const results:any[]=[];
try{
 const scene=[model.rootShape,...model.shapes.values()].filter(isSceneBackend).find(s=>s.assemblyName==="esp32c3-oled-enclosure")!;
 const native=new Map(scene.parts.map(p=>[p.name,analysisBodyOf(p.shape).located(p.worldTransform)]));
 const source=native.get("lid-screw-0")!;
 const bounds=source.boundingBox();const x=(bounds.min[0]+bounds.max[0])/2,y=(bounds.min[1]+bounds.max[1])/2;
 try{
  const proof=makeNativeSweep(source,[0,0,1],100);
  try{
   const actualPairs=[...native].filter(([n])=>n!=="lid-screw-0").map(([part,shape])=>({part,...proof.check(shape)}));
   results.push({case:"actual-upper-lid-screw-positive",expected:"clear",passed:actualPairs.every(p=>p.clear),proof:proof.report,pairs:actualPairs});
   const cap=OcctBackend.box(2,2,1).translate(x-1,y-1,bounds.max[2]+8);
   try{const result=proof.check(cap);results.push({case:"later-cap-eight-mm-beyond-initial-screw",expected:"blocked",initialBounds:bounds,obstacleBounds:cap.boundingBox(),passed:!result.clear,result});}finally{cap.dispose();}
   const original=OcctBackend.prototype.intersectionVolume;
   try{OcctBackend.prototype.intersectionVolume=function(){return NaN;};let message="";try{proof.check(native.get("lid-standoff-0")!);}catch(error){message=error instanceof Error?error.message:String(error);}results.push({case:"unknown-native-measurement",expected:"closed-failure",passed:message==="unknown swept intersection",message});}finally{OcctBackend.prototype.intersectionVolume=original;}
  }finally{proof.dispose();}
  const wrong=makeNativeSweep(source,[0,0,-1],100);
  try{const result=wrong.check(native.get("lid")!);results.push({case:"source-screw-through-lid-wrong-direction",expected:"blocked",passed:!result.clear,result});}finally{wrong.dispose();}
  const shifted=source.located(Transform.translation(.2,0,0));
  try{const proof=makeNativeSweep(shifted,[0,0,1],100);try{const result=proof.check(native.get("lid-standoff-0")!);results.push({case:"source-screw-shifted-0.2-mm-into-spacer",expected:"blocked",passed:!result.clear,result});}finally{proof.dispose();}}finally{shifted.dispose();}
  const protrusion=OcctBackend.box(.5,.4,.5).translate(bounds.max[0]-.1,y-.2,bounds.max[2]-1);
  const changed=source.union(protrusion);
  try{let message="";try{const proof=makeNativeSweep(changed,[0,0,1],100);proof.dispose();}catch(error){message=error instanceof Error?error.message:String(error);}results.push({case:"source-protrusion-outside-analytic-envelope",expected:"closed-failure",passed:message.startsWith("source outside conservative envelope:"),message});}finally{changed.dispose();protrusion.dispose();}
 }finally{for(const b of native.values())b.dispose();}
 const receipt={sourceSha256:createHash("sha256").update(readFileSync(file)).digest("hex"),helperSha256:createHash("sha256").update(readFileSync("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/native-axisymmetric-sweep.mts")).digest("hex"),allControlsPassed:results.every(r=>r.passed),results};
 writeFileSync("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-native-sweep-controls.json",JSON.stringify(receipt,null,2));
 console.log(JSON.stringify({allControlsPassed:receipt.allControlsPassed,results:results.map(r=>({case:r.case,passed:r.passed,message:r.message,result:r.result}))}));
}finally{disposeModelShapes(model);}
