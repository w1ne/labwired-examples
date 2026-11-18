#!/usr/bin/env python3
"""Check the retained physical-station acceptance result and its exact files."""
import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent


def require(value, detail):
    if not value:
        raise SystemExit("FAIL: " + detail)


def main():
    manifest = json.loads((PACKAGE / "evidence/physical-runtime-station/manifest.json").read_text())
    for item in manifest["firmware"] + manifest["artifacts"]:
        path = PACKAGE / item["path"]
        require(path.stat().st_size == item["bytes"], item["path"] + " size")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], item["path"] + " SHA-256")
    require(manifest["sourceFrozenDuringRun"], "runtime source changed during the run")
    result = json.loads((PACKAGE / "evidence/physical-runtime-station/result.json").read_text())
    before = next(s for s in result["stages"] if s["time_ps"] == 650_000_000_000)
    final = result["stages"][-1]
    require(final["time_ps"] == 680_000_000_000, "final simulated time")
    for stage, patterns in [(before, [0xA5, 0x3C]), (final, [0x5A, 0xC3])]:
        nodes = stage["nodes"]
        master = nodes["master"]
        require(master["g_master_state"] == [3, 3], "both master ports must be OPERATE")
        require(master["g_master_pd"] == patterns, "master must read the two expected device bytes")
        require(master["g_wake_count"] == [1, 1], "one wake per master port")
        for field in ["g_phy_error", "g_phy_faults", "g_uart_errors", "g_rx_overflows", "g_master_tick_result"]:
            require(master[field] == [0, 0], "master " + field)
        for index, identity in enumerate(["input1", "input2"]):
            node = nodes[identity]
            require(node["g_device_state"] == 4, identity + " must be OPERATE")
            require(node["g_device_pd"] == patterns[index], identity + " input byte")
            require(node["g_wake_events"] == 1 and node["g_overload_edges"] == 1, identity + " wake/OL count")
            for field in ["g_phy_error", "g_uart_errors", "g_rx_overflows", "g_tx_deadline_errors"]:
                require(node[field] == 0, identity + " " + field)
            require(node["uid_fixture"] == manifest["uidFixtures"][identity], identity + " UID")
        require(nodes["input1"]["serial"] != nodes["input2"]["serial"], "distinct firmware serial numbers")
        for identity, node in nodes.items():
            require(node["SystemCoreClock"] == 80_000_000 and node["g_startup_error"] == 0, identity + " clock/startup")
            require(node["uart1_brr"] == [2083], identity + " UART divider")
    network = result["network"]
    require(network["events_dropped"] == 0, "trace must retain all events")
    require(len(network["links"]) == 2, "exactly two point-to-point links")
    directions = []
    errors = ["framing_errors", "parity_errors", "overruns", "false_starts", "misframed", "truncated", "late", "dropped_link_cut", "dropped_rx_disabled"]
    for link in network["links"]:
        require(link["connected"], "connected link")
        require(link["a_node"] == "master" and link["b_node"] in ["input1", "input2"], "master/device topology")
        for side in ["a_format", "b_format"]:
            fmt = link[side]
            require(fmt["data_bits"] == 8 and fmt["parity"] == "even" and fmt["stop_half_bits"] == 2 and fmt["bit_ps"] == 26_037_500, "C/Q COM2 8E1 format")
        for direction in link["directions"]:
            directions.append((direction["from_node"], direction["from_uart"], direction["to_node"], direction["to_uart"]))
            require(direction["chars_delivered"] > 0, "actual traffic in every direction")
            for field in errors:
                require(direction[field] == 0, str(directions[-1]) + " " + field)
    require(set(directions) == {("master", "uart1", "input1", "uart1"), ("input1", "uart1", "master", "uart1"), ("master", "uart4", "input2", "uart1"), ("input2", "uart1", "master", "uart4")}, "exact physical UART routing")
    print("PASS: exact firmware/config hashes, three OPERATE nodes, two input transitions, distinct identities, zero reported node and wire errors")


if __name__ == "__main__":
    main()
