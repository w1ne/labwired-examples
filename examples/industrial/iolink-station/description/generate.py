#!/usr/bin/env python3
"""Reuse the pinned iolinki generator, then describe the actual terminal block.

IODD 1.1.5 OtherConnectionT requires Description and each
wire's Name, colour and function. The generator's M12 default does not
describe this shield; no alternate protocol/schema implementation is used.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--iolinki", type=Path, default=ROOT.parent / "firmware/master/.deps/iolinki")
parser.add_argument("--schema", type=Path, required=True, help="Official extracted IODD1.1.xsd")
args = parser.parse_args()
iolinki = args.iolinki.resolve()
pins = json.loads((ROOT.parent / "firmware/master/dependencies.json").read_text())
actual = subprocess.check_output(["git", "-C", str(iolinki), "rev-parse", "HEAD"], text=True).strip()
if actual != pins["iolinki"]["revision"]:
    raise SystemExit("IODD generator checkout differs from the pinned stack source")
spec = importlib.util.spec_from_file_location("iodd_gen", iolinki / "tools/iodd_gen.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
config = json.loads((ROOT / "device.json").read_text())
tree = ET.fromstring(generator.generate_bytes(config))
ns = {"i": generator.NS}
connection = tree.find(".//i:Connection", ns)
connection.clear()
connection.set("{" + generator.XSI + "}type", config["terminalConnection"]["type"])
generator.element(connection, "ProductRef", {"productId": config["productId"]})
language = tree.find(".//i:PrimaryLanguage", ns)
generator.element(connection, "Description", {"textId": "T_TerminalConnection"})
generator.element(language, "Text", {"id": "T_TerminalConnection", "value": config["terminalConnection"]["description"]})
for wire in config["terminalConnection"]["wires"]:
    node = generator.element(connection, "Wire" + str(wire["pin"]), {"function": wire["function"], "color": wire["color"]})
    text_id = "T_Terminal" + str(wire["pin"])
    generator.element(node, "Name", {"textId": text_id})
    generator.element(language, "Text", {"id": text_id, "value": wire["name"]})
ET.indent(tree, space="  ")
destination = ROOT / "LabWired-L476-L6362A-DI8-20261118-IODD1.1.xml"
with tempfile.TemporaryDirectory(prefix="labwired-iodd-") as temporary:
    draft = Path(temporary) / destination.name
    draft.write_bytes(ET.tostring(tree, encoding="utf-8", xml_declaration=True) + b"\n")
    subprocess.run(["node", str(iolinki / "tools/iodd_stamp.mjs"), "write", str(draft)], check=True)
    subprocess.run(["python3", str(iolinki / "tools/iodd_cli.py"), "validate",
                    str(draft), "--schema", str(args.schema.resolve())], check=True)
    destination.write_bytes(draft.read_bytes())
print(destination.name)
