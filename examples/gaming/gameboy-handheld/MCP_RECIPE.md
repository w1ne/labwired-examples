# Generic MCP recipe: saved handheld

The circuit, firmware, input track, behavioral proof and saved CAD bindings use
existing generic LabWired and KernelCAD tools. The saved Brick Breaker project
passed its unchanged six-clause oracle through MCP on 2026-11-11. The exact
[request, result and unchanged-content readback](firmware/brick-breaker-saved-project-verification-mcp.json)
record the 50,000,000-step budget and matching content/verified hash
`626abc0c2c33242a95223c8fd37523338a2965b2a0da5b11dace42d75c60825b`.

This recipe uses generic tool calls and checked-in data. It adds no device tool,
separate simulator or orchestration service.

## Read the live contract and existing project

Call `labwired_context`, then `labwired_search` for the operation you need. The
live discovery schema is authoritative when a connector's older wrapper omits a
field. During this audit, live revision `mcp-2bd081b7` exposed `max_steps` on
`labwired_project_verify`; the older registered wrapper did not list it. The
connected tool accepted the live-defined field and passed the exact proof.

```json
{"query":"labwired_project_verify"}
```

Read the saved state with `labwired_project_get`:

```json
{"project_id":"f44771855a18a70d418e363622de2e28"}
```

Retain the returned `content_hash` for any subsequent write. Keep the full
`diagram_json`, input `stimuli`, firmware profile and unlisted visibility. The
saved diagram contains KernelCAD `kQAFdaQs`, revision 3, its mesh provenance, one
LCD binding and eight input bindings. These are normal design fields; no
handheld-specific MCP interface is needed.

Use `labwired_list` and `labwired_describe` to check the requested
`stm32f411ceu6-blackpill`, `ili9341` and `button` capabilities. Use
`labwired_validate` on the exact diagram before a circuit change.

## Compile and test changed firmware

Use `labwired_put_source` with the full `firmware/brick_breaker.c` contents and
`entryPath: "src/main.c"`. Pass its `source_tree_ref` to `labwired_compile` with
`board: "stm32f411ceu6-blackpill"`, `language: "c"` and the same entry path.

The complete precompiled verification call is stored in
[brick-breaker-verify-request.json](firmware/brick-breaker-verify-request.json).
For a new build, replace only its `firmware_ref` with the compile result, retain
the diagram, all four input events and the full declared oracle, then call
`labwired_verify`. `labwired_run` is observational; it does not mint proof.
`labwired_inspect` reads a stored run's UART, registers and framebuffer.

To save a verified change, call `labwired_project_update` with `project_id`, the
fresh `expected_content_hash`, complete source and updated `diagram`. Update
both `diagram.firmware.artifact.ref` and its source-tree/file references so the
browser cannot replay an older cached ELF. Preserve the mechanical object,
PCB attachment, visibility and input track. Read back the resulting project
before verifying its saved content.

## Verify the exact saved project

Call `labwired_project_verify` with this complete request:

```json
{
  "project_id": "f44771855a18a70d418e363622de2e28",
  "max_steps": 50000000,
  "oracle": {
    "serial": [
      {"contains": "DMG_ROM_OK title=BRICK_BREAKER"},
      {"contains": "INPUT=000000ef"},
      {"contains": "INPUT=000000fe"},
      {"matches": "DMG_FRAME=[0-9]+ x=([7-9][0-9]|1[0-3][0-9]) ball_x="},
      {"matches": "DMG_FRAME=[0-9]+ .*phase=1"}
    ],
    "display": {"painted": true, "min_ink_bytes": 10000}
  }
}
```

The saved input events occur at 22M, 35M, 36M and 42M cycles. A shorter default
run cannot reach this track. Do not remove input or display clauses to obtain a
badge. Read the project again and require `content_hash === verified_hash` for
the content that was actually tested. The successful receipt above preserves
source, diagram, input events, mechanical bindings, native PCB reference and
visibility.

## Open the actual interactive device

The current high-level entry is `labwired_hardware`, not the stale companion
name `labwired_hardware_pack`. To open this existing hardware card without
asking the agent to change or route it, call exactly:

```json
{"request":"view","project_id":"f44771855a18a70d418e363622de2e28"}
```

The current handler recognizes `view` as a read-only request and returns the
existing board card before the agent/design/routing branch. Other instructions
can revise hardware; do not use a mutation request merely to inspect the saved
native carrier.

[Open the saved device in KernelCAD with Run enabled](https://app.labwired.com/p/f44771855a18a70d418e363622de2e28/edit?run=1&view=kernelcad).
Press A to launch and hold LEFT/RIGHT to steer. The on-model controls feed the
simulated STM32 GPIO; the firmware updates the real modeled ILI9341 through SPI.
The [visible-browser receipt](media/promo-v4/browser-verification.json) records
RIGHT movement, A launch, changing LCD hashes and continued display frames in
the native exploded view. This browser QA used a browser tool, not LabWired MCP.

For an isolated candidate, `labwired_lab` accepts the same diagram, a compiled
`firmware_ref` and `autorun: true`. It returns a temporary share URL without
replacing the saved project. Add `view=kernelcad` to that returned URL to select
the linked CAD view. Live discovery lists `firmware_ref` and `autorun`, although
older connector projections can omit them.

## Native PCB and movie boundaries

The attached native carrier is `pcb_c8da1d7776dba9bc`, revision 0. Its original
attachment used the authenticated project-board HTTP route. Existing-board
attachment is not yet a published argument of `labwired_project_update`; a
bounded `board_ref` extension is under review. Do not recreate or autoroute a
replacement board to work around this gap. Native import has 2 mapped,
9 design-only and 5 ignored parts and reports `twin_buildable: false`. The
working MCU circuit is explicit and independently verified; a routed native
board view is not automatic circuit-simulation proof.

The promotional movie uses offline rendering of the actual saved CAD and exact
ROM-emulator frame capture. Its 60 fps export does not measure browser or STM32
wall-clock speed. The attempted hosted KernelCAD `capture_animation` call
returned zero frames and `cli.invalid-args`; its exact request/result is in
[mcp-capture-probe.json](media/promo-v4/mcp-capture-probe.json). That receipt
records a failed capability probe, not a completed MCP recording. Synchronized
LabWired simulation, controls, native explosion and movie recording through a
single product-MCP path remain incomplete at this checkpoint.

## Contract sources

The audited LabWired source revision is
[`6093f09869e99c28e079dee5c4a1d018434b9966`](https://github.com/w1ne/labwired/tree/6093f09869e99c28e079dee5c4a1d018434b9966).
The relevant existing implementations are
[`mcp/handlers/project.ts`](https://github.com/w1ne/labwired/blob/6093f09869e99c28e079dee5c4a1d018434b9966/packages/api/src/mcp/handlers/project.ts),
[`mcp/handlers/hardware.ts`](https://github.com/w1ne/labwired/blob/6093f09869e99c28e079dee5c4a1d018434b9966/packages/api/src/mcp/handlers/hardware.ts),
[`project-board.ts`](https://github.com/w1ne/labwired/blob/6093f09869e99c28e079dee5c4a1d018434b9966/packages/api/src/project-board.ts),
and [`studio/viewSettings.ts`](https://github.com/w1ne/labwired/blob/6093f09869e99c28e079dee5c4a1d018434b9966/packages/playground/src/studio/viewSettings.ts).
