"""Recreate the exact source variants evaluated in pose-checks.json."""
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output_dir", type=Path)
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
base = (HERE / "labwired-gameboy-assembly.kcad.ts").read_text()
cases = []
for name in ["btn-up", "btn-down", "btn-left", "btn-right", "btn-a", "btn-b", "btn-select", "btn-start"]:
    source = base.replace("param('pressedControl','rest'", f"param('pressedControl','{name}'")
    source = source.replace("param('travelCase','nominal'", "param('travelCase','maximum'")
    cases.append((name, source))
source = base.replace("const screw=(await lib.part(", "let screw=(await lib.part(")
source = source.replace("addFixed(`${name}-screw`,screw.finish", "if(name.startsWith('case-'))screw=screw.union(cylinder(10.1,F.driverShaftReservationDiameterMm/2).translate(x,y,seat+F.headHeightMm-0.1));\n addFixed(`${name}-screw`,screw.finish")
cases.append(("case-driver-access", source))
source = base.replace("box(usb.plugOvermoldMm[0],usb.plugOvermoldMm[1],usb.plugOvermoldMm[2]", "box(usb.plugOvermoldMm[0],usb.plugOvermoldMm[1]+30,usb.plugOvermoldMm[2]")
source = source.replace("cylinder(usb.strainReliefLengthMm,usb.cableDiameterMm/2)", "cylinder(usb.strainReliefLengthMm+30,usb.cableDiameterMm/2)")
cases.append(("usb-overmold-withdrawal", source))
expected = {c["id"]: c["evaluationEvidence"]["source"]["sha256"] for c in json.loads((HERE / "pose-checks.json").read_text())["checks"]}
records = []
for name, source in cases:
    digest = hashlib.sha256(source.encode()).hexdigest()
    assert digest == expected[name], f"{name}: source changed; reevaluate before refreshing evidence"
    path = args.output_dir / f"{name}.kcad.ts"
    path.write_text(source)
    records.append({"id": name, "file": path.name, "sha256": digest, "bytes": len(source.encode())})
(args.output_dir / "cases.json").write_text(json.dumps(records, indent=2) + "\n")
print(json.dumps({"matchedEvaluatedSources": len(records), "outputDirectory": str(args.output_dir)}))
