import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const dir = resolve(process.argv[2] ?? '');
assert.ok(process.argv[2], 'Usage: node fetch-repaired-cad.mjs FRESH_READBACK_DIR');
const current = JSON.parse(readFileSync(resolve(dir, 'getProject-ready.json')));
assert.equal(current.ok, true);
assert.equal(current.slug, 'DyJ405zg');
assert.equal(current.version, 6);
assert.equal(current.meshStatus, 'ready');
assert.equal(current.meshReady, true);
const sha = value => createHash('sha256').update(value).digest('hex');
const canonical = value => Array.isArray(value)
  ? '[' + value.map(canonical).join(',') + ']'
  : value !== null && typeof value === 'object'
    ? '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
    : JSON.stringify(value);
const requests = [
  ['current-stored', current.meshDownloadUrl, 'https://api.kernelcad.com', '/api/v1/projects/DyJ405zg/revisions/6/mesh-artifact'],
  ['current-cdn', current.meshUrl, 'https://mesh.kernelcad.com', '/mesh-artifacts/DyJ405zg/v6.json'],
];
for (const [name, value, origin, path] of requests) {
  const url = new URL(value);
  assert.equal(url.origin, origin);
  assert.equal(url.pathname, path);
  assert.match(url.searchParams.get('provenance') ?? '', /^[0-9a-f]{64}$/);
  if (name === 'current-stored') assert.equal(url.searchParams.get('download'), '1');
  for (const suffix of ['-body.bin', '-receipt.json', '-failure.json']) {
    assert.equal(existsSync(resolve(dir, name + suffix)), false, 'Preserve previous attempts; use a fresh directory');
  }
}
const results = await Promise.allSettled(requests.map(async ([name, url]) => {
  const startedAt = new Date().toISOString();
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(12000) });
    const bytes = Buffer.from(await response.arrayBuffer());
    const receipt = {
      startedAt, completedAt: new Date().toISOString(), url, finalUrl: response.url,
      status: response.status, headers: Object.fromEntries(response.headers),
      sha256: sha(bytes), byteLength: bytes.length,
    };
    writeFileSync(resolve(dir, name + '-body.bin'), bytes, { flag: 'wx' });
    try {
      const body = JSON.parse(bytes);
      receipt.bodyKeys = Object.keys(body);
      receipt.revision = body.revision;
      receipt.error = body.error;
      if (body.provenance) {
        receipt.provenance = body.provenance;
        receipt.provenanceSha256 = sha(canonical(body.provenance));
        receipt.requestedProvenance = new URL(url).searchParams.get('provenance');
        receipt.provenanceMatchesRequest = receipt.provenanceSha256 === receipt.requestedProvenance;
      }
    } catch {
      receipt.textPrefix = bytes.toString().slice(0, 300);
    }
    writeFileSync(resolve(dir, name + '-receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
    return { name, status: receipt.status, sha256: receipt.sha256, bytes: receipt.byteLength,
      requestedProvenance: receipt.requestedProvenance, provenanceSha256: receipt.provenanceSha256,
      provenanceMatchesRequest: receipt.provenanceMatchesRequest, error: receipt.error };
  } catch (error) {
    const failure = { startedAt, failedAt: new Date().toISOString(), url, error: String(error) };
    writeFileSync(resolve(dir, name + '-failure.json'), JSON.stringify(failure, null, 2) + '\n', { flag: 'wx' });
    throw new Error(JSON.stringify({ name, ...failure }));
  }
}));
for (const result of results) {
  if (result.status === 'fulfilled') {
    console.log(JSON.stringify(result.value));
    if (result.value.status !== 200 || result.value.provenanceMatchesRequest !== true) process.exitCode = 1;
  } else {
    console.log(String(result.reason));
    process.exitCode = 1;
  }
}
