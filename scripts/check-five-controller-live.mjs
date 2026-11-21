#!/usr/bin/env node
// Immutable readback audit: this is a receipt check, not an active simulation.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const evidence = JSON.parse(readFileSync(
  'examples/robotics/quadrotor-bldc/labwired/evidence/20261121-five-controller-live.json', 'utf8',
));
assert.equal(evidence.schema, 'labwired-live-multi-mcu-proof-v1');
assert.match(evidence.source_reproducer, /^https:\/\/github\.com\/w1ne\/labwired-examples\/pull\/34$/);
for (const [name, project, expectedParts, expectedWires] of [
  ['bench', evidence.bench, 16, 78],
  ['full_wiring_candidate', evidence.full_wiring_candidate, 17, 81],
]) {
  assert.match(project.project_id, /^[a-f0-9]{32}$/);
  assert.equal(project.parts, expectedParts);
  assert.equal(project.wires, expectedWires);
  assert.match(project.content_hash, /^[a-f0-9]{64}$/);
  assert.equal(project.verified_hash, project.content_hash);
  assert.equal(project.evidence.status, 'model_verified');
  assert.equal(project.evidence.fresh, true);
  assert.deepEqual(project.requirements, { passed: 4, total: 4 });
  assert.match(project.run_id, /^world-job:[a-f0-9-]+$/);
}
assert.notEqual(evidence.bench.project_id, evidence.full_wiring_candidate.project_id);
assert.equal(evidence.oracle.length, 4);
for (let i = 1; i <= 4; i++) {
  assert.deepEqual(evidence.oracle[i - 1], { node: `ctrl${i}`, contains: `ROTOR ${i} HALL LOCKED` });
}
assert.ok(evidence.fc_serial_observed.includes('FC TAKEOFF COMMAND'));
assert.ok(evidence.limitations.some(x => x.includes('do not demonstrate body movement')));
assert.ok(evidence.limitations.some(x => x.includes('physical flight')));
const fault = evidence.fault_campaign;
assert.equal(fault.result, 'model_verified');
assert.equal(fault.mcu_count, 5);
assert.deepEqual(fault.assertions, { passed: 9, total: 9 });
assert.match(fault.run_id, /^world-job:[a-f0-9-]+$/);
assert.equal(fault.oracle.length, 9);
assert.ok(fault.oracle.some((c) => c.node === 'fc' && c.contains === 'FC FAULT DETECTED - ALL ESC DISARM'));
assert.ok([2, 3, 4].every(i => fault.oracle.some((c) => c.node === `ctrl${i}` && c.contains === `ESC ${i} DISARMED`)));
assert.ok(fault.source_scope.includes('Test-only'));
assert.ok(fault.limits.some(s => s.includes('No measured motor torque')));
console.log('PASS source-pinned 16/17-part saved five-MCU motor-controller proofs: two current hashes, 4/4 Hall-lock clauses each; direct test-only fault campaign 9/9');
console.log('Scope: motor-control models only; six-DOF flight, safety and physical equivalence NOT verified.');
