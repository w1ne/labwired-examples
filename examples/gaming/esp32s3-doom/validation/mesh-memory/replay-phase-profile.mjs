import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const root=process.env.DOOM_RUNTIME_ROOT || '/data/worktrees/kernelcad-collab-project-assets-20261118';
const evidence=process.env.DOOM_EVIDENCE_DIR || '/data/work-evidence/labwired-featured-implementation-20261118/doom-mesh-probe';
const saved=JSON.parse(readFileSync(process.env.DOOM_PROJECT_JSON || '/data/work-evidence/labwired-featured-implementation-20261118/doom-mesh-probe/saved-revision-v1.json','utf8'));
const assetsDir='/data/worktrees/labwired-examples-doom-package-20261118/examples/gaming/esp32s3-doom/mechanical';
const {withMaterializedProject}=await import(pathToFileURL(root+'/dist/src/lib/projectAssets.js'));
const {runPooledKernelJob,occtPoolStats,__resetOcctPoolForTests}=await import(pathToFileURL(root+'/dist/src/mesh/occtPool.js'));
const started=Date.now();
const result={scope:'Local production OCCT pool replay of immutable saved Doom revision; no hosted project write.',slug:saved.slug,version:saved.version,sourceSha256:createHash('sha256').update(saved.code).digest('hex'),assets:saved.assets,runtimeSourceHash:JSON.parse(readFileSync(root+'/src/assemblyInstructions/privateRuntimeContract.json','utf8')).sourceHash,samples:[],progress:[],status:'running'};
const save=()=>writeFileSync(evidence+'/result.json',JSON.stringify({...result,elapsedMs:Date.now()-started},null,2)+'\n');
const ticker=setInterval(()=>{result.samples.push({elapsedMs:Date.now()-started,pool:occtPoolStats()});save();},1000);
try {
 const hashes=Object.entries(saved.assets).sort(([a],[b])=>a.localeCompare(b)).map(([path,entry])=>path+':'+entry.sha256).join('|');
 const mesh=await withMaterializedProject(saved.code,saved.assets,async entry=>{const pair=Object.entries(saved.assets).find(([,candidate])=>candidate.sha256===entry.sha256);return readFileSync(assetsDir+'/'+pair[0]);},async fileName=>runPooledKernelJob({kind:'mesh',source:saved.code,fileName,identity:saved.slug+'@'+saved.version+':'+hashes,jobClass:'agent'},300000,'revision-mesh-artifact',{onProgress:data=>{result.progress.push({elapsedMs:Date.now()-started,data});save();}}),{tempRoot:'/tmp'});
 result.status='passed'; result.mesh={features:mesh.features.length,records:mesh.featureRecords.length,bounds:mesh.bounds,failedFeatureIds:mesh.failedFeatureIds,rootFeatureIds:mesh.rootFeatureIds};
 writeFileSync(evidence+'/mesh.json',JSON.stringify(mesh));
 console.log(JSON.stringify({elapsedMs:Date.now()-started,mesh:result.mesh}));
} catch(error) {result.status='failed';result.error={name:error.name,message:error.message,code:error.code,ranMs:error.ranMs};console.error(JSON.stringify(result.error));process.exitCode=1;}
finally {clearInterval(ticker);result.finalPool=occtPoolStats();save();__resetOcctPoolForTests();}
