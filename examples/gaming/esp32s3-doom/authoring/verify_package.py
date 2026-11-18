#!/usr/bin/env python3
"""Verify the shipped package's files and cross-discipline contracts.

This checks recorded design/build evidence. It does not rerun KiCad, KernelCAD,
the simulator, or physical qualification. Use the documented native/runtime
commands to reproduce those checks.
"""
from __future__ import annotations
import argparse
import csv
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {
    "firmware/source/build", "firmware/source/.idf-cache",
    "firmware/source/.ccache", "firmware/source/wad", "validation/recheck",
}
IGNORED_FILES = {"firmware/source/sdkconfig", "firmware/source/sdkconfig.old"}
IGNORED_NAMES = ("*.kicad_prl", "*.kicad-save-*", "*.lck", "*.qa.b64")

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load(root, name):
    return json.loads((root / name).read_text())

def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def package_files(root):
    result = {}
    for current, dirs, files in os.walk(root):
        base = Path(current)
        dirs[:] = sorted(d for d in dirs if d != "__pycache__"
                         and (base / d).relative_to(root).as_posix() not in IGNORED_DIRS)
        for name in sorted(files):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if (relative in IGNORED_FILES or relative == "release-manifest.json"
                    or any(fnmatch.fnmatch(name, pattern) for pattern in IGNORED_NAMES)):
                continue
            require(not path.is_symlink(), f"Package contains a symbolic link: {relative}")
            result[relative] = identity(path)
    return dict(sorted(result.items()))

def write_manifest(root):
    manifest = {
        "schema": 1, "package": "esp32s3-doom-rev-a", "status": "candidate",
        "hardware_tested": False,
        "tracker": "https://github.com/w1ne/labwired/issues/3552",
        "scope": "Source and artifact integrity; physical qualification is recorded separately.",
        "files": package_files(root),
    }
    (root / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return len(manifest["files"])

def verify_manifest(root):
    manifest = load(root, "release-manifest.json")
    require(manifest["schema"] == 1, "Unsupported package manifest schema")
    require(manifest["status"] == "candidate" and manifest["hardware_tested"] is False,
            "This revision has no physical qualification")
    for name in manifest["files"]:
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and "\\" not in name,
                f"Invalid package path: {name}")
    actual = package_files(root)
    require(actual.keys() == manifest["files"].keys(),
            "Manifest file coverage differs from the shipped package")
    for name, expected in manifest["files"].items():
        require(actual[name] == expected, f"Package file changed: {name}")
    return len(actual)

def verify_electrical_contract(root):
    contract = load(root, "electronics/interface-contract.json")
    xml = ET.parse(root / "manufacturing/doom-carrier.net.xml").getroot()
    nets = {net.attrib["name"].removeprefix("/"):
            {(node.attrib["ref"], node.attrib["pin"]) for node in net.findall("node")}
            for net in xml.findall("./nets/net")}
    components = {c.attrib["ref"]: c for c in xml.findall("./components/comp")}
    with (root / "connector-map.csv").open(newline="") as file:
        rows = list(csv.DictReader(file))
    require(len(rows) == 34, "Display connector must have 34 physical pins")
    display = {int(row["Carrier J3 pin"]): row for row in rows}
    require(set(display) == set(range(1, 35)), "Display connector pin set is incomplete")
    for pin, row in display.items():
        require(int(row["Display pin via1to1 ribbon"]) == pin,
                f"Ribbon conductor {pin} is reversed or remapped")
    header = (root / "firmware/source/main/doom_lcd_pins.h").read_text()
    gpio = {name: int(value) for name, value in re.findall(
        r"^#define\s+DOOM_LCD_([A-Z0-9]+)\s+(\d+)\s*$", header, re.M)}
    for entry in contract["signals"]:
        name, pin, resistor = entry["signal"], entry["display_pin"], entry["resistor"]
        require(gpio.get(name) == entry["gpio"], f"Firmware pin differs for {name}")
        require(nets.get(f"MCU_{name}") == {
            (entry["carrier_header"], str(entry["carrier_pin"])), (resistor, "1")},
            f"MCU_{name} must connect only the specified module pin and source resistor")
        expected_lcd = {("J3", str(pin)), (resistor, "2")}
        expected_lcd.update((reference, "1") for reference in entry.get("testpoints", []))
        require(nets.get(f"LCD_{name}") == expected_lcd,
                f"LCD_{name} must connect its series resistor, named testpoint, and display pin")
        require(components[resistor].findtext("fields/field[@name='MPN']")
                == "RC0603FR-0733RL", f"{resistor} must be the specified 33 ohm part")
        require(display[pin]["Carrier destination"] == f"GPIO{entry['gpio']} through33R",
                f"Connector instructions disagree with firmware for {name}")
    for entry in contract["pullups"]:
        name, pin, resistor = entry["signal"], entry["display_pin"], entry["resistor"]
        require(nets.get(f"LCD_{name}") == {("J3", str(pin)), (resistor, "2")},
                f"{name} must be a dedicated pulled-high display signal")
        require((resistor, "1") in nets["3V3"], f"{name} pull-up supply is wrong")
        require(components[resistor].findtext("fields/field[@name='MPN']")
                == "RC0603FR-0710KL", f"{resistor} must be the specified 10 kohm part")
        require(display[pin]["Carrier destination"] == "3V3 through10k",
                f"Connector instructions disagree for {name}")
    for pin in [24, 25]:
        require(("J3", str(pin)) in nets["3V3"], f"Display VDD pin {pin} is missing")
    for pin in [26, 27]:
        require(("J3", str(pin)) in nets["GND"], f"Display ground pin {pin} is missing")
    for pin in [28, 29, 30, 31, 34]:
        memberships = [nodes for nodes in nets.values() if ("J3", str(pin)) in nodes]
        require(len(memberships) == 1 and len(memberships[0]) == 1,
                f"Unused display pin {pin} must remain isolated")
        require(display[pin]["Carrier destination"] == "unconnected",
                f"Unused display pin {pin} instructions are wrong")
    with (root / "bom.csv").open(newline="") as file:
        bom = {row["Reference"]: row for row in csv.DictReader(file)}
    for ref, mpn in [("C1", "C2012X7R1A106K125AC"), ("C2", "C2012X8R1H104K125AA"),
                     ("J3", "TSW-117-07-G-D")]:
        require(components[ref].findtext("fields/field[@name='MPN']") == mpn
                and bom[ref]["MPN"] == mpn, f"Native design and BOM differ for {ref}")
    require(bom["J1,J2"]["MPN"] == "SSW-122-01-G-S"
            and bom["CABLE1"]["MPN"] == "IDSD-17-D-04.00-G",
            "The mated socket/ribbon parts differ from the reviewed geometry")
    require("DOOM_LCD_BUS DOOM_LCD_BUS_I80" in header, "Physical panel requires I80")
    return {"signals": len(contract["signals"]), "pullups": len(contract["pullups"]),
            "display_pins": len(display)}

def check_native_reports(erc, drc):
    for kind, report in [("ERC", erc), ("DRC", drc)]:
        require(report["kicad_version"].startswith("10."), f"{kind} must use KiCad 10")
        require(set(report["included_severities"]) == {"error", "warning", "exclusion"},
                f"{kind} must include all severities")
    require(bool(erc["sheets"]), "ERC receipt has no schematic sheets")
    require(all(not sheet["violations"] for sheet in erc["sheets"]),
            "ERC reports findings")
    require(not drc["violations"], "DRC reports findings")
    require(not drc["unconnected_items"], "PCB has unrouted connections")
    require(not drc["schematic_parity"], "PCB differs from the schematic")
    ignored = {row["key"] for row in drc["ignored_checks"]}
    require(not (ignored & {"shorting_items", "clearance", "unconnected_items",
                            "track_dangling", "via_dangling", "schematic_parity"}),
            "A required electrical/routing check is disabled")

def verify_firmware(root):
    manifest = load(root, "firmware/artifacts/build-manifest.json")
    provenance = load(root, "firmware/source-provenance.json")
    require(manifest["inputs"] == load(root, "firmware/build-inputs.json"),
            "Build recipe inputs differ from the artifact receipt")
    require(manifest["reviewed_source_manifest_sha256"]
            == identity(root / "firmware/source-provenance.json")["sha256"],
            "Build receipt was recorded against a different reviewed source manifest")
    require(manifest["source_files_sha256"] == provenance["packaged_files_sha256"],
            "Built source differs from the reviewed packaged source")
    require(len(manifest["source_files_sha256"]) >= 190, "Firmware source inventory is incomplete")
    for name, digest in manifest["source_files_sha256"].items():
        require(identity(root / "firmware/source" / name)["sha256"] == digest,
                f"Firmware source changed after build: {name}")
    for name, expected in manifest["files"].items():
        require(identity(root / "firmware/artifacts" / name) == expected,
                f"Firmware artifact differs from build receipt: {name}")
    flash = (root / "firmware/artifacts/doom-s3-flash.bin").read_bytes()
    for name, offset in [("bootloader.bin", 0), ("partition-table.bin", 0x8000),
                         ("doom-s3.bin", 0x10000)]:
        segment = (root / "firmware/artifacts" / name).read_bytes()
        require(flash[offset:offset + len(segment)] == segment,
                f"Merged flash does not contain {name} at the documented offset")
    wad = manifest["inputs"]["wad"]
    require(hashlib.sha256(flash[wad["offset"]:wad["offset"] + wad["bytes"]]).hexdigest()
            == wad["sha256"], "Merged flash contains the wrong IWAD")
    config = (root / "firmware/artifacts/sdkconfig").read_text().splitlines()
    for line in ["CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y", "CONFIG_SPIRAM_MODE_OCT=y",
                 "CONFIG_ESP_CONSOLE_UART_DEFAULT=y", "CONFIG_ESP_CONSOLE_UART_NUM=0",
                 "# CONFIG_FREERTOS_UNICORE is not set"]:
        require(line in config, f"Physical firmware configuration is missing {line}")
    comparison = load(root, "validation/final-source-rebuild-comparison.json")
    require(comparison["all_artifacts_identical"] and not comparison["changed_files"]
            and comparison["files"] == manifest["files"],
            "Recipe replay does not match the shipped artifacts")
    return {"source_files": len(manifest["source_files_sha256"]),
            "artifacts": len(manifest["files"])}

def verify_mechanical(root):
    digest = identity(root / "mechanical/doom-desktop.kcad.ts")["sha256"]
    record = load(root, "validation/mechanical-review.json")
    require(record["sourceSha256"] == digest, "CAD source differs from the strict review")
    require(record["result"]["ok"] is True, "Strict mechanical review did not pass")
    attempt = record["result"]["attempts"][-1]
    require(attempt["functional"] and attempt["qualityOk"] and not attempt["blockingReasons"],
            "Mechanical review has a functional, quality, or blocking failure")
    requirements = attempt["requirements"]["entries"]
    require(len(requirements) == 10 and all(r["status"] == "pass" for r in requirements),
            "The ten fit requirements did not all pass")
    visual = attempt["visualReview"]
    require(visual["accepted"] and len(visual["checks"]) == 7
            and all(check["passed"] for check in visual["checks"]),
            "Mechanical screenshot review is incomplete")
    negative = load(root, "validation/mechanical-usb-negative.json")
    require(negative["result"]["ok"] is False, "USB obstruction negative control must fail")
    entries = negative["result"]["attempts"][-1]["requirements"]["entries"]
    failed = [entry for entry in entries if entry["status"] == "fail"]
    require(len(entries) == 10 and len(failed) == 1
            and failed[0]["name"] == "usb-plug-access"
            and failed[0]["measured"] == 0 and failed[0]["limit"] == 0.5,
            "USB obstruction negative control no longer detects lost access")
    exports = load(root, "validation/mechanical-exports.json")
    require(exports["sourceSha256"] == digest, "Exports use a different CAD source")
    records = [exports["assemblyStep"]]
    records += [exports[name][kind] for name in
                ["base-print", "lid-print", "ribbon-spacer-print"]
                for kind in ["step", "stl", "3mf"]]
    for result in records:
        require(result["ok"] and result["sceneSummary"]["valid"], "A mechanical export is invalid")
        path = root / "mechanical" / Path(result["output_path"]).name
        require(path.stat().st_size == result["byte_count"], f"Export size differs: {path.name}")
    hosted = load(root, "validation/hosted-cad.json")
    require(hosted["sourceSha256"] == digest and hosted["evaluation"]["ok"],
            "Hosted evaluation did not validate this CAD source")
    require(hosted["assetSha256"]
            == identity(root / "mechanical/inputs/doom-carrier-board.step")["sha256"],
            "Hosted revision contains a different native PCB asset")
    return {"requirements": len(requirements), "visual_checks": len(visual["checks"]),
            "exports": len(records)}

def verify_package(root=ROOT):
    result = {"manifest_files": verify_manifest(root),
              "electrical_contract": verify_electrical_contract(root)}
    check_native_reports(load(root, "validation/erc.json"), load(root, "validation/drc.json"))
    result["firmware"] = verify_firmware(root)
    result["mechanical"] = verify_mechanical(root)
    require(load(root, "validation/acceptance.json")["hardware_tested"] is False,
            "No physical qualification was performed for this package")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifest", action="store_true",
                        help="Refresh hashes after reviewing deliberate package changes.")
    args = parser.parse_args()
    if args.write_manifest:
        print(json.dumps({"manifest_files": write_manifest(ROOT)}))
    else:
        print(json.dumps(verify_package(), indent=2))
