#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';

const [boardPath, assemblyPath, outputDirectory] = process.argv.slice(2);
const root = process.env.LABWIRED_ROOT;
if (!root || !boardPath || !assemblyPath || !outputDirectory)
  throw new Error('Set LABWIRED_ROOT; usage: node generate-native-schematic.mjs board.kicad_pcb assembly.json output-directory');
const config = await import(pathToFileURL(path.join(root, 'packages/board-config/dist/index.js')));
const pcb = await import(pathToFileURL(path.join(root, 'packages/board-pcb/dist/index.js')));
const renderer = process.env.LABWIRED_SCHEMATIC_RENDERER
  ? await import(pathToFileURL(process.env.LABWIRED_SCHEMATIC_RENDERER)) : config;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const content = fs.readFileSync(boardPath, 'utf8'), source = JSON.parse(fs.readFileSync(assemblyPath, 'utf8'));
const pcbRef = `sha256:${digest(content)}`;
const imported = await config.importCircuit({ source_kind: 'kicad_pcb', content });
const read = pcb.readBoardFromText(content);
const metadataRead = spawnSync('/usr/bin/python3', ['-c',
  `import pcbnew,json,sys
b=pcbnew.LoadBoard(sys.argv[1])
print(json.dumps({f.GetReference():{'fields':{a.GetName():a.GetText() for a in f.GetFields()},'footprint':f.GetFPIDAsString(),'description':f.GetLibDescription(),'attributes':f.GetAttributes(),'pads':[{'number':p.GetNumber(),'uuid':p.m_Uuid.AsString(),'netCode':p.GetNetCode(),'net':p.GetNetname(),'position':[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],'size':[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)],'drill':[pcbnew.ToMM(p.GetDrillSize().x),pcbnew.ToMM(p.GetDrillSize().y)]}for p in f.Pads()]}for f in b.GetFootprints()}))`, boardPath], { encoding:'utf8' });
if (metadataRead.status !== 0) throw new Error(metadataRead.stderr);
const nativeRecords = JSON.parse(metadataRead.stdout);
const nativeProperties = Object.fromEntries(Object.entries(nativeRecords).map(([ref,record]) => [ref,record.fields]));
// These exact primary-source mounting pads are mechanical retention features.
// They are never assigned an electrical pin or a shared no-connect net.
const mechanicalFootprints = new Map([
  ...['J10','J11','J12','J13'].map(ref => [ref,'Molex_Micro-Fit_3.0_43650-0410_1x04-1MP_P3.00mm_Horizontal']),
  ...['J22','J23'].map(ref => [ref,'JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical']),
]);
const mechanicalPads = [];
for (const [ref,footprint] of mechanicalFootprints) {
  const record = nativeRecords[ref], pads = record?.pads.filter(p => p.number==='MP');
  if (!record || record.footprint!==footprint || pads.length!==2 || pads.some(p=>p.netCode!==0 || p.net))
    throw new Error(`Mechanical mounting classification no longer matches the native source: ${ref}`);
  const expectedSpan = ref==='J22'||ref==='J23' ? 5.6 : 13.3;
  if (Math.abs(Math.abs(pads[0].position[0]-pads[1].position[0])-expectedSpan)>1e-6 || Math.abs(pads[0].position[1]-pads[1].position[1])>1e-6)
    throw new Error(`Mounting-pad geometry differs from its source drawing: ${ref}`);
  mechanicalPads.push({ref,footprint,nativeDescription:record.description,reason:'Two mechanical retention pads; neither is an electrical circuit terminal.',drawing:expectedSpan===13.3
    ? 'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/436/43650/436500211_sd.pdf'
    : 'https://www.jst-mfg.com/product/pdf/eng/eSH.pdf',drawingMountSpanMm:expectedSpan,pads});
}
const resolved = pcb.resolveNativeAssembly(source, read, pcbRef, imported);
fs.mkdirSync(outputDirectory, { recursive: true });
const writeJson = (name, value) => fs.writeFileSync(path.join(outputDirectory, name), JSON.stringify(value, null, 2) + '\n');
writeJson('native-assembly-validation.json', resolved.ok
  ? { ok: true, pcbRef, model: resolved.model, bindings: resolved.bindings }
  : { ok: false, pcbRef, gaps: resolved.gaps });
if (!resolved.ok) throw new Error('Native assembly refused: ' + resolved.gaps.join('\n'));

// Connectivity is the existing resolver's graph. The physical fields below
// come only from the board whose content hash and assembly just passed.
const netlist = config.buildNetlist(resolved.diagram);
const nativeByRef = new Map(read.components.map(c => [c.ref, c]));
const bindingByPart = new Map(resolved.bindings.map(b => [b.partId, b]));
const unboundPads = [], connectorGraphics = [];
netlist.components = netlist.components.filter(c => bindingByPart.has(c.partId)).map(c => {
  const binding = bindingByPart.get(c.partId), native = nativeByRef.get(binding.ref);
  if (!native) throw new Error(`No native component ${binding.ref}`);
  const padOf = new Map(Object.entries(binding.pinToPad).map(([pin, pads]) => [pin, [...pads]]));
  const covered = new Set([...padOf.values()].flat());
  for (const pad of native.pads) {
    if (!pad.number || covered.has(pad.number)) continue;
    if (pad.number==='MP' && mechanicalFootprints.has(native.ref)) continue;
    if ((pad.net ?? 0) > 0) throw new Error(`Unbound connected native pad ${native.ref}.${pad.number}`);
    // Native pad has no net. Keep it visible and explicitly unconnected without
    // claiming that the vendor calls it NC or that it is bonded internally.
    const pin = `PAD_${pad.number}`;
    if (padOf.has(pin)) throw new Error(`Unwired pad identity collision ${native.ref}.${pad.number}`);
    padOf.set(pin, [pad.number]); covered.add(pad.number);
    unboundPads.push({ ref: native.ref, pad: pad.number, pin, nativeNet: null });
  }
  return { ...c, ref: native.ref, value: native.value, footprint: native.footprintId,
    mpn: nativeProperties[native.ref]?.MPN || undefined,
    manufacturer: nativeProperties[native.ref]?.Manufacturer || undefined,
    datasheet: nativeProperties[native.ref]?.Datasheet || undefined,
    description: nativeProperties[native.ref]?.Description || undefined,
    excludeFromBom: Boolean(nativeRecords[native.ref].attributes & 8),
    padOf, padsUnavailable: new Set() };
});
const byPart = new Map(netlist.components.map(c => [c.partId, c]));
if (byPart.size !== resolved.bindings.length) throw new Error('A validated native binding is not exportable');
netlist.nets = netlist.nets.map(n => ({ ...n, nodes: n.nodes.filter(p => byPart.has(p.part)) })).filter(n => n.nodes.length);
// V1 graphs preserve groups but can infer different names. Project each
// validated group onto exactly one native net identity, never infer copper.
const nativeNames = new Map(read.snapshot.nets.map(n => [n.code,n.name]));
const nativePinNet = new Map(), nativeMembers = new Map();
for (const binding of resolved.bindings) {
  const native = nativeByRef.get(binding.ref);
  for (const [pin,pads] of Object.entries(binding.pinToPad)) {
    const codes = [...new Set(native.pads.filter(p => pads.includes(p.number) && (p.net ?? 0)>0).map(p => p.net))];
    if (codes.length>1) throw new Error(`${binding.ref}:${pin} spans native net codes`);
    if (codes.length===1) {
      const key = `${binding.partId}:${pin}`, code = codes[0];
      nativePinNet.set(key, code);
      const members = nativeMembers.get(code) ?? [];
      members.push({part:binding.partId,pin});nativeMembers.set(code,members);
    }
  }
}
const coveredPins = new Set(), exportedCodes = new Set();
netlist.nets = netlist.nets.map(net => {
  const codes = [...new Set(net.nodes.map(n => nativePinNet.get(`${n.part}:${n.pin}`)))];
  if (codes.length!==1 || codes[0]===undefined) throw new Error(`Resolved graph group ${net.name} has no unique native identity`);
  const code = codes[0];
  if (exportedCodes.has(code)) throw new Error(`Native net ${nativeNames.get(code)} spans two resolved graph groups`);
  exportedCodes.add(code);
  for (const n of net.nodes) coveredPins.add(`${n.part}:${n.pin}`);
  return {...net,code,name:nativeNames.get(code),declared:true};
});
for (const [code,members] of nativeMembers) {
  const missing = members.filter(n => !coveredPins.has(`${n.part}:${n.pin}`));
  if (!missing.length) continue;
  if (members.length!==1 || exportedCodes.has(code)) throw new Error(`A connected native group is absent from the resolved graph: ${nativeNames.get(code)}`);
  // Native singleton pads need no wire edge in V1, but their explicit native
  // NC/test net name must survive the schematic projection.
  netlist.nets.push({code,name:nativeNames.get(code),declared:true,nodes:missing});
  exportedCodes.add(code);
}
netlist.nets.sort((a,b)=>a.code-b.code);


// A connector can bind an external motor, heater or screen in the twin. Its
// native PCB symbol represents the connector itself, with the same named
// terminals and physical pad map. The validated logical model remains intact.
const diagram = { ...resolved.diagram, parts: resolved.diagram.parts.filter(p => byPart.has(p.id)).map(p => {
  const physical = byPart.get(p.id);
  if (!/^(J|TP)\d+$/.test(physical.ref)) return { ...p };
  connectorGraphics.push({ ref: physical.ref, partId: p.id, originalModelType: p.type, schematicType: 'pin-header' });
  return { ...p, type: 'pin-header' };
}) };

// Device-specific page placement uses the existing renderer's position input.
// Eight columns make the full native controller readable on one A0 sheet.
const titles = ['MCU / USB', 'POWER INPUT / REGULATORS', 'X AXIS', 'Y AXIS', 'Z AXIS', 'EXTRUDER', 'HEATERS / FANS', 'I/O / CONTROLS'];
const groupFor = ref => {
  const number = Number(ref.replace(/^\D+/, ''));
  if (['U1','U31','Y1','SW1','J20'].includes(ref) || (/^[CR]\d+$/.test(ref) && number < 20)) return 0;
  if (['J1','F1','D1','U20','U21','L1'].includes(ref) || (/^[CR]\d+$/.test(ref) && number >= 100 && number < 120) || /^TP2[0-3]$/.test(ref)) return 1;
  for (let axis = 0; axis < 4; axis++) {
    if ([`U${10+axis}`,`J${10+axis}`,`TP${1+axis}`].includes(ref) || (/^[CR]\d+$/.test(ref) && number >= 30+10*axis && number < 40+10*axis)) return 2+axis;
  }
  if (['U30','D3','D4','J2','J3','J4','J5'].includes(ref) || /^Q\d+$/.test(ref) || (/^[CR]\d+$/.test(ref) && number >= 120 && number < 140)) return 6;
  return 7;
};
const groups = titles.map(() => []);
for (const p of diagram.parts) groups[groupFor(byPart.get(p.id).ref)].push(p);
for (const [column, parts] of groups.entries()) {
  parts.sort((a,b) => {
    const ar = byPart.get(a.id).ref, br = byPart.get(b.id).ref;
    const priority = r => r.startsWith('U') ? 0 : r.startsWith('J') ? 1 : 2;
    return priority(ar)-priority(br) || ar.localeCompare(br, 'en', { numeric:true });
  });
  let nextY = 47.0;
  for (const p of parts) {
    const physical = byPart.get(p.id), count = new Set([...physical.padOf.values()].flat()).size;
    const height = Math.max(25.4, Math.ceil(count / 2) * 2.54 + 20.32);
    const x = 69.85 + 139.7 * column, y = nextY + height/2;
    p.x = (x-25.4)/0.25; p.y = (y-25.4)/0.25; p.rotate = 0;
    nextY += height;
  }
  if (nextY > 790) throw new Error(`Schematic column ${titles[column]} exceeds its A0 page region: ${nextY} mm`);
}
let schematic = renderer.diagramToKicadSchematic(diagram, { netlist });
// Page annotations contain no electrical nodes and do not alter connectivity.
const quote = s => JSON.stringify(s);
const uuid = s => { const h = digest(s); return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20,32)}`; };
const annotations = titles.map((title, i) => `  (text ${quote(title)} (at ${69.85+139.7*i} 27.94 0) (effects (font (size 2.54 2.54))) (uuid ${quote(uuid('heading:'+title))}))`).join('\n');
const mechanicalAnnotations = mechanicalPads.map(m => {
  const part = diagram.parts.find(p => byPart.get(p.id).ref===m.ref);
  const x = Math.round((part.x*0.25+25.4)/2.54)*2.54;
  const y = Math.round((part.y*0.25+25.4)/2.54)*2.54+15.24;
  return `  (text ${quote(m.ref+' MP x2: mechanical retention, no net')} (at ${x} ${y} 0) (effects (font (size 1.27 1.27))) (uuid ${quote(uuid('mechanical:'+m.ref))}))`;
}).join('\n');

schematic = schematic.replace(/\)\s*$/, annotations + '\n' + mechanicalAnnotations + '\n)\n');
const schPath = path.join(outputDirectory, 'a1-printcore.kicad_sch');
fs.writeFileSync(schPath, schematic);
writeJson('native-schematic-projection.json', { schema:'labwired.native-schematic-projection.v1', pcbRef,
  assemblySha256:digest(fs.readFileSync(assemblyPath)), schematicSha256:digest(schematic),
  scope:'Electrical components and pad connectivity from the validated native PCB. Four mechanical holes and twelve drawing-identified retention pads remain physical PCB features with an explicit mechanical inventory. External test supplies are excluded.',
  componentCount:netlist.components.length, netCount:netlist.nets.length, connectorGraphics, unboundPads, mechanicalPads,
  components:netlist.components.map(c => ({ ref:c.ref,partId:c.partId,value:c.value,footprint:c.footprint,mpn:c.mpn,manufacturer:c.manufacturer,datasheet:c.datasheet,description:c.description,excludeFromBom:c.excludeFromBom,pinToPad:Object.fromEntries(c.padOf) })),
  nets:netlist.nets, groups:groups.map((parts,i) => ({ title:titles[i],refs:parts.map(p=>byPart.get(p.id).ref) })) });
writeJson('native-mechanical-pad-inventory.json', {schema:'labwired.native-mechanical-pad-inventory.v1',pcbRef,groups:mechanicalPads,physicalMountingPadCount:mechanicalPads.reduce((n,g)=>n+g.pads.length,0)});
const run = args => {
  const r = spawnSync('kicad-cli', args, { encoding:'utf8', cwd:outputDirectory });
  if (r.status !== 0) throw new Error(`${args.join(' ')} failed:\n${r.stdout}\n${r.stderr}`);
};
run(['sch','export','netlist','--format','kicadxml','-o','a1-printcore.net.xml','a1-printcore.kicad_sch']);
run(['sch','export','pdf','-o','a1-printcore.pdf','a1-printcore.kicad_sch']);
if (digest(fs.readFileSync(boardPath)) !== digest(content)) throw new Error('Native source changed during export');
console.log(JSON.stringify({ ok:true, pcbRef, components:netlist.components.length, nets:netlist.nets.length, schematic:schPath }));
