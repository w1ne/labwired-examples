/** Reproduce local identity, physical copper extraction and compiler parity.
 * Run with the reviewed LabWired checkout's tsx and LABWIRED_CHECKOUT set. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here=dirname(fileURLToPath(import.meta.url)), root=dirname(here);
const checkout=process.env.LABWIRED_CHECKOUT;
assert(checkout, 'Set LABWIRED_CHECKOUT to the reviewed source checkout in source-provenance.json');
const fromRepo=(path:string)=>import(pathToFileURL(resolve(checkout!,path)).href);
const sha=(input:string|Buffer)=>createHash('sha256').update(input).digest('hex');
const git=(...args:string[])=>execFileSync('git',args,{cwd:checkout,encoding:'utf8'}).trim();
const implementationCommit=git('rev-parse','HEAD');
const expected=JSON.parse(readFileSync(join(root,'source-provenance.json'),'utf8')).native_identity_commit;
assert.equal(implementationCommit,expected,'Use the exact reviewed implementation, not an unrecorded branch head');
assert.equal(git('status','--porcelain','--untracked-files=no'),'','Tracked source changes invalidate the implementation identity');
const {buildNetlist,compile,importCircuit,migrateToV2,resolveNets,resolvePart,normalizeLabWiredDiagramV1,validateDevice}=await fromRepo('packages/board-config/dist/index.mjs');
const {readBoardFromText}=await fromRepo('packages/board-pcb/src/layout/read-board.ts');
const {importedBoardDoc}=await fromRepo('packages/board-pcb/src/layout/imported-board-doc.ts');
const {resolveNativeAssembly}=await fromRepo('packages/board-pcb/src/board/native-assembly.ts');
const {copperDiagram}=await fromRepo('packages/board-pcb/src/board/copper-diagram.ts');
const pcb=readFileSync(join(here,'pathfinder-routed.kicad_pcb'),'utf8');
const inputText=readFileSync(join(root,'design-input.json'),'utf8'), input=JSON.parse(inputText);
const bindingText=readFileSync(join(root,'pcb-assembly.json'),'utf8');
const source={...(input.diagram??input),pcbAssembly:JSON.parse(bindingText)};
const pcbRef='sha256:'+sha(pcb), native=readBoardFromText(pcb,'pathfinder-routed.kicad_pcb');
const imported=await importCircuit({source_kind:'kicad_pcb',content:pcb});
const assembly=resolveNativeAssembly(source,native,pcbRef,imported);
assert.equal(imported.twin_buildable,true);
assert.equal(assembly.ok,true,assembly.gaps?.join('; '));
const implementation={commit:implementationCommit,node:process.version,board_config_bundle_sha256:sha(readFileSync(resolve(checkout!,'packages/board-config/dist/index.mjs'))),source_sha256:Object.fromEntries([
  'packages/board-config/src/import-circuit.ts','packages/board-config/src/import/board-file.ts',
  'packages/board-config/src/import/manufacturer-identity.ts','packages/board-pcb/src/board/native-assembly.ts',
  'packages/board-pcb/src/board/copper-diagram.ts','packages/board-pcb/src/board/copper-netlist.ts',
].map(path=>[path,sha(readFileSync(resolve(checkout!,path)))]))};
const provenance={pcbRef,design_input_sha256:sha(inputText),pcb_assembly_sha256:sha(bindingText),implementation};
const savedInputText=readFileSync(join(root,'project.input.json'),'utf8');
const savedInput=JSON.parse(savedInputText), normalized=normalizeLabWiredDiagramV1(savedInput.diagram);
assert(normalized,'Saved candidate diagram must normalize without replacing hardware');
const deviceDiagnostics=validateDevice(normalized), savedCompile=compile(normalized);
assert.deepEqual(deviceDiagnostics,[]);
assert.equal(savedCompile.ok,true);
writeFileSync(join(root,'project-schema-check.json'),JSON.stringify({implementation_commit:implementationCommit,
  project_input_sha256:sha(savedInputText),normalized:true,device_diagnostics:deviceDiagnostics,
  compiled:savedCompile.ok,diagnostics:savedCompile.diagnostics},null,2)+'\n');

const exported=new Map(buildNetlist(source).components.map((part:{partId:string})=>[part.partId,part]));
const sourcedRecords=new Map<string,object>();
const selection=source.parts.map((part:{id:string;type:string;manufacturerPart?:string;attrs?:Record<string,string>})=>{
  const resolved=resolvePart(part.type,part.manufacturerPart,part.attrs?.package);
  if(part.manufacturerPart){
    assert.equal(resolved.manufacturerPart.id,part.manufacturerPart,`${part.id}: explicit identity must resolve exactly`);
    sourcedRecords.set(part.manufacturerPart,{record:resolved.manufacturerPart,manufacturer:resolved.manufacturer});
  }
  const component=exported.get(part.id) as {footprint?:string;padOf:Map<string,string[]>}|undefined;
  const binding=assembly.bindings.find((entry:{partId:string})=>entry.partId===part.id);
  return {part_id:part.id,type:part.type,manufacturer_part:part.manufacturerPart??null,explicit_package:part.attrs?.package??null,
    native_reference:binding?.ref??null,offboard:!binding,resolved_footprint:component?.footprint??null,
    resolved_physical_pads:resolved.pads??null,pin_to_pad:component?Object.fromEntries(component.padOf):null};
});
writeFileSync(join(root,'source-parts.json'),JSON.stringify({schema:'pathfinder.source-parts.v1',implementation_commit:implementationCommit,
  design_input_sha256:sha(inputText),scope:'Exact selected records and canonical resolved pin/package evidence. An unsourced generic part remains unsourced; offboard source models do not establish purchased hardware identity.',
  selections:selection,manufacturer_records:Object.fromEntries(sourcedRecords)},null,2)+'\n');

writeFileSync(join(here,'native-assembly-after-importer-fix-local.json'),JSON.stringify({
  ...provenance,scope:'Local generic source-checkout import and explicit native binding. Hosted replay and physical qualification are separate gates.',
  importer:{twinBuildable:imported.twin_buildable,mapping:imported.mapping},assembly:{ok:assembly.ok,model:assembly.model,bindings:assembly.bindings},
},null,2)+'\n');
const doc=importedBoardDoc(native,{pcbRef});
const copper=copperDiagram(assembly.diagram,doc.doc,{parasitics:false,bindings:assembly.bindings});
const flatten=(diagram:Parameters<typeof migrateToV2>[0])=>({board:diagram.board,parts:diagram.parts,wires:resolveNets(migrateToV2(diagram)).flatMap((net:{members:object[]})=>net.members.slice(1).map(to=>({from:net.members[0],to})))});
const original=compile(source), a=compile(flatten(assembly.diagram)), b=compile(flatten(copper.diagram));
const compileReceipt=(result:ReturnType<typeof compile>)=>({ok:result.ok,diagnostics:result.diagnostics,system_yaml_sha256:result.systemYaml?sha(result.systemYaml):null});
const report={...provenance,scope:'Local generic native copper extraction and compile parity with parasitics disabled. Does not prove hosted runtime, physical analog behavior, thermal/current limits or flight qualification.',
  imported_model:assembly.model,copper_findings:copper.findings,offboard:copper.offBoard,
  source_compile:compileReceipt(original),assembly_compile:compileReceipt(a),copper_compile:compileReceipt(b),
  source_assembly_system_yaml_identical:original.ok&&a.ok&&original.systemYaml===a.systemYaml,
  assembly_copper_system_yaml_identical:a.ok&&b.ok&&a.systemYaml===b.systemYaml};
writeFileSync(join(here,'native-circuit-parity-local.json'),JSON.stringify(report,null,2)+'\n');
assert.deepEqual(copper.findings,[]);
assert.equal(report.source_assembly_system_yaml_identical,true);
assert.equal(report.assembly_copper_system_yaml_identical,true);
console.log(JSON.stringify({implementationCommit,pcbRef,model:assembly.model,copperFindings:copper.findings.length,systemYaml:report.copper_compile.system_yaml_sha256,offboard:copper.offBoard}));
