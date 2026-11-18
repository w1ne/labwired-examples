import{evaluateAndBuildScript}from"/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/agent/cli/commands/evaluate.ts";
import{isSceneBackend}from"/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/sceneBackend.ts";
import{analysisBodyOf,OcctBackend}from"/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/occtBackend.ts";
import{brepExtremaDistanceBetween}from"/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/kernel/backends/occt/brepDistance.ts";
import{disposeModelShapes}from"/data/worktrees/kernelcad-collab-project-assets-20261118/product-web/src/modeling/warm/releaseShapes.ts";
import{readFileSync,writeFileSync,unlinkSync}from"node:fs";import{createHash}from"node:crypto";import{execFileSync}from"node:child_process";
const root="/data/worktrees/labwired-examples-oled-tool-access-20261118",p=root+"/examples/displays/esp32c3-oled",file=p+"/cad/esp32c3-oled-enclosure.kcad.ts",out=p+"/cad/verification/tool-access/engagement-proof.json";
const hash=(b:any)=>createHash("sha256").update(b).digest("hex"),source=readFileSync(file),started=Date.now();
const report:any={sourceSha256:hash(source),sourceBytes:source.length,assetSha256:hash(readFileSync(p+"/cad/inputs/47111971a61f.step")),runtimeCommit:execFileSync("git",["rev-parse","HEAD"],{cwd:"/data/worktrees/kernelcad-collab-project-assets-20261118",encoding:"utf8"}).trim(),tool:{manufacturer:"Wera",series:"2069",partNumber:"05118120001",acrossFlatsMm:4,bladeDiameterMm:5.7,bladeLengthMm:60,handleLengthMm:97,overallCrossSectionMm:[13,13],source:"https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118120001.pdf"},scope:"Lid removed and held away from base. Driver socket engages1.4mm of the1.6mm M2 nut; selected nut and its mating screw are intentional tool contacts. Other lid/display parts remain present. This is a conservative occupied-volume and withdrawal proof, not a physical torque, hand-access, friction or print qualification."};
const save=()=>writeFileSync(out,JSON.stringify(report,null,2));save();
const {evaluation,model}=await evaluateAndBuildScript({file});report.evaluation=evaluation;if(!model||evaluation.exitCode!==0){save();throw Error("current source evaluation failed");}
const scene=[model.rootShape,...model.shapes.values()].filter(isSceneBackend).find(x=>x.assemblyName==="esp32c3-oled-enclosure")!;
const all=new Map(scene.parts.map(x=>[x.name,analysisBodyOf(x.shape).located(x.worldTransform)]));
const signatures=[...all].map(([name,b])=>({name,volume:b.volume(),bounds:b.boundingBox(),meshSha256:hash(JSON.stringify(b.getReplicadShape().mesh({tolerance:.05,angularTolerance:.1})))}));
const obstacleNames=["lid","oled-pcba-envelope","oled-display-surface",...[0,1,2,3].flatMap(i=>["display-screw-"+i,"display-nut-"+i])];
const receipts:any[]=[];
function cylinderAt(d:number,h:number,x:number,y:number,z:number){const original=OcctBackend.cylinder(h,d/2),body=original.translate(x,y,z);original.dispose();return body;}
function compare(tool:OcctBackend,body:OcctBackend){const m=tool.intersectionMetrics(body);const distanceMm=brepExtremaDistanceBetween((tool.getReplicadShape()as any).wrapped,(body.getReplicadShape()as any).wrapped);return{...m,distanceMm,finite:Number.isFinite(m.volumeMm3)&&Number.isFinite(distanceMm)};}
for(let i=0;i<4;i++){
 const nut=all.get("display-nut-"+i)!;const bb=nut.boundingBox();const x=(bb.min[0]+bb.max[0])/2,y=(bb.min[1]+bb.max[1])/2,tip=bb.max[2]-.2;
 const blade=cylinderAt(5.7,160,x,y,tip-160),handle=cylinderAt(Math.hypot(13,13),197,x,y,tip-60-197);
 const checks=[];for(const name of obstacleNames){if(name==="display-nut-"+i||name==="display-screw-"+i)continue;checks.push({obstacle:name,blade:compare(blade,all.get(name)!),handle:compare(handle,all.get(name)!)});}
 const controls=[];for(const [label,d,offset]of[["diameter5.9-insufficient-margin",5.9,0],["diameter6.2-interference",6.2,0],["tip0.2-inside-PCB",5.7,.4]]as const){const t=cylinderAt(d,160,x,y,tip+offset-160);controls.push({label,diameterMm:d,tipOffsetMm:offset,...compare(t,all.get("oled-pcba-envelope")!)});t.dispose();}
 receipts.push({nut:i,nutBounds:bb,bladeTipZ:tip,nutEngagementMm:tip-bb.min[2],PCBTipGapMm:bb.max[2]-tip,withdrawalMm:100,handleDiameterConservativeMm:Math.hypot(13,13),checks,negativeControls:controls,passed:checks.every(x=>x.blade.finite&&x.handle.finite&&x.blade.volumeMm3===0&&x.handle.volumeMm3===0&&x.blade.distanceMm!>=.1&&x.handle.distanceMm!>=.1)&&controls[0].finite&&controls[0].volumeMm3===0&&controls[0].distanceMm!<.1&&controls[1].volumeMm3>0&&controls[2].volumeMm3>0});
 blade.dispose();handle.dispose();report.nuts=receipts;save();
}
report.currentPhysicalSignatures=signatures;save();
for(const b of all.values())b.dispose();disposeModelShapes(model);
const old=execFileSync("git",["show","371f42957e4af52bc1968a4dd26b602d410b8fec:examples/displays/esp32c3-oled/cad/esp32c3-oled-enclosure.kcad.ts"],{cwd:root});
const priorFile=p+"/cad/tool-access-prior-source.kcad.ts";writeFileSync(priorFile,old);
const previous=await evaluateAndBuildScript({file:priorFile});unlinkSync(priorFile);report.priorEvaluation=previous.evaluation;save();if(!previous.model)throw Error("historical source build failed");
const oldScene=[previous.model.rootShape,...previous.model.shapes.values()].filter(isSceneBackend).find(x=>x.assemblyName==="esp32c3-oled-enclosure")!;
const oldSignatures=oldScene.parts.map(x=>{const b=analysisBodyOf(x.shape).located(x.worldTransform);const s={name:x.name,volume:b.volume(),bounds:b.boundingBox(),meshSha256:hash(JSON.stringify(b.getReplicadShape().mesh({tolerance:.05,angularTolerance:.1})))};b.dispose();return s;});
report.manufacturedGeometryEquivalence={oldSourceSha256:hash(old),oldPackageCommit:"371f42957e4af52bc1968a4dd26b602d410b8fec",oldEvaluationExitCode:previous.evaluation.exitCode,current:signatures,previous:oldSignatures,exactAllPartSignaturesEqual:JSON.stringify(signatures)===JSON.stringify(oldSignatures)};
disposeModelShapes(previous.model);report.sourceUnchanged=hash(readFileSync(file))===report.sourceSha256;report.elapsedMs=Date.now()-started;report.ok=receipts.length===4&&receipts.every(x=>x.passed)&&report.manufacturedGeometryEquivalence.exactAllPartSignaturesEqual&&report.sourceUnchanged;save();console.log(JSON.stringify({ok:report.ok,nuts:receipts.map(x=>({nut:x.nut,passed:x.passed,minBladeClearanceMm:Math.min(...x.checks.map(y=>y.blade.distanceMm)),negativeControls:x.negativeControls})),geometryUnchanged:report.manufacturedGeometryEquivalence.exactAllPartSignaturesEqual,elapsedMs:report.elapsedMs}));process.exitCode=report.ok?0:1;
