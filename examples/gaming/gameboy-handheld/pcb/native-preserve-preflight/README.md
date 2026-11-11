# Exact-source native preservation preflight

The local preservation preparation and independent KiCad 9.0.2 DRC passed on 2026-11-11. The checked PCB is the existing `../handheld-carrier.kicad_pcb`, SHA256 `e7224485efa449271fa0512791f898469b48650111884b55052957224e9cb9df`, 573,344 bytes. No second PCB copy is stored here.

This run called the existing `routeImportedKiCadNative` function with `mode: "preserve"` and the exact `requested-rules.json` values. It returned the original source bytes, resolved project settings and custom rules. An injected fetch guard recorded zero network calls. It did not invoke KiCad DSN export, Freerouting or SES import.

Independent `kicad-cli pcb drc` then returned exit code 0, zero violations and zero unconnected items. The PCB, generated project settings and custom rules kept their before-run hashes. The command used the same flags as the existing hosted `drcBoard` implementation: JSON, millimetres, all severities and nonzero exit on violations. No schematic was supplied, so schematic parity was not checked.

## Evidence and rule identities

| Artifact | Meaning |
| --- | --- |
| `local-preserve-drc-preflight.json` | Combined observed result, exact source/rule identities and limits. |
| `preparation-result.json` | Preservation output identities, input/resolved-rule hashes, zero network calls and the implementation source-file hashes. |
| `drc-execution.json` | Actual local command, timestamps, return code and before/after input hashes. |
| `drc.json`, `drc-stdout.txt`, `drc-stderr.txt` | Unmodified KiCad report and process output. |
| `requested-rules.json` | The explicit rule request used for the measured preservation preparation. |
| `applied-rules.json` | The resolved rule plan, including per-net entries. |
| `board.kicad_pro`, `board.kicad_dru` | Exact generated rules checked by KiCad; they do not replace the authored project settings beside the carrier source. |
| `rule-artifact.json` | Exact serialized rule bundle in the existing API format, bound to the preserved PCB reference. Its SHA256 is the expected content-addressed rules reference. |

The resolved rules digest is `85915592fc0647b75a752e74a1cb3bf552990c2d538ce6f1156da769b9fe1b2e`. The rule artifact is `sha256:389ac1b2b1d20720e62044bddd96947134d28b1bdad5cd4ec13597fb4be20819`. Absolute paths in the raw reports identify the measured execution directories; the generated input bytes are included here.

The rule source is an explicit prototype-design assumption. It has not been qualified against a fabrication supplier. This result is a local preflight. It did not submit a hosted job, create or attach a native LabWired board, or establish physical fit, schematic parity or hardware operation. `../../project-binding.json` records the separate pending hosted steps. The original design-only import and explicit simulation binding remain authoritative for the model coverage limits.

## Re-run DRC without changing the authored source

From this example's `pcb/` directory, using KiCad 9.0.2:

```sh
gameboy_check_dir=$(mktemp -d)
cp handheld-carrier.kicad_pcb "$gameboy_check_dir/board.kicad_pcb"
cp native-preserve-preflight/board.kicad_pro "$gameboy_check_dir/board.kicad_pro"
cp native-preserve-preflight/board.kicad_dru "$gameboy_check_dir/board.kicad_dru"
kicad-cli pcb drc --format json --units mm --severity-all \
  --exit-code-violations --output "$gameboy_check_dir/drc.json" \
  "$gameboy_check_dir/board.kicad_pcb"
```

Check the three input hashes against `drc-execution.json` before and after the run. Keep the new DRC output separate from these recorded observations. A hosted admission must still preserve this exact PCB, run `validate_imported` with its owner-bound rules reference, and pass independent DRC before attachment.
