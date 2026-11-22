/** Read the real production build and immutable engine bytes after deployment.
 * Usage: node fetch-shipped-runtime.mjs EXPECTED_MAIN_COMMIT OUTPUT_DIRECTORY
 * Writes a fresh artifact directory. It never builds or changes a served asset.
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { validateBuildManifest } from '/data/lw-quadrotor-app-20261122/packages/playground/scripts/check-live-build-manifest.mjs';
const [commit, destination] = process.argv.slice(2);
if (!/^[0-9a-f]{40}$/.test(commit ?? '') || !destination) throw new Error('Expected exact main SHA and a fresh output directory');
const base='https://app.labwired.com';
const manifestResponse=await fetch(base+'/build-manifest.json', { cache:'no-store' });
if(!manifestResponse.ok) throw new Error(`Build manifest HTTP ${manifestResponse.status}`);
const manifestBytes=new Uint8Array(await manifestResponse.arrayBuffer());
const manifest=validateBuildManifest(JSON.parse(new TextDecoder().decode(manifestBytes)),commit);
const js=manifest.assets.wasm.filter(p=>/^\/wasm\/labwired_wasm\.[0-9a-f]+\.js$/.test(p));
const wasm=manifest.assets.wasm.filter(p=>/^\/wasm\/labwired_wasm_bg\.[0-9a-f]+\.wasm$/.test(p));
if(js.length!==1||wasm.length!==1) throw new Error('Expected one hashed engine JS/WASM pair in the deployed manifest');
const assets=[];
for(const [path,name] of [[js[0],'engine.mjs'],[wasm[0],'engine.wasm']]) {
 const response=await fetch(base+path,{cache:'no-store'});
 const contentType=response.headers.get('content-type')??'';
 if(!response.ok||contentType.includes('text/html')) throw new Error(`${path} returned ${response.status} ${contentType}`);
 const bytes=new Uint8Array(await response.arrayBuffer());
 if(name.endsWith('.wasm')&&[0,97,115,109,1,0,0,0].some((v,i)=>bytes[i]!==v)) throw new Error('Invalid WebAssembly file header');
 const digest=createHash('sha256').update(bytes).digest('hex');
 const fingerprint=path.match(/\.([0-9a-f]{12})\.(?:js|wasm)$/)?.[1];
 if(fingerprint!==digest.slice(0,12)) throw new Error(`${path} does not match its content-hashed filename`);
 assets.push({name,url:base+path,sha256:digest,size:bytes.length,contentType,bytes});
}
await mkdir(resolve(destination),{recursive:false});
await writeFile(resolve(destination,'build-manifest.json'),manifestBytes,{flag:'wx'});
for(const asset of assets) await writeFile(resolve(destination,asset.name),asset.bytes,{flag:'wx'});
const receipt={kind:'downloaded-production-runtime-not-yet-qualified',fetchedAt:new Date().toISOString(),
 buildCommit:commit,manifestUrl:base+'/build-manifest.json',
 manifestSha256:createHash('sha256').update(manifestBytes).digest('hex'),
 assets:assets.map(({bytes,...metadata})=>metadata),nativeOraclePassed:false,browserFlightPassed:false};
await writeFile(resolve(destination,'download-receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(receipt,null,2));
