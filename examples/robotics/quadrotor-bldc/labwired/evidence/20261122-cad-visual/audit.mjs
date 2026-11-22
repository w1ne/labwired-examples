import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Verify this recorded local-player comparison without launching a browser,
// evaluating CAD, running firmware, or changing a project.
const root = dirname(fileURLToPath(import.meta.url));
const correction = resolve(root, '../20261122-cad-correction');
const preflight = resolve(root, '../20261122-deployment-preflight');
const sha = value => createHash('sha256').update(value).digest('hex');
const bytes = name => readFileSync(resolve(root, name));
const json = name => JSON.parse(bytes(name));
const manifest = json('artifacts.json');
for (const [name, expected] of Object.entries(manifest.files)) {
  assert.ok(resolve(root, name).startsWith(root + '/'));
  const data = bytes(name);
  assert.equal(data.length, expected.bytes, name);
  assert.equal(sha(data), expected.sha256, name);
}
const baseline = json('baseline-reference.json');
assert.equal(baseline.correctionCommit, '7cffafcd99b3a0a02fb8e1247c3a0d3bc71b92ce');
assert.equal(baseline.correctionManifestSha256, '7c73e9443f4f0307bbf30f3fc0aacc869a72f9292f2e7deacb074083dc82e41e');
assert.equal(baseline.preflightManifestSha256, '31e905b0788cfae3699f31cf7f81ae8a782bbe48e0b03159ed7776dbc016c4b2');
assert.equal(sha(readFileSync(resolve(correction, 'artifacts.json'))), baseline.correctionManifestSha256);
assert.equal(sha(readFileSync(resolve(preflight, 'artifacts.json'))), baseline.preflightManifestSha256);
for (const [directory, names] of [[correction, ['artifact.json.gz', 'qualification/deployed.json', 'status.json']],
  [preflight, ['cad/current-stored-body.bin.gz']]]) {
  const frozen = JSON.parse(readFileSync(resolve(directory, 'artifacts.json'))).files;
  for (const name of names) {
    const data = readFileSync(resolve(directory, name));
    assert.equal(data.length, frozen[name].bytes); assert.equal(sha(data), frozen[name].sha256);
  }
}
const qualificationBytes = readFileSync(resolve(correction, 'qualification/deployed.json'));
assert.equal(sha(qualificationBytes), baseline.qualificationSha256);
const qualification = JSON.parse(qualificationBytes);
assert.equal(qualification.passed, true);
assert.equal(qualification.scriptSha256, 'a26b40eff0c40dc0d0e64563be9c93e780e1f5c0248c4c4993d9c6cd8885d677');
assert.equal(JSON.parse(readFileSync(resolve(correction, 'status.json'))).localPlayerVideoInspected, false);
const captureBytes = bytes('receipts/capture.json');
assert.equal(sha(captureBytes), '484a05abbaf4aec1c6536655110b7b0850bef2f4897e7005050ea8b94b6266e5');
const capture = JSON.parse(captureBytes);
assert.equal(capture.passed, true);
assert.equal(capture.qualificationSha256, sha(qualificationBytes));
assert.equal(capture.oldArtifactSha256, baseline.oldArtifactSha256);
assert.equal(capture.repairedArtifactSha256, baseline.repairedArtifactSha256);
assert.equal(capture.repairedArtifactSha256, qualification.currentArtifact.sha256);
assert.deepEqual(capture.repairedProducer, qualification.currentArtifact.provenance.producer);
assert.equal(capture.sourceSha256, qualification.currentArtifact.provenance.source.sha256);
assert.equal(capture.part, 'fc-population-native-mesh');
const population = qualification.populations.find(part => part.part === capture.part);
assert.equal(capture.triangles, 47778);
assert.equal(capture.triangles, population.triangles);
assert.deepEqual(capture.changedIndices, population.changes.map(change => change.index));
assert.equal(capture.changedIndices.length, 28);
assert.equal(capture.sourceGeometryMutated, false);
assert.equal(capture.remeshingPerformed, false);
assert.equal(capture.localPlayer, true);
assert.equal(capture.actualStoredArtifactComparison, true);
assert.equal(capture.interactiveHostedViewerPaintClaim, false);
assert.equal(capture.playerReadyBeforeGeometryTransfer, true);
assert.equal(capture.ownedBrowserCloseReturned, true);
assert.equal(capture.ownedServerCloseReturned, true);
assert.equal(capture.attachment.attachedOverCdp, false);
assert.equal(capture.attachment.freshTemporaryProfile, true);
assert.deepEqual(capture.attachment.customGpuFlags, []);
assert.equal(capture.attachment.existingTargetsReloadedOrClosed, false);
const build = json('receipts/source-build.json');
assert.equal(build.bundleSha256, capture.rendererBuild);
assert.equal(build.sourceHash, capture.runtimeSourceHash);
assert.equal(build.sourceHead, capture.rendererSourceHead);
assert.equal(build.sourceTree, capture.rendererSourceTree);
assert.equal(build.sourceHash, 'f00d5beda7bb1f5befa8f001329013b0c2b1e6b9ae85019837415deee2d89977');
assert.equal(build.sourceHead, '4aa581464aff2e09b8c2366fb1d166202e0e72d2');
assert.equal(build.sourceTree, 'f879597f14fad52180a9655c5e8835c33256b41d');
assert.equal(build.cleanTrackedSourceBeforeAndAfter, true);
assert.equal(build.committedInputBytesVerified, true);
assert.equal(build.inputByteHashesRecorded, 700);
assert.equal(build.nonDependencyInputOriginsVerified, 549);
assert.deepEqual(build.inputOriginsByRepository, { 'vendor/kernelcad': 398, 'private-overlay': 151 });
assert.equal(build.privateRuntimeFingerprintBeforeAndAfter, build.sourceHash);
assert.equal(build.settings.codeGenerationOrMeshing, false);
const processes = json('receipts/processes.json');
assert.equal(processes.captureScriptSha256, capture.scriptSha256);
assert.equal(processes.scriptSha256, '613595ca4d69828dec537dc80e13345a7db49c58a7871d48e2bf16f92539bc57');
assert.equal(processes.wallLimitSeconds, 100);
assert.equal(processes.captureInternalLimitSeconds, 90);
assert.equal(processes.nodeHeapMiB, 1024);
assert.equal(processes.aggregateOwnedRssCapBytes, 2147483648);
assert.ok(processes.sampledPeakOwnedRssBytes < processes.aggregateOwnedRssCapBytes);
assert.ok(processes.elapsedSeconds < processes.wallLimitSeconds);
assert.equal(processes.captureExitCode, 0);
assert.equal(processes.limitReason, null);
assert.deepEqual(processes.cleanupSignals, []);
assert.equal(processes.allOwnedProcessesExited, true);
assert.deepEqual(processes.remainingOwnedProcesses, []);
assert.equal(processes.existingBrowserProcessesTouched, false);
const browser = json('receipts/browser-install.json');
assert.equal(processes.pinnedBrowserInstallReceiptSha256, browser.originalReceiptSha256);
assert.equal(processes.pinnedBrowserExecutable.sha256, browser.installedExecutable.sha256);
assert.equal(browser.installedExecutable.sha256, '27e55cc30e487493b89b663085d6deeb0707be201a568657c922fac9076c317c');
assert.equal(browser.playwrightVersion, capture.attachment.driverVersion);
assert.equal(browser.requiredBrowser.browserVersion, capture.attachment.browserVersion);
assert.equal(browser.requiredBrowser.revision, '1208');
assert.equal(browser.exitCode, 0);
assert.equal(browser.previousCacheEntriesPreserved, true);
assert.equal(browser.productDependenciesChanged, false);
const frameNames = ['after-iso.png', 'after-top.png', 'before-iso.png', 'before-top.png'];
assert.deepEqual(Object.keys(capture.frames).sort(), frameNames);
for (const name of frameNames) {
  const data = bytes('frames/' + name), expected = capture.frames[name];
  assert.equal(data.length, expected.bytes);
  assert.equal(sha(data), expected.sha256);
  assert.equal(data.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
  assert.equal(data.toString('ascii', 12, 16), 'IHDR');
  assert.equal(data.readUInt32BE(16), 960);
  assert.equal(data.readUInt32BE(20), 960);
}
const encoding = json('receipts/encoding.json');
assert.equal(encoding.captureSha256, sha(captureBytes));
assert.equal(encoding.visualInspectionPerformed, false); // Retain the encoder's earlier observation.
assert.equal(encoding.output, 'crease-corners-stored-artifacts.mp4');
const video = bytes('video/' + encoding.output);
assert.equal(video.length, encoding.bytes);
assert.equal(sha(video), encoding.sha256);
assert.equal(sha(video), 'e5f59905e8e420554a1cd805e077c26ed4badbba8e297d9279a93c70f30ec0b4');
assert.equal(video.toString('ascii', 4, 8), 'ftyp');

const previousEncoding = json('prior/encoding.json');
const previousVideo = bytes('prior/crease-corners-clipped-footer.mp4');
assert.equal(sha(previousVideo), previousEncoding.sha256);
assert.equal(sha(previousVideo), 'ad8b5462377be4cc3bb733bf751a41061e96d6cee50dddadd8b2920d49dafe99');
assert.equal(previousVideo.length, previousEncoding.bytes);
assert.equal(previousEncoding.captureSha256, encoding.captureSha256);
const layout = json('prior/layout-correction.json');
assert.equal(layout.previousVideoSha256, sha(previousVideo));
assert.equal(layout.finalVideoSha256, sha(video));
assert.equal(layout.originalFourPngsAndCaptureByteIdentical, true);
assert.equal(layout.otherInvocationArgumentsUnchanged, true);
assert.equal(layout.previousEncoderSha256, previousEncoding.scriptSha256);
assert.equal(layout.finalEncoderSha256, encoding.scriptSha256);
assert.equal(encoding.scriptSha256, '6dc83e66dd6f15b68c005f7517de6c419923201cf2ab64f44fb15e55d836011e');
assert.deepEqual(layout.normalizedFfmpegInvocationDelta, [
  { before: 'fontsize=23:x=(w-text_w)/2:y=1035', after: 'fontsize=22:x=(w-text_w)/2:y=1032' },
  { before: 'fontsize=18:x=(w-text_w)/2:y=1063', after: 'fontsize=16:x=(w-text_w)/2:y=1059' },
]);
assert.equal(encoding.invocations.length, previousEncoding.invocations.length);
for (const [index, prior] of previousEncoding.invocations.entries()) {
  const current = encoding.invocations[index];
  assert.equal(current.command, prior.command);
  const args = prior.args.map(arg => layout.normalizedFfmpegInvocationDelta.reduce(
    (value, change) => value.replaceAll(change.before, change.after), arg));
  assert.deepEqual(current.args, args);
}
const decodeBytes = bytes('inspection/decode-receipt.json');
const decode = JSON.parse(decodeBytes);
assert.equal(decode.video.sha256, sha(video));
assert.equal(decode.video.bytes, video.length);
assert.deepEqual(decode.video.dimensions, [1920, 1080]);
assert.equal(decode.video.durationSeconds, 8);
assert.equal(decode.video.fps, '24/1');
assert.equal(decode.video.decodedFrameCount, 192);
assert.equal(decode.decodedSequence.complete, true);
assert.deepEqual(decode.decodedSequence.pts, Array.from({ length: 192 }, (_, index) => index));
assert.equal(decode.decodedSequence.framesPerView, 96);
assert.deepEqual(decode.originalFrames, capture.frames);
for (const [name, expected] of Object.entries(decode.outputs)) {
  const data = bytes('inspection/' + name);
  assert.equal(data.length, expected.bytes);
  assert.equal(sha(data), expected.sha256);
}
const probe = json('inspection/ffprobe.json');
assert.equal(probe.streams.length, 1);
const stream = probe.streams[0];
assert.equal(stream.codec_type, 'video');
assert.equal(stream.codec_name, 'h264');
assert.equal(stream.width, 1920); assert.equal(stream.height, 1080);
assert.equal(stream.r_frame_rate, '24/1'); assert.equal(stream.avg_frame_rate, '24/1');
assert.equal(Number(stream.nb_frames), 192); assert.equal(Number(stream.nb_read_frames), 192);
assert.equal(Number(stream.duration), 8); assert.equal(Number(probe.format.duration), 8);
assert.equal(Number(probe.format.size), video.length);
const frameHashesBytes = bytes('inspection/all-192-decoded-frames.framemd5');
const frameHashesText = frameHashesBytes.toString('utf8');
assert.ok(frameHashesText.includes('#tb 0: 1/24'));
assert.ok(frameHashesText.includes('#dimensions 0: 1920x1080'));
const frameRows = frameHashesText.trim().split('\n').filter(line => !line.startsWith('#'))
  .map(line => line.split(',').map(value => value.trim()));
assert.equal(frameRows.length, 192);
for (const [index, row] of frameRows.entries()) {
  assert.equal(row.length, 6); assert.equal(Number(row[0]), 0);
  assert.equal(Number(row[1]), index); assert.equal(Number(row[2]), index);
  assert.equal(Number(row[3]), 1); assert.equal(Number(row[4]), 3110400);
  assert.match(row[5], /^[0-9a-f]{32}$/);
}
assert.equal(new Set(frameRows.map(row => row[5])).size, decode.decodedSequence.uniqueHashes);
const inspectionBytes = bytes('receipts/inspection.json');
assert.equal(sha(inspectionBytes), 'faf75d0668155b9ff3af3e42f574b98b7ffb83710fa134f69a50afa6514f8826');
const inspection = JSON.parse(inspectionBytes);
assert.equal(inspection.observerReview, 'passed');
assert.equal(inspection.video.sha256, sha(video));
assert.equal(inspection.captureSha256, sha(captureBytes));
assert.equal(inspection.encodingReceiptSha256, encoding.originalReceiptSha256);
assert.equal(inspection.decodeReceiptSha256, sha(decodeBytes));
assert.equal(inspection.all192FrameHashesSha256, sha(frameHashesBytes));
assert.deepEqual(inspection.originalFrames, capture.frames);
assert.equal(inspection.playback.exitCode, 0);
assert.ok(inspection.playback.lastReportedTimestampSeconds >= 7.9);
assert.equal(inspection.scope.localPlayerVideoInspected, true);
assert.equal(inspection.scope.actualHostedViewerPaintClaim, false);
assert.equal(inspection.scope.sourceGeometryMutated, false);
assert.equal(inspection.scope.remeshingPerformed, false);
assert.equal(inspection.scope.hardwareOrFlightAcceptanceClaim, false);
assert.equal(inspection.scope.desktopOrUserTargetImagesIncluded, false);
for (const view of ['decoded-top.png', 'decoded-iso.png']) {
  assert.equal(inspection.footerPixelChecks[view].blankRowsBelowFooter, 5);
}
const presentationBytes = bytes('receipts/independent-presentation-review.json');
assert.equal(sha(presentationBytes), inspection.independentRootReview.receiptSha256);
assert.equal(presentationBytes.length, inspection.independentRootReview.receiptBytes);
const presentation = JSON.parse(presentationBytes);
assert.equal(presentation.presentationReviewPassed, true);
assert.equal(presentation.videoSha256, sha(video));
assert.equal(presentation.captureSha256, sha(captureBytes));
assert.equal(presentation.fourCaptureFramesByteIdentical, true);
assert.equal(presentation.fullVideoPlaybackReviewedByRoot, false);
assert.equal(presentation.separateFullPlaybackReviewRequired, true);
assert.equal(presentation.completeDecode.frames, 192);
assert.equal(presentation.completeDecode.ptsContiguous, true);
assert.equal(presentation.decodeReceiptSha256, sha(decodeBytes));
assert.equal(presentation.finalFooterCropSha256, sha(bytes('inspection/footer-root-inspection.png')));
assert.equal(inspection.priorObserverReviewReceiptSha256, sha(bytes('prior/observer-review-before-independent-review.json')));
const status = json('status.json');
assert.equal(status.cadGeometryAccepted, true);
assert.equal(status.localPlayerVideoInspected, true);
assert.equal(status.videoSha256, sha(video));
assert.equal(status.captureSha256, sha(captureBytes));
assert.equal(status.qualifiedArtifactSha256, capture.repairedArtifactSha256);
assert.equal(status.videoBytes, video.length);
assert.equal(status.videoDurationSeconds, 8); assert.equal(status.videoFramesPerSecond, 24);
assert.equal(status.videoDecodedFrames, 192); assert.equal(status.capturedImages, 4);
for (const key of ['interactiveHostedViewerPainted', 'qualifiedDeployedEngine',
  'savedProjectUpdated', 'browserFlightPerformed', 'sourceGeometryChanged', 'remeshingPerformed']) {
  assert.equal(status[key], false, key);
}
console.log(JSON.stringify({ kind: 'offline-local-cad-visual-record-audit', recordIntegrityVerified: true,
  artifactFiles: Object.keys(manifest.files).length, storedArtifactsBound: true,
  renderedPart: capture.part, renderedTriangles: capture.triangles, correctedIndices: capture.changedIndices.length,
  capturedFrames: frameNames.length, decodedVideoFrames: frameRows.length, videoDurationSeconds: 8,
  localPlayerVideoInspected: true, priorEncodingPreserved: true,
  allOwnedProcessesExited: processes.allOwnedProcessesExited,
  qualifiedDeployedEngine: false, savedProjectUpdated: false, browserFlightPerformed: false,
  interactiveHostedViewerPainted: false,
}, null, 2));
