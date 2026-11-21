#!/usr/bin/env node
// Runs unchanged AXIOM firmware in the real engine. Only SimInput is driven.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const { values } = parseArgs({ options: {
  app: { type: 'string' }, wasm: { type: 'string' },
  flash: { type: 'string' }, output: { type: 'string' },
} });
for (const name of ['app', 'wasm', 'flash', 'output']) {
  assert.ok(values[name], `Required: --${name}. See the AXIOM README.`);
}
const app = resolve(values.app);
const wasm = resolve(values.wasm);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const read = path => readFileSync(path);
const example = resolve(root, 'examples/robotics/axiom-h1');
const project = JSON.parse(read(resolve(example, '20-servo-powered-input.json')));
const inputs = JSON.parse(read(resolve(example, 'actuator-runtime-inputs.json')));
const flash = read(resolve(values.flash));
assert.equal(sha(project.source), inputs.source_sha256, 'firmware source must match compiled flash');
assert.equal(sha(flash), inputs.combined_flash_sha256, 'flash bytes must match the source compile receipt');
const { compile } = await import(pathToFileURL(resolve(app, 'packages/board-config/dist/index.mjs')));
const compiled = compile(project.diagram);
assert.equal(compiled.ok, true);
assert.equal((compiled.systemYaml.match(/source_oe_pin:/g) ?? []).length, 20);
const wasmBytes = read(resolve(wasm, 'labwired_wasm_bg.wasm'));
const runtime = await import(pathToFileURL(resolve(wasm, 'labwired_wasm.js')));
if (runtime.initSync) runtime.initSync({ module: wasmBytes });
const WasmSimulator = runtime.WasmSimulator ?? runtime.default?.WasmSimulator;
assert.ok(WasmSimulator, 'the real engine must expose WasmSimulator');
const blobs = {
  esp32c3_irom: read(resolve(app, 'core/crates/core/roms/esp32c3/esp32c3_rom.bin')),
  esp32c3_drom: read(resolve(app, 'core/crates/core/roms/esp32c3/esp32c3_drom.bin')),
  esp32c3_flash: flash,
  labwired_esp32c3_flash_fast_start: new Uint8Array([1]),
};
const sim = WasmSimulator.new_from_config(compiled.systemYaml, compiled.chipYaml, new Uint8Array(), blobs);
const receipt = {
  schema: 'labwired-examples/axiom-actuator-runtime/v1',
  proof_class: 'local_model_runtime',
  started_at: new Date().toISOString(),
  core_commit: read(resolve(wasm, 'core-commit.txt')).toString().trim(),
  app_commit: execFileSync('git', ['-C', app, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  source_sha256: sha(project.source), diagram_sha256: sha(JSON.stringify(project.diagram)),
  system_yaml_sha256: sha(compiled.systemYaml), chip_yaml_sha256: sha(compiled.chipYaml),
  wasm_sha256: sha(wasmBytes), flash_sha256: sha(flash),
  simulation_options: { flash_fast_start: true, idle_fast_forward: false, peripheral_tick_interval: 1 },
  input_method: 'unchanged firmware and generic set_inputs; no debugger register writes',
  compile_diagnostics: compiled.diagnostics, samples: [], serial: '',
  limits: [
    'SG90 pulse-to-angle model stand-ins; physical AXIOM joint calibration is not established.',
    'active and angle retain the last modeled command while OE is disabled.',
    'Ideal 5 V source; servo current, voltage sag, torque and physical hardware are not verified.',
    'No executable KernelCAD joint graph, hierarchical CAD motion or MuJoCo coupling is demonstrated.',
    'Local exact-source engine evidence; this does not establish deployment or hosted project verification.',
  ],
};
let steps = 0;
function capture(phase) {
  const row = { phase, steps, pc: sim.get_pc(), actuators: sim.get_actuator_states() };
  receipt.samples.push(row);
  return row;
}
function run(phase, budget) {
  for (let n = 0; n < budget; n += 500_000) {
    const requested = Math.min(500_000, budget - n);
    const done = sim.step_batch(requested);
    assert.equal(done, requested, `${phase}: firmware stopped before the instruction budget`);
    steps += done;
    receipt.serial += new TextDecoder().decode(sim.drain_uart_output());
    if (n % 5_000_000 === 4_500_000) capture(phase);
  }
  const result = capture(phase);
  console.log(`${phase}: ${steps} instructions; ${[...new Set(result.actuators.map(a => a.source_status))].join(', ')}`);
  return result;
}
function sources(row, expected) {
  assert.deepEqual(new Set(row.actuators.map(a => a.id)), new Set(Array.from({ length: 20 }, (_, i) => `servo${i}`)));
  assert.ok(row.actuators.every(a => a.source_status === expected), `${row.phase}: every source must be ${expected}`);
}
function commands(row) {
  return row.actuators.map(({ id, active, angle, pulse_us }) => ({ id, active, angle, pulse_us }));
}
try {
  sim.set_inputs(project.stimuli);
  const initial = capture('initial');
  assert.ok(initial.actuators.every(a => !a.active && a.pulse_us === 0));
  const normal = run('normal', 120_000_000);
  sources(normal, 'modeled_pwm');
  assert.ok(normal.actuators.every(a => a.active && a.pulse_us > 0));
  receipt.command_ranges = normal.actuators.map(a => {
    const states = receipt.samples.filter(s => s.phase === 'normal').map(s => s.actuators.find(v => v.id === a.id)).filter(v => v?.active);
    return { id: a.id, min_angle: Math.min(...states.map(v => v.angle)), max_angle: Math.max(...states.map(v => v.angle)), initial_command_received: true };
  });
  for (const id of ['servo0', 'servo2', 'servo4']) {
    const range = receipt.command_ranges.find(r => r.id === id);
    assert.ok(range.max_angle > range.min_angle, `${id}: the firmware must change its command`);
  }
  sim.set_inputs([{ component: 'tof', channel: 'distance', value: 100 }]);
  const blocked = run('proximity_blocked', 10_000_000); sources(blocked, 'disabled');
  const held = run('proximity_held', 5_000_000); sources(held, 'disabled');
  assert.deepEqual(commands(held), commands(blocked), 'disabled PCA sources must not update commands');
  sim.set_inputs([{ component: 'tof', channel: 'distance', value: 1500 }]);
  sources(run('proximity_recovered', 10_000_000), 'modeled_pwm');
  sim.set_inputs([{ component: 'imu', channel: 'ax', value: 1 }, { component: 'imu', channel: 'az', value: 1 }]);
  sources(run('tilt_blocked', 10_000_000), 'disabled');
  sim.set_inputs([{ component: 'imu', channel: 'ax', value: 0 }, { component: 'imu', channel: 'az', value: 1 }]);
  sources(run('tilt_recovered', 10_000_000), 'modeled_pwm');
  sim.set_inputs([{ component: 'estop', channel: 'pressed', value: 1 }]);
  const stop = run('estop_pressed', 10_000_000); sources(stop, 'disabled');
  sim.set_inputs([{ component: 'estop', channel: 'pressed', value: 0 }]);
  const released = run('estop_released_latched', 10_000_000); sources(released, 'disabled');
  assert.deepEqual(commands(released), commands(stop), 'releasing E-stop must not reset the firmware latch');
  for (const marker of ['AXIOM_PCA_I2C:OK', 'AXIOM_CLEAR_PATH', 'AXIOM_STATE:WAVE', 'AXIOM_STATE:PROX_STOP', 'AXIOM_STATE:TILT_STOP', 'AXIOM_STATE:ESTOP']) {
    assert.ok(receipt.serial.includes(marker), `firmware must report ${marker}`);
  }
  const disconnected = structuredClone(project.diagram);
  disconnected.wires = disconnected.wires.filter(w => !(w.to.part === 'servo19' && w.to.pin === 'PWM'));
  const negative = compile(disconnected);
  assert.ok(!negative.systemYaml.includes('id: "servo19"'));
  receipt.disconnected_signal = { servo: 'servo19', emitted: false, diagnostics: negative.diagnostics.filter(d => String(d.message).includes('servo19')) };
  receipt.status = 'passed';
  console.log('PASS: 20 initial commands, three animated channels, proximity and tilt recovery, latched E-stop, disconnected signal rejected.');
} catch (error) {
  receipt.status = 'failed'; receipt.error = String(error); process.exitCode = 1;
  console.error(String(error));
} finally {
  receipt.steps = steps; receipt.finished_at = new Date().toISOString();
  writeFileSync(resolve(values.output), `${JSON.stringify(receipt, null, 2)}\n`);
  sim.free();
}
