import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';

// Read-only comparison of a separately captured repaired deployed artifact.
// No source edits, generation, simulator, network request, or project mutation.
const [baselineArg, currentArg, serverCommit, runtimeSourceHash, outputArg] = process.argv.slice(2);
if (!baselineArg || !currentArg || !/^[0-9a-f]{40}$/.test(serverCommit ?? '') ||
    !/^[0-9a-f]{64}$/.test(runtimeSourceHash ?? '') || !outputArg) {
  throw new Error('Usage: node qualify-repaired-cad.mjs BASELINE_BUNDLE CURRENT_READBACK_DIR SERVER_COMMIT RUNTIME_SOURCE_SHA256 FRESH_OUTPUT_JSON');
}
const baseline = resolve(baselineArg), current = resolve(currentArg), output = resolve(outputArg);
assert.equal(existsSync(output), false, 'A new output path is required; preserve every prior attempt');
const sha = data => createHash('sha256').update(data).digest('hex');
const canonical = value => Array.isArray(value)
  ? '[' + value.map(canonical).join(',') + ']'
  : value !== null && typeof value === 'object'
    ? '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
    : JSON.stringify(value);
const read = (root, name) => readFileSync(resolve(root, name));
const json = (root, name) => JSON.parse(read(root, name));
const report = {
  schema: 'kernelcad.repaired-deployed-artifact-qualification.v1',
  checkedAt: new Date().toISOString(),
  expectedServerCommit: serverCommit,
  expectedRuntimeSourceHash: runtimeSourceHash,
  scriptSha256: sha(readFileSync(new URL(import.meta.url))),
  baselineExamplesCommit: '4d21fea30c19d856d2d1ecd16272d9fab934df46',
  inputs: {},
  passed: false,
  cadSourceChanged: false,
  savedProjectUpdated: false,
  viewerPainted: false,
  browserFlightPerformed: false,
};
try {
  const manifestBytes = read(baseline, 'artifacts.json');
  assert.equal(sha(manifestBytes), '31e905b0788cfae3699f31cf7f81ae8a782bbe48e0b03159ed7776dbc016c4b2');
  const manifest = JSON.parse(manifestBytes);
  for (const [name, expected] of Object.entries(manifest.files)) {
    assert.ok(resolve(baseline, name).startsWith(baseline + '/'));
    const data = read(baseline, name);
    assert.equal(data.length, expected.bytes, name);
    assert.equal(sha(data), expected.sha256, name);
  }
  for (const name of [
    'getProject-ready.json', 'getProjectRevision.json',
    'current-stored-body.bin', 'current-stored-receipt.json',
    'current-cdn-body.bin', 'current-cdn-receipt.json',
  ]) {
    const data = read(current, name);
    report.inputs[name] = { bytes: data.length, sha256: sha(data) };
  }
  const oldMetadata = json(baseline, 'cad/getProject-ready.json');
  const oldRevision = json(baseline, 'cad/getProjectRevision.json');
  const metadata = json(current, 'getProject-ready.json');
  const revision = json(current, 'getProjectRevision.json');
  const source = read(baseline, 'cad/revision-6.kcad.ts');
  assert.equal(sha(source), 'f87316c6a9de81148c8985e9387641a0ead22d5d2744186d2041678c0364a10e');
  assert.equal(metadata.ok, true);
  assert.equal(revision.ok, true);
  assert.equal(metadata.slug, 'DyJ405zg');
  assert.equal(metadata.version, 6);
  assert.equal(revision.slug, 'DyJ405zg');
  assert.equal(revision.version, 6);
  assert.equal(metadata.meshStatus, 'ready');
  assert.equal(metadata.meshReady, true);
  assert.equal(metadata.code, source.toString());
  assert.equal(revision.code, source.toString());
  assert.deepEqual(metadata.assets, oldMetadata.assets);
  assert.deepEqual(revision.assets, oldRevision.assets);
  assert.equal(metadata.privacy, oldMetadata.privacy);
  assert.equal(metadata.updated_at, oldMetadata.updated_at);
  assert.deepEqual(metadata.parameters, oldMetadata.parameters);
  assert.deepEqual(revision.parameters, oldRevision.parameters);
  const data = read(current, 'current-stored-body.bin');
  assert.deepEqual(read(current, 'current-cdn-body.bin'), data, 'Stored-only and CDN bodies must be identical');
  const mesh = JSON.parse(data);
  const producerPin = sha(canonical(mesh.provenance));
  assert.equal(mesh.revision, 6);
  assert.equal(mesh.provenance.source.sha256, sha(source));
  assert.equal(mesh.provenance.source.byteLength, source.length);
  assert.equal(mesh.provenance.assetsSha256, sha(canonical(Object.fromEntries(
    Object.entries(revision.assets).map(([name, asset]) => [name, asset.sha256])))));
  assert.equal(mesh.provenance.producer.serverCommit, serverCommit);
  assert.equal(mesh.provenance.producer.runtimeSourceHash, runtimeSourceHash);
  assert.equal(metadata.serverBuild, mesh.provenance.producer.serverBuild);
  for (const [name, field, origin] of [
    ['current-stored', 'meshDownloadUrl', 'https://api.kernelcad.com'],
    ['current-cdn', 'meshUrl', 'https://mesh.kernelcad.com'],
  ]) {
    const receipt = json(current, name + '-receipt.json');
    const url = new URL(metadata[field]);
    assert.equal(url.origin, origin);
    assert.equal(url.pathname, name === 'current-stored'
      ? '/api/v1/projects/DyJ405zg/revisions/6/mesh-artifact'
      : '/mesh-artifacts/DyJ405zg/v6.json');
    if (name === 'current-stored') assert.equal(url.searchParams.get('download'), '1');
    assert.equal(url.searchParams.get('provenance'), producerPin);
    assert.equal(receipt.url, metadata[field]);
    assert.equal(receipt.finalUrl, metadata[field]);
    assert.equal(receipt.status, 200);
    assert.equal(receipt.sha256, sha(data));
    assert.equal(receipt.byteLength, data.length);
    assert.equal(receipt.requestedProvenance, producerPin);
    assert.equal(receipt.provenanceSha256, producerPin);
    if (name === 'current-stored') {
      assert.equal(receipt.headers['x-mesh-artifact'], 'stored-verified');
      assert.equal(receipt.headers['x-mesh-provenance'], producerPin);
      assert.equal(receipt.headers['x-mesh-source-sha256'], sha(source));
      assert.equal(receipt.headers['x-mesh-server-build'], mesh.provenance.producer.serverBuild);
    }
  }
  report.currentArtifact = { sha256: sha(data), bytes: data.length, producerPin, provenance: mesh.provenance };
  const oldData = gunzipSync(read(baseline, 'cad/current-stored-body.bin.gz'));
  assert.equal(sha(oldData), 'e041191cfd930893229d3d569dece43dc5ed8441dff865270f65e09b1f78e141');
  const oldMesh = JSON.parse(oldData);
  const local = json(baseline, 'cad/crease-normal-corrected-local.json');
  assert.equal(local.fixedSourceSha256, 'a35a61f22730d2f7259d17e8e8ccb1d4cdc8483f1b53f079850922dbba1678ff');
  assert.equal(local.realAssetComparisonPassed, true);
  const fixedFc = local.results.find(part => part.part === 'fc-population-native-mesh');
  assert.equal(fixedFc.indexChanges, 28);
  const expectedGeometry = structuredClone(oldMesh);
  const expectedFc = expectedGeometry.features.find(part => part.assemblyPartName === fixedFc.part);
  for (const change of fixedFc.changes) {
    assert.equal(expectedFc.mesh.indices[change.index], change.before);
    expectedFc.mesh.indices[change.index] = change.after;
  }
  const populationResults = [];
  for (const [partName, file, assetSha, offset] of [
    ['esc-population-native-mesh', 'esc-population-native.stl.gz', '297c5f78a471d07d12020dfa259906af6ed22339c0b1b8f95531bab1bcb6b3f3', [-75.63257, 34.6, 14.4]],
    ['fc-population-native-mesh', 'fc-components.stl.gz', '70a02a51dfa161cb3eca7974f200a58232c7db43c317ea6d5c2837f216e45a0e', [0, -12.75, 22]],
  ]) {
    const stl = gunzipSync(read(baseline, 'cad/prior-v6-archive/' + file));
    assert.equal(sha(stl), assetSha);
    const count = stl.readUInt32LE(80);
    assert.equal(stl.length, 84 + 50 * count);
    const part = mesh.features.find(value => value.assemblyPartName === partName);
    assert.equal(part.mesh.indices.length, count * 3);
    let wrongCorners = 0, maximumSerializationErrorMm = 0;
    for (let t = 0; t < count; t++) for (let v = 0; v < 3; v++) {
      const index = part.mesh.indices[t * 3 + v];
      assert.ok(Number.isInteger(index) && index >= 0 && index < part.mesh.positions.length / 3);
      let wrong = false;
      for (let a = 0; a < 3; a++) {
        const sourceValue = Math.fround(stl.readFloatLE(84 + t * 50 + 12 + v * 12 + a * 4) + offset[a]);
        const actual = part.mesh.positions[index * 3 + a];
        assert.ok(Number.isFinite(actual));
        maximumSerializationErrorMm = Math.max(maximumSerializationErrorMm, Math.abs(sourceValue - actual));
        wrong ||= Math.round(sourceValue * 1000) !== Math.round(actual * 1000);
      }
      if (wrong) wrongCorners++;
    }
    const prior = oldMesh.features.find(value => value.assemblyPartName === partName);
    const changes = [];
    assert.equal(part.mesh.indices.length, prior.mesh.indices.length);
    for (let i = 0; i < part.mesh.indices.length; i++) {
      if (part.mesh.indices[i] !== prior.mesh.indices[i]) {
        changes.push({ index: i, triangle: Math.floor(i / 3), corner: i % 3, before: prior.mesh.indices[i], after: part.mesh.indices[i] });
      }
    }
    const row = {
      part: partName, assetSha256: assetSha, triangles: count, wrongCorners,
      maximumSerializationErrorMm, indexChanges: changes.length, changes,
      positionsUnchanged: sha(canonical(part.mesh.positions)) === sha(canonical(prior.mesh.positions)),
      normalsUnchanged: sha(canonical(part.mesh.normals)) === sha(canonical(prior.mesh.normals)),
    };
    populationResults.push(row);
  }
  report.populations = populationResults;
  delete expectedGeometry.provenance;
  const actualGeometry = structuredClone(mesh);
  delete actualGeometry.provenance;
  report.geometry = {
    expectedSha256: sha(canonical(expectedGeometry)),
    actualSha256: sha(canonical(actualGeometry)),
    assemblyParts: mesh.features.filter(part => part.assemblyPartName).length,
  };
  assert.equal(report.geometry.assemblyParts, 38);
  for (const part of populationResults) {
    assert.equal(part.wrongCorners, 0, part.part + ' must preserve every source corner');
    assert.ok(part.maximumSerializationErrorMm <= 0.0005000001, part.part + ' serialization must remain within 1 micrometer rounding');
    assert.equal(part.positionsUnchanged, true);
    assert.equal(part.normalsUnchanged, true);
  }
  assert.deepEqual(populationResults[0].changes, []);
  assert.deepEqual(populationResults[1].changes, fixedFc.changes);
  assert.equal(report.geometry.actualSha256, report.geometry.expectedSha256, 'Every other geometry/transform field must be identical to the preserved artifact');
  report.passed = true;
  report.scope = 'Actual stored and CDN mesh bytes, unchanged saved revision/source/assets, exact expected geometry correction; no viewer or flight claim';
} catch (error) {
  report.failure = { name: error.name, message: String(error.message).slice(0, 3000) };
  process.exitCode = 1;
}
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ passed: report.passed, output, inputs: Object.keys(report.inputs).length,
  populations: report.populations?.map(({ changes, ...row }) => row), geometry: report.geometry, failure: report.failure }));
