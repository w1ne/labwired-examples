#!/usr/bin/env node
// Negative geometry acceptance only. An immutable pad-position sample proves
// a PCB too wide for a declared CAD coupler, but cannot ever prove a PCB fits.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const fixture = JSON.parse(readFileSync(
  'examples/aerospace/pathfinder-rocket/pcb-cad-fit-negative.json', 'utf8',
));
assert.equal(fixture.schema, 'labwired-pathfinder-fit-negative-v1');
assert.equal(fixture.source.pcb_board_id, 'pcb_e2ec5d2f4ade4aac');
assert.equal(fixture.source.pcb_revision, 1);
assert.match(fixture.source.project_content_hash, /^[a-f0-9]{64}$/);
assert.equal(fixture.cad.slug, 'K_DmeiaD');
assert.equal(fixture.cad.version, 2);
assert.ok(fixture.cad.coupler_inner_diameter_mm > 0);
assert.ok(Array.isArray(fixture.pads) && fixture.pads.length >= 100);

const points = fixture.pads.map(([ref, pad, x, y]) => {
  assert.equal(typeof ref, 'string');
  assert.equal(typeof pad, 'string');
  assert.ok(Number.isFinite(x) && Number.isFinite(y));
  return { x, y };
});
// 2D convex-hull minimum caliper width. Rotation of the board within its
// plane cannot reduce the pad-center strip width below this value.
// Physical pad edges and board outline make the actual occupied width larger.
function minimumStripWidth(pts) {
  const sorted = [...pts].sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (a, b, c) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
  const half = (array) => {
    const out = [];
    for (const p of array) {
      while (out.length >= 2 && cross(out.at(-2), out.at(-1), p) <= 0) out.pop();
      out.push(p);
    }
    out.pop();
    return out;
  };
  const hull = [...half(sorted), ...half([...sorted].reverse())];
  if (hull.length < 3) return 0; // underconstrained: no proof of fit
  let min = Infinity;
  for (let i = 0; i < hull.length; i++) {
    const a = hull[i], b = hull[(i + 1) % hull.length];
    const dx = b.x - a.x, dy = b.y - a.y;
    const len = Math.hypot(dx, dy);
    if (!len) continue;
    const dot = (p) => ((p.x - a.x) * -dy + (p.y - a.y) * dx) / len;
    const projections = hull.map(dot);
    min = Math.min(min, Math.max(...projections) - Math.min(...projections));
  }
  return min;
}
const minWidth = minimumStripWidth(points);
assert.ok(Math.abs(minWidth - 50.8956840664) < 0.002,
  `Pinned pad geometry changed: got ${minWidth} mm`);
assert.ok(minWidth > fixture.cad.coupler_inner_diameter_mm,
  'Expected known BAD PCB/CAD fit; do not mark fit verified without new source revisions and complete board-outline/clearance checks');
// Negative control for a narrow, collinear fixture: cannot assert fit from pads alone.
assert.equal(minimumStripWidth([{ x: 0, y: 0 }, { x: 0, y: 100 }, { x: 0, y: 50 }]), 0);
console.log(`REJECTED — PCB pad minimum strip width ${minWidth.toFixed(3)} mm > coupler ID ${fixture.cad.coupler_inner_diameter_mm.toFixed(1)} mm`);
console.log('This script only proves the pinned physical design does NOT fit. It is not a positive mechanical acceptance test.');
