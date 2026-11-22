import fs from 'node:fs'; import assert from 'node:assert/strict'; import {createHash} from 'node:crypto'; import {gunzipSync} from 'node:zlib';
const dir=new URL('../examples/robotics/axiom-h1/mechanical/producer-refresh-20261122/',import.meta.url); const read=n=>fs.readFileSync(new URL(n,dir)); const json=n=>JSON.parse(read(n));
const sha=b=>createHash('sha256').update(b).digest('hex');
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
const oldArchive=new URL('../artifact-refresh-20261122/mesh.json.gz',dir);
const oldArchiveBytes=fs.readFileSync(oldArchive); assert.equal(sha(oldArchiveBytes),'6f718fefe6c0712e5827bc5feb8adba59fe10b7eda3ef8ae65e696f0ef299134');
const oldBytes=gunzipSync(oldArchiveBytes),bytes=gunzipSync(read('mesh.json.gz'));
assert.equal(sha(oldBytes),'aaa16db035e4563a94fd3a7e236fe50bcc048f5ef731564912a9083b54e8b8e5');
assert.equal(sha(bytes),'3fccde237da7ee0b96019f291f866882766fc42973046747b9470ed1be8a4eb6');
const before=JSON.parse(oldBytes),after=JSON.parse(bytes),ready=json('current-readback.json');
const source=Buffer.from(ready.revision.code);
assert.equal(ready.project.ok,true); assert.equal(ready.revision.ok,true);assert.equal(ready.project.slug,'45f5VM8t');assert.equal(ready.revision.slug,'45f5VM8t');
assert.equal(ready.project.version,1);assert.equal(ready.revision.version,1);assert.equal(ready.project.meshStatus,'ready');assert.equal(ready.project.meshReady,true);
assert.equal(ready.project.code,ready.revision.code);assert.deepEqual(ready.project.parameters,ready.revision.parameters);assert.deepEqual(ready.revision.parameters,[]);assert.deepEqual(ready.revision.assets??{},{});assert.deepEqual(ready.project.assets??{},{});
assert.equal(fs.readFileSync(new URL('../axiom-compact-frame.kcad.ts',dir),'utf8'),ready.revision.code);
assert.equal(sha(source),'5c392121b7cccfd8dc41fb0226ac68e3f344b06bf954ccb35db74e0fd9ac4496');assert.equal(source.length,5966);
assert.equal(after.provenance.schema,'kernelcad.revision-mesh-provenance.v1');
assert.deepEqual(after.provenance.source,{sha256:sha(source),byteLength:source.length});
assert.equal(after.provenance.assetsSha256,sha(canonical({})));
assert.equal(after.provenance.geometryHash,'3b2b45447f0efdec5c17247dae53c8ade82b19b71779a97ee58db135b4032f28');
assert.deepEqual({...after.provenance,producer:null},{...before.provenance,producer:null});
const producer=after.provenance.producer;
assert.equal(producer.serverCommit,'fd52f2c20b801c8a7ab875ebeb6b844a928baf97');
assert.equal(producer.runtimeSourceHash,'f00d5beda7bb1f5befa8f001329013b0c2b1e6b9ae85019837415deee2d89977');
assert.equal(producer.sessionArtifactSha256,'bbbbcf04ef339960dfd03e83f6d1d9725971e80c35a50337957e46144985c507');
assert.equal(producer.serverBuild,ready.project.serverBuild);assert.equal(ready.revision.serverBuild,ready.project.serverBuild);
const oldPin=sha(canonical(before.provenance)),newPin=sha(canonical(after.provenance));
assert.equal(oldPin,'613a4609e40d62c218cd4e276c3bf5835525feb1e068a64acd18a1e6fd1a89ea');
assert.equal(newPin,'857d1a3086a88873bcf79a27f5ce6a28f644aaf5877ddedb6e80369180906420');
for(const name of ['stored','cdn']){
 const fetch=json(name+'-fetch.json');assert.equal(fetch.status,200);assert.equal(fetch.sha256,sha(bytes));assert.equal(fetch.bytes,bytes.length);
 const u=new URL(fetch.url);assert.equal(u.protocol,'https:');assert.equal(u.host,name==='stored'?'api.kernelcad.com':'mesh.kernelcad.com');
 assert.equal(u.pathname,name==='stored'?'/api/v1/projects/45f5VM8t/revisions/1/mesh-artifact':'/mesh-artifacts/45f5VM8t/v1.json');
 assert.equal(u.searchParams.get('provenance'),newPin);
 assert.equal(fetch.url,name==='stored'?ready.project.meshDownloadUrl:ready.project.meshUrl);
 if(name==='stored'){assert.equal(u.searchParams.get('download'),'1');assert.equal(fetch.headers['x-mesh-provenance'],newPin);assert.equal(fetch.headers['x-mesh-source-sha256'],sha(source));}
}
assert.deepEqual(Object.keys(after),Object.keys(before));
const {provenance:oldProvenance,...oldGeometry}=before;const{provenance:newProvenance,...newGeometry}=after;
assert.deepEqual(newGeometry,oldGeometry,'Every geometry, transform, joint/mate and bound field must remain identical');
assert.equal(after.features.length,27);
const archive=read('mesh.json.gz');
assert.deepEqual(gunzipSync(archive),bytes);assert.equal(sha(archive),'3127d99a2cc4a434bedbc74a836af6d8d198f5ed852d65a40ae18ceb5a6cc7ef');
const model=json('model.json'),oldModel=JSON.parse(fs.readFileSync(new URL('../artifact-refresh-20261122/model.json',dir)));
assert.equal(model.meshProvenance,newPin);assert.deepEqual({...model,meshProvenance:oldModel.meshProvenance},oldModel);assert.equal(model.electronics.motions.length,20);
const files={};for(const name of ['current-readback.json','stored-fetch.json','cdn-fetch.json','mesh.json.gz','model.json']){const b=read(name);files[name]={bytes:b.length,sha256:sha(b)};}
const receipt={schema:'labwired.axiom-cad-producer-refresh.v1',passed:true,observedAt:new Date().toISOString(),script:'../../../../../scripts/check-axiom-producer-refresh.mjs',scriptSha256:sha(fs.readFileSync(new URL(import.meta.url))),
 project:{slug:'45f5VM8t',version:1,sourceSha256:sha(source),sourceBytes:source.length,parameters:[]},
 previous:{examplesMergeCommit:'cdb8ef44689501b3b1fbb9eebb38d7ecdaa1e4ce',meshProvenance:oldPin,rawSha256:sha(oldBytes),rawBytes:oldBytes.length,archiveSha256:sha(oldArchiveBytes),provenance:oldProvenance},
 current:{meshProvenance:newPin,rawSha256:sha(bytes),rawBytes:bytes.length,archiveSha256:sha(archive),provenance:newProvenance},
 comparison:{allNonProvenanceFieldsDeepEqual:true,onlyProvenanceProducerChanged:true,canonicalGeometrySha256:sha(canonical(newGeometry)),features:27,sourceParametersAssetsUnchanged:true,modelChangedFields:['meshProvenance'],motionBindingsUnchanged:20,bounds:after.bounds},
 acceptance:{original59DiscretePosesRetained:true,original20BindingTransformReceiptRetained:true,additionalDenseSweep:'previous timeout retained; not rerun',physicalAcceptance:'failed; unchanged',savedProjectCasPerformed:false,viewerPainted:false},
 actions:{sourceResavePerformed:false,modelEvaluationPerformed:false,meshGenerationRequested:false,readOnlyStoredArtifactQualification:true},
 files};
const args=process.argv.slice(2);
assert.ok(args.length===0 || args.length===2&&args[0]==='--out','Usage: node scripts/check-axiom-producer-refresh.mjs [--out NEW_RECEIPT.json]');
const output=JSON.stringify(receipt,null,2)+'\n';
if(args.length){fs.writeFileSync(args[1],output,{flag:'wx'});console.log(JSON.stringify({passed:true,meshProvenance:newPin,meshSha256:sha(bytes),output:args[1]}));}
else process.stdout.write(output);
