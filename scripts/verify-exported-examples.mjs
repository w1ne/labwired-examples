#!/usr/bin/env node
// Structural and provenance checks for saved LabWired example exports.
// These checks do NOT run firmware, reroute PCBs or assert physical acceptance.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const packs = [
  'examples/aerospace/pathfinder-rocket',
  'examples/robotics/axiom-h1',
  'examples/fabrication/a1-mini-printer',
  'examples/robotics/pig-arm',
];

for (const dir of packs) {
  const input = JSON.parse(readFileSync(join(dir, 'project.input.json'), 'utf8'));
  const saved = JSON.parse(readFileSync(join(dir, 'evidence.json'), 'utf8'));
  const readme = readFileSync(join(dir, 'README.md'), 'utf8');
  assert.equal(saved.schema, 'labwired-saved-example-evidence-v1', dir);
  assert.ok(input.name && input.board && input.language, dir);
  assert.ok(typeof input.source === 'string' && input.source.length > 100, dir);
  assert.ok(input.diagram && typeof input.diagram === 'object', dir);
  assert.ok(Array.isArray(input.requirements) && input.requirements.length > 0, dir);
  assert.ok(Array.isArray(input.stimuli), dir);
  assert.equal(input.visibility, 'unlisted', dir);
  assert.equal(input.board, saved.board_id, dir);
  assert.match(saved.content_hash, /^[a-f0-9]{64}$/, dir);
  assert.equal(saved.content_hash, saved.verified_hash, dir);
  assert.equal(saved.requirements.length, input.requirements.length, dir);
  const verification = saved.evidence.find(
    event => event.kind === 'sim_verify'
      && event.status === 'model_verified'
      && event.fresh === true
      && event.content_hash === saved.content_hash,
  );
  assert.ok(verification, `${dir}: missing matching current model verification`);
  for (const requirement of saved.requirements) {
    assert.equal(requirement.status, 'verified', `${dir}: ${requirement.id} not verified`);
  }
  assert.match(readme, new RegExp(saved.saved_project_id), dir);
  assert.equal(saved.physical_acceptance, false, dir);
  process.stdout.write(`PASS ${dir}: ${input.requirements.length} saved requirements and a matching verification record\n`);
}
process.stdout.write('Static provenance checks passed; execution and mechanical acceptance require separate tests.\n');
