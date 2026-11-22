import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';

// This reader audits recorded files only. It does not run the product, firmware,
// a simulator, network requests, browser actions, or project mutation.
const root = dirname(fileURLToPath(import.meta.url));
const nativeRoot = resolve(process.argv[2] ?? resolve(root, '../20261122-native-flight'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const canonical = value => Array.isArray(value)
  ? '[' + value.map(canonical).join(',') + ']'
  : value !== null && typeof value === 'object'
    ? '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
    : JSON.stringify(value);
const bytes = name => readFileSync(resolve(root, name));
const json = name => JSON.parse(bytes(name));
const manifest = json('artifacts.json');
for (const [name, expected] of Object.entries(manifest.files)) {
  assert.ok(resolve(root, name).startsWith(root + '/'), 'Artifact path leaves this bundle');
  const data = bytes(name);
  assert.equal(data.length, expected.bytes, name);
  assert.equal(sha(data), expected.sha256, name);
}
const payloads = json('payloads.json');
const decoded = name => {
  const data = gunzipSync(bytes(name)), expected = payloads[name];
  assert.equal(data.length, expected.decodedBytes, name);
  assert.equal(sha(data), expected.decodedSha256, name);
  return data;
};
for (const name of Object.keys(payloads)) decoded(name);
const nativeReference = json('native-reference.json');
for (const [name, expected] of Object.entries(nativeReference.files)) {
  const data = readFileSync(resolve(nativeRoot, name));
  assert.equal(data.length, expected.bytes, name);
  assert.equal(sha(data), expected.sha256, name);
}
assert.equal(sha(readFileSync(resolve(nativeRoot, 'capture/analyze-flight.py'))), '2cdbc99ff9467743b9ceff4e9857276b2aef9e2128512f3a02c26c9ac8f32ae0');
const frozen = json('release-checks/preflight-artifacts.json');
for (const [name, expected] of Object.entries(frozen.files)) {
  const data = bytes('release-checks/' + name);
  assert.equal(data.length, expected.size, name);
  assert.equal(sha(data), expected.sha256, name);
}
assert.equal(sha(bytes('release-checks/replay-shipped-native-world.mts')), '33a6eacc83065d950406cbc883e5dc4a56662956c20e2a1c753bff440f6ec6b2');
const current = json('cad/getProject-ready.json'), revision = json('cad/getProjectRevision.json');
const oldSave = json('cad/prior-v6-archive/native-current-studio-save-20261118.json');
const oldLab = json('cad/prior-v6-archive/native-current-lab-binding-20261118.json');
const oldEvaluation = json('cad/prior-v6-archive/native-current-evaluate-20261118.json');
const code = bytes('cad/revision-6.kcad.ts').toString(), oldCode = bytes('cad/prior-v6-archive/drone.kcad.ts').toString();
assert.equal(code, current.code); assert.equal(code, revision.code);
assert.equal(sha(Buffer.from(code)), 'f87316c6a9de81148c8985e9387641a0ead22d5d2744186d2041678c0364a10e');
const pattern = /lib\.(?:fromSTEP|meshFromSTL)\("([^"]+)"/g;
const imports = [...code.matchAll(pattern)].map(match => match[1]);
let at = 0;
let localized = oldCode.replace(pattern, (match, uri) => {
  const local = imports[at++], asset = revision.assets[local.replace(/^\.\//, '')];
  assert.ok(asset && local.includes(asset.sha256.slice(0, 12)));
  return match.replace(uri, local);
});
assert.equal(at, 15);
if (localized.endsWith('\n') && !code.endsWith('\n')) localized = localized.slice(0, -1);
assert.equal(localized, code);
assert.deepEqual([...oldSave.assetHashes].sort(), Object.values(revision.assets).map(asset => asset.sha256).sort());
assert.deepEqual(current.assets, revision.assets);
const meshBytes = decoded('cad/current-stored-body.bin.gz'), mesh = JSON.parse(meshBytes);
const producerHash = sha(canonical(mesh.provenance));
assert.equal(producerHash, '98618663029a83e4c28d833e398203f0510277938e07128a05dafe1c1a1be348');
assert.equal(mesh.provenance.source.sha256, sha(Buffer.from(code)));
assert.equal(mesh.provenance.assetsSha256, sha(canonical(Object.fromEntries(Object.entries(revision.assets).map(([key, asset]) => [key, asset.sha256])))));
for (const name of ['current-cdn-receipt.json', 'current-stored-receipt.json']) {
  const response = json('cad/' + name);
  assert.equal(response.status, 200); assert.equal(response.sha256, sha(meshBytes));
  assert.equal(response.requestedProvenance, producerHash); assert.equal(response.provenanceSha256, producerHash);
}
const oldCdn = json('cad/old-cdn-receipt.json'), oldStored = json('cad/old-stored-receipt.json');
assert.equal(oldCdn.status, 200); assert.equal(oldCdn.sha256, sha(meshBytes));
assert.notEqual(oldCdn.requestedProvenance, producerHash); assert.equal(oldCdn.provenanceSha256, producerHash);
assert.equal(oldStored.status, 404); assert.equal(oldStored.error, 'verified_mesh_artifact_missing');
assert.equal(sha(bytes('cad/old-stored-body.bin')), oldStored.sha256);
const project = JSON.parse(readFileSync(resolve(nativeRoot, 'candidate-project.json')));
const model = project.diagram.mechanical;
assert.deepEqual(model, oldLab.mechanical);
assert.equal(model.slug, 'DyJ405zg'); assert.equal(model.version, 6); assert.equal(mesh.revision, 6);
const parts = mesh.features.filter(part => part.assemblyPartName);
const names = parts.map(part => part.assemblyPartName).sort();
assert.equal(parts.length, 38);
assert.deepEqual(names, [...oldEvaluation.parts.names].sort());
assert.deepEqual(names, [...model.electronics.bodies[0].parts].sort());
const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
let totalTriangles = 0, displayTriangles = 0;
for (const part of parts) {
  assert.deepEqual(part.transform, identity);
  const surfaces = part.faces.map(face => ({ positions: face.vertices, indices: face.indices }));
  if (part.mesh) { surfaces.push(part.mesh); displayTriangles += part.mesh.indices.length / 3; }
  let count = 0;
  for (const surface of surfaces) {
    assert.equal(surface.positions.length % 3, 0); assert.equal(surface.indices.length % 3, 0);
    assert.ok(surface.positions.every(Number.isFinite));
    assert.ok(surface.indices.every(index => Number.isInteger(index) && index >= 0 && index < surface.positions.length / 3));
    count += surface.indices.length / 3;
  }
  assert.ok(count > 0, part.assemblyPartName); totalTriangles += count;
}
assert.equal(totalTriangles, 161702); assert.equal(displayTriangles, 103850);
for (const motion of model.electronics.motions) {
  const part = parts.find(value => value.assemblyPartName === motion.parts[0]);
  assert.ok(part.faces.some(face => face.cylinder && face.cylinder.radius === 14
    && face.cylinder.origin.every((v, i) => Math.abs(v - motion.origin[i]) < 1e-8)
    && face.cylinder.axis.every((v, i) => Math.abs(v - motion.axis[i]) < 1e-8)));
}
const triangleKey = points => {
  const v = points.map(point => point.join(','));
  return [v.join(';'), [v[1], v[2], v[0]].join(';'), [v[2], v[0], v[1]].join(';')].sort()[0];
};
const add = (map, key) => map.set(key, (map.get(key) ?? 0) + 1);
const recordedGeometry = json('cad/imported-population-geometry.json');
const comparisons = [];
for (const [name, file, offset] of [
  ['esc-population-native-mesh', 'esc-population-native.stl', [-75.63257, 34.6, 14.4]],
  ['fc-population-native-mesh', 'fc-components.stl', [0, -12.75, 22]],
]) {
  const data = decoded('cad/prior-v6-archive/' + file + '.gz'), count = data.readUInt32LE(80);
  assert.equal(data.length, 84 + 50 * count);
  const part = parts.find(value => value.assemblyPartName === name);
  assert.equal(part.mesh.indices.length / 3, count);
  const expected = new Map(), actual = new Map(), wrongCorners = [];
  const firstRaw = offset.map((v, a) => Math.fround(data.readFloatLE(96 + a * 4) + v));
  for (let t = 0; t < count; t++) {
    const sourcePoints = [], servedPoints = [];
    for (let v = 0; v < 3; v++) {
      const raw = offset.map((delta, a) => Math.fround(data.readFloatLE(84 + 50 * t + 12 + 12 * v + 4 * a) + delta));
      const point = raw.map(value => Math.round(value * 1000));
      const index = part.mesh.indices[t * 3 + v];
      const served = part.mesh.positions.slice(index * 3, index * 3 + 3).map(value => Math.round(value * 1000));
      sourcePoints.push(point); servedPoints.push(served);
      if (point.some((value, a) => value !== served[a])) {
        assert.equal(index, 0, 'This captured defect must substitute the first output vertex');
        wrongCorners.push({ triangle: t, corner: v, displacementMm: Math.hypot(...raw.map((value, a) => value - firstRaw[a])) });
      }
    }
    add(expected, triangleKey(sourcePoints)); add(actual, triangleKey(servedPoints));
  }
  const missing = [...expected].reduce((sum, [key, n]) => sum + Math.max(0, n - (actual.get(key) ?? 0)), 0);
  const extra = [...actual].reduce((sum, [key, n]) => sum + Math.max(0, n - (expected.get(key) ?? 0)), 0);
  const recorded = recordedGeometry.parts.find(value => value.part === name);
  assert.equal(sha(data), recorded.assetSha256);
  assert.equal(missing, recorded.missingTriangles); assert.equal(extra, recorded.extraTriangles);
  assert.equal(sha(JSON.stringify([...expected].sort())), recorded.expectedCanonicalSha256);
  assert.equal(sha(JSON.stringify([...actual].sort())), recorded.actualCanonicalSha256);
  comparisons.push({ part: name, sourceTriangles: count, missingTriangles: missing, extraTriangles: extra,
    wrongCorners: wrongCorners.length, maximumDisplacementMm: Math.max(0, ...wrongCorners.map(value => value.displacementMm)) });
}
assert.equal(comparisons[0].wrongCorners, 0); assert.equal(comparisons[1].wrongCorners, 28);
assert.ok(Math.abs(comparisons[1].maximumDisplacementMm - 28.023209685591127) < 1e-10);
const status = json('status.json');
for (const field of ['qualifiedDeployedEngine', 'savedProjectUpdated', 'browserFlightPerformed', 'cadGeometryAccepted']) assert.equal(status[field], false);
console.log(JSON.stringify({ kind: 'offline-preflight-record-audit', recordIntegrityVerified: true,
  artifactFiles: Object.keys(manifest.files).length, originalPayloadsVerified: Object.keys(payloads).length,
  reviewedFilesPreserved: Object.keys(frozen.files).length, sourceRevisionAndInitialBindingsVerified: true,
  staleProducerPinNegativePreserved: true, correctedTriangleInventory: totalTriangles,
  importedPopulations: comparisons, cadGeometryAccepted: false, qualifiedDeployedEngine: false,
  savedProjectUpdated: false, browserFlightPerformed: false }, null, 2));
