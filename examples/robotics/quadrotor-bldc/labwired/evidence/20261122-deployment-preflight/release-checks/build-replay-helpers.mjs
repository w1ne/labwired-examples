/** Build the existing generated planner helpers at one exact application commit.
 * Usage: node build-replay-helpers.mjs APP_CHECKOUT EXPECTED_COMMIT FRESH_RECEIPT_DIR
 * This does not qualify a deployed runtime or execute a flight.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
const [checkout, expectedCommit, output] = process.argv.slice(2);
if (!checkout || !/^[0-9a-f]{40}$/.test(expectedCommit ?? '') || !output) {
  throw new Error('Expected checkout, exact commit, and fresh receipt directory');
}
const app = resolve(checkout), destination = resolve(output);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const git = (...args) => execFileSync('git', args, { cwd: app, encoding: 'utf8' }).trim();
if (git('rev-parse', 'HEAD') !== expectedCommit) throw new Error('Helper checkout is not the expected commit');
const inputs = ['package.json', 'package-lock.json', 'packages/board-config'];
const assertClean = () => {
  if (git('status', '--porcelain', '--untracked-files=all', '--', ...inputs)) throw new Error('Planner build inputs are not clean');
};
assertClean();
const coreCommit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: resolve(app, 'core'), encoding: 'utf8' }).trim();
const command = ['npm', 'run', 'build', '-w', 'packages/board-config'];
mkdirSync(destination, { recursive: false });
const startedAt = new Date().toISOString();
const built = spawnSync(command[0], command.slice(1), { cwd: app, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
const log = (built.stdout ?? '') + (built.stderr ?? '') + (built.error ? String(built.error) : '');
writeFileSync(resolve(destination, 'build.log'), log, { flag: 'wx' });
const names = ['index.js', 'index.mjs', 'registry.js', 'registry.mjs', 'svd.js', 'svd.mjs', 'labwired-lower.mjs'];
const artifacts = built.status === 0 ? names.map(name => {
  const path = 'packages/board-config/dist/' + name;
  const bytes = readFileSync(resolve(app, path));
  return { path, size: bytes.length, sha256: sha(bytes) };
}) : [];
assertClean();
const receipt = { kind: 'exact-commit-planner-helper-build', appDirectory: app, appCommit: expectedCommit,
  appTree: git('rev-parse', 'HEAD^{tree}'), coreCommit, command, startedAt, finishedAt: new Date().toISOString(),
  exitCode: built.status, signal: built.signal, nodeVersion: process.version,
  npmVersion: execFileSync('npm', ['--version'], { cwd: app, encoding: 'utf8' }).trim(),
  lockfileSha256: sha(readFileSync(resolve(app, 'package-lock.json'))),
  buildScriptSha256: sha(readFileSync(fileURLToPath(import.meta.url))), buildLogSha256: sha(log), artifacts,
  flightExecuted: false };
writeFileSync(resolve(destination, 'helper-build-receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(receipt, null, 2));
if (built.status !== 0) process.exitCode = 1;
