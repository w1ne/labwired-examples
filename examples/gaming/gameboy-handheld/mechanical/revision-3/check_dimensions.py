"""Record independent nominal stack calculations, not manufacturing acceptance."""
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
cfg = json.loads((HERE / "assembly-config.json").read_text())
interfaces = json.loads((ROOT / "design-interfaces.json").read_text())
derived_file = json.loads((HERE / "derived-interfaces.json").read_text())
derived = derived_file["derived"]
pcb = interfaces["pcb"]
case = interfaces["case"]
header = derived["header"]
module = cfg["module"]
switch = cfg["switch"]
fastener = cfg["fasteners"]
usb = cfg["directUsb"]

def rounded(value):
    return round(value, 6)

top = pcb["center"][2] + pcb["thickness"] / 2
bottom = pcb["center"][2] - pcb["thickness"] / 2
module_front = bottom - header["bodyHeightMm"]
module_back = module_front - module["boardThicknessMm"]
post_tip = bottom + header["postLengthMm"]
usb_center_z = module_back - usb["receptacleHeightMm"] / 2
usb_mouth_y = derived["moduleCenter"][1] + module["boardLengthMm"] / 2
usb_shoulder_y = usb_mouth_y + usb["shoulderBeyondMatingPlaneMm"]
lcd_bottom = cfg["displayStack"]["pcbBottomZ"]
tip_at_rest = top + switch["heightMm"] + switch["freeGapMm"]
max_press = switch["freeGapMm"] + switch["pretravelMm"]["maximum"]

stations = []
for mount in interfaces["caseFasteners"] + pcb["mounts"]:
    is_case = mount["id"].startswith("case-")
    lower = mount["at"][1] < case["height"] / 2
    seat = fastener["caseHeadSeatZ"] if is_case else (
        switch["supportPlateBottomZ"] + switch["supportPlateThicknessMm"] if lower else top)
    length = fastener["caseScrewLengthMm"] if is_case else (
        fastener["pcbBottomScrewLengthMm"] if lower else fastener["pcbTopScrewLengthMm"])
    nut_top = fastener["caseNutTopZ"] if is_case else fastener["pcbNutTopZ"]
    nut_top -= 0.05  # unloaded axial pocket allowance in the authored rest pose
    nut_bottom = nut_top - fastener["nutHeightMm"]
    tip = seat - length
    bore_bottom = fastener["caseBoreBottomZ"] if is_case else (
        fastener["pcbBottomBoreBottomZ"] if lower else fastener["pcbTopBoreBottomZ"])
    stations.append({"id": mount["id"], "lengthMm": length,
        "headSeatZ": seat, "tipZ": rounded(tip), "nutZ": [rounded(nut_bottom), rounded(nut_top)],
        "axialEngagementMm": rounded(max(0, min(seat, nut_top) - max(tip, nut_bottom))),
        "tipProtrusionMm": rounded(nut_bottom - tip), "blindBoreTipClearanceMm": rounded(tip - bore_bottom)})

dpad = next(c for c in interfaces["controls"] if c["kind"] == "cross")
poses = []
for control in derived["switches"]:
    item = {"id": control["id"], "switchCenterMm": control["center"],
            "maximumSpecifiedPretravelMm": switch["pretravelMm"]["maximum"]}
    if control["id"] in ["btn-up", "btn-down", "btn-left", "btn-right"]:
        radius = math.dist(control["center"], dpad["center"][:2])
        vertical = switch["dpadPivotCenterZ"] - tip_at_rest - switch["plungerRadiusMm"]
        angle = math.asin((vertical + max_press) / math.hypot(radius, vertical)) - math.atan2(vertical, radius)
        drop = radius * math.sin(angle) - vertical * (1 - math.cos(angle))
        item.update({"leverRadiusMm": radius, "rotationDegrees": rounded(math.degrees(angle)),
                     "sphereTipDescentMm": rounded(drop)})
    else:
        item["capTranslationMm"] = rounded(max_press)
    poses.append(item)

clearances = {
    "header": {
        "collarHeightMm": header["bodyHeightMm"], "moduleHeaderFaceZ": rounded(module_front),
        "moduleComponentFaceZ": rounded(module_back), "postTipZ": rounded(post_tip),
        "fullPinProtrusionAboveCarrierMm": rounded(post_tip - top),
        "pinToLcdUndersideMm": rounded(lcd_bottom - post_tip),
        "componentEnvelopeToRearFloorMm": rounded(module_back - module["componentHeightAllowanceMm"] - case["wall"]),
        "moduleTailTipZ": rounded(module_front - header["tailLengthMm"]),
        "pinDiagonalMm": rounded(header["pinSquareMm"] * math.sqrt(2)),
        "carrierHoleNominalDiametricMarginMm": rounded(header["carrierHoleDiameterMm"] - header["pinSquareMm"] * math.sqrt(2)),
        "moduleHoleBasis": module["holeDiameterBasis"],
        "physicalFit": "unverified; pin, finished-hole and module tolerances are not established"
    },
    "usb": {
        "mouthYAssumption": rounded(usb_mouth_y), "centerZAssumption": rounded(usb_center_z),
        "mouthToInsideWallMm": rounded(case["height"] - case["wall"] - usb_mouth_y),
        "mouthToOutsideWallMm": rounded(case["height"] - usb_mouth_y),
        "overmoldShoulderYAssumption": rounded(usb_shoulder_y),
        "overmoldInsertionPastOutsideWallMm": rounded(case["height"] - usb_shoulder_y),
        "openingSideClearanceMm": rounded((usb["openingMm"][0] - usb["plugOvermoldMm"][0]) / 2),
        "openingVerticalClearanceMm": rounded((usb["openingMm"][1] - usb["plugOvermoldMm"][2]) / 2),
        "overmoldToRearFloorMm": rounded(usb_center_z - usb["plugOvermoldMm"][2] / 2 - case["wall"]),
        "overmoldToCarrierUndersideMm": rounded(bottom - usb_center_z - usb["plugOvermoldMm"][2] / 2),
        "physicalFit": usb["limitation"]
    },
    "buttons": {
        "nominalGapMm": switch["freeGapMm"],
        "nominalCapStrokeMm": rounded(switch["freeGapMm"] + switch["pretravelMm"]["nominal"]),
        "maximumNominalHeightCapStrokeMm": rounded(max_press),
        "minimumHeightWorstCaseStrokeMm": rounded(max_press + switch["heightToleranceMm"]),
        "ordinaryButtonStopTravelMm": switch["roundButtonStopTravelMm"],
        "requiresMeasuredPlungerAdjustment": True,
        "poses": poses, "physicalFit": switch["limitation"]
    },
    "fasteners": stations,
    "fastenerProofLimit": "These are axial calculations. See fastener-installation.json for BREP measurements and unsupported blind/captive-bore results. No thread strength or torque proof.",
    "driver": {"reservedShaftDiameterMm": fastener["driverShaftReservationDiameterMm"],
        "shellCounterboreDiameterMm": 5.1, "bezelScallopDiameterMm": fastener["bezelAccessDiameterMm"],
        "nominalRadialClearanceMm": rounded((5.1 - fastener["driverShaftReservationDiameterMm"]) / 2),
        "limitation": fastener["driverAccessLimitation"]}
}
if "j1" in derived:
    j1 = derived["j1"]
    low, high = j1["bodyBoundsCaseMm"]
    tail_tip = top - j1["terminalTailLengthMm"]
    battery_top = interfaces["battery"]["center"][2] + interfaces["battery"]["size"][2] / 2
    clearances["J1"] = {"bodyBoundsCaseMm": j1["bodyBoundsCaseMm"],
        "matedZ": [top, top + j1["matedHeightMm"]],
        "separationToLcdInYmm": rounded(interfaces["display"]["center"][1] - interfaces["display"]["outline"][1] / 2 - high[1]),
        "wireExitReservationMm": cfg["connectorAccess"]["J1"]["wireExitHeightMm"],
        "tailTipZ": rounded(tail_tip), "tailToBatteryReservationMm": rounded(tail_tip - battery_top),
        "previousPlacementNominalLcdOverlapMm": 0.4,
        "limitation": "Combined nominal header/housing box, straight nominal terminal envelope and reserved wire-exit volume. Retention kinks, exact supplied housing and the harness route are unverified."}

result = {"schema": "labwired.nominal-clearance-ledger.v1", "units": "mm",
    "proofClass": "nominal geometric calculations; no physical fit or manufacturing acceptance",
    "cadSourceSha256": hashlib.sha256((HERE / "labwired-gameboy-assembly.kcad.ts").read_bytes()).hexdigest(),
    "pcbSha256": derived["pcbSha256"], "inputSources": derived_file["sources"],
    "nominalCalculations": clearances, "omissions": cfg["omissions"]}
(HERE / "clearance-ledger.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"pcbSha256": result["pcbSha256"], "header": clearances["header"], "J1": clearances.get("J1")}, indent=2))
