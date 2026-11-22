#!/usr/bin/env node
// Read-only, exact comparison against the archived ready Pathfinder artifact.
// Usage: node compare-cad-artifacts.mjs ARTIFACT[.gz] READBACK.json DOWNLOADS.json EXPECTED_RUNTIME_SHA
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('.',import.meta.url));
const [artifactPath,readbackPath,downloadsPath,expectedRuntime,...extra]=process.argv.slice(2);
assert.ok(artifactPath&&readbackPath&&downloadsPath&&expectedRuntime&&!extra.length,'Supply artifact, readback, downloads and expected runtime');
assert.match(expectedRuntime,/^[a-f0-9]{64}$/);
const sha=body=>createHash('sha256').update(body).digest('hex');
const readJson=path=>JSON.parse(readFileSync(path,'utf8'));
const readBody=path=>{const body=readFileSync(path);return body[0]===0x1f&&body[1]===0x8b?gunzipSync(body):body;};
const canonical=value=>{
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  if(typeof value==='number'){assert.ok(Number.isFinite(value));if(Object.is(value,-0))return '-0';}
  return JSON.stringify(value);
};
const digest=value=>sha(canonical(value));
const baseline=readJson(resolve(root,'cad-artifact-20261122/archive.json'));
const beforeRaw=readBody(resolve(root,'cad-artifact-20261122/mesh.json.gz'));
assert.equal(sha(beforeRaw),baseline.mesh.decompressed_sha256);assert.equal(beforeRaw.length,baseline.mesh.decompressed_bytes);
const afterRaw=readBody(resolve(artifactPath)),before=JSON.parse(beforeRaw),after=JSON.parse(afterRaw);
const readback=readJson(resolve(readbackPath)),downloads=readJson(resolve(downloadsPath));
const savedBefore=readJson(resolve(root,'cad-artifact-20261122/project-readback.json'));
const source=readFileSync(resolve(root,'pathfinder-extended.kcad.ts'));
assert.equal(sha(source),baseline.project.source_sha256);
for(const response of [readback.project,readback.revision]){
  assert.equal(response.ok,true);assert.equal(response.slug,baseline.project.slug);assert.equal(response.version,baseline.project.revision);
  assert.equal(response.code,source.toString('utf8'));
}
assert.equal(readback.source_sha256,sha(source));
assert.equal(readback.project.updated_at,savedBefore.project.updated_at,'Saved revision changed');
assert.equal(readback.project.meshReady,true);assert.equal(readback.project.meshStatus,'ready');
assert.equal(readback.project.viewerPainted,false);
assert.equal(after.revision,baseline.project.revision);
assert.equal(after.provenance.source.sha256,sha(source));assert.equal(after.provenance.source.byteLength,source.length);
const assetHashes=response=>{
  const assets=response.assets??{};assert.ok(assets&&typeof assets==='object'&&!Array.isArray(assets));
  return Object.fromEntries(Object.entries(assets).map(([path,asset])=>{
    assert.ok(asset&&typeof asset==='object'&&!Array.isArray(asset));assert.match(asset.sha256,/^[a-f0-9]{64}$/);
    return [path,asset.sha256];
  }));
};
const archivedAssets=assetHashes(savedBefore.project);
assert.equal(digest(archivedAssets),before.provenance.assetsSha256);
assert.deepEqual(assetHashes(savedBefore.revision),archivedAssets);
for(const response of [readback.project,readback.revision]){
  assert.deepEqual(assetHashes(response),archivedAssets,'Saved asset manifest changed');
  assert.equal(digest(assetHashes(response)),after.provenance.assetsSha256,'Artifact/readback asset identity differs');
}
assert.equal(after.provenance.assetsSha256,before.provenance.assetsSha256,'Asset manifest changed');
assert.equal(after.provenance.producer.runtimeSourceHash,expectedRuntime,'Wrong runtime producer');
assert.equal(after.provenance.producer.serverBuild,readback.project.serverBuild,'Readback/producer build mismatch');
for(const [name,urlField]of [['api','meshDownloadUrl'],['cdn','meshUrl']]){
  const row=downloads[name];assert.equal(row.http_status,200);assert.equal(row.bytes,afterRaw.length);assert.equal(row.sha256,sha(afterRaw));
  assert.equal(row.url,readback.project[urlField]);
  const url=new URL(row.url),slug=baseline.project.slug,version=baseline.project.revision;
  assert.equal(url.origin,name==='api'?'https://api.kernelcad.com':'https://mesh.kernelcad.com');
  assert.equal(url.pathname,name==='api'?`/api/v1/projects/${slug}/revisions/${version}/mesh-artifact`:`/mesh-artifacts/${slug}/v${version}.json`);
  assert.equal(url.username,'');assert.equal(url.password,'');assert.equal(url.hash,'');
  assert.deepEqual([...url.searchParams.keys()].sort(),name==='api'?['download','provenance']:['provenance']);
  assert.deepEqual(url.searchParams.getAll('provenance'),[digest(after.provenance)],'Stale artifact provenance URL pin');
  if(name==='api')assert.deepEqual(url.searchParams.getAll('download'),['1']);
}
const withoutProducer=artifact=>{const copy={...artifact};delete copy.provenance;return copy;};
const beforeGeometry=withoutProducer(before),afterGeometry=withoutProducer(after);
const changedKeys=Array.from(new Set([...Object.keys(beforeGeometry),...Object.keys(afterGeometry)])).sort()
  .filter(key=>canonical(beforeGeometry[key])!==canonical(afterGeometry[key]));
const featureChanges=[];
for(let i=0;i<Math.max(before.features.length,after.features.length);i++){
  const a=before.features[i],b=after.features[i];if(canonical(a)===canonical(b))continue;
  const faces=[];for(let f=0;f<Math.max(a?.faces?.length??0,b?.faces?.length??0);f++){
    if(canonical(a?.faces?.[f])!==canonical(b?.faces?.[f]))faces.push(f);
  }
  featureChanges.push({index:i,before_id:a?.featureId??null,after_id:b?.featureId??null,changed_face_indices:faces});
}
const passed=changedKeys.length===0;
const result={schema:'labwired-examples/pathfinder-cad-artifact-comparison/v1',status:passed?'passed':'failed',
  source_sha256:sha(source),slug:baseline.project.slug,revision:baseline.project.revision,
  before:{raw_sha256:sha(beforeRaw),raw_bytes:beforeRaw.length,producer:before.provenance.producer,canonical_without_provenance_sha256:digest(beforeGeometry)},
  after:{artifact_path:relative(root,resolve(artifactPath)),raw_sha256:sha(afterRaw),raw_bytes:afterRaw.length,producer:after.provenance.producer,provenance_sha256:digest(after.provenance),canonical_without_provenance_sha256:digest(afterGeometry)},
  evidence:{readback_path:relative(root,resolve(readbackPath)),readback_sha256:sha(readFileSync(resolve(readbackPath))),downloads_path:relative(root,resolve(downloadsPath)),downloads_sha256:sha(readFileSync(resolve(downloadsPath))),comparator_sha256:sha(readFileSync(fileURLToPath(import.meta.url)))},
  comparison:{excluded_top_level_fields:['provenance'],object_keys_sorted:true,array_order_preserved:true,exact_numbers:true,negative_zero_preserved:true,changed_top_level_keys:changedKeys,changed_features:featureChanges,feature_count:after.features.length,face_count:after.features.reduce((n,f)=>n+f.faces.length,0)},
  mutation_performed:false,viewer_paint_observed:false,physical_acceptance:false};
console.log(JSON.stringify(result,null,2));
if(!passed)process.exitCode=1;
