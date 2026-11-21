#!/usr/bin/env node
// Static source/provenance checks only. Runtime servo motion and physical power
// remain unverified; this is NOT a replacement for compile()/run()/verify().
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const at = 'examples/robotics/axiom-h1/';
const original = JSON.parse(readFileSync(`${at}project.input.json`, 'utf8'));
const record = JSON.parse(readFileSync(`${at}20-servo-candidate.json`, 'utf8'));
const candidate = record.candidate;
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
assert.equal(record.schema, 'labwired-examples/axiom-pca-actuator-candidate/v1');
assert.equal(record.source_project_id, 'e6b30d45ba55e64aa450a2aa292edd4b');
assert.equal(candidate.board, original.board);
assert.equal(candidate.source, original.source);
assert.equal(candidate.language, original.language);
assert.equal(candidate.entry_path, original.entry_path);
assert.deepEqual(candidate.stimuli, original.stimuli);
assert.deepEqual(candidate.requirements, original.requirements);
assert.equal(record.joint_order.length, 20);
assert.equal(new Set(record.joint_order).size, 20);
assert.equal(candidate.diagram.parts.length, original.diagram.parts.length + 20);
assert.equal(candidate.diagram.wires.length, original.diagram.wires.length + 40);
assert.equal(record.acceptance.firmware_model_verdict, 'not_run');
assert.equal(record.acceptance.servo_motion, 'not_run');
assert.equal(record.acceptance.physical_hardware, 'not_run');
for (const part of original.diagram.parts)
  assert.deepEqual(candidate.diagram.parts.find((p) => p.id === part.id), part);
for (const wire of original.diagram.wires)
  assert.ok(candidate.diagram.wires.some((w) => JSON.stringify(w) === JSON.stringify(wire)), `original wire missing: ${JSON.stringify(wire)}`);
function missingServoBindings(d) {
  const missing = [];
  for (let i = 0; i < 20; i++) {
    const id = `servo${i}`;
    const part = d.parts.find((p) => p.id === id);
    assert.equal(part?.type, 'servo', id);
    assert.equal(part.attrs?.label, record.joint_order[i]);
    const pca = i < 16 ? 'pwm1' : 'pwm2';
    const channel = `LED${i % 16}`;
    const pwm = d.wires.filter((w) => w.from.part === pca && w.from.pin === channel && w.to.part === id && w.to.pin === 'PWM');
    if (pwm.length !== 1) missing.push(id);
    assert.ok(d.wires.some((w) => w.from.part === 'mcu' && w.from.pin === 'GND' && w.to.part === id && w.to.pin === 'GND'));
    // No model of power distribution. Do not make VCC a bogus 3V3 supply.
    assert.ok(!d.wires.some((w) => (w.from.part === id && w.from.pin === 'VCC') || (w.to.part === id && w.to.pin === 'VCC')));
  }
  return missing;
}
assert.deepEqual(missingServoBindings(candidate.diagram), []);
const negative = structuredClone(candidate.diagram);
negative.wires = negative.wires.filter((w) => !(w.from.part === 'pwm2' && w.from.pin === 'LED3' && w.to.part === 'servo19'));
assert.deepEqual(missingServoBindings(negative), ['servo19']);
for (const [board, address, oePin] of [['pwm1','0x40','GPIO3'],['pwm2','0x41','GPIO4']]) {
  assert.equal(candidate.diagram.parts.find((p) => p.id === board)?.attrs?.i2c_address, address);
  assert.ok(candidate.diagram.wires.some((w) => w.from.part === 'mcu' && w.from.pin === oePin && w.to.part === board && w.to.pin === 'OE'));
}
// A source-bound live receipt is NOT an assertion that unmodeled servos move.
const live = JSON.parse(readFileSync(`${at}live-20-servo-evidence.json`, 'utf8'));
assert.equal(live.schema, 'labwired-axiom-live-candidate-model-proof-v1');
assert.equal(live.project_id, 'dab8622b41adbf3b9e2175909146b207');
assert.match(live.content_hash, /^[a-f0-9]{64}$/);
assert.equal(live.content_hash, live.verified_hash);
const powered = JSON.parse(readFileSync(`${at}20-servo-powered-input.json`, 'utf8'));
assert.equal(powered.source, candidate.source);
assert.equal(powered.language, candidate.language);
assert.equal(powered.entry_path, candidate.entry_path);
assert.deepEqual(powered.stimuli, candidate.stimuli);
assert.deepEqual(powered.requirements, candidate.requirements);
assert.deepEqual(powered.diagram.parts.slice(0, candidate.diagram.parts.length), candidate.diagram.parts);
assert.deepEqual(powered.diagram.wires.slice(0, candidate.diagram.wires.length), candidate.diagram.wires);
assert.equal(powered.diagram.parts.length, 31);
assert.equal(powered.diagram.wires.length, 88);
assert.equal(powered.diagram.parts.at(-1)?.id, 'servo_rail');
assert.equal(powered.diagram.parts.at(-1)?.type, 'dc-barrel-jack');
for (let i = 0; i < 20; i++) {
  const vcc = powered.diagram.wires.filter(w => w.from.part === 'servo_rail' && w.from.pin === '+' && w.to.part === `servo${i}` && w.to.pin === 'VCC');
  assert.equal(vcc.length, 1, `servo${i} missing or duplicate supply`);
}
assert.ok(powered.diagram.wires.some(w => w.from.part === 'servo_rail' && w.from.pin === '-' && w.to.part === 'mcu' && w.to.pin === 'GND'));
assert.ok(!powered.diagram.wires.some(w => w.from.part === 'mcu' && w.from.pin === '3V3' && w.to.pin === 'VCC' && /^servo\d+$/.test(w.to.part)));
const brokenRail = structuredClone(powered.diagram);
brokenRail.wires = brokenRail.wires.filter(w => !(w.from.part === 'servo_rail' && w.to.part === 'servo19'));
assert.equal(brokenRail.wires.filter(w => w.from.part === 'servo_rail' && w.to.part === 'servo19').length, 0);
assert.equal(live.source_candidate, 'examples/robotics/axiom-h1/20-servo-powered-input.json');
assert.equal(live.diagram_part_count, powered.diagram.parts.length);
assert.equal(live.diagram_wire_count, powered.diagram.wires.length);
assert.equal(live.power_assumption.physical_supply_verified, false);
assert.equal(live.circuit_validation.errors, 0);
assert.equal(live.circuit_validation.warnings_by_code.SERVO_EXPANDER_UNMODELED, 20);
assert.equal(live.circuit_validation.unconnected_supply_warnings, 0);
assert.deepEqual(live.requirements.map((item) => [item.id, item.status]), candidate.requirements.map((item) => [item.id, 'verified']));
assert.ok(live.evidence.some((e) => e.kind === 'sim_verify' && e.status === 'model_verified' && e.fresh === true && e.content_hash === live.content_hash));
assert.ok(live.unverified_scope.some((item) => item.includes('servo')));
console.log(`PASS AXIOM 20-servo source ${hash(original.source).slice(0,12)}…; 20 one-to-one PCA PWM outputs, OE on GPIO3/4, negative control rejected`);
console.log('Status: saved controller 3/3 verified; power idealized; servo movement, physical power capacity, CAD motion and hardware NOT verified.');
