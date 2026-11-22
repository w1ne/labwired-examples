import assert from 'node:assert/strict';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here=dirname(fileURLToPath(import.meta.url));
const checkout=process.env.LABWIRED_CHECKOUT;
assert(checkout, 'Set LABWIRED_CHECKOUT to the source checkout documented in source-provenance.json');
const fromRepo=(p:string)=>import(pathToFileURL(resolve(checkout!,p)).href);
import { readFileSync, writeFileSync } from 'node:fs';
const { erc, ercWiring, buildNetlist }=await fromRepo('packages/board-config/src/index.ts');
const { diagramToBoardLayout, emitKicadPcb }=await fromRepo('packages/board-pcb/src/layout/kicad-pcb.ts');
const { nodeFootprintText }=await fromRepo('packages/board-pcb/src/layout/footprint-text.node.ts');
const { footprintFor }=await fromRepo('packages/board-pcb/src/layout/footprints.ts');
const { courtyardsOverlap, annealWithinSpan }=await fromRepo(process.env.LABWIRED_PLACEMENT_SOURCE || 'packages/board-pcb/src/layout/placement.ts');
const { buildKernelcadHandoff }=await fromRepo('packages/board-pcb/src/export-kernelcad.ts');

{
  const input = JSON.parse(readFileSync(join(here,'design-input.json'), 'utf8'));
  const { diagram } = input;
  const electrical = erc(diagram), wiring = ercWiring(diagram);
  const netlist = buildNetlist(diagram);
  const layout = diagramToBoardLayout(diagram, components => annealWithinSpan(components, { width: 28, height: 256 }));
  // Source-bound layout reconciliation. Keep the established 31.5 x 235 mm
  // carrier and use the area recovered by exact 0603 signal resistors for
  // horizontal terminal wire entry and eight insulated-wire pass-throughs.
  for (const c of layout.components) c.x -= .5;
  layout.outline = { minX: 10, minY: 10, maxX: 41.5, maxY: 245 };
  const place = (id: string, wx: number, wz: number, rot: number) => {
    const c = layout.components.find(v => v.partId === id)!;
    c.rot = rot;
    const b = footprintFor(c).courtyard, a = -rot * Math.PI / 180;
    const lx = (b.minX + b.maxX) / 2, ly = (b.minY + b.maxY) / 2;
    c.x = wx + 25.75 - (lx * Math.cos(a) - ly * Math.sin(a));
    c.y = wz - 227.5 - (lx * Math.sin(a) + ly * Math.cos(a));
  };
  place('boost_harness', 0, 398.325, 0);
  place('pyro_term', -4.75, 427.325, 0);
  place('battery_harness', 4.75, 427.325, 0);
  place('c_bulk', -8, 459.8, 0);
  place('c_5v', 5, 449, 90); place('c_3v3', 6, 459.5, 90);
  place('c_dec', 12.2, 456.5, 90); place('led_status', -9.75, 451.5, 90);
  place('d_pyro', -1.5, 449, 90); place('d_buzz', -12, 426, 90);
  place('q_buzz', -10, 467.5, 90); place('q_cam_drv', -3.7, 467.5, 90);
  place('q_rec', 2.59, 467.5, 90); place('q_pyro', 11.5, 463.2, 90);
  place('q_cam', 11.5, 468.2, 90);
  place('cam', 12, 390, 0); place('uart', -12, 390, 0);
  place('arm_harness', 12, 403, 0);
  const resistors = diagram.parts.filter((p: {type: string; id: string}) => p.type === 'resistor' && p.id !== 'ematch');
  resistors.forEach((p: {id: string}, i: number) => place(p.id, -9 + (i % 7) * 3, 416 + Math.floor(i / 7) * 5, 90));
  // R1 requires a full-width VBAT start cap; the spare right column avoids the GND corridor.
  place('r_vbat_hi', 12.75, 416, 90);
  const wireHoles = [
    ...[-5.25, -1.75, 1.75, 5.25].map(x => ({ x: x + 25.75, y: 411.5 - 227.5, diameter: 2.4 })),
    ...[-6.5, -3, 3, 6.5].map(x => ({ x: x + 25.75, y: 440.5 - 227.5, diameter: 2.4 })),
  ];
  const serviceVolumes = [
    { name: 'converter-terminal-entry', x0: -8.525, x1: 8.525, y0: 1.8, y1: 13, z0: 402.65, z1: 413.65 },
    { name: 'supply-load-terminal-entry', x0: -9.775, x1: 9.775, y0: 1.8, y1: 13, z0: 431.65, z1: 442.65 },
  ];
  const handoff = buildKernelcadHandoff(diagram, layout);
  const overlaps = courtyardsOverlap(layout.components);
  const components = layout.components.map(part => ({
    ...part, padNets: Object.fromEntries(part.padNets), local_courtyard: footprintFor(part).courtyard,
    geometry: footprintFor(part), physical: handoff.parts.find(p => p.ref === part.ref)?.physical,
  }));
  const result = {
    ...input, candidate_erc: electrical, candidate_wiring: wiring,
    requested_mm: [32, 260], actual_mm: [layout.outline.maxX-layout.outline.minX, layout.outline.maxY-layout.outline.minY],
    outline: layout.outline, component_count: components.length, device_part_count: diagram.parts.length,
    overlaps, warnings: layout.warnings, netlist_warnings: netlist.warnings,
    components, handoff, nets: layout.nets, wireHoles, serviceVolumes,
    stackup: { copper_oz: 2, copper_mm: .07, board_mm: 1.6, finished_width_tolerance_fraction: .2 },
    component_pin_map: netlist.components.map(c => ({partId:c.partId,ref:c.ref,type:c.type,mpn:c.mpn,manufacturer:c.manufacturer,buyUrl:c.buyUrl,value:c.value,footprint:c.footprint,padOf:Object.fromEntries(c.padOf)})),
  };
  writeFileSync(join(here,'placement-result.json'), JSON.stringify(result,null,2)+'\n');
  let pcb = emitKicadPcb(layout, nodeFootprintText);
  // Native Edge.Cuts circles are actual non-plated wire holes, visible to the
  // router, independent KiCad DRC and fabrication export; they are not drawn
  // only in CAD. Copper must keep the declared edge clearance around them.
  const holesText = wireHoles.map((h, i) => `(gr_circle (center ${h.x} ${h.y}) (end ${h.x + h.diameter/2} ${h.y}) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts"))`).join('\n');
  pcb = pcb.trimEnd().slice(0, -1) + holesText + '\n)\n';
  pcb = pcb.replace('(setup\n', `(setup\n    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.07))
      (layer "dielectric 1" (type "core") (thickness 1.44) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.07))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG") (dielectric_constraints no))\n`);
  writeFileSync(join(here,'pathfinder-unrouted.kicad_pcb'), pcb);
  assert.deepEqual(electrical.filter(x=>x.severity==='error'),[]);
  assert.deepEqual(wiring.filter(x=>x.severity==='error'),[]);
  assert.deepEqual(overlaps,[]);
  for (const c of components) {
    const b = c.local_courtyard, a = -c.rot * Math.PI / 180;
    for (const x of [b.minX, b.maxX]) for (const y of [b.minY, b.maxY]) {
      const px = c.x + x * Math.cos(a) - y * Math.sin(a), py = c.y + x * Math.sin(a) + y * Math.cos(a);
      assert(px>=layout.outline.minX+.5);
      assert(px<=layout.outline.maxX-.5);
      assert(py>=layout.outline.minY+.5);
      assert(py<=layout.outline.maxY-.5);
    }
  }
  assert.equal(components.length,37);
  assert.equal(handoff.parts.length,41);
}
console.log('Pathfinder placement: 37 carrier parts, 41 device parts; electrical, wiring and courtyard checks passed.');
