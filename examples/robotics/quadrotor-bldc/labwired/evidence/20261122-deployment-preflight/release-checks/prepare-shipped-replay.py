#!/usr/bin/env python3
"""Reuse the archived replay. Change only artifact loading and provenance gates."""
from pathlib import Path
import difflib,hashlib,json
base=Path('/data/lw-quadrotor-examples-20261122/examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight')
out=Path(__file__).resolve().parent
original=(base/'replay-native-world.mts').read_text();s=original
old="import { initSync, WasmWorld } from './runtime/candidate-wasm.mjs';"
new=r"""// The module and binary are unchanged response bytes from the live deployment.
const shipped = process.env.LABWIRED_SHIPPED_RUNTIME;
if (!shipped) throw new Error('Set LABWIRED_SHIPPED_RUNTIME to fetch-shipped-runtime output.');
const deployedReceiptBytes = readFileSync(resolve(shipped, 'download-receipt.json'));
const deployed = JSON.parse(deployedReceiptBytes.toString('utf8'));
if (deployed.kind !== 'downloaded-production-runtime-not-yet-qualified') throw new Error('Wrong deployed artifact receipt kind');
const deployedManifestBytes = readFileSync(resolve(shipped, 'build-manifest.json'));
if (createHash('sha256').update(deployedManifestBytes).digest('hex') !== deployed.manifestSha256) throw new Error('Deployed build manifest changed');
const deployedManifest = JSON.parse(deployedManifestBytes.toString('utf8'));
if (deployedManifest.commit !== deployed.buildCommit || !/^[0-9a-f]{40}$/.test(deployedManifest.commit)) throw new Error('Deployed build commit differs from manifest');
if (!Array.isArray(deployedManifest.assets?.wasm)) throw new Error('Deployed manifest has no WASM asset list');
for (const name of ['engine.mjs', 'engine.wasm']) {
  const expected = deployed.assets.find((a: { name: string }) => a.name === name);
  const bytes = readFileSync(resolve(shipped, name));
  if (!expected || bytes.length !== expected.size || createHash('sha256').update(bytes).digest('hex') !== expected.sha256) throw new Error(`Deployed artifact changed: ${name}`);
  const suffix = name === 'engine.mjs' ? /^\/wasm\/labwired_wasm\.[0-9a-f]+\.js$/ : /^\/wasm\/labwired_wasm_bg\.[0-9a-f]+\.wasm$/;
  const paths = deployedManifest.assets.wasm.filter((path: string) => suffix.test(path));
  if (paths.length !== 1 || expected.url !== 'https://app.labwired.com' + paths[0]) throw new Error(`Deployed asset is not bound to the stored manifest: ${name}`);
}
const { initSync, WasmWorld } = await import(pathToFileURL(resolve(shipped, 'engine.mjs')).href);"""
assert s.count(old)==1;s=s.replace(old,new)
old='const bundle = dirname(fileURLToPath(import.meta.url));'
assert s.count(old)==1;s=s.replace(old,'const bundle = '+json.dumps(str(base))+';')
old='if (appHead !== receipt.appCommit) throw new Error(`Expected app ${receipt.appCommit}, got ${appHead}`);'
new='if (appHead !== deployed.buildCommit) throw new Error(`Expected deployed app ${deployed.buildCommit}, got ${appHead}`);'
assert s.count(old)==1;s=s.replace(old,new)
old="""const readAsset = (name: string): Uint8Array => name === 'candidate-wasm.mjs'
  ? readFileSync(resolve(bundle, 'runtime', name))
  : gunzipSync(readFileSync(resolve(bundle, name.endsWith('.elf') ? 'firmware' : 'runtime', name + '.gz')));"""
new="""const readAsset = (name: string): Uint8Array => name === 'candidate-wasm.mjs'
  ? readFileSync(resolve(shipped, 'engine.mjs'))
  : name === 'candidate-wasm.wasm' ? readFileSync(resolve(shipped, 'engine.wasm'))
    : gunzipSync(readFileSync(resolve(bundle, 'firmware', name + '.gz')));"""
assert s.count(old)==1;s=s.replace(old,new)
old="kind: 'direct-native-world-with-existing-flight-runtime', appCommit: appHead"
new="kind: 'direct-native-world-with-deployed-wasm-and-existing-flight-runtime', deployedBuildCommit: deployed.buildCommit, deployedManifestSha256: deployed.manifestSha256, deployedReceiptSha256: createHash('sha256').update(deployedReceiptBytes).digest('hex'), helperBuildReceiptSha256: createHash('sha256').update(helperBuildBytes).digest('hex'), qualificationBaselineAppCommit: receipt.appCommit, appCommit: appHead"
assert s.count(old)==1;s=s.replace(old,new)
old="const receipt = JSON.parse(readFileSync(resolve(bundle, 'acceptance.json'), 'utf8'));"
new="""// Read expected identities from the reviewed immutable examples commit, not a mutable sidecar.
const archiveCommit = 'cbb23bc84bf5d5f2e3ae1346893c99de14aa18fe';
const archivePrefix = 'examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight/';
const archiveManifest = JSON.parse(execFileSync('git', ['show', `${archiveCommit}:${archivePrefix}artifacts.json`], { cwd: bundle, encoding: 'utf8' }));
for (const name of ['acceptance.json', 'candidate-project.json', 'resolved-plan.json.gz']) {
  if (createHash('sha256').update(readFileSync(resolve(bundle, name))).digest('hex') !== archiveManifest.files[name].sha256) {
    throw new Error(`Reviewed source/plan archive changed: ${name}`);
  }
}
const receipt = JSON.parse(readFileSync(resolve(bundle, 'acceptance.json'), 'utf8'));"""
assert s.count(old)==1;s=s.replace(old,new)
old="writeFileSync(`${dir}/runtime-assets.json`, JSON.stringify(assets, null, 2));"
new="""for (const asset of assets.filter(a => a.name.endsWith('.elf'))) {
  const expected = archiveManifest.files[`firmware/${asset.name}.gz`]?.uncompressedSha256;
  if (!expected || asset.sha256 !== expected) throw new Error(`Reviewed ELF identity changed: ${asset.name}`);
}
writeFileSync(`${dir}/runtime-assets.json`, JSON.stringify(assets, null, 2));"""
assert s.count(old)==1;s=s.replace(old,new)
old="const fromApp = (path: string) => import(pathToFileURL(resolve(app, path)).href);"
new="""// Generated dist is ignored by git, so require a successful normal build at this exact commit.
const helperDirectory = process.env.LABWIRED_REPLAY_HELPERS;
if (!helperDirectory) throw new Error('Set LABWIRED_REPLAY_HELPERS to the exact-commit helper build receipt directory.');
const helperBuildBytes = readFileSync(resolve(helperDirectory, 'helper-build-receipt.json'));
const helperBuild = JSON.parse(helperBuildBytes.toString('utf8'));
if (helperBuild.kind !== 'exact-commit-planner-helper-build' || helperBuild.exitCode !== 0 || helperBuild.appCommit !== appHead || helperBuild.coreCommit !== coreHead) throw new Error('Planner helpers were not built successfully at the qualified commit');
if (helperBuild.appTree !== execFileSync('git', ['rev-parse', 'HEAD^{tree}'], { cwd: app, encoding: 'utf8' }).trim() || JSON.stringify(helperBuild.command) !== JSON.stringify(['npm', 'run', 'build', '-w', 'packages/board-config'])) throw new Error('Planner helper build recipe or source tree differs');
if (helperBuild.lockfileSha256 !== createHash('sha256').update(readFileSync(resolve(app, 'package-lock.json'))).digest('hex')) throw new Error('Planner helper dependency lock changed');
if (helperBuild.buildLogSha256 !== createHash('sha256').update(readFileSync(resolve(helperDirectory, 'build.log'))).digest('hex')) throw new Error('Planner helper build log changed');
const requiredHelpers = ['index.js', 'index.mjs', 'registry.js', 'registry.mjs', 'svd.js', 'svd.mjs', 'labwired-lower.mjs'];
for (const name of requiredHelpers) {
  const path = `packages/board-config/dist/${name}`;
  const artifact = helperBuild.artifacts.find((a: { path: string }) => a.path === path);
  const bytes = readFileSync(resolve(app, path));
  if (!artifact || artifact.size !== bytes.length || artifact.sha256 !== createHash('sha256').update(bytes).digest('hex')) throw new Error(`Generated planner helper changed: ${name}`);
}
const fromApp = (path: string) => import(pathToFileURL(resolve(app, path)).href);"""
assert s.count(old)==1;s=s.replace(old,new)
(out/'replay-shipped-native-world.mts').write_text(s)
(out/'shipped-replay-adapter.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='archived/replay-native-world.mts',tofile='staged/replay-shipped-native-world.mts')))
print(json.dumps({'kind':'staged-replay-asset-loader-change','originalSha256':hashlib.sha256(original.encode()).hexdigest(),'adapterSha256':hashlib.sha256(s.encode()).hexdigest(),'executed':False,'modelOrClockChanges':False},indent=2))
