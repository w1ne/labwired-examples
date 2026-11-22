import { readFileSync, writeFileSync, appendFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';
import { execFileSync } from 'node:child_process';
// The module and binary are unchanged response bytes from the live deployment.
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
const { initSync, WasmWorld } = await import(pathToFileURL(resolve(shipped, 'engine.mjs')).href);

// This is a driver for the existing production World and flight runtime.
// The archived module/ELFs and the pinned app source are the only simulators.
const bundle = "/data/lw-quadrotor-examples-20261122/examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight";
// Read expected identities from the reviewed immutable examples commit, not a mutable sidecar.
const archiveCommit = 'cbb23bc84bf5d5f2e3ae1346893c99de14aa18fe';
const archivePrefix = 'examples/robotics/quadrotor-bldc/labwired/evidence/20261122-native-flight/';
const archiveManifest = JSON.parse(execFileSync('git', ['show', `${archiveCommit}:${archivePrefix}artifacts.json`], { cwd: bundle, encoding: 'utf8' }));
for (const name of ['acceptance.json', 'candidate-project.json', 'resolved-plan.json.gz']) {
  if (createHash('sha256').update(readFileSync(resolve(bundle, name))).digest('hex') !== archiveManifest.files[name].sha256) {
    throw new Error(`Reviewed source/plan archive changed: ${name}`);
  }
}
const receipt = JSON.parse(readFileSync(resolve(bundle, 'acceptance.json'), 'utf8'));
const app = process.env.LABWIRED_APP;
if (!app) throw new Error('Set LABWIRED_APP to the pinned LabWired application checkout.');
const appHead = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: app, encoding: 'utf8' }).trim();
if (appHead !== deployed.buildCommit) throw new Error(`Expected deployed app ${deployed.buildCommit}, got ${appHead}`);
const coreHead = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: resolve(app, 'core'), encoding: 'utf8' }).trim();
if (coreHead !== receipt.coreCommit) throw new Error(`Expected core ${receipt.coreCommit}, got ${coreHead}`);
execFileSync('git', ['diff', '--quiet', 'HEAD', '--', 'packages/board-config', 'packages/ui/src/wasm',
  'packages/playground/src/mechanical', 'packages/wasm-runtime'], { cwd: app });
// Generated dist is ignored by git, so require a successful normal build at this exact commit.
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
const fromApp = (path: string) => import(pathToFileURL(resolve(app, path)).href);
const { planMultiChipRun, planWorldLinks, worldEnvironmentYaml, mcuSubdiagram, migrateToV2, boardKeyForPart } =
  await fromApp('packages/board-config/dist/index.js');
const { SimulatorBridge } = await fromApp('packages/ui/src/wasm/simulator-bridge.ts');
const { FlightBodyRuntime } = await fromApp('packages/playground/src/mechanical/flightRuntime.ts');
const { FlightRuntimeSources } = await fromApp('packages/playground/src/mechanical/flightRuntimeSources.ts');
const dir = resolve(process.env.LABWIRED_EVIDENCE_OUT ?? 'quadrotor-native-replay');
mkdirSync(dir, { recursive: true });
const readAsset = (name: string): Uint8Array => name === 'candidate-wasm.mjs'
  ? readFileSync(resolve(shipped, 'engine.mjs'))
  : name === 'candidate-wasm.wasm' ? readFileSync(resolve(shipped, 'engine.wasm'))
    : gunzipSync(readFileSync(resolve(bundle, 'firmware', name + '.gz')));
const duration = Number(process.argv[2] ?? '15');
const faultTime = Number(process.argv[3] ?? 'Infinity');
const tag = process.argv[4] ?? 'initial';
const faultKind = process.argv[5] ?? 'button';
const batchRounds = Number(process.argv[6] ?? '5000');
if (![1000, 5000].includes(batchRounds)) throw new Error('This evidence qualifies 1000 or 5000 World rounds per poll.');
const started = Date.now();
const project = JSON.parse(readFileSync(resolve(bundle, 'candidate-project.json'), 'utf8'));
const plan = planMultiChipRun(project.diagram);
writeFileSync(`${dir}/plan.json`, JSON.stringify(plan, null, 2));
if (!plan.ok) throw new Error(`Invalid plan: ${JSON.stringify(plan.nodes.map(n => ({ id: n.id, diagnostics: n.diagnostics })))}`);
const expectedPlan = JSON.parse(gunzipSync(readFileSync(resolve(bundle, 'resolved-plan.json.gz'))).toString('utf8'));
if (JSON.stringify(plan) !== JSON.stringify(expectedPlan)) throw new Error('Resolved five-MCU plan differs from accepted capture.');
const ids = plan.nodes.map(n => n.id);
const environmentYaml = worldEnvironmentYaml({ name: `Quadrotor exact draft ${project.content_hash}`, nodeIds: ids,
  links: planWorldLinks(plan), nets: plan.gpioNets, canBuses: plan.canBuses });
writeFileSync(`${dir}/environment.yaml`, environmentYaml);
const assets = ['candidate-wasm.mjs', 'candidate-wasm.wasm', ...ids.map(id => `${id}.elf`)].map(name => {
  const b = readAsset(name); return { name, size: b.length, sha256: createHash('sha256').update(b).digest('hex') };
});
for (const asset of assets.filter(a => a.name.endsWith('.elf'))) {
  const expected = archiveManifest.files[`firmware/${asset.name}.gz`]?.uncompressedSha256;
  if (!expected || asset.sha256 !== expected) throw new Error(`Reviewed ELF identity changed: ${asset.name}`);
}
writeFileSync(`${dir}/runtime-assets.json`, JSON.stringify(assets, null, 2));
initSync({ module: readAsset('candidate-wasm.wasm') });
const world = WasmWorld.new_from_resolved(environmentYaml, plan.nodes.map(n => ({ id: n.id,
  system_yaml: n.systemYaml, chip_yaml: n.chipYaml, firmware: new Uint8Array(readAsset(`${n.id}.elf`)) })));
const bridges = new Map(plan.nodes.map(n => [n.id, SimulatorBridge.fromWorldNode(world, n.id, n.systemYaml!, n.chipYaml)]));
// Read-only evidence of the actual L476 output controls. GPIO/TIM register
// reads do not write firmware state or substitute a motor/body observation.
function readU32(owner: string, address: number): number {
  const bytes = world.read_memory(owner, address, 4);
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(0, true);
}
function readGateRegisters() {
  return ids.filter(id => id.startsWith('ctrl')).map(owner => ({ owner,
    gpioBOutput: readU32(owner, 0x48000414), gpioBInput: readU32(owner, 0x48000410),
    gpioCInput: readU32(owner, 0x48000810),
    timer1BreakDeadTime: readU32(owner, 0x40012c44), timer1ChannelEnable: readU32(owner, 0x40012c20),
  }));
}

// Same compile-owned scoping rule as mcuOwnersByPart, without loading the browser UI bundle.
const normalized = migrateToV2(project.diagram);
const owners = new Map<string, string[]>();
for (const id of ids) {
  const scoped = mcuSubdiagram(normalized, id, boardKeyForPart(normalized, id));
  for (const part of scoped.parts) owners.set(part.id, [...(owners.get(part.id) ?? []), id]);
}
const errors: { controllerId: string; message: string }[] = [];
let feedbackWrites = 0;
const runtime = new FlightBodyRuntime(project.diagram.mechanical.electronics.bodies, owners,
  (partId, channel, value) => {
    const targets = owners.get(partId);
    if (!targets || targets.length !== 1) throw new Error(`Ambiguous feedback owner ${partId}`);
    bridges.get(targets[0])!.setInput(channel, value, partId); feedbackWrites++;
  }, (controllerId, error) => errors.push({ controllerId, message: error.message }));
const sources = new Map([...bridges].map(([id, bridge]) => [id, { identity: bridge, kind: 'main' as const,
  read: () => ({ cycles: bridge.totalCycles, clockHz: bridge.engineClockHz(), actuatorStates: bridge.getActuatorStates() }) }]));
const sampler = new FlightRuntimeSources(runtime, () => sources, () => true);
const uart = Object.fromEntries(ids.map(id => [id, '']));
const trace = `${dir}/${tag}.ndjson`; writeFileSync(trace, '');
let nextReport = 0, seconds = 0, faultInjected = false, batches = 0, maxAltitudeM = 0;
let stopped = 'duration', faultReleased = false;
let faultReleaseRejected: string | null = null;
const seed = [...bridges].map(([id, bridge]) => ({ id, cycles: bridge.totalCycles, clockHz: bridge.engineClockHz(),
  actuators: bridge.getActuatorStates(), inputs: bridge.listInputs() }));
writeFileSync(`${dir}/${tag}-seed.json`, JSON.stringify(seed, null, 2));
try {
  runtime.reportConfigurationErrors(); sampler.poll();
  while (seconds < duration) {
    world.step_batch(batchRounds); batches++;
    sampler.poll();
    seconds = Math.min(...[...bridges.values()].map(b => b.totalCycles / b.engineClockHz()));
    for (const [id, bridge] of bridges) uart[id] += new TextDecoder().decode(bridge.drainUartOutput());
    const body = runtime.getObservations()[0];
    if (body) maxAltitudeM = Math.max(maxAltitudeM, body.frame.altitudeM);
    if (seconds >= faultTime && !faultInjected) {
      if (faultKind === 'button') bridges.get('ctrl1')!.setBoardIoInput('fault1', true);
      else bridges.get('ctrl1')!.setInput(faultKind, 1, 'rotor1');
      faultInjected = true;
      appendFileSync(trace, JSON.stringify({ event: 'fault-injected', seconds, fault: faultKind, owner: 'ctrl1' }) + '\n');
    }
    if (faultInjected && !faultReleased && seconds >= faultTime + 0.1) {
      try {
        if (faultKind === 'button') bridges.get('ctrl1')!.setBoardIoInput('fault1', false);
        else bridges.get('ctrl1')!.setInput(faultKind, 0, 'rotor1');
      } catch (e) {
        if (faultKind !== 'overcurrent_fault') throw e;
        faultReleaseRejected = String(e);
      }
      faultReleased = true;
      appendFileSync(trace, JSON.stringify({ event: 'fault-release-attempt', seconds, fault: faultKind, rejected: faultReleaseRejected }) + '\n');
    }
    if (seconds >= nextReport || errors.length) {
      const row = { seconds, wallSeconds: (Date.now() - started) / 1000, feedbackWrites, body,
        motors: [...bridges].flatMap(([id, b]) => b.getActuatorStates().map(m => ({ owner: id, ...m }))), gateRegisters: readGateRegisters(), errors };
      appendFileSync(trace, JSON.stringify(row) + '\n');
      console.log(JSON.stringify({ seconds: +seconds.toFixed(3), wallSeconds: row.wallSeconds,
        altitudeM: body?.frame.altitudeM, mode: body?.frame.mode, feedbackWrites, errors }));
      nextReport += 0.01;
    }
    if (errors.length) { stopped = 'invalid-runtime'; break; }
    if (Date.now() - started > 12 * 60 * 1000) { stopped = 'wall-budget'; break; }
  }
} catch (e) { errors.push({ controllerId: 'harness', message: String(e) }); stopped = 'exception'; }
const result = { kind: 'direct-native-world-with-deployed-wasm-and-existing-flight-runtime', deployedBuildCommit: deployed.buildCommit, deployedManifestSha256: deployed.manifestSha256, deployedReceiptSha256: createHash('sha256').update(deployedReceiptBytes).digest('hex'), helperBuildReceiptSha256: createHash('sha256').update(helperBuildBytes).digest('hex'), qualificationBaselineAppCommit: receipt.appCommit, appCommit: appHead, coreCommit: coreHead, worldRoundsPerPoll: batchRounds, projectId: project.id,
  contentHash: project.content_hash, baseContentHash: project.base_content_hash, candidate: project.validation_candidate, duration, faultTime: Number.isFinite(faultTime) ? faultTime : null, stopped,
  seconds, wallSeconds: (Date.now() - started) / 1000, batches, maxAltitudeM, faultInjected, faultKind, faultReleased, faultReleaseRejected, feedbackWrites, errors,
  final: runtime.getDiagnostics(), uart, seed, assets };
writeFileSync(`${dir}/${tag}-result.json`, JSON.stringify(result, null, 2));
console.log(JSON.stringify({ ...result, seed: undefined, assets: undefined }));
sampler.dispose(); world.free();
if (errors.length || stopped !== 'duration') process.exitCode = 1;
