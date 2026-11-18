"""Check the Doom package and reject cross-discipline wiring drift."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / "examples/gaming/esp32s3-doom"
spec = importlib.util.spec_from_file_location("doom_package_verifier", ROOT / "authoring/verify_package.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

class DoomPackageTests(unittest.TestCase):
    def test_shipped_source_and_artifacts_match(self):
        result = verifier.verify_package(ROOT)
        self.assertEqual(result["electrical_contract"]["display_pins"], 34)

    def test_swapped_display_data_wires_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["electronics/interface-contract.json", "manufacturing/doom-carrier.net.xml",
                         "connector-map.csv", "bom.csv", "firmware/source/main/doom_lcd_pins.h"]:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            path = root / "manufacturing/doom-carrier.net.xml"
            tree = ET.parse(path)
            for node in tree.findall("./nets/net/node"):
                if node.get("ref") == "J3" and node.get("pin") in {"6", "7"}:
                    node.set("pin", "7" if node.get("pin") == "6" else "6")
            tree.write(path, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "LCD_D0"):
                verifier.verify_electrical_contract(root)

    def test_unrouted_connection_is_rejected(self):
        erc = verifier.load(ROOT, "validation/erc.json")
        drc = verifier.load(ROOT, "validation/drc.json")
        drc["unconnected_items"] = [{"description": "Unrouted LCD_D0"}]
        with self.assertRaisesRegex(ValueError, "unrouted"):
            verifier.check_native_reports(erc, drc)

    def test_empty_erc_receipt_is_rejected(self):
        erc = verifier.load(ROOT, "validation/erc.json")
        drc = verifier.load(ROOT, "validation/drc.json")
        erc["sheets"] = []
        with self.assertRaisesRegex(ValueError, "no schematic sheets"):
            verifier.check_native_reports(erc, drc)

if __name__ == "__main__":
    unittest.main()
