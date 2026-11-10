"""Mechanical/PCB release-data contract checks.

These are static source-consistency tests. They do not replace KiCad ERC,
physical DRC, circuit simulation, a first-article inspection or a flight test.
"""
import collections
import csv
import pathlib
import re
import unittest
from zipfile import ZipFile

ROOT = pathlib.Path(__file__).resolve().parents[1]
H = ROOT / "examples" / "robotics" / "quadrotor-bldc" / "hardware"
E = H / "esc-4in1"
R = E / "fabrication-review"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def findings(report):
    return collections.Counter(
        re.findall(r"^\[([^\]]+)\]", report.read_text(), re.MULTILINE)
    )


class ESCPhysicalBoard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = (E / "4in1.kicad_pcb").read_text()
        cls.sch = (E / "4in1.kicad_sch").read_text()
        cls.placements = read_csv(R / "placement.csv")
        cls.components = read_csv(R / "pcb-all-components.csv")
        cls.grouped = read_csv(R / "pcba-bom-grouped.csv")
        cls.system = read_csv(H / "system-bom.csv")

    def test_real_board_source_with_six_layer_stack(self):
        self.assertIn("(kicad_pcb", self.board)
        self.assertIn("(kicad_sch", self.sch)
        for layer in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"):
            self.assertIn('"' + layer + '"', self.board)
        self.assertGreater((E / "4in1.kicad_dru").stat().st_size, 1000)
        self.assertGreater((E / "4in1.kicad_pro").stat().st_size, 10000)
        self.assertGreater((E / "ESC.kicad_sch").stat().st_size, 200000)

    def test_footprint_references_unique_and_bom_identical(self):
        refs = re.findall(
            r'(?m)^\t\t\(property "Reference" "([^"]+)"', self.board
        )
        self.assertEqual(len(refs), 222)
        self.assertEqual(len(set(refs)), 222)
        bom_refs = {row["Designator"] for row in self.components}
        self.assertEqual(len(bom_refs), 222)
        self.assertEqual(bom_refs, set(refs))
        self.assertEqual(len([r for r in self.components if r["Population"] == "ASSEMBLE"]), 213)

    def test_placements_and_grouped_bom_reconcile(self):
        placements = {row["Ref"] for row in self.placements}
        assembled = {
            row["Designator"] for row in self.components if row["Population"] == "ASSEMBLE"
        }
        self.assertEqual(len(self.placements), len(placements))
        self.assertEqual(len(placements), 213)
        self.assertEqual(placements, assembled)
        self.assertEqual(len(self.grouped), 22)
        self.assertEqual(sum(int(row["Quantity"]) for row in self.grouped), 213)
        self.assertTrue(all(row["LCSC Part #"] for row in self.grouped))
        for row in self.grouped:
            for ref in row["Designator"].split(", "):
                self.assertIn(ref, assembled)

    def test_four_real_motor_power_channels(self):
        by_value = collections.Counter(
            (row["Value"] for row in self.components
             if row["Population"] == "ASSEMBLE")
        )
        self.assertEqual(by_value["AT32F421G8U7"], 4)
        self.assertEqual(by_value["NSG2065Q"], 4)
        self.assertEqual(by_value["SP40N01GHNK"], 24)
        self.assertEqual(by_value["4.7uF"], 52)

    def test_49_bulk_caps_wired_in_schematic(self):
        references = {row["new_reference"] for row in read_csv(E / "board-only-caps.csv")}
        self.assertEqual(references, {"C" + str(i) for i in range(501, 550)})
        for ref in references:
            self.assertEqual(
                self.sch.count('(property "Reference" "' + ref + '"'), 1
            )
        # These are source-level checks; the archived KiCad netlist carries
        # exact node membership (C501..C549 on +BATT and GND).
        netlist = (R / "schematic.net").read_text()
        for ref in ("C501", "C510", "C530", "C549"):
            self.assertIn('(ref "' + ref + '")', netlist)

    def test_drc_report_is_not_misrepresented_as_clean(self):
        drc = findings(E / "validation" / "drc-final.txt")
        self.assertEqual(drc["lib_footprint_mismatch"], 1)
        self.assertEqual(drc["net_conflict"], 3)
        for violation in ("shorting_items", "clearance", "unconnected_items"):
            self.assertEqual(drc[violation], 0)
        self.assertEqual(sum(drc.values()), 4)

    def test_gate_driver_nc_pads_restored_and_isolated(self):
        # The five actual QFN pads must be physical PCB objects, each with a
        # unique isolated KiCad NC net, not a dummy schematic placeholder.
        for ref, pins in {"U6": ("5", "7"), "U10": ("5", "7", "8")}.items():
            marker = '(property "Reference" "' + ref + '"'
            at = self.board.find(marker)
            self.assertGreater(at, 0, ref)
            begin = self.board.rfind("\n\t(footprint ", 0, at)
            self.assertGreater(begin, 0, ref)
            end = self.board.find("\n\t(footprint ", at)
            footprint = self.board[begin:end if end >= 0 else None]
            for pin in pins:
                self.assertIn('(pad "' + pin + '" smd', footprint)
                self.assertIn(f'unconnected-({ref}-NC-Pad{pin})', footprint)


    def test_u9_nc_pads_and_blind_drill(self):
        marker = '(property "Reference" "U9"'
        idx = self.board.find(marker)
        self.assertGreater(idx, 0)
        begin = self.board.rfind("\n\t(footprint ", 0, idx)
        stop = self.board.find("\n\t(footprint ", idx)
        footprint = self.board[begin:stop if stop >= 0 else None]
        for pin, name in (("23", "PA15"), ("24", "PB3")):
            self.assertIn('(pad "' + pin + '" smd', footprint)
            self.assertIn(f'unconnected-(U9-{name}-Pad{pin})', footprint)
        self.assertIn('(via micro', self.board)
        self.assertIn('(layers "In4.Cu" "B.Cu")', self.board)
        self.assertIn('(at 70.64 38.46)', self.board)
        with ZipFile(R / "esc-4in1-gerbers-REVIEW-ONLY.zip") as archive:
            self.assertIn("4in1-in4-back.drl", archive.namelist())
        review = (E / "validation" / "u9-power-reroute-20261110.md").read_text()
        self.assertIn("Do NOT order", review)

    def test_u7_three_nc_pads_and_current_feedback_microvias(self):
        marker = '(property "Reference" "U7"'
        idx = self.board.find(marker)
        self.assertGreater(idx, 0)
        start = self.board.rfind("\n\t(footprint ", 0, idx)
        end = self.board.find("\n\t(footprint ", idx)
        footprint = self.board[start:end if end >= 0 else None]
        for number, name in (("8", "PA2"), ("23", "PA15"), ("24", "PB3")):
            self.assertIn('(pad "' + number + '" smd', footprint)
            self.assertIn(f'unconnected-(U7-{name}-Pad{number})', footprint)
        for x,y in ((71.35,48.1198), (71.92,50.2), (70.4,51.05),
                    (70.71,48.1198), (73.67,52.05), (73.9,53.509117)):
            self.assertIn(f'(at {x} {y})', self.board)
        self.assertIn('"/ESC3/FBCOMMON"', self.board)
        with ZipFile(R / "esc-4in1-gerbers-REVIEW-ONLY.zip") as archive:
            self.assertIn('4in1-in4-back.drl', archive.namelist())
        evidence = (E / 'validation' / 'u7-power-feedback-reroute-20261110.md').read_text()
        self.assertIn('not an approved product', evidence)

    def test_u5_three_nc_pads_and_four_new_blind_vias(self):
        marker = '(property "Reference" "U5"'
        idx = self.board.find(marker)
        self.assertGreater(idx, 0)
        start = self.board.rfind("\n\t(footprint ", 0, idx)
        end = self.board.find("\n\t(footprint ", idx)
        footprint = self.board[start:end if end >= 0 else None]
        for number, name in (("8", "PA2"), ("23", "PA15"), ("24", "PB3")):
            self.assertIn('(pad "' + number + '" smd', footprint)
            self.assertIn(f'unconnected-(U5-{name}-Pad{number})', footprint)
        for x,y in ((79.99,42.4101), (80.63,42.4101),
                    (77.88,38.46), (77.5,36.99)):
            self.assertIn(f'(at {x} {y})', self.board)
        evidence = (E / 'validation' / 'u5-power-feedback-reroute-20261110.md').read_text()
        self.assertIn('not ready for', evidence)

    def test_inherited_erc_findings_explicit(self):
        erc = findings(E / "validation" / "erc-final.txt")
        self.assertEqual(sum(erc.values()), 352)
        self.assertEqual(erc["pin_to_pin"], 240)
        self.assertIn("Do not order", (E / "README.md").read_text())

    def test_gerber_data_is_review_only(self):
        with ZipFile(R / "esc-4in1-gerbers-REVIEW-ONLY.zip") as archive:
            names = archive.namelist()
            self.assertEqual(len(names), 16)
            self.assertTrue(any(name.endswith(".drl") for name in names))
            self.assertTrue(any(name.endswith(".gtl") for name in names))
            self.assertTrue(any(name.endswith(".gbl") for name in names))
            self.assertTrue(any(name.endswith(".g4") for name in names))
        self.assertGreater((R / "pcb-top.svg").stat().st_size, 100000)

    def test_factory_motors_and_props_specified_separately(self):
        index = {r["Designator"]: r for r in self.system}
        self.assertEqual(index["M1-M4"]["Quantity"], "4")
        self.assertIn("ECO223062400", index["M1-M4"]["Manufacturer Part Number"])
        self.assertEqual(index["P1-P4"]["Quantity"], "4")
        self.assertIn("Gemfan", index["P1-P4"]["Manufacturer"])
        self.assertIn("4S", index["BAT1"]["Description"])
        self.assertIn("12", (H / "assembly-wiring.md").read_text())
        modules = (ROOT / ".gitmodules").read_text()
        for name in ("esc-4in1/KiCad-Library", "flight-controller-openfc-lite",
                     "frame-openframe-5f"):
            self.assertIn(name, modules)


if __name__ == "__main__":
    unittest.main()
