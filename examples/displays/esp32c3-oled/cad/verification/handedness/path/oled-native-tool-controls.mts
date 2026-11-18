import {evaluateAndBuildScript} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/cli/commands/evaluate.ts";
import {isSceneBackend} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/sceneBackend.ts";
import {analysisBodyOf} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import {Transform} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/shared/runtime/se3.ts";
import {disposeModelShapes} from "/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/warm/releaseShapes.ts";
import {writeFileSync} from "node:fs";
const file="/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/esp32c3-oled-enclosure.kcad.ts";

import {makeNativeToolSweep} from "./native-tool-sweep.mts";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
const {evaluation,model}=await evaluateAndBuildScript({file});
if(!model)throw new Error(JSON.stringify(evaluation.diagnostics));
const results:any[]=[];
try{
 const scene=[model.rootShape,...model.shapes.values()].filter(isSceneBackend).find(s=>s.assemblyName==="esp32c3-oled-enclosure")!;
 const native=new Map(scene.parts.map(p=>[p.name,analysisBodyOf(p.shape).located(p.worldTransform)]));
 try{
  const bounds=native.get("display-nut-0")!.boundingBox();const tool={kind:"cylinder",lengthMm:25,diameterMm:6,label:"M2 nut driver envelope"};
  const proof=makeNativeToolSweep(bounds,{axis:[0,0,-1],tool},100);
  try{const result=proof.check(native.get("oled-pcba-envelope")!);results.push({case:"declared-six-mm-driver",expected:"clear",passed:result.clear,proof:proof.report,result});}finally{proof.dispose();}
  const larger=makeNativeToolSweep(bounds,{axis:[0,0,-1],tool:{...tool,diameterMm:6.2}},100);
  try{const result=larger.check(native.get("oled-pcba-envelope")!);results.push({case:"larger-six-point-two-mm-driver",expected:"blocked",passed:!result.clear,result});}finally{larger.dispose();}
  const wrong=makeNativeToolSweep(bounds,{axis:[0,0,1],tool},100);
  try{const result=wrong.check(native.get("oled-pcba-envelope")!);results.push({case:"driver-through-PCB-wrong-side",expected:"blocked",passed:!result.clear,result});}finally{wrong.dispose();}
 }finally{for(const b of native.values())b.dispose();}
 const receipt={sourceSha256:createHash("sha256").update(readFileSync(file)).digest("hex"),helperSha256:createHash("sha256").update(readFileSync("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/native-tool-sweep.mts")).digest("hex"),allControlsPassed:results.every(r=>r.passed),results};
 writeFileSync("/data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-native-tool-controls.json",JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
}finally{disposeModelShapes(model);}
