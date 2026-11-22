import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, copyFileSync, mkdtempSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { gunzipSync } from 'node:zlib';
import { spawnSync } from 'node:child_process';

// Offline record verification. This does not contact a service, render a model,
// run firmware, change a saved project, or claim that a browser flight occurred.
const root = dirname(fileURLToPath(import.meta.url));
const baseline = resolve(process.argv[2] ?? resolve(root, '../20261122-deployment-preflight'));
const sha = data => createHash('sha256').update(data).digest('hex');
const bytes = name => readFileSync(resolve(root, name));
const json = name => JSON.parse(bytes(name));
const manifest = json('artifacts.json');
for (const [name, expected] of Object.entries(manifest.files)) {
  assert.ok(resolve(root, name).startsWith(root + '/'), 'Artifact path leaves the bundle');
  const data = bytes(name);
  assert.equal(data.length, expected.bytes, name);
  assert.equal(sha(data), expected.sha256, name);
}
const previous = json('baseline-reference.json');
assert.equal(previous.examplesCommit, '4d21fea30c19d856d2d1ecd16272d9fab934df46');
assert.equal(previous.manifestSha256, '31e905b0788cfae3699f31cf7f81ae8a782bbe48e0b03159ed7776dbc016c4b2');
assert.equal(sha(readFileSync(resolve(baseline, 'artifacts.json'))), previous.manifestSha256);
const status = json('status.json');
assert.equal(status.cadGeometryAccepted, true);
assert.equal(status.cadProducerQualified, true);
assert.equal(status.localPlayerVideoInspected, false);
assert.ok(status.remaining.includes("inspected artifact-direct video"));
for (const name of ['qualifiedDeployedEngine', 'savedProjectUpdated', 'browserFlightPerformed',
  'cadSourceChanged', 'cadAssetsChanged', 'cadSavedRevisionChanged', 'manualMeshGenerationCalled']) {
  assert.equal(status[name], false, name);
}
const artifact = gunzipSync(bytes('artifact.json.gz'));
const expectedPayload = json('payloads.json')['artifact.json.gz'];
assert.equal(artifact.length, expectedPayload.decodedBytes);
assert.equal(sha(artifact), expectedPayload.decodedSha256);
assert.equal(sha(artifact), '166131d834781b76829ffa8d591da349e8c05b7a1206f2338c62cb73de748082');
assert.equal(artifact.length, 12865359);
const source = json('source-links.json');
assert.equal(source.serverCommit, 'fd52f2c20b801c8a7ab875ebeb6b844a928baf97');
assert.equal(source.runtimeSourceHash, 'f00d5beda7bb1f5befa8f001329013b0c2b1e6b9ae85019837415deee2d89977');
const qualificationBytes = bytes('qualification/deployed.json');
const recorded = JSON.parse(qualificationBytes);
assert.equal(recorded.passed, true);
assert.equal(recorded.scriptSha256, 'a26b40eff0c40dc0d0e64563be9c93e780e1f5c0248c4c4993d9c6cd8885d677');
assert.equal(sha(bytes('qualification/qualify-repaired-cad.mjs')), recorded.scriptSha256);
assert.equal(sha(bytes('qualification/fetch-repaired-cad.mjs')), '84ad521d18c64d238430f67361efc30e7227d2e6e508dc4d0c443040cdf55854');
const priorFailure = json('qualification/negative-old.json');
assert.equal(priorFailure.passed, false);
assert.equal(priorFailure.currentArtifact.sha256, previous.oldArtifactSha256);
assert.equal(priorFailure.scriptSha256, recorded.scriptSha256);
assert.deepEqual(priorFailure.populations.map(part => part.wrongCorners), [0, 28]);
const independent = json('qualification/independent-production-review.json');
assert.equal(independent.passed, true);
assert.equal(independent.sha256, sha(artifact));
assert.equal(independent.features, 39);
assert.equal(independent.assemblyParts, 38);
assert.equal(independent.correctedFcCorners, 28);
assert.equal(independent.independentCorrectedCornerSourceCheck, true);
assert.equal(independent.everyOtherFcFieldUnchanged, true);
assert.equal(independent.serverCommit, source.serverCommit);
assert.equal(independent.runtimeSourceHash, source.runtimeSourceHash);

const failedCaptureBytes = bytes('visual/capture-failed.json');
const failedCapture = JSON.parse(failedCaptureBytes);
assert.equal(failedCapture.passed, false);
assert.deepEqual(failedCapture.frames, {});
assert.equal(failedCapture.oldArtifactSha256, previous.oldArtifactSha256);
assert.equal(failedCapture.repairedArtifactSha256, sha(artifact));
assert.equal(failedCapture.qualificationSha256, sha(qualificationBytes));
assert.equal(failedCapture.runtimeSourceHash, source.runtimeSourceHash);
assert.equal(failedCapture.failure.name, 'TimeoutError');
assert.equal(failedCapture.failure.message, 'Waiting failed: 15000ms exceeded');
assert.equal(failedCapture.attachment.evaluateCalls, 0);
assert.equal(failedCapture.attachment.screenshotCalls, 0);
assert.deepEqual(failedCapture.attachment.typedArrayTransfers, []);
assert.equal(failedCapture.attachment.ownedContextDisposed, true);
assert.equal(failedCapture.attachment.connectionDisconnected, true);
const failedResources = json('visual/capture-failed-resources.json');
assert.equal(failedResources.captureSha256, sha(failedCaptureBytes));
assert.equal(failedResources.exitCode, 1);
assert.equal(failedResources.framesCaptured, 0);
assert.equal(failedResources.buffersTransferred, 0);

const input = mkdtempSync(join(tmpdir(), 'quadrotor-cad-record-audit-'));
let verified = false;
try {
  for (const name of ['getProject-ready.json', 'getProjectRevision.json']) {
    copyFileSync(resolve(root, 'readback', name), join(input, name));
  }
  for (const name of ['current-stored-receipt.json', 'current-cdn-receipt.json']) {
    copyFileSync(resolve(root, 'download', name), join(input, name));
  }
  for (const name of ['current-stored-body.bin', 'current-cdn-body.bin']) writeFileSync(join(input, name), artifact, { flag: 'wx' });
  const output = join(input, 'recomputed.json');
  const run = spawnSync(process.execPath, [
    '--max-old-space-size=1024', resolve(root, 'qualification/qualify-repaired-cad.mjs'),
    baseline, input, source.serverCommit, source.runtimeSourceHash, output,
  ], { encoding: 'utf8', timeout: 20000, maxBuffer: 65536 });
  assert.equal(run.status, 0, run.stderr || run.stdout || String(run.error));
  const recomputed = JSON.parse(readFileSync(output));
  recomputed.checkedAt = recorded.checkedAt; // Re-evaluation time is the sole expected difference.
  assert.deepEqual(recomputed, recorded);
  assert.equal(status.artifactSha256, recorded.currentArtifact.sha256);
  assert.equal(status.sourceSha256, recorded.currentArtifact.provenance.source.sha256);
  assert.equal(status.producerPin, recorded.currentArtifact.producerPin);
  assert.equal(status.geometrySha256, recorded.geometry.actualSha256);
  assert.equal(recorded.geometry.actualSha256, recorded.geometry.expectedSha256);
  assert.equal(recorded.geometry.assemblyParts, 38);
  assert.deepEqual(recorded.populations.map(part => part.wrongCorners), [0, 0]);
  assert.deepEqual(recorded.populations.map(part => part.indexChanges), [0, 28]);
  verified = true;
} finally {
  if (verified) rmSync(input, { recursive: true, force: true });
  else console.error('Failed audit inputs and output retained at ' + input);
}
console.log(JSON.stringify({
  kind: 'offline-deployed-cad-record-audit', recordIntegrityVerified: true,
  artifactFiles: Object.keys(manifest.files).length, cadGeometryAccepted: true,
  producer: recorded.currentArtifact.provenance.producer,
  assemblyParts: recorded.geometry.assemblyParts,
  importedSourceTriangles: recorded.populations.reduce((sum, part) => sum + part.triangles, 0),
  wrongCorners: 0, changedFcIndices: 28, priorNegativePreserved: true,
  inspectedLocalPlayerVideo: false, visualRecordPending: true,
  qualifiedDeployedEngine: false, savedProjectUpdated: false, browserFlightPerformed: false,
}, null, 2));
