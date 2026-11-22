#!/usr/bin/env node
// Source-bound receipt checks. This does not run hosted firmware or grant
// fabrication, current/thermal or flight acceptance.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
const root=new URL('../examples/aerospace/pathfinder-rocket/candidate/',import.meta.url);
const bytes=path=>readFileSync(new URL(path,root));
const json=path=>JSON.parse(bytes(path).toString('utf8'));
const sha=value=>createHash('sha256').update(value).digest('hex');
const record=json('acceptance.json');
assert.equal(record.schema,'labwired-examples/pathfinder-candidate-acceptance/v1');
for(const [path,hash]of Object.entries(record.files)){
  assert.match(hash,/^[a-f0-9]{64}$/);
  assert.equal(sha(bytes(path)),hash,`Stale or changed artifact: ${path}`);
}
const pcbHash=sha(bytes('routing/pathfinder-routed.kicad_pcb'));
const pcbRef='sha256:'+pcbHash, cadHash=sha(bytes('pathfinder-extended.kcad.ts'));
const designHash=sha(bytes('design-input.json'));
assert.equal(record.pcb.sha256,pcbHash);
assert.equal(record.cad.sha256,cadHash);
assert.equal(record.design_input_sha256,designHash);
const original=JSON.parse(readFileSync(new URL('../project.input.json',root),'utf8'));
const input=json('project.input.json'),design=json('design-input.json').diagram;
assert.equal(input.source,original.source);
assert.equal(input.board,original.board);
assert.equal(input.language,original.language);
assert.equal(input.entry_path,original.entry_path);
assert.deepEqual(input.stimuli,original.stimuli);
assert.deepEqual(input.requirements.map(r=>r.check),original.requirements.map(r=>r.check));
assert.equal(input.requirements.length,5);
assert.equal(input.diagram.parts.length,41);
assert.equal(design.parts.length,41);
assert.equal(new Set(design.parts.map(p=>p.id)).size,41);
for(const part of design.parts){
  const saved=input.diagram.parts.find(p=>p.id===part.id);
  assert.equal(saved?.type,part.type,part.id);
  assert.equal(saved?.manufacturerPart,part.manufacturerPart,part.id);
  assert.deepEqual(saved?.attrs,part.attrs,part.id);
}
assert.deepEqual(input.diagram.wires.map(w=>[w.from,w.to]),design.wires.map(w=>[w.from,w.to]));
const carrier=input.diagram.boards.find(b=>b.id==='flight-computer');
assert.equal(carrier.kind,'native');assert.equal(carrier.ref,pcbRef);
assert.deepEqual(carrier.pcbBoard,{id:record.pcb.id,rev:record.pcb.revision});
assert.deepEqual(carrier.pcbAssembly,json('pcb-assembly.json'));
assert.equal(carrier.pcbAssembly.pcbRef,pcbRef);
assert.equal(carrier.pcbAssembly.bindings.length,37);
assert.equal(new Set(carrier.pcbAssembly.bindings.map(b=>b.ref)).size,37);
assert.equal(input.diagram.pcbAssembly,undefined);
assert.equal(input.diagram.boards.length,5);
assert.deepEqual(input.diagram.mechanical.pcbBindings,[{id:'flight-computer',pcbRef,cadPart:'flight-computer-pcb'}]);
assert.equal(input.diagram.mechanical.slug,record.cad.slug);
assert.equal(input.diagram.mechanical.version,record.cad.revision);
for(const id of ['bat','boost','arm_switch','ematch']){
  const part=input.diagram.parts.find(p=>p.id===id);
  assert.equal(part.attrs.offboard,'true');
  assert.ok(part.board&&part.board!=='flight-computer');
}
assert.equal(design.parts.find(p=>p.id==='ematch').attrs.value,'1.5');
assert.equal(design.parts.find(p=>p.id==='boost_harness').attrs.package,undefined);
const saved=json('project-source-selection-update-receipt.json');
assert.equal(saved.project_id,record.project.id);
assert.equal(saved.content_hash,record.project.content_hash);
assert.equal(saved.readback_verified,true);
assert.ok(Object.values(saved.preserved_fields).every(Boolean));
assert.deepEqual(saved.native_board,carrier);
const schema=json('project-schema-check.json');
assert.equal(schema.project_input_sha256,sha(bytes('project.input.json')));
assert.equal(schema.normalized,true);assert.equal(schema.compiled,true);assert.deepEqual(schema.device_diagnostics,[]);
const compile=json('compile-receipt.json');
assert.equal(compile.ok,true);assert.equal(compile.runnable,true);
assert.equal(compile.request.source_sha256,sha(input.source));
assert.equal(compile.request.project_content_hash,record.project.content_hash);
assert.equal(compile.capability.automatic_substitution,false);
assert.equal(compile.verification_status,'not_run');
const local=json('routing/native-circuit-parity-local.json'),assembly=json('routing/native-assembly-after-importer-fix-local.json');
for(const result of [local,assembly]){
  assert.equal(result.pcbRef,pcbRef);assert.equal(result.design_input_sha256,designHash);
  assert.equal(result.implementation.commit,record.local_implementation_commit);
}
assert.deepEqual(local.imported_model,{twinBuildable:true,mapped:37,dropped:0,ignored:0,gaps:[]});
assert.deepEqual(assembly.assembly.model,local.imported_model);
assert.equal(assembly.importer.mapping.length,37);
assert.ok(assembly.importer.mapping.every(row=>row.status==='mapped'));
assert.deepEqual(local.copper_findings,[]);
assert.equal(local.source_assembly_system_yaml_identical,true);
assert.equal(local.assembly_copper_system_yaml_identical,true);
assert.equal(local.source_compile.system_yaml_sha256,local.copper_compile.system_yaml_sha256);
assert.deepEqual([...local.offboard].sort(),['arm_switch','bat','boost','ematch']);
const hosted=json('routing/hosted-drc.json'),drc=json('routing/route-drc-summary.json'),copper=json('routing/actual-copper-audit.json');
assert.equal(hosted.pcb_ref,pcbRef);assert.equal(hosted.drc.passed,true);
assert.deepEqual(hosted.drc.review.counts,{error:0,warning:0,info:0,excluded:0});
assert.equal(hosted.drc.schematic_parity_checked,false);
assert.equal(drc.routedSha256,pcbHash);assert.equal(drc.drcExit,5);
assert.deepEqual(drc.geometricErrors,[]);assert.deepEqual(drc.unconnected,[]);assert.deepEqual(drc.dimensionViolations,[]);
assert.deepEqual(drc.warnings,{lib_footprint_issues:37});
assert.ok(drc.routerSummary.every(line=>line.includes('1 unrouted and 13 violations')));
assert.equal(copper.pcb_sha256,pcbHash);assert.equal(copper.local_drc_exit,5);
assert.equal(copper.drc_summary_sha256,sha(bytes('routing/route-drc-summary.json')));
assert.equal(copper.native_pads_identical_to_unrouted_source,true);
assert.equal(copper.track_count,580);assert.equal(copper.via_count,65);
assert.equal(copper.all_declared_dimension_minima_pass,true);
const identity=json('routing/native-identity-correction.json');
assert.equal(identity.corrected_pcb_sha256,pcbHash);assert.equal(identity.exact_geometry_and_electrical_parity,true);
assert.equal(identity.source_pcb_sha256,sha(bytes('routing/history/before-native-identity/pathfinder-routed.kicad_pcb')));
const selection=json('source-selection-correction.json');
assert.equal(selection.design_input_sha256,designHash);assert.equal(selection.resolved_netlist_before_after_identical,true);
const fit=json('fit-envelope.json');
assert.equal(fit.pcb.sha256,pcbHash);assert.equal(fit.pcb.component_count,37);assert.equal(fit.components.length,37);
assert.deepEqual(fit.pcb.span_mm,[31.5,235]);
assert.equal(fit.cad_sources['pathfinder-extended.kcad.ts'],cadHash);
for(const row of fit.components){
  const clearance=19-Math.hypot(Math.max(Math.abs(row.x0),Math.abs(row.x1)),row.height);
  assert.ok(Math.abs(clearance-row.radialClearance)<1e-9,`${row.ref}: clearance differs from bounds`);
  assert.ok(clearance>=.6,`${row.ref}: outside the cassette bound`);
}
const minimum=Math.min(...fit.components.map(row=>row.radialClearance));
assert.ok(Math.abs(minimum-1.1205250356728875)<1e-9);
assert.equal(fit.battery.tray_minimum_radial_clearance_mm,.6);
assert.equal(fit.pcb.cad_drill_projection.shape_count,173);
assert.equal(fit.pcb.cad_drill_projection.maximum_center_rounding_mm,.0005);
const envelope=json('assembly-envelope-proof.json'),path=json('assembly-path-bounded.json');
assert.equal(envelope.full_cad_sha256,cadHash);assert.equal(envelope.pcb_sha256,pcbHash);
assert.equal(envelope.containment_checks.length,161);
assert.ok(envelope.containment_checks.every(row=>row.radius_upper_mm<=18.4+1e-8));
assert.equal(envelope.continuous_axial_slide.preconditions.length,3);
assert.deepEqual(path.parts[0].validDirections,[[0,0,1],[0,0,-1]]);
const cad=json('final-bay-cad-checks.json');assert.equal(cad.designLoop.ok,true);
assert.equal(cad.render.sourceSha256,sha(bytes('avionics-fit-envelope.kcad.ts')));
const ready=json('cad-artifact-readiness.json');
assert.equal(ready.project.source_sha256,cadHash);assert.equal(ready.project.version,record.cad.revision);
assert.equal(ready.saved_revision_readback.meshReady,true);
assert.equal(ready.saved_revision_readback.viewerPainted,false);
assert.equal(ready.cdn_download.sha256,ready.stored_api_download.sha256);
assert.equal(ready.cdn_download.http_status,200);assert.equal(ready.artifact.feature_count,66);
const meshArchive=json('cad-artifact-20261122/archive.json');
const meshGzip=bytes('cad-artifact-20261122/'+meshArchive.mesh.path);
assert.equal(meshGzip.readUInt32LE(4),0);assert.equal(meshGzip[3]&8,0);
assert.equal(meshArchive.mesh.compression,'gzip');assert.equal(meshArchive.mesh.mtime,0);
assert.equal(meshGzip.length,meshArchive.mesh.compressed_bytes);
assert.equal(sha(meshGzip),meshArchive.mesh.compressed_sha256);
const meshRaw=gunzipSync(meshGzip),meshArtifact=JSON.parse(meshRaw.toString('utf8'));
assert.equal(meshRaw.length,4659194);assert.equal(meshRaw.length,meshArchive.mesh.decompressed_bytes);
assert.equal(sha(meshRaw),ready.cdn_download.sha256);assert.equal(sha(meshRaw),meshArchive.mesh.decompressed_sha256);
assert.equal(meshArtifact.revision,record.cad.revision);assert.equal(meshArtifact.features.length,66);
assert.deepEqual(meshArtifact.provenance,ready.artifact.provenance);
assert.deepEqual(meshArchive.mesh.provenance,meshArtifact.provenance);
assert.equal(meshArchive.project.source_sha256,cadHash);assert.equal(meshArchive.mutation_performed,false);
assert.equal(meshArchive.viewer_paint_observed,false);assert.equal(meshArchive.physical_acceptance,false);
for(const [name,evidence]of Object.entries(meshArchive.readbacks)){
  const body=bytes('cad-artifact-20261122/'+name);
  assert.equal(body.length,evidence.bytes);assert.equal(sha(body),evidence.sha256);
}
const readySource=json('cad-artifact-20261122/project-readback.json');
assert.equal(readySource.project.meshReady,true);assert.equal(readySource.project.meshStatus,'ready');
for(const response of [readySource.project,readySource.revision]){
  assert.equal(response.slug,record.cad.slug);assert.equal(response.version,record.cad.revision);
  assert.equal(sha(response.code),cadHash);assert.equal(response.code,bytes('pathfinder-extended.kcad.ts').toString('utf8'));
}

const parts=json('source-parts.json');assert.equal(parts.design_input_sha256,designHash);
assert.equal(parts.selections.length,41);assert.equal(Object.keys(parts.manufacturer_records).length,22);
assert.equal(parts.selections.filter(p=>!p.offboard&&p.manufacturer_part).length,31);
const battery=json('battery-current-review.json');assert.equal(battery.diagram_file_sha256,designHash);
assert.equal(battery.fit_envelope_file_sha256,sha(bytes('fit-envelope.json')));
assert.equal(battery.electrical_findings.load_ohm_nominal,1.5);
const mass=json('mass-stability-review.json');assert.equal(mass.source_sha256,cadHash);assert.equal(mass.pcb_sha256,pcbHash);
assert.equal(mass.evidence.calculator_sha256,sha(bytes('calculate-mass-stability.py')));
assert.equal(mass.physical_assembly.mass_g,null);assert.equal(mass.physical_assembly.com_mm,null);
assert.equal(mass.static_aerodynamics_reference.full_airframe_cp_mm,null);assert.equal(mass.flight_acceptance.accepted,false);
const measurements=json('mass-inputs.template.json').entries;assert.equal(measurements.length,69);
assert.ok(measurements.every(row=>row.measured===false&&row.mass_g===null&&row.com_mm===null));
assert.equal(record.physical_acceptance.manufacturing,false);assert.equal(record.physical_acceptance.current_and_thermal,false);assert.equal(record.physical_acceptance.flight,false);
const verification=json(record.hosted_project_verification.receipt);
assert.equal(verification.content_hash,record.project.content_hash);
if(record.hosted_project_verification.status==='pending_deployment'){
  assert.equal(verification.verification.verified,false);assert.equal(verification.verification.reason,'DIAGRAM_INVALID');
  assert.ok(verification.verification.diagnostics.every(d=>['UNKNOWN_COMPONENT','PACKAGE_UNKNOWN','SCHEMA_PART_UNKNOWN','DEVICE_BOARD_REF'].includes(d.code)));
}else{
  assert.equal(record.hosted_project_verification.status,'model_verified');
  assert.equal(verification.verification.verified,true);
  assert.equal(verification.verification.verified_hash,record.project.content_hash);
}
console.log(`PASS source-bound Pathfinder receipts: 37 native models, 580 tracks, 65 vias, ${minimum.toFixed(6)} mm nominal component clearance.`);
console.log(`Hosted project verification: ${record.hosted_project_verification.status}. Manufacturing, current/thermal and flight acceptance remain false.`);
