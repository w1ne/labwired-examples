/* @ts-self-types="./labwired_wasm.d.ts" */

/**
 * Shared lab air: nRF `VirtualAirBus` + ESP `BleAirBus` +
 * [`SimMqttFabric`] + optional path-loss [`RfMedium`]. Create ONE per
 * lab-group and pass it to every chip via `attach_lab_air` — same pattern as
 * [`WireBus`]. Path-loss CSQ and MQTT fabric share this air.
 */
export class AirBus {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        AirBusFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_airbus_free(ptr, 0);
    }
    /**
     * @param {string} topic
     * @returns {boolean}
     */
    cellular_has_publish(topic) {
        const ptr0 = passStringToWasm0(topic, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.airbus_cellular_has_publish(this.__wbg_ptr, ptr0, len0);
        return ret !== 0;
    }
    /**
     * @param {number} limit
     * @returns {string}
     */
    cellular_inspect(limit) {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.airbus_cellular_inspect(this.__wbg_ptr, limit);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @param {string} topic
     * @returns {Uint8Array}
     */
    cellular_last_payload(topic) {
        const ptr0 = passStringToWasm0(topic, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.airbus_cellular_last_payload(this.__wbg_ptr, ptr0, len0);
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    clear_ble() {
        wasm.airbus_clear_ble(this.__wbg_ptr);
    }
    clear_cellular() {
        wasm.airbus_clear_cellular(this.__wbg_ptr);
    }
    clear_nrf() {
        wasm.airbus_clear_nrf(this.__wbg_ptr);
    }
    /**
     * Enable path-loss medium (seeded). Positions via `set_node_position`.
     * Co-located nodes stay lossless until placed apart.
     * @param {number} seed
     * @param {number} rssi_floor_dbm
     */
    enable_path_loss(seed, rssi_floor_dbm) {
        wasm.airbus_enable_path_loss(this.__wbg_ptr, seed, rssi_floor_dbm);
    }
    /**
     * Drop SimMqttFabric state (publish log + subscriptions).
     */
    mqtt_fabric_clear() {
        wasm.airbus_mqtt_fabric_clear(this.__wbg_ptr);
    }
    /**
     * True if any modem on this air published to `topic` (exact match).
     * @param {string} topic
     * @returns {boolean}
     */
    mqtt_fabric_has_publish(topic) {
        const ptr0 = passStringToWasm0(topic, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.airbus_mqtt_fabric_has_publish(this.__wbg_ptr, ptr0, len0);
        return ret !== 0;
    }
    /**
     * Inspect fabric: up to `limit` lines of `topic\\tpayload` (most recent first).
     * @param {number} limit
     * @returns {string}
     */
    mqtt_fabric_inspect(limit) {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.airbus_mqtt_fabric_inspect(this.__wbg_ptr, limit);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Latest payload bytes for an exact topic, or empty if none.
     * @param {string} topic
     * @returns {Uint8Array}
     */
    mqtt_fabric_last_payload(topic) {
        const ptr0 = passStringToWasm0(topic, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.airbus_mqtt_fabric_last_payload(this.__wbg_ptr, ptr0, len0);
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    constructor() {
        const ret = wasm.airbus_new();
        this.__wbg_ptr = ret;
        AirBusFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * Place a node (MCU part id) in metres for path-loss.
     * @param {string} node_id
     * @param {number} x
     * @param {number} y
     */
    set_node_position(node_id, x, y) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        wasm.airbus_set_node_position(this.__wbg_ptr, ptr0, len0, x, y);
    }
}
if (Symbol.dispose) AirBus.prototype[Symbol.dispose] = AirBus.prototype.free;

export class WasmFlexRuntime {
    static __wrap(ptr) {
        const obj = Object.create(WasmFlexRuntime.prototype);
        obj.__wbg_ptr = ptr;
        WasmFlexRuntimeFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmFlexRuntimeFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmflexruntime_free(ptr, 0);
    }
    /**
     * @param {number} delta_ns
     */
    advance_ns(delta_ns) {
        const ret = wasm.wasmflexruntime_advance_ns(this.__wbg_ptr, delta_ns);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * @param {bigint} cursor
     * @returns {any}
     */
    analog_trace_snapshot(cursor) {
        const ret = wasm.wasmflexruntime_analog_trace_snapshot(this.__wbg_ptr, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {bigint} cursor
     * @returns {any}
     */
    digital_trace_snapshot(cursor) {
        const ret = wasm.wasmflexruntime_digital_trace_snapshot(this.__wbg_ptr, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} yaml
     * @returns {WasmFlexRuntime}
     */
    static new_from_yaml(yaml) {
        const ptr0 = passStringToWasm0(yaml, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmflexruntime_new_from_yaml(ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return WasmFlexRuntime.__wrap(ret[0]);
    }
    /**
     * @param {string} name
     * @returns {number}
     */
    port_id(name) {
        const ptr0 = passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmflexruntime_port_id(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * @returns {any}
     */
    ports() {
        const ret = wasm.wasmflexruntime_ports(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {number} port
     * @returns {number}
     */
    read(port) {
        const ret = wasm.wasmflexruntime_read(this.__wbg_ptr, port);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0];
    }
    /**
     * @returns {bigint}
     */
    time_ns() {
        const ret = wasm.wasmflexruntime_time_ns(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return BigInt.asUintN(64, ret[0]);
    }
    /**
     * @param {number} port
     * @param {number} value
     */
    write(port, value) {
        const ret = wasm.wasmflexruntime_write(this.__wbg_ptr, port, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
}
if (Symbol.dispose) WasmFlexRuntime.prototype[Symbol.dispose] = WasmFlexRuntime.prototype.free;

export class WasmSimulator {
    static __wrap(ptr) {
        const obj = Object.create(WasmSimulator.prototype);
        obj.__wbg_ptr = ptr;
        WasmSimulatorFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmSimulatorFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmsimulator_free(ptr, 0);
    }
    /**
     * Snapshot of the shared virtual-air TX trace ring buffer (last
     * ~200 BLE/proprietary frames pushed by any chip in this WASM
     * instance, most-recent-first). The playground's BLE-on-canvas
     * visualization polls this to render the packet trace panel; the
     * underlying state lives in a Rust static, so any WasmSimulator
     * can return the same snapshot — pick whichever chip is alive.
     * @returns {any}
     */
    air_trace_snapshot() {
        const ret = wasm.wasmsimulator_air_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * Channel table of the in-core analog engine's waveform trace: one entry
     * per probed model output plus any extra `trace:` expressions, each with
     * its unit (`"V"` or `"A"`).
     *
     * Empty until a co-simulation runner carrying an `adapter: analog` model
     * is attached to the machine. Empty is the honest answer for a lab with no
     * circuit in it: the oscilloscope shows no channels rather than a flat
     * line at zero that nothing measured.
     * @returns {any}
     */
    analog_channels() {
        const ret = wasm.wasmsimulator_analog_channels(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The run-long, change-point series of every analog channel (a coil's
     * `i(L1)`, a probed node): the same block `labwired test` writes as
     * `result.json`'s `analog_series`, so a hosted oracle reads the identical
     * evidence. `null` when no co-simulation session is attached.
     * @returns {any}
     */
    analog_series() {
        const ret = wasm.wasmsimulator_analog_series(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Analog samples newer than `cursor`, plus the cursor to pass next time.
     *
     * Cursors are sample sequence numbers, the same contract as
     * `read_logic_edges`, and are JS numbers for the same reason: sample
     * counts stay far under 2^53, and a `BigInt` at this boundary would make
     * the scope panel the only caller in the playground that cannot pass a
     * plain `0`.
     *
     * `dropped` counts samples the ring overwrote before they were read, so
     * the panel can mark a gap instead of drawing a straight line across one.
     * @param {number} cursor
     * @returns {any}
     */
    analog_trace_snapshot(cursor) {
        const ret = wasm.wasmsimulator_analog_trace_snapshot(this.__wbg_ptr, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Apply a binary `MachineRuntimeSnapshot` (LWRS-framed bincode blob,
     * produced by `labwired-cli snapshot capture` or `Machine::take_runtime_snapshot`)
     * to the currently-loaded machine. Bypasses the cold boot — the firmware
     * resumes mid-flight from the captured CPU + peripheral state.
     *
     * Must be called after firmware has been loaded onto the same system
     * manifest (peripheral names + CPU arch must match the snapshot). On
     * mismatch the call returns an error and the machine state is left
     * partially overwritten — callers should treat that as a hard reset.
     * @param {Uint8Array} bytes
     */
    apply_runtime_snapshot(bytes) {
        const ptr0 = passArray8ToWasm0(bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_apply_runtime_snapshot(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Bind this chip's nRF RADIO + ESP32-C3 BT + cellular modem to a shared
     * multi-chip [`AirBus`] (browser lab-group). `node_id` is the MCU part id
     * for path-loss layout and UE identity.
     * @param {string} node_id
     * @param {AirBus} air
     */
    attach_lab_air(node_id, air) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        _assertClass(air, AirBus);
        wasm.wasmsimulator_attach_lab_air(this.__wbg_ptr, ptr0, len0, air.__wbg_ptr);
    }
    /**
     * Attach the emulated S110 SoftDevice to a built nRF51 whose firmware is
     * an S110 APPLICATION region at 0x18000 (micro:bit V1, Calliope mini 1).
     * Journaled. Also releases buttons A (P0.17) and B (P0.26), which the
     * board pulls up: left floating low, the DAL reads both as held at reset
     * and enters Bluetooth pairing mode, which never returns.
     * @param {string} node
     */
    attach_softdevice_s110(node) {
        const ptr0 = passStringToWasm0(node, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_attach_softdevice_s110(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Connect this chip's UART (`uart_id`, e.g. "uart2") to a shared cross-link
     * `bus`, so it exchanges bytes with the other chip on the same `link_id`.
     * The two chips of a point-to-point IO-Link use opposite `side`s (0 and 1)
     * of the SAME `WireBus`. Bytes flow through the bus with no per-byte host
     * round-trip, so both chips can keep stepping in batches. Chips wired to
     * different `WireBus` instances are fully isolated.
     * @param {string} uart_id
     * @param {number} link_id
     * @param {number} side
     * @param {WireBus} bus
     */
    attach_uart_wire(uart_id, link_id, side, bus) {
        const ptr0 = passStringToWasm0(uart_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        _assertClass(bus, WireBus);
        const ret = wasm.wasmsimulator_attach_uart_wire(this.__wbg_ptr, ptr0, len0, link_id, side, bus.__wbg_ptr);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Bench runner: execute `cycles` `step_with_esp32_aids` iterations
     * and return elapsed milliseconds (measured via
     * `performance.now()`). The caller drives this twice — once with
     * `set_jit_enabled(false)`, once with `set_jit_enabled(true)` —
     * and compares the two numbers to quantify JIT speedup.
     *
     * Returns a `Result<f64, JsValue>`: the `Err` path bubbles step
     * errors so the bench harness can show a useful message.
     * @param {number} cycles
     * @returns {number}
     */
    bench_jit(cycles) {
        const ret = wasm.wasmsimulator_bench_jit(this.__wbg_ptr, cycles);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0];
    }
    /**
     * Non-consuming universal bus trace snapshot for logic analyzers.
     * Returns the shared bus event log (seq, bus, payload) grouped by bus type.
     * @returns {any}
     */
    bus_trace_snapshot() {
        const ret = wasm.wasmsimulator_bus_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * The call stack of the debugged core, innermost first, at most
     * `max_frames` (and never more than 32) frames:
     * `[{ index, pc, function, file, line, column, inlined }]`.
     *
     * A real function's activation shows as its inline chain: inlined calls
     * (`inlined: true`) first, then the function they were inlined into.
     * Frame 0 is the frame `source_location` shows (the inline frame the last
     * source step stopped in). A caller's `pc` is its return address and its
     * `line` the line of the call. Callers are unwound with the ELF's call
     * frame information on Cortex-M/A and RISC-V; Xtensa and AVR show frame 0
     * only. `function`, `file`, `line` and `column` may be null.
     * @param {number} max_frames
     * @returns {any}
     */
    call_stack(max_frames) {
        const ret = wasm.wasmsimulator_call_stack(this.__wbg_ptr, max_frames);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Attach a CAN bridge to controller `controller` (e.g. `"fdcan1"`).
     * `config_json` takes the keys of a `can-bridge` in a system manifest:
     * `pause_mode` (`drop` | `capture` | `replay`), `capture_capacity`,
     * `overflow` (`drop_newest` | `drop_oldest`), `bitrate`, `faults`
     * (the fault-injection schema), `recording` (JSON-lines or candump
     * text; replay mode) and `replay_start` (`boot`, or `attach` to start the
     * recording at the current cycle).
     * @param {string} id
     * @param {string} controller
     * @param {string} config_json
     */
    can_bridge_attach(id, controller, config_json) {
        const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(controller, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ptr2 = passStringToWasm0(config_json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len2 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_can_bridge_attach(this.__wbg_ptr, ptr0, len0, ptr1, len1, ptr2, len2);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Remove bridge `id`; its controller is reached directly again.
     * @param {string} id
     */
    can_bridge_detach(id) {
        const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_can_bridge_detach(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Ids and controllers of the attached bridges, as JSON
     * `[{"id","controller","pause_mode","paused"}]`.
     * @returns {string}
     */
    can_bridge_list() {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmsimulator_can_bridge_list(this.__wbg_ptr);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * A live frame from outside the simulation for bridge `id`. `frame_json`
     * is `{"id": 2016 | "0x7E0", "data": "0322f190", "ext", "fd", "brs"}`;
     * `host_time_ms` is the wall-clock time it arrived (recorded only).
     * Returns `"queued"`, `"captured"` or `"dropped"`.
     * @param {string} id
     * @param {string} frame_json
     * @param {number | null} [host_time_ms]
     * @returns {string}
     */
    can_bridge_offer(id, frame_json, host_time_ms) {
        let deferred4_0;
        let deferred4_1;
        try {
            const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ptr1 = passStringToWasm0(frame_json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_can_bridge_offer(this.__wbg_ptr, ptr0, len0, ptr1, len1, !isLikeNone(host_time_ms), isLikeNone(host_time_ms) ? 0 : host_time_ms);
            var ptr3 = ret[0];
            var len3 = ret[1];
            if (ret[3]) {
                ptr3 = 0; len3 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred4_0 = ptr3;
            deferred4_1 = len3;
            return getStringFromWasm0(ptr3, len3);
        } finally {
            wasm.__wbindgen_free(deferred4_0, deferred4_1, 1);
        }
    }
    /**
     * Everything the bridge recorded, as `"jsonl"` (the replay format) or
     * `"candump"` text.
     * @param {string} id
     * @param {string} format
     * @returns {string}
     */
    can_bridge_recording(id, format) {
        let deferred4_0;
        let deferred4_1;
        try {
            const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ptr1 = passStringToWasm0(format, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_can_bridge_recording(this.__wbg_ptr, ptr0, len0, ptr1, len1);
            var ptr3 = ret[0];
            var len3 = ret[1];
            if (ret[3]) {
                ptr3 = 0; len3 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred4_0 = ptr3;
            deferred4_1 = len3;
            return getStringFromWasm0(ptr3, len3);
        } finally {
            wasm.__wbindgen_free(deferred4_0, deferred4_1, 1);
        }
    }
    /**
     * The bridge's report as JSON: delivered/dropped frames (every dropped
     * frame, exactly), capture queue, replay verdict, faults fired, and the
     * failure timeline (frames, faults, console lines, tester progress on one
     * cycle axis). The same block `labwired test` writes into `result.json`.
     * @param {string} id
     * @returns {string}
     */
    can_bridge_report(id) {
        let deferred3_0;
        let deferred3_1;
        try {
            const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_can_bridge_report(this.__wbg_ptr, ptr0, len0);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * Tell every bridge the run stopped (`true`: paused, halted at a
     * breakpoint) or resumed (`false`). What happens to live frames while
     * paused is each bridge's `pause_mode`.
     * @param {boolean} paused
     */
    can_bridge_set_paused(paused) {
        const ret = wasm.wasmsimulator_can_bridge_set_paused(this.__wbg_ptr, paused);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Names of the chip's CAN controllers (FDCAN, bxCAN) as JSON
     * `["fdcan1"]`; `[]` when it has none.
     * @returns {string}
     */
    can_controllers() {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmsimulator_can_controllers(this.__wbg_ptr);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * Remove a held level set by [`Self::set_adc_channel_millivolts`],
     * returning the channel to the engine's modeled internal source.
     * @param {string} peripheral_name
     * @param {number} channel
     */
    clear_adc_channel(peripheral_name, channel) {
        const ptr0 = passStringToWasm0(peripheral_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_clear_adc_channel(this.__wbg_ptr, ptr0, len0, channel);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Why the Serial pane can be empty while the firmware is talking.
     *
     * An ESP32-C3/S3 has two consoles and a board's USB socket is soldered to
     * exactly one of them, so the twin taps one — the same one the developer's
     * cable is on. If the firmware prints to the OTHER one, a real board shows
     * nothing and the twin faithfully shows nothing too. That is correct, and
     * completely baffling, so this says what happened.
     *
     * `null` when nothing was lost. See `labwired_core::console`.
     * @returns {string | undefined}
     */
    console_mismatch() {
        const ret = wasm.wasmsimulator_console_mismatch(this.__wbg_ptr);
        let v1;
        if (ret[0] !== 0) {
            v1 = getStringFromWasm0(ret[0], ret[1]).slice();
            wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        }
        return v1;
    }
    /**
     * @returns {boolean}
     */
    coverage_enabled() {
        const ret = wasm.wasmsimulator_coverage_enabled(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * The firmware coverage report as JSON: per-file lines, per-function
     * summary, branches, percentages, the LCOV text under `lcov`, and
     * `method`: `"live"` (recording since `enable_coverage`) or `"replay"`
     * (measured from power-on by replaying the run on a fresh copy).
     * @returns {string}
     */
    coverage_report() {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmsimulator_coverage_report(this.__wbg_ptr);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * Decode the instruction at `addr` (not only at the PC), in the engine's
     * own debug form -- the same text `get_disassembly` gives for the PC.
     * @param {number} addr
     * @returns {string}
     */
    disassemble_at(addr) {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmsimulator_disassemble_at(this.__wbg_ptr, addr);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * Drain ITM stimulus port 0 bytes accumulated since the last call.
     * Empty when the machine has no ITM or firmware has not emitted.
     *
     * Errors when this simulator has no machine. An empty buffer is "the
     * machine produced no ITM bytes", which a missing machine is not.
     * @returns {Uint8Array}
     */
    drain_itm_output() {
        const ret = wasm.wasmsimulator_drain_itm_output(this.__wbg_ptr);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Drain SEGGER RTT output bytes accumulated since the last call. Empty for
     * firmware that does not link the vendor RTT library (nothing is attached).
     *
     * Errors when this simulator has no machine. An empty buffer is "the
     * machine produced no RTT bytes", which a missing machine is not.
     * @returns {Uint8Array}
     */
    drain_rtt_output() {
        const ret = wasm.wasmsimulator_drain_rtt_output(this.__wbg_ptr);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Drain ARM semihosting output captured since the last call. Empty when
     * firmware has not executed `bkpt #0xAB`. Not mixed into UART, RTT, or ITM.
     * @returns {Uint8Array}
     */
    drain_semihosting_output() {
        const ret = wasm.wasmsimulator_drain_semihosting_output(this.__wbg_ptr);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Drain UART TX output bytes accumulated since the last call.
     * @returns {Uint8Array}
     */
    drain_uart_output() {
        const ret = wasm.wasmsimulator_drain_uart_output(this.__wbg_ptr);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Start recording which instructions execute. The browser JIT is turned
     * off while recording: compiled blocks do not report each instruction.
     */
    enable_coverage() {
        const ret = wasm.wasmsimulator_enable_coverage(this.__wbg_ptr);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Run a lockstep fault experiment and return the report as JSON (see
     * `labwired_core::vfi::FaultReport`). `plan_json` is
     * `{"until_cycle": N, "faults": [{"at_cycle": C, "kind": ..., ...}]}`.
     *
     * Two fresh copies of this machine are built and brought to the same
     * point: the current one, or the start of the run when `from_boot` is
     * true. This simulator is not changed.
     * @param {string} plan_json
     * @param {boolean} from_boot
     * @returns {string}
     */
    fault_experiment(plan_json, from_boot) {
        let deferred3_0;
        let deferred3_1;
        try {
            const ptr0 = passStringToWasm0(plan_json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_fault_experiment(this.__wbg_ptr, ptr0, len0, from_boot);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * The Cortex-M fault verdict as JSON, or `undefined` when nothing
     * faulted: why and where the firmware faulted, in one sentence
     * (`summary`), plus the decoded HFSR/CFSR/BFAR/MMFAR, the stacked frame
     * and the symbolized PC and caller. See
     * `labwired_core::fault_verdict::FaultVerdict`. Non-draining; safe to poll.
     * @returns {string | undefined}
     */
    fault_verdict() {
        const ret = wasm.wasmsimulator_fault_verdict(this.__wbg_ptr);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        let v1;
        if (ret[0] !== 0) {
            v1 = getStringFromWasm0(ret[0], ret[1]).slice();
            wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        }
        return v1;
    }
    /**
     * Non-consuming FDCAN frame trace snapshot for CAN/UDS instruments.
     * @returns {any}
     */
    fdcan_trace_snapshot() {
        const ret = wasm.wasmsimulator_fdcan_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * Push bytes into RTT down-channel 0, the buffer `SEGGER_RTT_GetKey` and
     * `SEGGER_RTT_Read` drain. No-op success when the machine has no RTT model
     * is the wrong signal — callers learn that from `rtt_attached`.
     * @param {Uint8Array} data
     */
    feed_rtt_input(data) {
        const ptr0 = passArray8ToWasm0(data, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_feed_rtt_input(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Push bytes into all UART RX buffers (bidirectional serial input).
     * @param {Uint8Array} data
     */
    feed_uart_input(data) {
        const ptr0 = passArray8ToWasm0(data, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        wasm.wasmsimulator_feed_uart_input(this.__wbg_ptr, ptr0, len0);
    }
    /**
     * Deliver bytes only to the named UART and re-arm its scheduler wake.
     *
     * Returns the accepted byte count. A missing machine, unknown UART or
     * failed RX queue returns an error; input is never redirected to another
     * port. Use the peripheral ID from the system/chip descriptor.
     * @param {string} peripheral_name
     * @param {Uint8Array} data
     * @returns {number}
     */
    feed_uart_input_named(peripheral_name, data) {
        const ptr0 = passStringToWasm0(peripheral_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passArray8ToWasm0(data, wasm.__wbindgen_malloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_feed_uart_input_named(this.__wbg_ptr, ptr0, len0, ptr1, len1);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Everything this machine failed to model so far, as a flat list of
     * [`labwired_core::fidelity::FidelityGap`].
     *
     * Phases 3.1-3.3 built the census — `record_undecoded` / `record_unmapped`
     * on the silent paths, `to_gaps()` to flatten it — and then only the CLI
     * ever read it. `to_gaps` had exactly three callers, all under `crates/cli`,
     * and the word "fidelity" appeared in this crate only inside comments. So
     * the engine knew precisely which instructions it had skipped and which
     * addresses nothing claimed, and the browser — where nearly every user
     * actually runs a lab — was never told. An undecoded instruction is a
     * silent no-op that leaves registers stale; it looks exactly like firmware
     * running correctly.
     *
     * Non-draining ON PURPOSE: this reads `report()`, not `take()`. A UI polls,
     * and `take()` would hand the gaps to whichever poll happened to land first
     * and show nothing to the next — a warning that blinks out is worse than no
     * warning. Scoping is done by resetting at construction instead, so the
     * list always means "gaps for the machine you are looking at".
     * @returns {any}
     */
    fidelity_gaps() {
        const ret = wasm.wasmsimulator_fidelity_gaps(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The variables and parameters of call-stack frame `frame_index` (as
     * `call_stack` numbers them), with typed values:
     * `[{ name, type, value, available, address, children: [...] }]`.
     *
     * `value` is the display text (`42`, `true`, `0x20000010`,
     * `Game { paddle_x: 42, … }`, `[u8; 504]`, `Some(3)`); `available` is
     * false when the value is optimized out at this pc or a register or
     * memory it needs cannot be read (then `value` says which). `address`
     * is where the value lives in memory, or null. Structs, unions, arrays
     * (first 64 elements), Rust enums and pointers to aggregates have
     * `children` of the same shape, at most 4 levels deep. Throws for a
     * frame that does not exist.
     * @param {number} frame_index
     * @returns {any}
     */
    frame_variables(frame_index) {
        const ret = wasm.wasmsimulator_frame_variables(this.__wbg_ptr, frame_index);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Browser-side GDB stub entry point.
     *
     * Disabled in this build: the GdbStub `Target` impl in `labwired-gdbstub`
     * is concrete on `LabwiredTarget<CortexM>` / `LabwiredTarget<RiscV>`,
     * but `WasmSimulator` now holds `Machine<Box<dyn Cpu>>` so the bound
     * isn't satisfied. The playground has no JS caller for this method,
     * so we return an empty packet rather than refactor `labwired-gdbstub`
     * to be dyn-aware. Track via the v0.6 plan.
     * @param {Uint8Array} _packet
     * @returns {Uint8Array}
     */
    gdb_process_packet(_packet) {
        const ptr0 = passArray8ToWasm0(_packet, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_gdb_process_packet(this.__wbg_ptr, ptr0, len0);
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Live actuator state for canvas animation.
     *
     * Returns servo states, STEP/DIR steppers, then configured motor-plant states.
     * - hobby servos (`kind: "servo"`) export shaft `angle` in degrees
     * - STEP/DIR steppers (`kind` = YAML type, e.g. `nema17` / `a4988`) export
     *   shaft `angle` in degrees plus signed `steps`
     * - `dc-motor` exports scalar `current_a`
     * - `bldc-motor` exports DC-bus `current_a`, `phase_currents_a`, and
     *   `commutation_sector`
     *
     * Servo `active`, `angle` and `pulse_us` retain the last modeled command.
     * `source_status` is a snapshot of modeled source configuration, not
     * freshness, servo power, physical output or a reset-fresh observation.
     * Ids match the diagram part id / external_devices id so the UI maps
     * straight onto `boardIoStates[partId]`.
     * @returns {any}
     */
    get_actuator_states() {
        const ret = wasm.wasmsimulator_get_actuator_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * Read back NTC thermistor state from `external_devices` + live analog kit.
     *
     * Returns `[{ id, kind: "ntc-thermistor", divider_mv, adc_count }]`.
     * Identity is the external_devices id (no board_io twin).
     * @returns {any}
     */
    get_adc_device_states() {
        const ret = wasm.wasmsimulator_get_adc_device_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * Returns analog state for ADC and PWM board_io bindings.
     * @returns {any}
     */
    get_board_io_analog_states() {
        const ret = wasm.wasmsimulator_get_board_io_analog_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * Returns the board_io configuration as a JSON array.
     * Each entry: { id, kind, peripheral, pin, signal, active_high }
     * @returns {any}
     */
    get_board_io_config() {
        const ret = wasm.wasmsimulator_get_board_io_config(this.__wbg_ptr);
        return ret;
    }
    /**
     * Returns the current state of all board_io bindings as a JSON array.
     * Each entry: { id, active }
     * Uses peripheral snapshot() to read ODR regardless of register layout.
     * @returns {any}
     */
    get_board_io_states() {
        const ret = wasm.wasmsimulator_get_board_io_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {string}
     */
    get_disassembly() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsimulator_get_disassembly(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * **THE door.** Whatever the display called `device_id` is showing — any
     * model, any transport, any chip, however it was bound.
     *
     * Returns `null` when there is no such display, otherwise:
     *
     * ```text
     * { id, kind, format, width, height, bytes, text, meta }
     * ```
     *
     * * `kind` — `"framebuffer"` (packed pixels) or `"text_display"` (decoded
     *   characters). Between them, every way this engine has of saying "a human
     *   can see this".
     * * `format` — how `bytes` are packed (`"rgb565_be"`, `"ssd1306_page"`,
     *   `"epaper_tricolor_1bpp_planes"`, …).
     * * `width` / `height` — the panel's own geometry, in pixels (or in
     *   characters, for a text display), `null` when the model reports none.
     * * `bytes` — the payload, present only when `include_bytes`.
     * * `text` — the decoded string, for a `text_display`.
     * * `meta` — everything else the model chose to report (ink counts, power
     *   state, `generation`, `refresh_generation`), so a caller can poll for
     *   change without pulling pixels.
     *
     * **Geometry and packing are DATA, deliberately.** The accessors this
     * replaces carried them as prose in a doc comment — "153,600 bytes =
     * 240×320×2, big-endian RGB565" — which is lore that lives in the reader.
     * A model that arrives tomorrow cannot put anything into last year's doc
     * comment, so every new panel needed a new accessor AND a new renderer
     * branch before it could show a single pixel. Here a caller can paint a
     * display it has never heard of, and a new model is renderable the day its
     * own `artifacts()` lands.
     *
     * `generation` is stringified: it is a 64-bit FNV hash, and a `u64` past
     * 2^53 makes `serde_wasm_bindgen` refuse the WHOLE payload. That is not
     * hypothetical — it is why [`Self::inspect`] currently returns `null` for
     * every machine that has a device with an artifact.
     * @param {string} device_id
     * @param {boolean} include_bytes
     * @returns {any}
     */
    get_display(device_id, include_bytes) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_display(this.__wbg_ptr, ptr0, len0, include_bytes);
        return ret;
    }
    /**
     * Read back live I²C sensor samples for the canvas.
     *
     * Identity comes from `external_devices:` (the one home for bus parts) —
     * **not** a second `board_io` twin. Returns
     * `[{ id, kind: "adxl345", x, y, z }, ...]` or
     * `[{ id, kind: "mpu6050", ax, ay, az, gx, gy, gz }, ...]`.
     *
     * BME280 is intentionally OMITTED: its model has no register-backed
     * engineering-unit sample API for the panel (SimInput is the stimulus path).
     * @returns {any}
     */
    get_i2c_sensor_states() {
        const ret = wasm.wasmsimulator_get_i2c_sensor_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * Return the ILI9341 RGB565 framebuffer for the device identified by `device_id`.
     *
     * Returns a 153,600-byte `Uint8Array` (240×320 pixels × 2 bytes, row-major, big-endian RGB565).
     * Returns a JS error if the device is not found.
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_ili9341_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_ili9341_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Read the IO-Link master peer's live state. The optional evaluation phase
     * and error are read-only diagnostics, null for legacy peers.
     * Returns `null` if no master is wired.
     * @returns {any}
     */
    get_iolink_master_state() {
        const ret = wasm.wasmsimulator_get_iolink_master_state(this.__wbg_ptr);
        return ret;
    }
    /**
     * Return the visible text of the LCD1602 identified by `device_id`.
     *
     * Returns exactly 32 characters — row 0 then row 1, no separator — so the
     * caller slices `[0..16]` and `[16..32]`. A display the firmware has not
     * switched on reads as all spaces, matching the dark panel.
     * Returns a JS error if the device is not found.
     *
     * The panel's evidence carries this text in `meta.text`, so this reads the
     * same string the CLI and `inspect` print rather than a second decode.
     * The default address matches the kit's own: 0x27, the PCF8574T backpack.
     * @param {string} device_id
     * @returns {string}
     */
    get_lcd1602_text(device_id) {
        let deferred3_0;
        let deferred3_1;
        try {
            const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_get_lcd1602_text(this.__wbg_ptr, ptr0, len0);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * Return the MAX7219 LED-matrix framebuffer for the device identified by `device_id`.
     *
     * Returns an 8-byte `Uint8Array`: one byte per matrix row, row 0 first,
     * bit 7 = the leftmost column (`SEG A` on the driver). The bytes already
     * account for shutdown (all zero) and display test (all `0xFF`), so the
     * renderer can paint them directly.
     * Returns a JS error if the device is not found.
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_led_matrix_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_led_matrix_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Legacy LED state query (hardcoded GPIOB pin 5 for backward compat).
     * @returns {boolean}
     */
    get_led_state() {
        const ret = wasm.wasmsimulator_get_led_state(this.__wbg_ptr);
        return ret !== 0;
    }
    /**
     * The pc of the core a debugger follows: core 0, or the second core of a
     * dual-core chip after a breakpoint stopped it (see
     * [`source_debug::focused_cpu`]).
     * @returns {number}
     */
    get_pc() {
        const ret = wasm.wasmsimulator_get_pc(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Return the PCD8544 (Nokia 5110) framebuffer for the device identified
     * by `device_id`.
     *
     * Returns 504 bytes: 84 columns × 6 banks, bank-major. Pixel (x, y) is
     * bit `(y % 8)` of byte `[(y / 8) * 84 + x]` (1 = on/dark).
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_pcd8544_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_pcd8544_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * List all peripherals: [{ name, base_address }]
     * @returns {any}
     */
    get_peripheral_list() {
        const ret = wasm.wasmsimulator_get_peripheral_list(this.__wbg_ptr);
        return ret;
    }
    /**
     * Get a peripheral's full state snapshot as JSON.
     * @param {string} name
     * @returns {any}
     */
    get_peripheral_snapshot(name) {
        const ptr0 = passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_peripheral_snapshot(this.__wbg_ptr, ptr0, len0);
        return ret;
    }
    /**
     * A register of the core `get_pc` reads.
     * @param {number} id
     * @returns {number}
     */
    get_register(id) {
        const ret = wasm.wasmsimulator_get_register(this.__wbg_ptr, id);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * @returns {any}
     */
    get_register_names() {
        const ret = wasm.wasmsimulator_get_register_names(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Return the character shown on the direct-drive 7-segment digit
     * identified by `device_id`.
     *
     * Returns the single decoded character, with `'.'`
     * appended when the decimal point is lit — so a blank digit is `" "`,
     * a lit `0` is `"0"`, and `0` with the dp is `"0."`. An unrecognised
     * segment pattern decodes to `"?"` rather than silently blanking.
     *
     * The lit-segment mask is polarity-normalised by the model (COM low =
     * common cathode, COM high = common anode), so the text reads the same
     * either way it is wired. Like the TM1637 above, this now reads the
     * artifact rather than a typed bus field.
     * @param {string} device_id
     * @returns {string}
     */
    get_seven_segment_text(device_id) {
        let deferred3_0;
        let deferred3_1;
        try {
            const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_get_seven_segment_text(this.__wbg_ptr, ptr0, len0);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * Return the SH1107 GDDRAM framebuffer for the device identified by `device_id`.
     *
     * Returns a 2048-byte `Uint8Array` (128 columns × 16 pages, page-major) — the
     * same bit layout as the SSD1306, just twice as tall (128 rows).
     * Returns a JS error if the device is not found.
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_sh1107_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_sh1107_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Read the 74HC165's live input byte (bit `i` = channel `i`), or `-1` if
     * no shifter is wired. Lets the UI reflect the device's real state rather
     * than tracking it in JS.
     * @returns {number}
     */
    get_sn74hc165_inputs() {
        const ret = wasm.wasmsimulator_get_sn74hc165_inputs(this.__wbg_ptr);
        return ret;
    }
    /**
     * Read back the current state of each SPI sensor declared in `board_io`.
     * Returns `[{ id, kind: "max31855", tc_c, internal_c }, ...]`.
     * @returns {any}
     */
    get_spi_device_states() {
        const ret = wasm.wasmsimulator_get_spi_device_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * Return the SSD1306 GDDRAM framebuffer for the device identified by `device_id`.
     *
     * Returns a 1024-byte `Uint8Array` (128 columns × 8 pages, page-major) for
     * the 128×64 panel. Both SSD1306 form factors surface through this one
     * accessor: the framebuffer length (1024 vs 512 bytes) is what tells the
     * renderer the panel height, so one readback path serves both.
     * Returns a JS error if the device is not found.
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_ssd1306_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_ssd1306_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Return the SSD1680 tri-color e-paper framebuffer for the device identified by `device_id`.
     *
     * Returns a 9472-byte `Uint8Array`: first 4736 bytes are the black plane
     * (1 = white / 0 = black), next 4736 bytes are the red plane on the wire
     * (1 = no-red / 0 = red — see GxEPD2 inversion in writeImage). Row-major,
     * 128 pixels wide / 296 tall native, MSB-first packing within each byte.
     * Returns a JS error if the device is not found.
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_ssd1680_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_ssd1680_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Cheap accessor returning just the SSD1680 refresh-generation counter.
     * UI uses this to decide whether to re-fetch the (larger) framebuffer.
     * @param {string} device_id
     * @returns {number}
     */
    get_ssd1680_refresh_generation(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_ssd1680_refresh_generation(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Return the decoded four-character text currently latched into a TM1637
     * 4-digit display.
     *
     * Read through the SAME artifact door every other panel uses. It used to
     * reach into `machine.bus.tm1637` — a typed field that existed only
     * because a GPIO-bound display had nowhere else to live. The display is
     * now one `BusResidentDevice` among many and reports through
     * `BusResidentDevice::evidence`, so this accessor cannot tell it apart
     * from an OLED except by the `format` it filters on.
     * @param {string} device_id
     * @returns {string}
     */
    get_tm1637_text(device_id) {
        let deferred3_0;
        let deferred3_1;
        try {
            const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_get_tm1637_text(this.__wbg_ptr, ptr0, len0);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * Read back the current state of all NEO-6M GPS devices declared in `board_io`.
     * Returns `[{ id, kind: "neo6m-gps", lat, lon, has_fix }]`.
     * @returns {any}
     */
    get_uart_device_states() {
        const ret = wasm.wasmsimulator_get_uart_device_states(this.__wbg_ptr);
        return ret;
    }
    /**
     * Same shape as [`Self::get_ssd1680_framebuffer`], kept as a separate name
     * because the UI selects an accessor by the diagram part's type.
     *
     * It resolves to the SAME query: a tri-color e-paper on the bound
     * controller, whichever of the two controller models the builder attached.
     * That is not a shortcut — it is the honest reading of a `board_io`
     * `device_type:` that says `ssd1680_tricolor_290` for a panel the ESP32
     * builder attaches as a `Uc8151dTricolor290`. This accessor already ignored
     * the declared type for exactly that reason; now its twin does too, so a
     * lab can no longer render blank purely because the UI picked the accessor
     * named after the type string rather than the one named after the model.
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_uc8151d_framebuffer(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_uc8151d_framebuffer(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * Cheap accessor returning just the UC8151D refresh-generation counter.
     * @param {string} device_id
     * @returns {number}
     */
    get_uc8151d_refresh_generation(device_id) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_get_uc8151d_refresh_generation(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Cumulative cycles advanced by idle fast-forward (WFI skip), not
     * interpreted. Browser `?perf=1` uses this to prove FF is firing; stays
     * 0 when FF is off or firmware never parks in a skippable idle.
     * @returns {bigint}
     */
    idle_fast_forward_cycles_skipped() {
        const ret = wasm.wasmsimulator_idle_fast_forward_cycles_skipped(this.__wbg_ptr);
        return BigInt.asUintN(64, ret);
    }
    /**
     * Universal inspect: decoded register + artifact state for one peripheral
     * (`name = Some`) or all (`name = None`). Serializes a
     * [`labwired_core::inspect::MachineInspect`]. In summary mode
     * (`include_bytes = false`) large artifact payloads (framebuffers) are
     * omitted; each artifact still carries `meta.generation` so the UI can skip
     * re-pulling unchanged buffers. Snapshot semantics — reads the current
     * paused machine state, side-effect-free.
     *
     * Two fields of that payload changed shape and the UI must handle both:
     * `devices` (new) lists the external I²C/SPI devices the manifest placed,
     * which are owned by their controller and so never appeared under
     * `peripherals`; and `peripherals[].registers[].value` is now `null`
     * rather than `0` when the model did not answer the probe, so an
     * unmodeled-but-named register must render as unknown, not as zero.
     * @param {string | null | undefined} name
     * @param {boolean} include_bytes
     * @returns {any}
     */
    inspect(name, include_bytes) {
        var ptr0 = isLikeNone(name) ? 0 : passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        var len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_inspect(this.__wbg_ptr, ptr0, len0, include_bytes);
        return ret;
    }
    /**
     * Arduino-ESP32 boot bootstrap (symbol-table autodiscovery).
     *
     * Mirrors the CLI's `arduino-esp32` snapshot-capture profile —
     * resolves Arduino-ESP32 thunk PCs from the ELF symbol table instead
     * of hand-curated hardcoded addresses. Works for any GxEPD2-class
     * sketch (labwired-ereader, future user sketches) without needing
     * to know its binary layout in advance.
     *
     * Caller must pass the same ELF bytes that were loaded via
     * `load_firmware`. The thunks are installed as flash patches over
     * the resolved PCs; calling this without the matching ELF is a no-op
     * (symbols don't resolve → no thunks installed).
     *
     * Attaches no peripheral of its own: the panel (model, CS, DC) comes
     * from the board manifest via `attach_esp32_external_devices` at system
     * load — see the body below. This method used to hardcode a panel here;
     * that behaviour is gone, and the manifest is the single source of truth.
     *
     * For the record, because the deleted comment had it backwards:
     * `GxEPD2_290_C90c` is an **SSD1680** controller (0x12 SWRESET, 0x11 data
     * entry, 0x24/0x26 RAM, 0x22+0x20 update), not UC8151D. UC8151D
     * (`0x00 PSR` / `0x04 PON` / `0x10 DTM1` / `0x12 DRF` / `0x13 DTM2`) is
     * what `GxEPD2_290_Z13c` emits. `peripherals::kit::registry::TYPE_ALIASES`
     * owns that mapping.
     * @param {Uint8Array} elf_bytes
     */
    install_arduino_esp32_quirks(elf_bytes) {
        const ptr0 = passArray8ToWasm0(elf_bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_install_arduino_esp32_quirks(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Clear the IO-Link master's trace ring.
     */
    iolink_trace_clear() {
        wasm.wasmsimulator_iolink_trace_clear(this.__wbg_ptr);
    }
    /**
     * Snapshot of the IO-Link master's captured transactions (oldest→newest),
     * for the IO-Link Analyzer instrument. Empty array if no master is wired.
     * @returns {any}
     */
    iolink_trace_snapshot() {
        const ret = wasm.wasmsimulator_iolink_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * True once firmware has written ITM_TCR, ITM_TER, or any stimulus port.
     * There is no ELF symbol. A Cortex-M image that never touches ITM stays
     * false, and a non-Cortex-M machine stays false.
     *
     * Errors when this simulator has no machine.
     * @returns {boolean}
     */
    itm_attached() {
        const ret = wasm.wasmsimulator_itm_attached(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Number of compiled blocks the browser JIT has installed.
     *
     * `jit_hits()` proves a compiled block RAN; this proves one was BUILT.
     * An end-to-end gate needs both: a run where the emit walk refuses
     * every block has zero hits too, so a hit-only check cannot tell "the
     * JIT is off" from "the JIT compiled nothing". Zero after a batch that
     * went through the opt-in path fails the gate.
     *
     * Returns `Result` even though the answer is always available: every
     * other accessor at this boundary hands back `Result<T, JsValue>` so a
     * caller can never read a fabricated value as data (see
     * `error_boundary_ratchet.rs`).
     * @returns {bigint}
     */
    jit_compiled_blocks() {
        const ret = wasm.wasmsimulator_jit_compiled_blocks(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return BigInt.asUintN(64, ret[0]);
    }
    /**
     * Total number of times the browser JIT has dispatched a
     * compiled block. Useful for confirming the JIT path actually
     * fired during a benchmark.
     * @returns {bigint}
     */
    jit_hits() {
        const ret = wasm.wasmsimulator_jit_hits(this.__wbg_ptr);
        return BigInt.asUintN(64, ret);
    }
    /**
     * Total number of JIT refusals (host bus errors, JS-side
     * dispatch failures). Surfaced for the bench harness so it can
     * distinguish "JIT was tried and rejected" from "JIT was never
     * hit because PC never reached the block".
     * @returns {bigint}
     */
    jit_refusals() {
        const ret = wasm.wasmsimulator_jit_refusals(this.__wbg_ptr);
        return BigInt.asUintN(64, ret);
    }
    /**
     * Loop-trace iterations the browser JIT retired inside traced runs.
     *
     * Zero after a batch through the loop-trace path means either no trace
     * was compiled or every trace dispatch retired nothing; non-zero is the
     * non-vacuity proof for the browser-layer gate and the bench.
     * @returns {bigint}
     */
    jit_trace_iters() {
        const ret = wasm.wasmsimulator_jit_trace_iters(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return BigInt.asUintN(64, ret[0]);
    }
    /**
     * Number of loop-trace dispatches (one per entry of a counted-loop
     * trace), the companion of [`Self::jit_trace_iters`].
     * @returns {bigint}
     */
    jit_trace_runs() {
        const ret = wasm.wasmsimulator_jit_trace_runs(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return BigInt.asUintN(64, ret[0]);
    }
    /**
     * Discover the drivable input channels on the running machine, as JSON:
     * `[{"peripheral":"imu","key":"ax","label":"Accel X","unit":"g","min":-16,"max":16}, …]`.
     * `peripheral` is the system.yaml external-device id when stamped (the
     * same name `set_input`'s component selector accepts), else the owning
     * peripheral's bus name. The "what can I drive?" query an agent calls
     * before `set_input`.
     * @returns {any}
     */
    list_inputs() {
        const ret = wasm.wasmsimulator_list_inputs(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Bounded live numeric observations on their own per-machine epoch and
     * cursor. Plain JS numbers, not BigInt. max_points trims only this read;
     * historical analog_series and the co-simulation cursor are unchanged.
     * @param {number} cursor
     * @param {number} max_points
     * @returns {any}
     */
    live_numeric_capture(cursor, max_points) {
        const ret = wasm.wasmsimulator_live_numeric_capture(this.__wbg_ptr, cursor, max_points);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Variables and parameters of the function containing `pc`:
     * `[{ name, kind, register?, offset?, address?, expr?, value }]`.
     *
     * Only single-expression DWARF locations are decoded. `kind: "register"`
     * carries the current register value in `value`; `"frame_offset"` (an
     * offset from the DWARF frame base) and the rest are reported without a
     * value. Location lists — what optimised builds emit for most locals —
     * are not decoded, so such variables are absent.
     * @param {number} pc
     * @returns {any}
     */
    locals(pc) {
        const ret = wasm.wasmsimulator_locals(this.__wbg_ptr, pc);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The whole probeable WIRE surface of this chip: every peripheral that
     * publishes wire lines, with the exact line names it publishes.
     *
     * Returns `[{ peripheral, lines: ["TX", "RX"] }]`, bus order.
     *
     * This exists so a probe menu is built from engine truth instead of a
     * second, hand-maintained copy of the vocabulary. The spellings are not
     * uniform and are not derivable from the protocol — generic STM32 SPI
     * publishes `SCK/MOSI/MISO` and NO chip select, RP2040 SPI spells it
     * `CSn`, ESP GPSPI spells it `CS`. Anything that guesses `"CS"` offers a
     * lane that cannot resolve on two of those three.
     * @returns {any}
     */
    logic_wire_surface() {
        const ret = wasm.wasmsimulator_logic_wire_surface(this.__wbg_ptr);
        return ret;
    }
    /**
     * Legacy constructor: hardcoded STM32F107 Cortex-M3 with 128KB flash + 20KB RAM.
     * Kept for backward compatibility with the existing landing page sandbox.
     * @param {Uint8Array} firmware
     */
    constructor(firmware) {
        const ptr0 = passArray8ToWasm0(firmware, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_new(ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        this.__wbg_ptr = ret[0];
        WasmSimulatorFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * Config-driven constructor: initialize from system YAML, chip YAML, and firmware ELF.
     *
     * Dispatches on `chip.arch`:
     *   * `Arm` → `SystemBus::from_config` + `configure_cortex_m` (existing path).
     *   * `Xtensa` → `configure_xtensa_esp32` + inline external-device attach.
     *     ESP32 chip YAMLs declare RAM banks (IRAM/DRAM/flash XIP/ROM) via
     *     `peripherals: [{type: ram, ...}]`, which `from_config` doesn't
     *     understand — it'd stub them out and break instruction fetch. So
     *     ESP32 takes the dedicated path that explicitly registers those
     *     banks before attaching SPI / I²C external devices.
     * @param {string} system_yaml
     * @param {string} chip_yaml
     * @param {Uint8Array} firmware
     * @param {any} blobs
     * @returns {WasmSimulator}
     */
    static new_from_config(system_yaml, chip_yaml, firmware, blobs) {
        const ptr0 = passStringToWasm0(system_yaml, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(chip_yaml, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ptr2 = passArray8ToWasm0(firmware, wasm.__wbindgen_malloc);
        const len2 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_new_from_config(ptr0, len0, ptr1, len1, ptr2, len2, blobs);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return WasmSimulator.__wrap(ret[0]);
    }
    /**
     * Construct a browser simulator with a host-owned persistent ngspice solver.
     * @param {string} system_yaml
     * @param {string} chip_yaml
     * @param {Uint8Array} firmware
     * @param {any} blobs
     * @param {any} callback
     * @returns {WasmSimulator}
     */
    static new_from_config_with_ngspice_callback(system_yaml, chip_yaml, firmware, blobs, callback) {
        const ptr0 = passStringToWasm0(system_yaml, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(chip_yaml, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ptr2 = passArray8ToWasm0(firmware, wasm.__wbindgen_malloc);
        const len2 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_new_from_config_with_ngspice_callback(ptr0, len0, ptr1, len1, ptr2, len2, blobs, callback);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return WasmSimulator.__wrap(ret[0]);
    }
    /**
     * Raw escape hatch: read `len` bytes at absolute `addr`, side-effect-free.
     * Bytes outside any mapped region read back as `0` here (the honest
     * mapped/unmapped markers live on the core [`labwired_core::Machine::peek`]
     * / the `inspect` payload; this raw byte view is the fast path).
     *
     * Errors when there is no machine at all, rather than handing back an empty
     * buffer: a zero-length read is data-shaped, so a caller that checks
     * `.length` could not tell "nothing is mapped here" from "this simulator
     * never started". The per-byte lossy zero-fill above is unchanged.
     * @param {number} addr
     * @param {number} len
     * @returns {Uint8Array}
     */
    peek(addr, len) {
        const ret = wasm.wasmsimulator_peek(this.__wbg_ptr, addr, len);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Resolve the signal routing of GPIO pads for the logic analyzer — the
     * engine's honest answer to "what is this pad wired to?", replacing UI-side
     * pin-NAME regex guessing.
     *
     * Input: `[{ kind: "gpio", peripheral, pin }]`.
     * Output: the same refs each extended with:
     *   * `mode`: `"input" | "output" | "af" | "analog" | "unknown"` — derived
     *     from the same register truth `read_gpio_pad` reads (STM32 F1 CRL/CRH,
     *     V2 MODER+AFR, ESP32-family GPIO-matrix ENABLE + FUNCn_OUT_SEL, nRF52
     *     DIR, Kinetis PDDR). `"unknown"` where a family cannot say.
     *   * `func`: best-effort signal NAME (`"I2CEXT0_SDA"`, `"FSPICLK"`,
     *     `"AF4"`, …) or `null` — never a guess.
     * @param {any} refs
     * @returns {any}
     */
    pin_routing(refs) {
        const ret = wasm.wasmsimulator_pin_routing(this.__wbg_ptr, refs);
        return ret;
    }
    /**
     * #124 Phase 4: enable/disable the browser-side JIT fast-path. When
     * on, `step_with_esp32_aids` short-circuits any pre-fetch step
     * whose PC matches the JIT'd hot block (`0x400829cc`) into a wasm
     * call constructed via `js_sys::WebAssembly`. Off by default —
     * callers opt in from JS once they've benchmarked.
     * Wall-clock attribution for the open profiling window, as text, with this
     * chip's peripheral names resolved.
     *
     * The window is per-THREAD, not per-simulator: on a multi-chip lab every
     * chip in this worker records into it, and the report says so.
     * @returns {string}
     */
    profile_report() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsimulator_profile_report(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * The same attribution as JSON, for a HUD to render.
     * @returns {string}
     */
    profile_report_json() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.wasmsimulator_profile_report_json(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * Read logic edges captured since `cursor`. Pass `0` right after
     * [`watch_logic_signals`], then pass back the returned `cursor` to
     * acknowledge those retained edges and receive only newer ones.
     *
     * Returns `{ cursor, dropped, nowCycle, edges: [{ ch, cycle, value }] }`:
     * - `cursor` — monotonic edge sequence number to pass back next time.
     * - `dropped` — edges lost to ring-buffer overflow since the watch armed.
     * - `nowCycle` — current engine cycle, to extend flat traces to "now".
     * - `edges` — transitions oldest-first; `cycle` is the engine cycle.
     *
     * Cycles are emitted as JS numbers (f64), matching the sub-2^53 engine
     * cycle counts the playground runs to.
     * @param {number} cursor
     * @returns {any}
     */
    read_logic_edges(cursor) {
        const ret = wasm.wasmsimulator_read_logic_edges(this.__wbg_ptr, cursor);
        return ret;
    }
    /**
     * Read FOUR-STATE pad transitions captured since `cursor` — the
     * high-Z / contention companion of [`read_logic_edges`], on its own
     * cursor space.
     *
     * Returns `{ cursor, dropped, initial: [state|null per ch], edges:
     * [{ ch, cycle, state }] }` where `state` is `"0"`, `"1"`, `"z"`
     * (nothing drives the pad: an undriven input, a released open-drain
     * line) or `"x"` (the MCU output fights an external driver). A channel
     * whose pad model has not reported drive starts with `initial: null`.
     * A later explicit drive report starts its state edges at that cycle;
     * a never-known channel keeps no state edges. No initial state is guessed.
     * `read_logic_edges` is unchanged: its boolean
     * `value` is what the pad reads, so every existing consumer keeps working.
     * @param {number} cursor
     * @returns {any}
     */
    read_logic_states(cursor) {
        const ret = wasm.wasmsimulator_read_logic_states(this.__wbg_ptr, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Read `len` bytes at `addr` through the real bus read path.
     *
     * Errors rather than substituting `0` for a byte the bus refused. The old
     * `unwrap_or(0)` made a failed read byte-identical to a register or memory
     * cell that genuinely reads zero, and `null`/`0` is exactly the answer a
     * verdict cannot tell apart from data. `WasmWorld::read_memory` has always
     * returned `Result`; this brings the single-machine path to the same
     * contract.
     *
     * Note this fires read side effects (it is a bus read, not a peek) — see
     * [`labwired_core::MachineTrait::read_memory`]. Use `peek`/`inspect` for
     * anything a human is merely looking at.
     * @param {number} addr
     * @param {number} len
     * @returns {Uint8Array}
     */
    read_memory(addr, len) {
        const ret = wasm.wasmsimulator_read_memory(this.__wbg_ptr, addr, len);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * The largest `peripheral_tick_interval` this machine's bus can run at
     * without losing fidelity (see `SystemBus::max_safe_tick_interval`): a
     * batching interval when every peripheral is scheduler-driven, `1` when
     * anything non-relaxable (IO-Link master, a live legacy walk, forced
     * HC-SR04 legacy path) is present. H5 op-modeling FLASH still clamps
     * CPU quantum via `requires_cycle_accurate` but does not pin this
     * interval. The TS side calls this once at engine init and feeds the
     * answer straight into `set_peripheral_tick_interval`.
     * @returns {number}
     */
    recommended_tick_interval() {
        const ret = wasm.wasmsimulator_recommended_tick_interval(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * Whether the SEGGER RTT probe model is attached to this machine —
     * i.e. the firmware ELF resolved a `_SEGGER_RTT` symbol. The console
     * shows its RTT source only when this is true, so a lab without RTT
     * never grows a dead toggle.
     *
     * Errors when this simulator has no machine. `Ok(false)` means a loaded
     * machine has no RTT model, which a missing machine is not.
     * @returns {boolean}
     */
    rtt_attached() {
        const ret = wasm.wasmsimulator_rtt_attached(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Sample the live level of logic-analyzer channels — the per-frame
     * readout beside [`watch_logic_signals`]'s captured waveform. It takes
     * the SAME flat ref surface, both kinds:
     *
     * * `{ kind: "gpio", peripheral, pin }` — the chip pad.
     * * `{ kind: "wire", peripheral, line }` — the peripheral's own line.
     *
     * ⚠️ `pin` is `#[serde(default)]` for a reason a test pins down: a wire
     * ref legitimately carries no `pin`, and a required field made
     * `from_value` fail for the WHOLE array, so one wire lane silently
     * blanked the live readout of every pad lane beside it.
     *
     * Output mirrors each ref, extended with `value: bool | null` — `null`
     * when the level is unknown (missing peripheral, out-of-range pin,
     * unknown line, or a pad handed to a bus controller the GPIO model does
     * not track) — plus an `error` string on a wire ref that could not
     * resolve, so a blank lane says why. Cheap enough to call every frame.
     * @param {any} refs
     * @returns {any}
     */
    sample_logic_signals(refs) {
        const ret = wasm.wasmsimulator_sample_logic_signals(this.__wbg_ptr, refs);
        return ret;
    }
    /**
     * True once any `bkpt #0xAB` has retired on this machine, so a UART-only
     * Cortex-M lab does not grow a dead source button.
     * @returns {boolean}
     */
    semihosting_attached() {
        const ret = wasm.wasmsimulator_semihosting_attached(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Inject a held analog level into one input of a named ADC, in millivolts.
     * The peripheral's configured gain/reference determines the sample code.
     * Nordic SAADC channel numbers here mean physical AIN0..7, not CH[n] slots.
     * Unlike [`Self::set_adc_value`],
     * which pokes the data register once and is overwritten by the very next
     * conversion (for an un-injected channel the engine converts an
     * incrementing counter), this holds: every later conversion of `channel`
     * uses this level at its configured resolution until [`Self::clear_adc_channel`].
     * This is the entry point an external circuit solver needs — it knows the
     * voltage at a pad and which ADC channel that pad carries, and must not
     * race the conversion engine for the data register.
     * @param {string} peripheral_name
     * @param {number} channel
     * @param {number} millivolts
     */
    set_adc_channel_millivolts(peripheral_name, channel, millivolts) {
        const ptr0 = passStringToWasm0(peripheral_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_adc_channel_millivolts(this.__wbg_ptr, ptr0, len0, channel, millivolts);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Inject an ADC value into a named ADC peripheral's data register.
     * @param {string} peripheral_name
     * @param {number} value
     */
    set_adc_value(peripheral_name, value) {
        const ptr0 = passStringToWasm0(peripheral_name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_adc_value(this.__wbg_ptr, ptr0, len0, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Set the ambient temperature the chip's own temperature sensor reports,
     * in °C (STM32F1: ADC1_IN16, read once firmware sets `ADC_CR2.TSVREFE`).
     *
     * The chip-level counterpart of [`Self::set_ntc_temperature`]: no
     * `external_devices` entry — every peripheral with an on-chip sensor
     * takes the one value. Returns how many took it (`0` on a chip with no
     * modelled sensor). The default before any call is 25 °C. A non-finite
     * value is an error.
     * @param {number} celsius
     * @returns {number}
     */
    set_ambient_temperature(celsius) {
        const ret = wasm.wasmsimulator_set_ambient_temperature(this.__wbg_ptr, celsius);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Set an input board_io binding (e.g. button press).
     * Writes to the GPIO IDR register bit for the specified binding.
     * @param {string} id
     * @param {boolean} active
     */
    set_board_io_input(id, active) {
        const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_board_io_input(this.__wbg_ptr, ptr0, len0, active);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Make `step_batch` stop before executing any of `addresses` (Thumb bit
     * ignored), replacing the previous set. The check runs inside the
     * engine's own advance loop, so a run with breakpoints keeps its batch
     * speed instead of being driven one instruction at a time from JS. A
     * batch that stops early returns fewer cycles than asked, with the pc on
     * the breakpoint; the next batch runs past it. `step_source_line`
     * honours the same set. Journaled, so a snapshot replay stops at the
     * same places.
     * @param {Uint32Array} addresses
     */
    set_breakpoints(addresses) {
        const ptr0 = passArray32ToWasm0(addresses, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_breakpoints(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Set a co-simulation signal from outside the engine: a canvas touch pad
     * sends `('ui.<partId>.pressed', 1)` on press and `0` on release.
     *
     * For an input its model calls a logic level (an analog switch control),
     * 0 is false and anything else true; any other input takes the number as
     * given. Every model reading `path` sees the value from its next step.
     *
     * Throws when the lab has no `cosim_models`, when no model input reads
     * `path` (a typo would otherwise do nothing and report success), when
     * `path` is a board path the machine owns, and for NaN or an infinity.
     * @param {string} path
     * @param {number} value
     */
    set_cosim_signal(path, value) {
        const ptr0 = passStringToWasm0(path, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_cosim_signal(this.__wbg_ptr, ptr0, len0, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Enable/disable scheduler-safe CPU idle fast-forwarding. Off by default;
     * browser callers opt in explicitly after comparing accelerated and
     * non-accelerated traces for the target firmware.
     * @param {boolean} enabled
     */
    set_idle_fast_forward_enabled(enabled) {
        wasm.wasmsimulator_set_idle_fast_forward_enabled(this.__wbg_ptr, enabled);
    }
    /**
     * Generic input-scripting entry point: drive `channel` to `value` (in the
     * channel's engineering unit — g, cm, °C …) on the unique attached input
     * device that exposes it. Type-agnostic (see `labwired_core::sim_input`),
     * so the browser panel, an MCP tool, and a test-script stimulus all share
     * ONE surface. Errors if no device (or more than one) exposes the channel,
     * or the value is out of range.
     * @param {string} channel
     * @param {number} value
     */
    set_input(channel, value) {
        const ptr0 = passStringToWasm0(channel, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_input(this.__wbg_ptr, ptr0, len0, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Apply several input sets as ONE atomic transaction. `sets` is a JSON
     * array of `{channel, value, component?}`; every set is validated first
     * and either all apply or none do, with no simulation steps in between —
     * the way to drive a multi-channel pose (an IMU's x/y/z, a GPS lat+lon)
     * without the firmware observing a torn update, especially from a
     * worker-engine bridge where single calls interleave with execution.
     * @param {any} sets
     */
    set_inputs(sets) {
        const ret = wasm.wasmsimulator_set_inputs(this.__wbg_ptr, sets);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * @param {boolean} enabled
     */
    set_jit_enabled(enabled) {
        wasm.wasmsimulator_set_jit_enabled(this.__wbg_ptr, enabled);
    }
    /**
     * Enable/disable Cortex-M loop TRACES on top of the browser JIT.
     *
     * When on, a counted pure-ALU loop whose conditional backedge targets
     * its own entry compiles to a single wasm `loop` that runs many
     * iterations per dispatch, instead of one dispatch per iteration (see
     * `labwired_core`'s `emit_loop_trace`). Only meaningful with
     * `set_jit_enabled(true)`. Off by default; the RP2040 demo opts in.
     *
     * Toggling drops the compiled-block cache: a block keeps the mode it
     * was compiled under, so a cached untraced block would otherwise
     * survive the switch.
     * @param {boolean} on
     */
    set_jit_loop_traces_enabled(on) {
        const ret = wasm.wasmsimulator_set_jit_loop_traces_enabled(this.__wbg_ptr, on);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Toggle one allowlisted injected motor fault.
     * @param {string} id
     * @param {string} fault
     * @param {boolean} active
     */
    set_motor_fault(id, fault, active) {
        const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(fault, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_motor_fault(this.__wbg_ptr, ptr0, len0, ptr1, len1, active);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Apply one allowlisted motor-plant input in SI units.
     * @param {string} id
     * @param {string} name
     * @param {number} value
     */
    set_motor_input(id, name, value) {
        const ptr0 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_motor_input(this.__wbg_ptr, ptr0, len0, ptr1, len1, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Set the simulated temperature on an NTC thermistor.
     *
     * `device_id` is the `external_devices` id (stamped on the kit at attach).
     * Routes through the ONE SimInput path (`temperature` °C → kit → ADC sync).
     * No `board_io` twin required.
     * @param {string} device_id
     * @param {number} temperature_c
     */
    set_ntc_temperature(device_id, temperature_c) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_ntc_temperature(this.__wbg_ptr, ptr0, len0, temperature_c);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Set the peripheral tick interval used by `Machine::run`.
     *
     * `1` is the exact default: tick orchestration runs after every executed
     * instruction. Larger values are a bounded browser acceleration knob for
     * firmware bring-up paths whose active peripherals are scheduler-driven or
     * inactive.
     *
     * The machine and bus each hold a `SimulationConfig`; both are updated —
     * the run loop paces ticks off the machine's copy while the legacy-walk
     * quantum (`tick_elapsed(interval)`) and the HC-SR04 event-scheduling
     * gate read the bus's, and they must agree or walked peripherals run
     * `interval`× slow.
     * @param {number} interval
     */
    set_peripheral_tick_interval(interval) {
        wasm.wasmsimulator_set_peripheral_tick_interval(this.__wbg_ptr, interval);
    }
    /**
     * Set the simulated wiper position on a potentiometer kit.
     *
     * Thin wrapper over [`Machine::set_input_on`] — identity is the
     * `external_devices` id (no board_io twin). Kit math drives the ADC.
     * `position_pct` must be in 0..=100.
     * @param {string} device_id
     * @param {number} position_pct
     */
    set_potentiometer(device_id, position_pct) {
        const ptr0 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_set_potentiometer(this.__wbg_ptr, ptr0, len0, position_pct);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Write register `id` (the index `get_register_names` gives it).
     * Journaled. An index the core does not name is refused, not ignored.
     * @param {number} id
     * @param {number} value
     */
    set_register(id, value) {
        const ret = wasm.wasmsimulator_set_register(this.__wbg_ptr, id, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Saved points, oldest first, as JSON `[{"id","label","cycles"}]`.
     * @returns {string}
     */
    snapshot_list() {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmsimulator_snapshot_list(this.__wbg_ptr);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * Return the machine to saved point `id`: a fresh machine is built from
     * the same inputs and the recorded calls are replayed up to that point.
     * Console output already shown is not shown again. Refused, with the
     * machine untouched, when the replay does not reproduce the saved state.
     * @param {number} id
     * @returns {string}
     */
    snapshot_restore(id) {
        let deferred2_0;
        let deferred2_1;
        try {
            const ret = wasm.wasmsimulator_snapshot_restore(this.__wbg_ptr, id);
            var ptr1 = ret[0];
            var len1 = ret[1];
            if (ret[3]) {
                ptr1 = 0; len1 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred2_0 = ptr1;
            deferred2_1 = len1;
            return getStringFromWasm0(ptr1, len1);
        } finally {
            wasm.__wbindgen_free(deferred2_0, deferred2_1, 1);
        }
    }
    /**
     * Save the current point. Returns JSON `{"id","label","cycles"}`.
     * @param {string | null} [label]
     * @returns {string}
     */
    snapshot_save(label) {
        let deferred3_0;
        let deferred3_1;
        try {
            var ptr0 = isLikeNone(label) ? 0 : passStringToWasm0(label, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            var len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_snapshot_save(this.__wbg_ptr, ptr0, len0);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * `null` when this simulator can be snapshotted, else the reason it
     * cannot (built by the legacy constructor, or wired to another MCU).
     * @returns {string | undefined}
     */
    snapshot_unavailable_reason() {
        const ret = wasm.wasmsimulator_snapshot_unavailable_reason(this.__wbg_ptr);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        let v1;
        if (ret[0] !== 0) {
            v1 = getStringFromWasm0(ret[0], ret[1]).slice();
            wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        }
        return v1;
    }
    /**
     * Where `line` of `file` starts: `{ pc, pcs: number[], file, line }`, or
     * `null` when no DWARF file matches. `file` is matched by trailing path
     * components, so an editor path (`src/main.rs`,
     * `my-project/src/main.rs`) finds the DWARF absolute path; the most
     * components shared wins. A line without code snaps to the next line
     * that has some (else the previous one); the returned `line` says which.
     * `pc` is the lowest statement address on that line, `pcs` all of them
     * (set breakpoints on all to catch inlined copies).
     * @param {string} file
     * @param {number} line
     * @returns {any}
     */
    source_line_to_pc(file, line) {
        const ptr0 = passStringToWasm0(file, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_source_line_to_pc(this.__wbg_ptr, ptr0, len0, line);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The lines of `file` (matched as in `source_line_to_pc`) that carry
     * code, ascending: where a breakpoint can sit. Empty for an unknown file.
     * @param {string} file
     * @returns {Uint32Array}
     */
    source_lines(file) {
        const ptr0 = passStringToWasm0(file, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_source_lines(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU32FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 4, 4);
        return v2;
    }
    /**
     * The source position of `pc`, from the firmware's DWARF:
     * `{ file, line, column: number | null, function: string | null }`, or
     * `null` when `pc` has no line information. `file` is the full path DWARF
     * records. Throws when the firmware ELF is missing or has no line info.
     * @param {number} pc
     * @returns {any}
     */
    source_location(pc) {
        const ret = wasm.wasmsimulator_source_location(this.__wbg_ptr, pc);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {number} cycles
     */
    step(cycles) {
        const ret = wasm.wasmsimulator_step(this.__wbg_ptr, cycles);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Execute up to max_cycles steps, returning the number actually executed.
     * @param {number} max_cycles
     * @returns {number}
     */
    step_batch(max_cycles) {
        const ret = wasm.wasmsimulator_step_batch(this.__wbg_ptr, max_cycles);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Execute one measured batch and return both wall-clock timing and core
     * run-loop counters. Intended for worker/Playwright profiling; normal
     * animation still calls `step_batch`.
     *
     * Routes through the same path `step_batch` uses — including the opt-in
     * browser JIT — so a profile describes the run the page actually
     * animates.
     * @param {number} max_cycles
     * @returns {any}
     */
    step_batch_profile(max_cycles) {
        const ret = wasm.wasmsimulator_step_batch_profile(this.__wbg_ptr, max_cycles);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    step_single() {
        const ret = wasm.wasmsimulator_step_single(this.__wbg_ptr);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Run until the source line changes:
     * `{ reason, pc, instructions, location }`.
     *
     * Steps single instructions and stops at the first statement boundary
     * on a different line than the one it started on (`"line_changed"`).
     * With `over`, calls (and exception handlers) entered on the way are run
     * through to where they return, at batch speed (Cortex-M, RISC-V,
     * Xtensa, AVR). Stops early on a pc in
     * `breakpoints` or in the machine's own breakpoint set
     * (`"breakpoint"`), when the firmware halts (`"halted"`), or after
     * `max_instructions` single steps or 256 cycles per such step run
     * through calls (`"cap"`). `instructions` counts both. Journaled.
     * `location` is as `source_location` returns it.
     * @param {boolean} over
     * @param {number} max_instructions
     * @param {Uint32Array} breakpoints
     * @returns {any}
     */
    step_source_line(over, max_instructions, breakpoints) {
        const ptr0 = passArray32ToWasm0(breakpoints, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_step_source_line(this.__wbg_ptr, over, max_instructions, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Step `cycles` cycles with the ESP32-classic IPI bridge active. Each
     * cycle samples the DPORT FROM_CPU intmatrix mapping and trigger
     * registers, raises the corresponding INTERRUPT bit, and clears the
     * trigger so the next write re-edges. The dual-core handshake bytes
     * are re-applied every 10k cycles (matching the e2e test cadence).
     * Falls back to plain `step` if `install_esp32_arduino_quirks` hasn't
     * been called yet.
     *
     * Dual-core machines use batched [`AdvanceRequest::run`] (same as
     * [`Self::step_batch`]) so idle fast-forward can engage while PRO_CPU is
     * WAITI-parked. The old N× `AdvanceRequest::single` path forced quantum-1
     * and permanently disabled idle FF for the classic-aids playground path.
     * @param {number} cycles
     */
    step_with_esp32_aids(cycles) {
        const ret = wasm.wasmsimulator_step_with_esp32_aids(this.__wbg_ptr, cycles);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * The MCU's supply, as its supervisor sees it: whether a circuit drives
     * VDD (`routed`), the last VDD it delivered, whether the core is held in
     * reset right now, the power-on and brown-out resets it has come out of,
     * the last cause (`"power_on"` / `"brown_out"`), and the thresholds. See
     * [`labwired_core::power::SupplyStatus`].
     *
     * This is what the canvas shows as "brown-out" / "held in reset" and the
     * reset cause. An unrouted board reports `routed: false` — the ideal rail
     * — and `fidelity_gaps()` carries the matching `unpowered_rail_assumed`.
     * @returns {any}
     */
    supply_status() {
        const ret = wasm.wasmsimulator_supply_status(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Capture the current machine state as a binary `MachineRuntimeSnapshot`
     * (LWRS-framed bincode blob). Mirror of `apply_runtime_snapshot` —
     * returned bytes can be fed back to `apply_runtime_snapshot` on a fresh
     * `WasmSimulator` with the same firmware + bus topology.
     * @returns {Uint8Array}
     */
    take_runtime_snapshot() {
        const ret = wasm.wasmsimulator_take_runtime_snapshot(this.__wbg_ptr);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Non-consuming UART trace snapshot for instruments such as the logic analyzer.
     *
     * Reads the machine's ONE bus trace and groups by bus name. It does NOT
     * walk peripherals looking for a concrete type, and that is the whole
     * point: this used to be `downcast_ref::<Uart>()`, which silently found
     * only the generic STM32-family model. `EspUart` (ESP32-C3 / ESP32-S3),
     * `Esp32Uart`, `Nrf52Uarte` and `Nrf54lUarte` are all UARTs and none of
     * them is a `Uart`, so on every ESP and nRF lab this returned `[]` — the
     * analyzer's UART panel sat empty forever with nothing to indicate an
     * error. Asking the trace what it recorded, rather than asking the type
     * system what a UART is, is what makes the answer complete.
     * @returns {any}
     */
    uart_trace_snapshot() {
        const ret = wasm.wasmsimulator_uart_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * UDS evidence for this run: each `uds-tester`'s executed steps (request,
     * expected, response, cycles, pass/fail), the CAN frames on the tester
     * ids decoded as ISO-TP and UDS, and the firmware console lines. `null`
     * when the lab has no `uds-tester` (a real answer, not a failure); throws
     * when no machine is loaded.
     * @returns {any}
     */
    uds_evidence() {
        const ret = wasm.wasmsimulator_uds_evidence(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The UDS evidence report (Markdown) for this run: the same renderer the
     * CLI uses for `uds-report.md`. `meta_json` carries what only the page
     * knows, all optional: `{"title", "firmware", "firmware_sha256",
     * "system", "chip", "tool_versions": [[tool, version]], "reproduce":
     * [line], "extra_limits": [line]}`. The verdict is PASS only when every
     * tester finished its script; each tester's result is one assertion.
     * @param {string} meta_json
     * @returns {string}
     */
    uds_report_markdown(meta_json) {
        let deferred3_0;
        let deferred3_1;
        try {
            const ptr0 = passStringToWasm0(meta_json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len0 = WASM_VECTOR_LEN;
            const ret = wasm.wasmsimulator_uds_report_markdown(this.__wbg_ptr, ptr0, len0);
            var ptr2 = ret[0];
            var len2 = ret[1];
            if (ret[3]) {
                ptr2 = 0; len2 = 0;
                throw takeFromExternrefTable0(ret[2]);
            }
            deferred3_0 = ptr2;
            deferred3_1 = len2;
            return getStringFromWasm0(ptr2, len2);
        } finally {
            wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
        }
    }
    /**
     * Raw bytes the firmware wrote to the console this board's USB connector is
     * not wired to. Empty when there are none. Diagnostic only — these bytes
     * are deliberately NOT merged into the Serial pane, because no real board
     * would have delivered them.
     * @returns {Uint8Array}
     */
    unheard_console_output() {
        const ret = wasm.wasmsimulator_unheard_console_output(this.__wbg_ptr);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * Arm deterministic, in-engine logic-analyzer capture. TWO channel kinds,
     * one capture layer — same ring, same cursor, same [`read_logic_edges`],
     * same decoders. The ref surface is FLAT:
     *
     * * `{ kind: "gpio", peripheral, pin }` — a chip PAD. Reads what a probe
     *   clipped to that pin would see and nothing else. An unmuxed pad reads
     *   the GPIO output latch and draws a flat line; it NEVER falls back to
     *   the owning peripheral's wire, because a pad probe that quietly showed
     *   bus traffic on a pin no bus reaches would hide the commonest serial
     *   bring-up bug there is.
     * * `{ kind: "wire", peripheral, line }` — a peripheral's OWN line, by
     *   name: `{ kind: "wire", peripheral: "usart2", line: "TX" }`. Line names
     *   are the datasheet role labels (`"TX"`/`"RX"`, `"SCL"`/`"SDA"`,
     *   `"SCK"`/`"MOSI"`/…), matched ignoring case. Independent of pad muxing,
     *   of alternate-function tables, and of which instances a family's pad
     *   table happens to cover.
     *
     * Each ref is resolved ONCE here (to a peripheral index plus a pin or a
     * line index) so the in-loop sampling path never does a string lookup.
     * An unresolvable ref gets `value: null`, an `error` string saying why,
     * and is never sampled — it is not silently dropped and never falls
     * through to channel zero. Installing a watch set resets the capture ring
     * and cursor.
     *
     * Returns the initial state as `[{ ...ref, ch, value }]` where `ch` is the
     * channel index used in edge records (the ref's position) and `value` is
     * the current level (`bool | null`). A `gpio` row carries `pin`, a `wire`
     * row carries `line`. Poll new edges with [`read_logic_edges`]. Pass an
     * empty array to disarm capture.
     * @param {any} refs
     * @returns {any}
     */
    watch_logic_signals(refs) {
        const ret = wasm.wasmsimulator_watch_logic_signals(this.__wbg_ptr, refs);
        return ret;
    }
    /**
     * Non-consuming WiFi 802.11 frame-trace snapshot for the network analyzer
     * (the WiFi analog of `air_trace_snapshot`). Returns, per ESP32-C3 WiFi MAC,
     * the recently captured TX/RX frames (most-recent first); the analyzer UI
     * decodes 802.11 type/addresses and the L3 payload (DHCP/ARP/IP).
     * @returns {any}
     */
    wifi_trace_snapshot() {
        const ret = wasm.wasmsimulator_wifi_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * Write `data` at `addr` through the bus, as a debugger poke. Journaled;
     * the core's cached code is dropped so a write into code takes effect.
     * A byte the bus refuses fails the call, naming the address.
     * @param {number} addr
     * @param {Uint8Array} data
     */
    write_memory(addr, data) {
        const ptr0 = passArray8ToWasm0(data, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_write_memory(this.__wbg_ptr, addr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Bytes accepted into SEGGER RTT down-channel 0, the buffer
     * `SEGGER_RTT_GetKey` reads. A short count means the ring was full; the
     * rest is discarded and the simulator does not stall.
     *
     * Errors when this simulator has no machine, same as `drain_rtt_output`.
     * @param {Uint8Array} data
     * @returns {number}
     */
    write_rtt_down(data) {
        const ptr0 = passArray8ToWasm0(data, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_write_rtt_down(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * Append host bytes for `SYS_READ` (stdin, handle 0). Does not block the guest.
     * @param {Uint8Array} data
     */
    write_semihosting_input(data) {
        const ptr0 = passArray8ToWasm0(data, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmsimulator_write_semihosting_input(this.__wbg_ptr, ptr0, len0);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
}
if (Symbol.dispose) WasmSimulator.prototype[Symbol.dispose] = WasmSimulator.prototype.free;

export class WasmWorld {
    static __wrap(ptr) {
        const obj = Object.create(WasmWorld.prototype);
        obj.__wbg_ptr = ptr;
        WasmWorldFinalization.register(obj, obj.__wbg_ptr, obj);
        return obj;
    }
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WasmWorldFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wasmworld_free(ptr, 0);
    }
    /**
     * @returns {any}
     */
    air_trace_snapshot() {
        const ret = wasm.wasmworld_air_trace_snapshot(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {any}
     */
    analog_channels() {
        const ret = wasm.wasmworld_analog_channels(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @returns {any}
     */
    analog_series() {
        const ret = wasm.wasmworld_analog_series(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {number} cursor
     * @returns {any}
     */
    analog_trace_snapshot(cursor) {
        const ret = wasm.wasmworld_analog_trace_snapshot(this.__wbg_ptr, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The world's BLE air, most recent first (at most 200 frames), each
     * decoded: advertising, LL control, empty PDUs and ATT operations.
     * @returns {any}
     */
    ble_air_trace() {
        const ret = wasm.wasmworld_ble_air_trace(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * The scripted BLE centrals (`ble_central` interconnects): connection
     * state, discovered GATT database, reads, writes, notifications and the
     * full transcript. `[{ id, report }]`, manifest order.
     * @returns {any}
     */
    ble_centrals() {
        const ret = wasm.wasmworld_ble_centrals(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} node_id
     * @returns {any}
     */
    bus_trace_snapshot(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_bus_trace_snapshot(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Every `can_bus`, manifest order, as
     * `{ buses: [{ id, bitrate, timed, now_ps, nodes, frames, frames_dropped,
     * totals }] }`: per node its derived bit rate, TEC/REC and
     * `active | passive | bus_off` state; the most recent frames (at most
     * 512) with SOF and end times in picoseconds, payload as hex and
     * `ok | error | no_ack | lost_arbitration`; frame totals by result. See
     * `labwired_core::network::timed_can::CanBusReport`. `{ buses: [] }`
     * without a `can_bus`.
     * @returns {any}
     */
    can_bus_report() {
        const ret = wasm.wasmworld_can_bus_report(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Shared analog trace and its declared sampling interval. The same core
     * session advances in native and browser worlds.
     * No model is a successful optional value; serialization failure is an error.
     * @returns {any}
     */
    cosim_status() {
        const ret = wasm.wasmworld_cosim_status(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} node_id
     * @returns {Uint8Array}
     */
    drain_uart_output(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_drain_uart_output(this.__wbg_ptr, ptr0, len0);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * @param {string} node_id
     * @returns {any}
     */
    fdcan_trace_snapshot(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_fdcan_trace_snapshot(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Node-local shaft state; unknown measured electrical quantities stay null.
     * @param {string} node_id
     * @returns {any}
     */
    get_actuator_states(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_actuator_states(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Node `node_id`'s `board_io` bindings.
     * @param {string} node_id
     * @returns {any}
     */
    get_board_io_config(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_board_io_config(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Node `node_id`'s `board_io` states, `[{ id, active }]`.
     * @param {string} node_id
     * @returns {any}
     */
    get_board_io_states(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_board_io_states(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} node_id
     * @returns {number}
     */
    get_pc(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_pc(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * @param {string} node_id
     * @param {number} id
     * @returns {number}
     */
    get_register(node_id, id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_register(this.__wbg_ptr, ptr0, len0, id);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    /**
     * @param {string} node_id
     * @returns {any}
     */
    get_register_names(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_register_names(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} node_id
     * @param {string} device_id
     * @returns {Uint8Array}
     */
    get_ssd1306_framebuffer(node_id, device_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(device_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_get_ssd1306_framebuffer(this.__wbg_ptr, ptr0, len0, ptr1, len1);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v3 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v3;
    }
    /**
     * Every GPIO net: its level, edge count, members and their drive, and
     * the diagnostics (`GPIO_NET_CONTENTION`, `GPIO_NET_FLOATING`) with
     * times in picoseconds, manifest order. `[]` without `gpio_net`s.
     * @returns {any}
     */
    gpio_net_report() {
        const ret = wasm.wasmworld_gpio_net_report(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Whether this world has GPIO nets (`gpio_net` interconnects).
     * @returns {boolean}
     */
    has_gpio_nets() {
        const ret = wasm.wasmworld_has_gpio_nets(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * Whether this world runs a timed UART network (`uart_network`).
     * @returns {boolean}
     */
    has_uart_network() {
        const ret = wasm.wasmworld_has_uart_network(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] !== 0;
    }
    /**
     * The drivable input channels on node `node_id`, as
     * `WasmSimulator::list_inputs` reports them.
     * @param {string} node_id
     * @returns {any}
     */
    list_inputs(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_list_inputs(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} node_id
     * @returns {any}
     */
    motor_series(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_motor_series(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Build a world from the environment YAML and the page's resolved nodes:
     * `[{ id, system_yaml, chip_yaml, firmware: Uint8Array, blobs? }]`, where
     * `blobs` is an optional `{ name: Uint8Array }` map with the single-chip
     * `new_from_config` names (an ESP node's mask ROM). A node's boot profile
     * (`profile: arduino-esp32` for a classic-ESP32 Arduino sketch) is read
     * from the environment YAML.
     * @param {string} environment_yaml
     * @param {any} nodes
     * @returns {WasmWorld}
     */
    static new_from_resolved(environment_yaml, nodes) {
        const ptr0 = passStringToWasm0(environment_yaml, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_new_from_resolved(ptr0, len0, nodes);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return WasmWorld.__wrap(ret[0]);
    }
    /**
     * @returns {any}
     */
    node_ids() {
        const ret = wasm.wasmworld_node_ids(this.__wbg_ptr);
        return ret;
    }
    /**
     * @param {string} node_id
     * @returns {any}
     */
    node_snapshot(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_node_snapshot(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Level edges of node `node_id`'s watch set since `cursor`; same shape as
     * `WasmSimulator::read_logic_edges`.
     * @param {string} node_id
     * @param {number} cursor
     * @returns {any}
     */
    read_logic_edges(node_id, cursor) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_read_logic_edges(this.__wbg_ptr, ptr0, len0, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Four-state (`0`/`1`/`z`/`x`) edges of node `node_id`'s watch set; same
     * shape as `WasmSimulator::read_logic_states`.
     * @param {string} node_id
     * @param {number} cursor
     * @returns {any}
     */
    read_logic_states(node_id, cursor) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_read_logic_states(this.__wbg_ptr, ptr0, len0, cursor);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * @param {string} node_id
     * @param {number} address
     * @param {number} len
     * @returns {Uint8Array}
     */
    read_memory(node_id, address, len) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_read_memory(this.__wbg_ptr, ptr0, len0, address, len);
        if (ret[3]) {
            throw takeFromExternrefTable0(ret[2]);
        }
        var v2 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v2;
    }
    /**
     * @param {string} node_id
     * @param {number} address
     * @returns {number}
     */
    read_u8(node_id, address) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_read_u8(this.__wbg_ptr, ptr0, len0, address);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0];
    }
    /**
     * Hand the page's ESP32-C3 mask ROM (IROM 384 KiB, DROM 128 KiB) to the
     * engine for every C3 node built afterwards in this worker. The browser
     * has no filesystem and no vendored copy.
     *
     * Kept for pages that already call it. The general mechanism is a node's
     * own `blobs` in [`Self::new_from_resolved`] (`esp32c3_irom` /
     * `esp32c3_drom`, the names the single-chip path takes), which covers the
     * ESP32-S3 too and wins over this registration.
     * @param {Uint8Array} irom
     * @param {Uint8Array} drom
     */
    static register_esp32c3_rom(irom, drom) {
        const ptr0 = passArray8ToWasm0(irom, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passArray8ToWasm0(drom, wasm.__wbindgen_malloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_register_esp32c3_rom(ptr0, len0, ptr1, len1);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * The level each ref reads now on node `node_id` (`value: bool | null`).
     * @param {string} node_id
     * @param {any} refs
     * @returns {any}
     */
    sample_logic_signals(node_id, refs) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_sample_logic_signals(this.__wbg_ptr, ptr0, len0, refs);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Press or release an input `board_io` binding (a button) on node `node_id`.
     * @param {string} node_id
     * @param {string} id
     * @param {boolean} active
     */
    set_board_io_input(node_id, id, active) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_set_board_io_input(this.__wbg_ptr, ptr0, len0, ptr1, len1, active);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * @param {string} path
     * @param {number} value
     */
    set_cosim_signal(path, value) {
        const ptr0 = passStringToWasm0(path, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_set_cosim_signal(this.__wbg_ptr, ptr0, len0, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Drive a simulated input channel on node `node_id`.
     * @param {string} node_id
     * @param {string} channel
     * @param {number} value
     */
    set_input(node_id, channel, value) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ptr1 = passStringToWasm0(channel, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len1 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_set_input(this.__wbg_ptr, ptr0, len0, ptr1, len1, value);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * @param {number} rounds
     * @returns {number}
     */
    step_batch(rounds) {
        const ret = wasm.wasmworld_step_batch(this.__wbg_ptr, rounds);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0] >>> 0;
    }
    step_single() {
        const ret = wasm.wasmworld_step_single(this.__wbg_ptr);
        if (ret[1]) {
            throw takeFromExternrefTable0(ret[0]);
        }
    }
    /**
     * Simulated time of the slowest node, ns (a BLE world steps in time
     * lockstep, so every node is within 10 µs of it).
     * @returns {number}
     */
    time_ns() {
        const ret = wasm.wasmworld_time_ns(this.__wbg_ptr);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return ret[0];
    }
    /**
     * @param {string} node_id
     * @returns {bigint}
     */
    total_cycles(node_id) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_total_cycles(this.__wbg_ptr, ptr0, len0);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return BigInt.asUintN(64, ret[0]);
    }
    /**
     * The timed UART network: per-link statistics (bytes, throughput,
     * in-flight depth, overruns, framing errors, latency), tagged messages
     * with per-node latency, and the unified timeline (TX start, delivery,
     * RX interrupt, overrun, node reset, link changes, GPIO markers) from
     * sequence number `since` on, ordered by world time. Times are
     * picoseconds. `null` when the world has no `uart_network`.
     * @param {number} since
     * @returns {any}
     */
    uart_network_report(since) {
        const ret = wasm.wasmworld_uart_network_report(this.__wbg_ptr, since);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
    /**
     * Arm node `node_id`'s logic-analyzer watch set (`[{kind, peripheral,
     * pin | line}]`), next to the world's own pad watches. Same rows as
     * `WasmSimulator::watch_logic_signals`.
     * @param {string} node_id
     * @param {any} refs
     * @returns {any}
     */
    watch_logic_signals(node_id, refs) {
        const ptr0 = passStringToWasm0(node_id, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.wasmworld_watch_logic_signals(this.__wbg_ptr, ptr0, len0, refs);
        if (ret[2]) {
            throw takeFromExternrefTable0(ret[1]);
        }
        return takeFromExternrefTable0(ret[0]);
    }
}
if (Symbol.dispose) WasmWorld.prototype[Symbol.dispose] = WasmWorld.prototype.free;

/**
 * A shared UART cross-link medium, owned by the host. Create one per multi-chip
 * lab-group and pass it to every chip's `attach_uart_wire`; chips sharing a bus
 * exchange bytes, chips on different buses are isolated. A fresh `WireBus` per
 * lab (re)load replaces the former module-global reset — a new bus starts empty,
 * so no stale link buffers can leak into the new station.
 */
export class WireBus {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        WireBusFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_wirebus_free(ptr, 0);
    }
    /**
     * Drop every link's buffered bytes on this bus. Rarely needed — prefer a
     * fresh `WireBus` per lab load — but exposed for in-place resets.
     */
    clear() {
        wasm.wirebus_clear(this.__wbg_ptr);
    }
    constructor() {
        const ret = wasm.wirebus_new();
        this.__wbg_ptr = ret;
        WireBusFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
}
if (Symbol.dispose) WireBus.prototype[Symbol.dispose] = WireBus.prototype.free;

/**
 * Parse a recording (JSON lines or candump) and summarize it as JSON:
 * `{"frames","rx","tx","first_cycle","last_cycle","clock_hz","controller"}`,
 * or throw with the line that failed. For a UI to check a file before
 * replaying it.
 * @param {string} text
 * @param {number} clock_hz
 * @returns {string}
 */
export function can_recording_summary(text, clock_hz) {
    let deferred3_0;
    let deferred3_1;
    try {
        const ptr0 = passStringToWasm0(text, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.can_recording_summary(ptr0, len0, clock_hz);
        var ptr2 = ret[0];
        var len2 = ret[1];
        if (ret[3]) {
            ptr2 = 0; len2 = 0;
            throw takeFromExternrefTable0(ret[2]);
        }
        deferred3_0 = ptr2;
        deferred3_1 = len2;
        return getStringFromWasm0(ptr2, len2);
    } finally {
        wasm.__wbindgen_free(deferred3_0, deferred3_1, 1);
    }
}

/**
 * Is the engine profiler recording?
 * @returns {boolean}
 */
export function profile_enabled() {
    const ret = wasm.profile_enabled();
    return ret !== 0;
}

/**
 * Start an engine profiling window in the browser, installing the
 * `performance.now()` clock. Without this the wasm build has no clock at all
 * and every duration would read zero — see `labwired_core::profile`.
 */
export function profile_start() {
    wasm.profile_start();
}

/**
 * Close the profiling window. The report survives until the next
 * [`profile_start`].
 */
export function profile_stop() {
    wasm.profile_stop();
}

/**
 * Inject the JSON body the virtual WiFi AP serves for
 * `GET /v1/public-stats` (LBC3.1 stats lab). The browser playground should
 * `fetch('https://api.labwired.com/v1/public-stats')` and pass the text here
 * **before** constructing the simulator so the device twin receives live
 * product numbers. Pass an empty string to clear the override (baked
 * fallback). Wasm has no sockets; native CLI fetches live itself.
 * @param {string} json
 */
export function set_wifi_ap_public_stats_json(json) {
    const ptr0 = passStringToWasm0(json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
    const len0 = WASM_VECTOR_LEN;
    wasm.set_wifi_ap_public_stats_json(ptr0, len0);
}

/**
 * Fulfill a DNS request with A records. `ips_json` is a JSON array of
 * dotted-quads, e.g. `["93.184.216.34"]`.
 * @param {number} id
 * @param {string} ips_json
 */
export function wifi_host_fulfill_dns(id, ips_json) {
    const ptr0 = passStringToWasm0(ips_json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
    const len0 = WASM_VECTOR_LEN;
    wasm.wifi_host_fulfill_dns(id, ptr0, len0);
}

/**
 * Fulfill an HTTP proxy request with a raw HTTP/1.1 response body (status
 * line + headers + body), as UTF-8 or binary string via byte array from JS.
 * @param {number} id
 * @param {Uint8Array} response
 */
export function wifi_host_fulfill_http(id, response) {
    const ptr0 = passArray8ToWasm0(response, wasm.__wbindgen_malloc);
    const len0 = WASM_VECTOR_LEN;
    wasm.wifi_host_fulfill_http(id, ptr0, len0);
}

/**
 * Enable browser host-network bridge so the virtual AP grants stations
 * internet via JS (DoH + `fetch`). Call once after loading the wasm module.
 * @param {boolean} active
 */
export function wifi_host_net_set_active(active) {
    wasm.wifi_host_net_set_active(active);
}

/**
 * Pending DNS names the host must resolve (DoH). JSON array of
 * `{ "id": number, "name": string }`.
 * @returns {string}
 */
export function wifi_host_poll_dns_requests() {
    let deferred1_0;
    let deferred1_1;
    try {
        const ret = wasm.wifi_host_poll_dns_requests();
        deferred1_0 = ret[0];
        deferred1_1 = ret[1];
        return getStringFromWasm0(ret[0], ret[1]);
    } finally {
        wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
    }
}

/**
 * Pending HTTP proxy requests. JSON array of
 * `{ "id", "url", "method", "body_b64" }` — any host URL; body is the
 * request entity after headers (client-side `fetch` uses the user's network).
 * @returns {string}
 */
export function wifi_host_poll_http_requests() {
    let deferred1_0;
    let deferred1_1;
    try {
        const ret = wasm.wifi_host_poll_http_requests();
        deferred1_0 = ret[0];
        deferred1_1 = ret[1];
        return getStringFromWasm0(ret[0], ret[1]);
    } finally {
        wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
    }
}
function __wbg_get_imports() {
    const import0 = {
        __proto__: null,
        __wbg_Error_bce6d499ff0a4aff: function(arg0, arg1) {
            const ret = Error(getStringFromWasm0(arg0, arg1));
            return ret;
        },
        __wbg_Number_b7972a139bfbfdf0: function(arg0) {
            const ret = Number(arg0);
            return ret;
        },
        __wbg_String_8564e559799eccda: function(arg0, arg1) {
            const ret = String(arg1);
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbg___wbindgen_bigint_get_as_i64_410e28c7b761ad83: function(arg0, arg1) {
            const v = arg1;
            const ret = typeof(v) === 'bigint' ? v : undefined;
            getDataViewMemory0().setBigInt64(arg0 + 8 * 1, isLikeNone(ret) ? BigInt(0) : ret, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, !isLikeNone(ret), true);
        },
        __wbg___wbindgen_boolean_get_2304fb8c853028c8: function(arg0) {
            const v = arg0;
            const ret = typeof(v) === 'boolean' ? v : undefined;
            return isLikeNone(ret) ? 0xFFFFFF : ret ? 1 : 0;
        },
        __wbg___wbindgen_debug_string_edece8177ad01481: function(arg0, arg1) {
            const ret = debugString(arg1);
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbg___wbindgen_in_07056af4f902c445: function(arg0, arg1) {
            const ret = arg0 in arg1;
            return ret;
        },
        __wbg___wbindgen_is_bigint_aeae3893f30ed54e: function(arg0) {
            const ret = typeof(arg0) === 'bigint';
            return ret;
        },
        __wbg___wbindgen_is_function_5cd60d5cf78b4eef: function(arg0) {
            const ret = typeof(arg0) === 'function';
            return ret;
        },
        __wbg___wbindgen_is_null_2042690d351e14f0: function(arg0) {
            const ret = arg0 === null;
            return ret;
        },
        __wbg___wbindgen_is_object_b4593df85baada48: function(arg0) {
            const val = arg0;
            const ret = typeof(val) === 'object' && val !== null;
            return ret;
        },
        __wbg___wbindgen_is_string_dde0fd9020db4434: function(arg0) {
            const ret = typeof(arg0) === 'string';
            return ret;
        },
        __wbg___wbindgen_is_undefined_35bb9f4c7fd651d5: function(arg0) {
            const ret = arg0 === undefined;
            return ret;
        },
        __wbg___wbindgen_jsval_eq_c0ed08b3e0f393b9: function(arg0, arg1) {
            const ret = arg0 === arg1;
            return ret;
        },
        __wbg___wbindgen_jsval_loose_eq_0ad77b7717db155c: function(arg0, arg1) {
            const ret = arg0 == arg1;
            return ret;
        },
        __wbg___wbindgen_number_get_f73a1244370fcc2c: function(arg0, arg1) {
            const obj = arg1;
            const ret = typeof(obj) === 'number' ? obj : undefined;
            getDataViewMemory0().setFloat64(arg0 + 8 * 1, isLikeNone(ret) ? 0 : ret, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, !isLikeNone(ret), true);
        },
        __wbg___wbindgen_string_get_d109740c0d18f4d7: function(arg0, arg1) {
            const obj = arg1;
            const ret = typeof(obj) === 'string' ? obj : undefined;
            var ptr1 = isLikeNone(ret) ? 0 : passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            var len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbg___wbindgen_throw_9c31b086c2b26051: function(arg0, arg1) {
            throw new Error(getStringFromWasm0(arg0, arg1));
        },
        __wbg__wbg_cb_unref_3fa391f3fcdb55f8: function(arg0) {
            arg0._wbg_cb_unref();
        },
        __wbg_apply_b593fcd87094fd23: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.apply(arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_buffer_09bfa2e33737b5fc: function(arg0) {
            const ret = arg0.buffer;
            return ret;
        },
        __wbg_call_084ee3e860ee9f92: function() { return handleError(function (arg0, arg1, arg2, arg3, arg4) {
            const ret = arg0.call(arg1, arg2, arg3, arg4);
            return ret;
        }, arguments); },
        __wbg_call_13665d9f14390edc: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.call(arg1);
            return ret;
        }, arguments); },
        __wbg_call_dfde26266607c996: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.call(arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_done_54b8da57023b7ed2: function(arg0) {
            const ret = arg0.done;
            return ret;
        },
        __wbg_entries_564a7e8b1e54ede5: function(arg0) {
            const ret = Object.entries(arg0);
            return ret;
        },
        __wbg_exports_fcb6c7dbab2808fc: function(arg0) {
            const ret = arg0.exports;
            return ret;
        },
        __wbg_get_3e9a707ab7d352eb: function() { return handleError(function (arg0, arg1) {
            const ret = Reflect.get(arg0, arg1);
            return ret;
        }, arguments); },
        __wbg_get_98fdf51d029a75eb: function(arg0, arg1) {
            const ret = arg0[arg1 >>> 0];
            return ret;
        },
        __wbg_get_dcf82ab8aad1a593: function() { return handleError(function (arg0, arg1) {
            const ret = Reflect.get(arg0, arg1);
            return ret;
        }, arguments); },
        __wbg_get_unchecked_1dfe6d05ad91d9b7: function(arg0, arg1) {
            const ret = arg0[arg1 >>> 0];
            return ret;
        },
        __wbg_get_with_ref_key_6412cf3094599694: function(arg0, arg1) {
            const ret = arg0[arg1];
            return ret;
        },
        __wbg_instanceof_ArrayBuffer_53db37b06f6b9afe: function(arg0) {
            let result;
            try {
                result = arg0 instanceof ArrayBuffer;
            } catch (_) {
                result = false;
            }
            const ret = result;
            return ret;
        },
        __wbg_instanceof_Map_16f217b9a2a08d8c: function(arg0) {
            let result;
            try {
                result = arg0 instanceof Map;
            } catch (_) {
                result = false;
            }
            const ret = result;
            return ret;
        },
        __wbg_instanceof_Object_03924e0dbda74bd8: function(arg0) {
            let result;
            try {
                result = arg0 instanceof Object;
            } catch (_) {
                result = false;
            }
            const ret = result;
            return ret;
        },
        __wbg_instanceof_Uint8Array_abd07d4bd221d50b: function(arg0) {
            let result;
            try {
                result = arg0 instanceof Uint8Array;
            } catch (_) {
                result = false;
            }
            const ret = result;
            return ret;
        },
        __wbg_isArray_94898ed3aad6947b: function(arg0) {
            const ret = Array.isArray(arg0);
            return ret;
        },
        __wbg_isSafeInteger_01e964d144ad3a55: function(arg0) {
            const ret = Number.isSafeInteger(arg0);
            return ret;
        },
        __wbg_iterator_1441b47f341dc34f: function() {
            const ret = Symbol.iterator;
            return ret;
        },
        __wbg_length_2591a0f4f659a55c: function(arg0) {
            const ret = arg0.length;
            return ret;
        },
        __wbg_length_56fcd3e2b7e0299d: function(arg0) {
            const ret = arg0.length;
            return ret;
        },
        __wbg_new_02d162bc6cf02f60: function() {
            const ret = new Object();
            return ret;
        },
        __wbg_new_070df68d66325372: function() {
            const ret = new Map();
            return ret;
        },
        __wbg_new_1f0e50fc5628cc27: function() { return handleError(function (arg0) {
            const ret = new WebAssembly.Module(arg0);
            return ret;
        }, arguments); },
        __wbg_new_22cc98ecc9876bce: function() { return handleError(function (arg0, arg1) {
            const ret = new WebAssembly.Instance(arg0, arg1);
            return ret;
        }, arguments); },
        __wbg_new_310879b66b6e95e1: function() {
            const ret = new Array();
            return ret;
        },
        __wbg_new_7ddec6de44ff8f5d: function(arg0) {
            const ret = new Uint8Array(arg0);
            return ret;
        },
        __wbg_new_d251f1787a7db662: function() { return handleError(function (arg0) {
            const ret = new WebAssembly.Memory(arg0);
            return ret;
        }, arguments); },
        __wbg_new_with_length_99887c91eae4abab: function(arg0) {
            const ret = new Uint8Array(arg0 >>> 0);
            return ret;
        },
        __wbg_new_with_length_c2a8f9ac6aaaac03: function(arg0) {
            const ret = new Array(arg0 >>> 0);
            return ret;
        },
        __wbg_next_2a4e19f4f5083b0f: function(arg0) {
            const ret = arg0.next;
            return ret;
        },
        __wbg_next_6429a146bf756f93: function() { return handleError(function (arg0) {
            const ret = arg0.next();
            return ret;
        }, arguments); },
        __wbg_now_01126724c5debde2: function() {
            const ret = performance.now();
            return ret;
        },
        __wbg_prototypesetcall_5f9bdc8d75e07276: function(arg0, arg1, arg2) {
            Uint8Array.prototype.set.call(getArrayU8FromWasm0(arg0, arg1), arg2);
        },
        __wbg_set_24d0fa9e104112f9: function(arg0, arg1, arg2) {
            arg0.set(getArrayU8FromWasm0(arg1, arg2));
        },
        __wbg_set_6be42768c690e380: function(arg0, arg1, arg2) {
            arg0[arg1] = arg2;
        },
        __wbg_set_78ea6a19f4818587: function(arg0, arg1, arg2) {
            arg0[arg1 >>> 0] = arg2;
        },
        __wbg_set_a0e911be3da02782: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = Reflect.set(arg0, arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_set_facb7a5914e0fa39: function(arg0, arg1, arg2) {
            const ret = arg0.set(arg1, arg2);
            return ret;
        },
        __wbg_subarray_7c6a0da8f3b4a1ba: function(arg0, arg1, arg2) {
            const ret = arg0.subarray(arg1 >>> 0, arg2 >>> 0);
            return ret;
        },
        __wbg_value_9cc0518af87a489c: function(arg0) {
            const ret = arg0.value;
            return ret;
        },
        __wbg_warn_4c4a738f436830df: function(arg0, arg1) {
            console.warn(getStringFromWasm0(arg0, arg1));
        },
        __wbindgen_cast_0000000000000001: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [I32, I32, I32], shim_idx: 17790, ret: I32, inner_ret: Some(I32) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm_bindgen__convert__closures_____invoke__hd380486714aed0de);
            return ret;
        },
        __wbindgen_cast_0000000000000002: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [I32, I32, I32], shim_idx: 17794, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm_bindgen__convert__closures_____invoke__hfd702cb450394e61);
            return ret;
        },
        __wbindgen_cast_0000000000000003: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [I32, I32], shim_idx: 17792, ret: I32, inner_ret: Some(I32) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm_bindgen__convert__closures_____invoke__h2c2ed4eaf3514dc2);
            return ret;
        },
        __wbindgen_cast_0000000000000004: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [I32, I32], shim_idx: 17796, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm_bindgen__convert__closures_____invoke__h7a1bd4c440d234ea);
            return ret;
        },
        __wbindgen_cast_0000000000000005: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [I32], shim_idx: 17788, ret: I32, inner_ret: Some(I32) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm_bindgen__convert__closures_____invoke__h544004abb09bb1df);
            return ret;
        },
        __wbindgen_cast_0000000000000006: function(arg0) {
            // Cast intrinsic for `F64 -> Externref`.
            const ret = arg0;
            return ret;
        },
        __wbindgen_cast_0000000000000007: function(arg0, arg1) {
            // Cast intrinsic for `I128 -> Externref`.
            const ret = (BigInt.asUintN(64, arg0) | (arg1 << BigInt(64)));
            return ret;
        },
        __wbindgen_cast_0000000000000008: function(arg0) {
            // Cast intrinsic for `I64 -> Externref`.
            const ret = arg0;
            return ret;
        },
        __wbindgen_cast_0000000000000009: function(arg0, arg1) {
            // Cast intrinsic for `Ref(String) -> Externref`.
            const ret = getStringFromWasm0(arg0, arg1);
            return ret;
        },
        __wbindgen_cast_000000000000000a: function(arg0, arg1) {
            // Cast intrinsic for `U128 -> Externref`.
            const ret = (BigInt.asUintN(64, arg0) | (BigInt.asUintN(64, arg1) << BigInt(64)));
            return ret;
        },
        __wbindgen_cast_000000000000000b: function(arg0) {
            // Cast intrinsic for `U64 -> Externref`.
            const ret = BigInt.asUintN(64, arg0);
            return ret;
        },
        __wbindgen_init_externref_table: function() {
            const table = wasm.__wbindgen_externrefs;
            const offset = table.grow(4);
            table.set(0, undefined);
            table.set(offset + 0, undefined);
            table.set(offset + 1, null);
            table.set(offset + 2, true);
            table.set(offset + 3, false);
        },
    };
    return {
        __proto__: null,
        "./labwired_wasm_bg.js": import0,
    };
}

function wasm_bindgen__convert__closures_____invoke__h544004abb09bb1df(arg0, arg1, arg2) {
    const ret = wasm.wasm_bindgen__convert__closures_____invoke__h544004abb09bb1df(arg0, arg1, arg2);
    return ret;
}

function wasm_bindgen__convert__closures_____invoke__h7a1bd4c440d234ea(arg0, arg1, arg2, arg3) {
    wasm.wasm_bindgen__convert__closures_____invoke__h7a1bd4c440d234ea(arg0, arg1, arg2, arg3);
}

function wasm_bindgen__convert__closures_____invoke__h2c2ed4eaf3514dc2(arg0, arg1, arg2, arg3) {
    const ret = wasm.wasm_bindgen__convert__closures_____invoke__h2c2ed4eaf3514dc2(arg0, arg1, arg2, arg3);
    return ret;
}

function wasm_bindgen__convert__closures_____invoke__hfd702cb450394e61(arg0, arg1, arg2, arg3, arg4) {
    wasm.wasm_bindgen__convert__closures_____invoke__hfd702cb450394e61(arg0, arg1, arg2, arg3, arg4);
}

function wasm_bindgen__convert__closures_____invoke__hd380486714aed0de(arg0, arg1, arg2, arg3, arg4) {
    const ret = wasm.wasm_bindgen__convert__closures_____invoke__hd380486714aed0de(arg0, arg1, arg2, arg3, arg4);
    return ret;
}

const AirBusFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_airbus_free(ptr, 1));
const WasmFlexRuntimeFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmflexruntime_free(ptr, 1));
const WasmSimulatorFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmsimulator_free(ptr, 1));
const WasmWorldFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wasmworld_free(ptr, 1));
const WireBusFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_wirebus_free(ptr, 1));

function addToExternrefTable0(obj) {
    const idx = wasm.__externref_table_alloc();
    wasm.__wbindgen_externrefs.set(idx, obj);
    return idx;
}

function _assertClass(instance, klass) {
    if (!(instance instanceof klass)) {
        throw new Error(`expected instance of ${klass.name}`);
    }
}

const CLOSURE_DTORS = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(state => wasm.__wbindgen_destroy_closure(state.a, state.b));

function debugString(val) {
    // primitive types
    const type = typeof val;
    if (type == 'number' || type == 'boolean' || val == null) {
        return  `${val}`;
    }
    if (type == 'string') {
        return `"${val}"`;
    }
    if (type == 'symbol') {
        const description = val.description;
        if (description == null) {
            return 'Symbol';
        } else {
            return `Symbol(${description})`;
        }
    }
    if (type == 'function') {
        const name = val.name;
        if (typeof name == 'string' && name.length > 0) {
            return `Function(${name})`;
        } else {
            return 'Function';
        }
    }
    // objects
    if (Array.isArray(val)) {
        const length = val.length;
        let debug = '[';
        if (length > 0) {
            debug += debugString(val[0]);
        }
        for(let i = 1; i < length; i++) {
            debug += ', ' + debugString(val[i]);
        }
        debug += ']';
        return debug;
    }
    // Test for built-in
    const builtInMatches = /\[object ([^\]]+)\]/.exec(toString.call(val));
    let className;
    if (builtInMatches && builtInMatches.length > 1) {
        className = builtInMatches[1];
    } else {
        // Failed to match the standard '[object ClassName]'
        return toString.call(val);
    }
    if (className == 'Object') {
        // we're a user defined class or Object
        // JSON.stringify avoids problems with cycles, and is generally much
        // easier than looping through ownProperties of `val`.
        try {
            return 'Object(' + JSON.stringify(val) + ')';
        } catch (_) {
            return 'Object';
        }
    }
    // errors
    if (val instanceof Error) {
        return `${val.name}: ${val.message}\n${val.stack}`;
    }
    // TODO we could test for more things here, like `Set`s and `Map`s.
    return className;
}

function getArrayU32FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint32ArrayMemory0().subarray(ptr / 4, ptr / 4 + len);
}

function getArrayU8FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint8ArrayMemory0().subarray(ptr / 1, ptr / 1 + len);
}

let cachedDataViewMemory0 = null;
function getDataViewMemory0() {
    if (cachedDataViewMemory0 === null || cachedDataViewMemory0.buffer.detached === true || (cachedDataViewMemory0.buffer.detached === undefined && cachedDataViewMemory0.buffer !== wasm.memory.buffer)) {
        cachedDataViewMemory0 = new DataView(wasm.memory.buffer);
    }
    return cachedDataViewMemory0;
}

function getStringFromWasm0(ptr, len) {
    return decodeText(ptr >>> 0, len);
}

let cachedUint32ArrayMemory0 = null;
function getUint32ArrayMemory0() {
    if (cachedUint32ArrayMemory0 === null || cachedUint32ArrayMemory0.byteLength === 0) {
        cachedUint32ArrayMemory0 = new Uint32Array(wasm.memory.buffer);
    }
    return cachedUint32ArrayMemory0;
}

let cachedUint8ArrayMemory0 = null;
function getUint8ArrayMemory0() {
    if (cachedUint8ArrayMemory0 === null || cachedUint8ArrayMemory0.byteLength === 0) {
        cachedUint8ArrayMemory0 = new Uint8Array(wasm.memory.buffer);
    }
    return cachedUint8ArrayMemory0;
}

function handleError(f, args) {
    try {
        return f.apply(this, args);
    } catch (e) {
        const idx = addToExternrefTable0(e);
        wasm.__wbindgen_exn_store(idx);
    }
}

function isLikeNone(x) {
    return x === undefined || x === null;
}

function makeMutClosure(arg0, arg1, f) {
    const state = { a: arg0, b: arg1, cnt: 1 };
    const real = (...args) => {

        // First up with a closure we increment the internal reference
        // count. This ensures that the Rust closure environment won't
        // be deallocated while we're invoking it.
        state.cnt++;
        const a = state.a;
        state.a = 0;
        try {
            return f(a, state.b, ...args);
        } finally {
            state.a = a;
            real._wbg_cb_unref();
        }
    };
    real._wbg_cb_unref = () => {
        if (--state.cnt === 0) {
            wasm.__wbindgen_destroy_closure(state.a, state.b);
            state.a = 0;
            CLOSURE_DTORS.unregister(state);
        }
    };
    CLOSURE_DTORS.register(real, state, state);
    return real;
}

function passArray32ToWasm0(arg, malloc) {
    const ptr = malloc(arg.length * 4, 4) >>> 0;
    getUint32ArrayMemory0().set(arg, ptr / 4);
    WASM_VECTOR_LEN = arg.length;
    return ptr;
}

function passArray8ToWasm0(arg, malloc) {
    const ptr = malloc(arg.length * 1, 1) >>> 0;
    getUint8ArrayMemory0().set(arg, ptr / 1);
    WASM_VECTOR_LEN = arg.length;
    return ptr;
}

function passStringToWasm0(arg, malloc, realloc) {
    if (realloc === undefined) {
        const buf = cachedTextEncoder.encode(arg);
        const ptr = malloc(buf.length, 1) >>> 0;
        getUint8ArrayMemory0().subarray(ptr, ptr + buf.length).set(buf);
        WASM_VECTOR_LEN = buf.length;
        return ptr;
    }

    let len = arg.length;
    let ptr = malloc(len, 1) >>> 0;

    const mem = getUint8ArrayMemory0();

    let offset = 0;

    for (; offset < len; offset++) {
        const code = arg.charCodeAt(offset);
        if (code > 0x7F) break;
        mem[ptr + offset] = code;
    }
    if (offset !== len) {
        if (offset !== 0) {
            arg = arg.slice(offset);
        }
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const view = getUint8ArrayMemory0().subarray(ptr + offset, ptr + len);
        const ret = cachedTextEncoder.encodeInto(arg, view);

        offset += ret.written;
        ptr = realloc(ptr, len, offset, 1) >>> 0;
    }

    WASM_VECTOR_LEN = offset;
    return ptr;
}

function takeFromExternrefTable0(idx) {
    const value = wasm.__wbindgen_externrefs.get(idx);
    wasm.__externref_table_dealloc(idx);
    return value;
}

let cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
cachedTextDecoder.decode();
const MAX_SAFARI_DECODE_BYTES = 2146435072;
let numBytesDecoded = 0;
function decodeText(ptr, len) {
    numBytesDecoded += len;
    if (numBytesDecoded >= MAX_SAFARI_DECODE_BYTES) {
        cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
        cachedTextDecoder.decode();
        numBytesDecoded = len;
    }
    return cachedTextDecoder.decode(getUint8ArrayMemory0().subarray(ptr, ptr + len));
}

const cachedTextEncoder = new TextEncoder();

if (!('encodeInto' in cachedTextEncoder)) {
    cachedTextEncoder.encodeInto = function (arg, view) {
        const buf = cachedTextEncoder.encode(arg);
        view.set(buf);
        return {
            read: arg.length,
            written: buf.length
        };
    };
}

let WASM_VECTOR_LEN = 0;

let wasmModule, wasmInstance, wasm;
function __wbg_finalize_init(instance, module) {
    wasmInstance = instance;
    wasm = instance.exports;
    wasmModule = module;
    cachedDataViewMemory0 = null;
    cachedUint32ArrayMemory0 = null;
    cachedUint8ArrayMemory0 = null;
    wasm.__wbindgen_start();
    return wasm;
}

async function __wbg_load(module, imports) {
    if (typeof Response === 'function' && module instanceof Response) {
        if (typeof WebAssembly.instantiateStreaming === 'function') {
            try {
                return await WebAssembly.instantiateStreaming(module, imports);
            } catch (e) {
                const validResponse = module.ok && expectedResponseType(module.type);

                if (validResponse && module.headers.get('Content-Type') !== 'application/wasm') {
                    console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n", e);

                } else { throw e; }
            }
        }

        const bytes = await module.arrayBuffer();
        return await WebAssembly.instantiate(bytes, imports);
    } else {
        const instance = await WebAssembly.instantiate(module, imports);

        if (instance instanceof WebAssembly.Instance) {
            return { instance, module };
        } else {
            return instance;
        }
    }

    function expectedResponseType(type) {
        switch (type) {
            case 'basic': case 'cors': case 'default': return true;
        }
        return false;
    }
}

function initSync(module) {
    if (wasm !== undefined) return wasm;


    if (module !== undefined) {
        if (Object.getPrototypeOf(module) === Object.prototype) {
            ({module} = module)
        } else {
            console.warn('using deprecated parameters for `initSync()`; pass a single object instead')
        }
    }

    const imports = __wbg_get_imports();
    if (!(module instanceof WebAssembly.Module)) {
        module = new WebAssembly.Module(module);
    }
    const instance = new WebAssembly.Instance(module, imports);
    return __wbg_finalize_init(instance, module);
}

async function __wbg_init(module_or_path) {
    if (wasm !== undefined) return wasm;


    if (module_or_path !== undefined) {
        if (Object.getPrototypeOf(module_or_path) === Object.prototype) {
            ({module_or_path} = module_or_path)
        } else {
            console.warn('using deprecated parameters for the initialization function; pass a single object instead')
        }
    }

    if (module_or_path === undefined) {
        module_or_path = new URL('labwired_wasm_bg.wasm', import.meta.url);
    }
    const imports = __wbg_get_imports();

    if (typeof module_or_path === 'string' || (typeof Request === 'function' && module_or_path instanceof Request) || (typeof URL === 'function' && module_or_path instanceof URL)) {
        module_or_path = fetch(module_or_path);
    }

    const { instance, module } = await __wbg_load(await module_or_path, imports);

    return __wbg_finalize_init(instance, module);
}

export { initSync, __wbg_init as default };
