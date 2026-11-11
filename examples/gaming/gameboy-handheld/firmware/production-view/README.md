# Deployed frontend evidence, 2026-11-11

The dedicated KernelCAD view rendered the saved revision 3 assembly in isolated desktop and mobile guest browsers. The same simulation Worker continued while CAD was visible and the same iframe survived return and reopen. This evidence does not establish native PCB attachment or owner-session rendering.

| Observation | Result | Record |
|---|---|---|
| Normal signed-in owner access | HTTP 200, owner role, unchanged project content and source/ELF/CAD pins; no PCB attached | `owner-access-webgl.json` |
| Real owner Chrome rendering | Failed: WebGL context creation failed. A blank 16 × 16 canvas reproduced the same failure. No browser setting or application source was changed | `owner-access-webgl.json` |
| Desktop guest, 1440 × 1000 | Exact CAD3 geometry, camera and frame ready; same Worker advanced 45,000,000 cycles while visible; zero uncaught exceptions | `desktop-guest.json`, `desktop-cad.png` |
| Mobile guest, 390 × 844 | Exact CAD3 geometry, camera and frame ready; same Worker advanced 65,000,000 cycles while visible; zero uncaught exceptions | `mobile-guest.json`, `mobile-cad.png` |
| Console/resource status | Desktop retains 8 errors; mobile retains 7. `clean_console` is false | Guest records |
| Native PCB | Not attached or verified in the production PCB view | `index.json` |

`index.json` binds the observed frontend builds, document modules, simulation Worker asset, exact saved firmware/source references, CAD revision/provenance, and screenshot hashes. Its asset URLs identify what the browser loaded; this run did not separately hash the full JavaScript, Wasm, or loaded ELF bytes.

The owner observation used the normal signed-in work-1 profile. The guest observations used fresh, separate Chromium profiles with software WebGL. They copied no owner storage, supplied no authorization header, and did not disable authentication. The unlisted saved project permitted normal anonymous reads. The mobile completion used the visible analytics Decline control before opening CAD.

The desktop observed build `bacc11ed98f975ff1849617678ac784463d9bca6`; mobile observed `93386ad2c73f06353e84915b13b847b2c49860de`. The Git difference between those commits is only `.github/workflows/pages-deploy.yml`. Their actual module filenames remain separate in the records. An earlier mobile case stopped when deployment changed between page load and manifest read. A second case stopped at the analytics overlay. `interrupted-attempts.json` retains both outcomes; they are not counted as rendering passes.

The errors include the unauthenticated board endpoint, KernelCAD font MIME handling, telemetry CORS, and optional animation requests. The exact static CAD mesh still reached the documented ready state. Owner diagnostics retain a bounded exception stack and hashes of the full task records, without account subjects, credentials, private session data, or owner screenshots.

These records were captured before native-preserve admission and project-board ownership fixes deployed. No hosted preservation job or canonical project mutation occurred in these frontend checks. The previous local production-preview evidence remains in `../browser-revision3-validation.json` and `../browser-revision3-assessment.json`.
