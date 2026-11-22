import { readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { planMultiChipRun, planWorldLinks, worldEnvironmentYaml, mcuSubdiagram, migrateToV2, boardKeyForPart } from '/data/lw-hosted-thrust-body-20261121/packages/board-config/dist/index.js';
import { SimulatorBridge } from '/data/lw-hosted-thrust-body-20261121/packages/ui/src/wasm/simulator-bridge.ts';
import { FlightBodyRuntime } from '/data/lw-hosted-thrust-body-20261121/packages/playground/src/mechanical/flightRuntime.ts';
import { FlightRuntimeSources } from '/data/lw-hosted-thrust-body-20261121/packages/playground/src/mechanical/flightRuntimeSources.ts';
import { initSync, WasmWorld } from './candidate-wasm.mjs';

const dir = '/data/work-evidence/quadrotor-world-adapter-20261121/candidate-altitude-damping';
const duration = Number(process.argv[2] ?? '15');
const faultTime = Number(process.argv[3] ?? 'Infinity');
const tag = process.argv[4] ?? 'initial';
const faultKind = process.argv[5] ?? 'button';
const started = Date.now();
const project = JSON.parse(readFileSync(`${dir}/project-readback.json`, 'utf8'));
const plan = planMultiChipRun(project.diagram);
writeFileSync(`${dir}/plan.json`, JSON.stringify(plan, null, 2));
if (!plan.ok) throw new Error(`Invalid plan: ${JSON.stringify(plan.nodes.map(n => ({ id: n.id, diagnostics: n.diagnostics })))}`);
const ids = plan.nodes.map(n => n.id);
const environmentYaml = worldEnvironmentYaml({ name: `Quadrotor exact draft ${project.content_hash}`, nodeIds: ids,
  links: planWorldLinks(plan), nets: plan.gpioNets, canBuses: plan.canBuses });
writeFileSync(`${dir}/environment.yaml`, environmentYaml);
const assets = ['candidate-wasm.mjs', 'candidate-wasm.wasm', ...ids.map(id => `${id}.elf`)].map(name => {
  const b = readFileSync(`${dir}/${name}`); return { name, size: b.length, sha256: createHash('sha256').update(b).digest('hex') };
});
writeFileSync(`${dir}/runtime-assets.json`, JSON.stringify(assets, null, 2));
initSync({ module: readFileSync(`${dir}/candidate-wasm.wasm`) });
const world = WasmWorld.new_from_resolved(environmentYaml, plan.nodes.map(n => ({ id: n.id,
  system_yaml: n.systemYaml, chip_yaml: n.chipYaml, firmware: new Uint8Array(readFileSync(`${dir}/${n.id}.elf`)) })));
const bridges = new Map(plan.nodes.map(n => [n.id, SimulatorBridge.fromWorldNode(world, n.id, n.systemYaml!, n.chipYaml)]));
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
    world.step_batch(1000); batches++;
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
        motors: [...bridges].flatMap(([id, b]) => b.getActuatorStates().map(m => ({ owner: id, ...m }))), errors };
      appendFileSync(trace, JSON.stringify(row) + '\n');
      console.log(JSON.stringify({ seconds: +seconds.toFixed(3), wallSeconds: row.wallSeconds,
        altitudeM: body?.frame.altitudeM, mode: body?.frame.mode, feedbackWrites, errors }));
      nextReport += 0.01;
    }
    if (errors.length) { stopped = 'invalid-runtime'; break; }
    if (Date.now() - started > 12 * 60 * 1000) { stopped = 'wall-budget'; break; }
  }
} catch (e) { errors.push({ controllerId: 'harness', message: String(e) }); stopped = 'exception'; }
const result = { kind: 'direct-native-world-with-existing-flight-runtime', projectId: project.id,
  contentHash: project.content_hash, baseContentHash: project.base_content_hash, candidate: project.validation_candidate, duration, faultTime: Number.isFinite(faultTime) ? faultTime : null, stopped,
  seconds, wallSeconds: (Date.now() - started) / 1000, batches, maxAltitudeM, faultInjected, faultKind, faultReleased, faultReleaseRejected, feedbackWrites, errors,
  final: runtime.getDiagnostics(), uart, seed, assets };
writeFileSync(`${dir}/${tag}-result.json`, JSON.stringify(result, null, 2));
console.log(JSON.stringify({ ...result, seed: undefined, assets: undefined }));
sampler.dispose(); world.free();
if (errors.length || stopped !== 'duration') process.exitCode = 1;
