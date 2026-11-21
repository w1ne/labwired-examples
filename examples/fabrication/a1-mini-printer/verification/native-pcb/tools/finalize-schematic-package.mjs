#!/usr/bin/env node
// A1 native source annotation and packaging. Geometry and connectivity remain
// the existing validated projection; this script does not infer nets or parts.
import fs from 'node:fs';
import path from 'node:path';
import {createHash}from'node:crypto';
import {pathToFileURL}from'node:url';
import {spawnSync}from'node:child_process';
const [source,outdir,footprintMapFile]=process.argv.slice(2);
if(!process.env.LABWIRED_ROOT||!source||!outdir)throw new Error('Set LABWIRED_ROOT; usage: source.kicad_sch output-directory [footprint-map.json]');
const root=process.env.LABWIRED_ROOT;
const {projectLibraryFiles}=await import(pathToFileURL(path.join(root,'packages/board-pcb/src/layout/project-libs.ts')));
const {parseSExpr}=await import(pathToFileURL(path.join(root,'packages/board-config/src/import/sexpr.ts')));
const sha=x=>createHash('sha256').update(x).digest('hex'),uuid=x=>{const h=sha(x);return`${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20,32)}`;},q=JSON.stringify;
const before=fs.readFileSync(source,'utf8');let sch=before;
const parsed=parseSExpr(sch);if(!parsed.ok)throw new Error(parsed.message);
const sheet=parsed.value[0],forms=(n,h)=>n.filter(x=>Array.isArray(x)&&x[0]===h),form=(n,h)=>forms(n,h)[0],rootUuid=form(sheet,'uuid')[1];
if(!forms(form(sheet,'lib_symbols'),'symbol').some(x=>x[1]==='power:PWR_FLAG'))throw new Error('Existing PWR_FLAG library definition is required');
const intents=[
 {net:'GND',ref:'#FLG901',x:101.6,description:'External supply return at J1 pin 2 and USB J20 ground contacts. Nonphysical power-intent marker.'},
 {net:'+24V',ref:'#FLG902',x:177.8,description:'External 24 V supply through J1 and F1. Nonphysical power-intent marker; operating voltage and fuse condition are not measured.'},
 {net:'USB_VBUS',ref:'#FLG903',x:254,description:'External USB host VBUS at J20 A4/A9/B4/B9. Nonphysical power-intent marker; USB connection and voltage are not measured.'},
];
for(const intent of intents)if(!sch.includes(`(global_label ${q(intent.net)}`)&&!sch.includes(`(lib_id "power:${intent.net}")`))throw new Error('Intent names absent native net '+intent.net);
const annotations=[];const hidden='(effects (font (size 1.27 1.27)) (hide yes))';
for(const intent of intents){const{x,ref,net,description}=intent,y=774.7,seed='a1-external-power:'+net;
 annotations.push(`  (wire (pts (xy ${x} ${y}) (xy ${x+2.54} ${y})) (stroke (width 0) (type default)) (uuid ${q(uuid(seed+':wire'))}))`,
 `  (global_label ${q(net)} (shape passive) (at ${x+2.54} ${y} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left)) (uuid ${q(uuid(seed+':label'))}) (property "Intersheetrefs" "\${INTERSHEET_REFS}" (at ${x+2.54} ${y} 0) ${hidden}))`,
 `  (symbol (lib_id "power:PWR_FLAG") (at ${x} ${y} 0) (unit 1)
    (in_bom no) (on_board no)
    (uuid ${q(uuid(seed))})
    (property "Reference" ${q(ref)} (at ${x} ${y} 0) ${hidden})
    (property "Value" "PWR_FLAG" (at ${x} ${y-5.08} 0) (effects (font (size 1.27 1.27))))
    (property "Power intent" ${q(description)} (at ${x} ${y} 0) ${hidden})
    (pin "1" (uuid ${q(uuid(seed+':pin'))}))
    (instances (project "labwired" (path "/${rootUuid}" (reference ${q(ref)}) (unit 1))))
  )`);
}
annotations.push(`  (text "External supply intent: J1 24 V through F1; USB host VBUS; common return. Flags are nonphysical." (at 198.12 787.4 0) (effects (font (size 1.27 1.27))) (uuid ${q(uuid('a1-external-power:note'))}))`);
sch=sch.replace(/\)\s*$/,annotations.join('\n')+'\n)\n');
let footprintUpdates=[];
if(footprintMapFile){
 const map=JSON.parse(fs.readFileSync(footprintMapFile));
 const byRef=new Map(map.map(entry=>[entry.reference,entry]));
 if(byRef.size!==map.length||map.some(e=>!e.reference||!e.before||!e.after||!e.after.includes(':')))throw new Error('Invalid per-reference footprint mapping');
 const occurrences=new Map();
 sch=sch.split(/(?=^  \(symbol \(lib_id )/m).map(block=>{
   if(!block.startsWith('  (symbol (lib_id '))return block;
   const reference=/\(property "Reference" "([^"]+)"/.exec(block)?.[1];
   const entry=byRef.get(reference);if(!entry)return block;
   const token=`(property "Footprint" ${q(entry.before)}`;
   if(block.split(token).length!==2)throw new Error(`Placed symbol footprint is ambiguous or changed: ${reference}`);
   occurrences.set(reference,(occurrences.get(reference)??0)+1);
   return block.replace(token,`(property "Footprint" ${q(entry.after)}`);
 }).join('');
 const defaults=new Map();for(const e of map){const values=defaults.get(e.before)??new Set();values.add(e.after);defaults.set(e.before,values);}
 // Defaults in embedded generic symbols also retain the same native item. An
 // ambiguous default (one item with multiple exact variants) cannot be guessed.
 for(const [before,values]of defaults){const token=`(property "Footprint" ${q(before)}`;if(!sch.includes(token))continue;if(values.size!==1)throw new Error('Ambiguous embedded footprint default '+before);sch=sch.split(token).join(`(property "Footprint" ${q([...values][0])}`);}
 for(const entry of map){if(!occurrences.has(entry.reference)&&!['H1','H2','H3','H4'].includes(entry.reference))throw new Error('Mapped reference is absent '+entry.reference);footprintUpdates.push({...entry,schematicOccurrences:occurrences.get(entry.reference)??0,boardOnlyMechanical:!occurrences.has(entry.reference)});}
}

if(!parseSExpr(sch).ok)throw new Error('Final annotation syntax is invalid');
fs.mkdirSync(outdir,{recursive:true});fs.writeFileSync(path.join(outdir,'a1-printcore.kicad_sch'),sch);
const libraries=projectLibraryFiles({pcb:'',sch},()=>{throw new Error('Footprint libraries are provided from the exact PCB by the native package task');});
for(const f of libraries)fs.writeFileSync(path.join(outdir,f.name),f.text);
fs.copyFileSync(path.join(root,'packages/board-config/src/export/KICAD_SYMBOLS_ATTRIBUTION.md'),path.join(outdir,'KICAD_SYMBOLS_ATTRIBUTION.md'));
const receipt={schema:'labwired.native-schematic-packaging.v1',inputSchematicSha256:sha(before),outputSchematicSha256:sha(sch),rootUuid,powerIntentAnnotations:intents,footprintUpdates,projectLibraries:libraries.map(f=>({file:f.name,sha256:sha(f.text)})),libraryMethod:'Existing packages/board-pcb/src/layout/project-libs.ts projectLibraryFiles: exact embedded symbol definitions, namespace-local tables via KIPRJMOD.',physicalPartChanges:0,physicalPinChanges:0};
fs.writeFileSync(path.join(outdir,'native-schematic-packaging.json'),JSON.stringify(receipt,null,2)+'\n');
for(const args of [['sch','export','netlist','--format','kicadxml','-o','a1-printcore.net.xml','a1-printcore.kicad_sch'],['sch','export','pdf','-o','a1-printcore.pdf','a1-printcore.kicad_sch']]){const r=spawnSync('kicad-cli',args,{cwd:outdir,encoding:'utf8'});if(r.status!==0)throw new Error(r.stdout+r.stderr);}
console.log(JSON.stringify(receipt));
