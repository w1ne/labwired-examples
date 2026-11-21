// Replay real firmware snapshots through production protocol and CAD transform runtimes.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import vm from "node:vm";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, arg, i, all) => i % 2 ? pairs : [...pairs, [arg, all[i + 1]]], []));
for (const key of ["--app", "--kernelcad-app"]) if (!args[key]) throw new Error("Usage: node scripts/check-axiom-joint-transforms.mjs --app APP_CHECKOUT --kernelcad-app KERNELCAD_APP_CHECKOUT [--output PATH]");
const app = path.resolve(args["--app"]), cadApp = path.resolve(args["--kernelcad-app"]);
const example = new URL("../examples/robotics/axiom-h1/", import.meta.url).pathname;
const qa = path.join(app, ".qa/axiom-mechanical-transform");
await fs.mkdir(qa, { recursive: true });
const sourcePath = path.join(example, "mechanical/axiom-compact-frame.kcad.ts");
const code = await fs.readFile(sourcePath, "utf8");
const project = JSON.parse(await fs.readFile(path.join(example, "current-project.input.json"), "utf8"));
const evidenceText = await fs.readFile(path.join(example, "actuator-runtime-evidence.json"), "utf8");
const evidence = JSON.parse(evidenceText);
const hash = (x) => createHash("sha256").update(x).digest("hex");
const names = [...project.source.match(/joint_name\[NUM_JOINTS\] = \{([\s\S]*?)\};/)[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]);
const nums = (name) => project.source.match(new RegExp(name + "\\[NUM_JOINTS\\]=\\{([^}]+)\\}"))[1].split(",").map(Number);
const mins = nums("jmin"), maxs = nums("jmax");
assert.equal(names.length, 20);
assert.match(project.source, /writeReg\(addr,0xFE,121\)/);
assert.match(project.source, /\(uint16_t\)\(110\+390\*fraction\)/);
const parts = /* @__PURE__ */ new Map(), joints = [];
const shape = {};
for (const key of ["translate", "color", "rotateX", "rotateY", "rotateZ", "alongAxis", "union", "subtract"]) shape[key] = () => shape;
const assembly = () => ({ part(name) {
  const p = { name, connectors: /* @__PURE__ */ new Map(), connector(name2, c) {
    this.connectors.set(name2, c);
    return this;
  } };
  parts.set(name, p);
  return p;
}, mate(name, a, b, type, opts) {
  joints.push({ name, a, b, type, ...opts });
}, model() {
  return null;
} });
vm.runInNewContext("(function(){" + code + "})()", { assembly, box: () => shape, sphere: () => shape, cylinder: () => shape, union: () => shape }, { timeout: 1e3 });
assert.equal(parts.size, 27);
const revolutes = joints.filter((j) => j.type === "revolute");
assert.equal(revolutes.length, 20);
const endpoint = (ref) => {
  const i = ref.indexOf(".");
  return { part: ref.slice(0, i), connector: ref.slice(i + 1) };
};
const parentByPart = new Map(joints.map((j) => [endpoint(j.b).part, j]));
const fixedDescendants = (name) => [name, ...joints.filter((j) => j.type === "fastened" && endpoint(j.a).part === name).flatMap((j) => fixedDescendants(endpoint(j.b).part))];
const parentMotion = (part) => {
  const edge = parentByPart.get(part);
  return !edge ? void 0 : edge.type === "revolute" ? edge.name : parentMotion(endpoint(edge.a).part);
};
const motions = names.map((name, i) => {
  const j = revolutes.find((j2) => j2.name === name);
  assert.ok(j, name);
  const a = endpoint(j.a), b = endpoint(j.b), c = parts.get(a.part).connectors.get(a.connector);
  assert.deepEqual(Array.from(j.limitsDeg), [mins[i], maxs[i]], name + " source limits");
  return { id: name, component: "servo" + i, joint: name, ...parentMotion(a.part) ? { parent: parentMotion(a.part) } : {}, parts: fixedDescendants(b.part), origin: Array.from(c.origin.value), axis: Array.from(c.axis), servoPulseMapping: { pulseUs: [536.8, 2440], jointRad: [mins[i] * Math.PI / 180, maxs[i] * Math.PI / 180] } };
});
const electronics = { version: 2, displays: [], inputs: [], motions };
await fs.writeFile(path.join(example, "mechanical/source-derived-electronics.json"), JSON.stringify(electronics, null, 2) + "\n");
const require2 = createRequire(path.join(app, "package.json"));
const { build } = require2("esbuild");
await build({ stdin: { contents: `export {KernelCadRuntimeHost} from ${JSON.stringify(app + "/packages/playground/src/mechanical/kernelcadRuntime.ts")}; export {ElectronicsRuntimeStore} from ${JSON.stringify(cadApp + "/src/funnel/electronics/runtimeStore.ts")}; export {motionGeometries} from ${JSON.stringify(cadApp + "/src/funnel/electronics/motionGeometry.ts")};`, resolveDir: app, sourcefile: "axiom-joint-proof-entry.ts", loader: "ts" }, bundle: true, platform: "node", format: "esm", outfile: path.join(qa, "joint-proof-runtime.mjs"), nodePaths: [app + "/node_modules", cadApp + "/node_modules"], alias: { "@labwired/ui": app + "/packages/ui/src/editor/displayDecoders.ts", "@core": cadApp + "/core/src" } });
const { KernelCadRuntimeHost, ElectronicsRuntimeStore, motionGeometries } = await import(pathToFileURL(path.join(qa, "joint-proof-runtime.mjs")).href);
const model = JSON.parse(await fs.readFile(path.join(example, "mechanical/compact-frame-model.json"), "utf8"));
const review = JSON.parse(await fs.readFile(path.join(example, "mechanical/compact-frame-review.json"), "utf8"));
assert.equal(hash(code), review.cadSourceSha256, "source matches saved revision and geometry receipt");
assert.deepEqual(electronics, model.electronics, "saved model uses the derived bindings");
const target = { slug: model.slug, revision: model.version, parentOrigin: "https://playground.labwired.com" };
const messages = [];
let host;
const store = new ElectronicsRuntimeStore(target, (m) => {
  assert.equal(host.receive(m), true, "CAD acknowledgement");
  messages.push(m);
});
const live = { active: true, electronics: { status: "running", displayBuffers: {}, boardIoStates: {}, cycles: 0, clockHz: 16e7, parts: names.map((_, i) => ({ id: "servo" + i, type: "servo" })), onButtonToggle() {
} } };
host = new KernelCadRuntimeHost({ model, sessionId: "axiom-source-proof", live: () => live, onConnection: (s) => {
  assert.equal(s.accepted, 20);
  assert.equal(s.missing, 0);
}, post: (m) => {
  messages.push(m);
  if (m.type === "kernelcad.runtime.bind") assert.equal(store.bind(m, new Set(parts.keys())), true, "CAD bind");
  else assert.equal(store.frame(m), true, "CAD frame");
} });
host.bind();
const baseline = [...parts.keys()].map((name) => ({ featureId: name, assemblyPartName: name, faces: [] }));
const byId = new Map(motions.map((m) => [m.id, m]));
const applyExpected = (point, id, positions) => {
  const m = byId.get(id);
  if (!m) return point;
  const a = m.axis, n = Math.hypot(...a), u = a.map((v2) => v2 / n), v = point.map((x, i) => x - m.origin[i]), angle = positions.get(id) ?? 0, c = Math.cos(angle), s = Math.sin(angle), dot = v.reduce((sum, x, i) => sum + x * u[i], 0), cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
  const rotated = v.map((x, i) => m.origin[i] + x * c + cross[i] * s + u[i] * dot * (1 - c));
  return m.parent ? applyExpected(rotated, m.parent, positions) : rotated;
};
const applyMatrix = (m, p) => [0, 1, 2].map((i) => m[i] * p[0] + m[4 + i] * p[1] + m[8 + i] * p[2] + m[12 + i]);
const samples = [];
let maxError = 0;
const firstTransforms = /* @__PURE__ */ new Map(), changedParts = /* @__PURE__ */ new Set();
let priorDisabled;
for (const [index, sample] of evidence.samples.entries()) {
  live.electronics.cycles = sample.steps;
  live.electronics.boardIoStates = Object.fromEntries(sample.actuators.map((a) => [a.id, { active: a.active, servoAngle: a.active ? a.angle : void 0, servoPulseUs: a.active ? a.pulse_us : void 0, servoSourceStatus: a.source_status }]));
  host.tick(index * 100);
  const frame = messages.at(-1);
  const expectedActive = sample.actuators.filter((a) => a.active && a.pulse_us >= Math.fround(536.8) && a.pulse_us <= 2440).length;
  assert.equal(frame.motions.length, expectedActive, sample.phase + " actuator count");
  const positions = new Map(frame.motions.map((m) => [m.id, m.positionRad]));
  for (const [i, m] of motions.entries()) {
    const a = sample.actuators.find((a2) => a2.id === m.component), f = frame.motions.find((f2) => f2.id === m.id);
    if (!f) continue;
    const angle = mins[i] + (Math.max(536.8, a.pulse_us) - 536.8) / (2440 - 536.8) * (maxs[i] - mins[i]);
    assert.ok(Math.abs(f.positionRad - angle * Math.PI / 180) < 1e-12, m.id + " pulse mapping");
    assert.equal(f.controlState, a.source_status === "disabled" ? "servo-source-disabled" : a.source_status === "modeled_pwm" ? "servo-modeled-pwm" : "servo-source-unknown");
  }
  const geometry = motionGeometries(baseline, store, baseline);
  const transforms = {};
  for (const motion of motions) for (const part of motion.parts) {
    const g = geometry.find((g2) => g2.assemblyPartName === part);
    if (!g.transform) continue;
    transforms[part] = g.transform;
    for (const point of [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]) {
      const expected = applyExpected(point, motion.id, positions), actual = applyMatrix(g.transform, point);
      const error = Math.max(...actual.map((x, i) => Math.abs(x - expected[i])));
      maxError = Math.max(maxError, error);
      assert.ok(error < 1e-8, part + " affine frame mismatch");
    }
    if (sample.phase === "normal") {
      if (!firstTransforms.has(part)) firstTransforms.set(part, g.transform);
      else if (g.transform.some((x, i) => Math.abs(x - firstTransforms.get(part)[i]) > 1e-8)) changedParts.add(part);
    }
  }
  const allDisabled = frame.motions.length === 20 && frame.motions.every((m) => m.controlState === "servo-source-disabled");
  if (sample.phase.startsWith("estop") && allDisabled) {
    if (priorDisabled) assert.deepEqual(transforms, priorDisabled, "latched E-stop retains joint transforms");
    priorDisabled = transforms;
  }
  samples.push({ phase: sample.phase, steps: sample.steps, acceptedMotions: frame.motions.length, allDisabled, commands: frame.motions, transforms });
}
assert.equal(messages[1].accepted.length, 20);
assert.ok(changedParts.has("neck_pitch"));
assert.ok(changedParts.has("left_gripper"));
assert.ok(priorDisabled);
const sha = (repo) => execFileSync("git", ["rev-parse", "HEAD"], { cwd: repo, encoding: "utf8" }).trim();
const runtimeSourceHashes = Object.fromEntries(await Promise.all([[app, "packages/playground/src/mechanical/kernelcadRuntime.ts"], [cadApp, "src/funnel/electronics/runtimeStore.ts"], [cadApp, "src/funnel/electronics/motionGeometry.ts"], [cadApp, "src/funnel/electronics/runtimeProtocol.ts"]].map(async ([root, file]) => [file, hash(await fs.readFile(path.join(root, file)))])));
const receipt = { model: { slug: model.slug, version: model.version, meshProvenance: model.meshProvenance }, runtimeSourceHashes, schema: "labwired-examples/axiom-joint-transform/v1", status: "passed", proofClass: "source_runtime_protocol_and_affine_geometry", appCommit: sha(app), kernelcadAppCommit: sha(cadApp), cadSourceSha256: hash(code), firmwareSourceSha256: hash(project.source), actuatorEvidenceSha256: hash(evidenceText), bindingCount: motions.length, dynamicPartCount: new Set(motions.flatMap((m) => m.parts)).size, changedParts: [...changedParts], maximumMatrixMarkerErrorMm: maxError, sourceLimitsDeg: names.map((name, i) => ({ name, min: mins[i], max: maxs[i] })), limits: ["No browser rendering, torque, force, gravity, contact or power assertion.", "The pinned CAD revision has a separate sampled collision receipt. This transform proof does not establish physical load capacity.", "Only three joint commands vary in the saved firmware. All 20 pulse mappings and hierarchical transforms are checked."], samples };
await fs.writeFile(args["--output"] ?? path.join(example, "mechanical/joint-transform-evidence.json"), JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify({ status: receipt.status, bindingCount: receipt.bindingCount, dynamicPartCount: receipt.dynamicPartCount, changedParts: receipt.changedParts, maximumMatrixMarkerErrorMm: maxError, samples: samples.length }, null, 2));
