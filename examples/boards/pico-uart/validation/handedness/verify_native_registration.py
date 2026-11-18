#!/usr/bin/env python3
"""Compare native KiCad pad centres with independently inspected STEP axes.

Run with the KiCad 10 Python module available:
  python3 verify_native_registration.py --kind oled --package /absolute/package/path
The OCCT inspection and evaluation receipts are immutable inputs to this check.
"""
from pathlib import Path
import argparse, hashlib, json, math, re
import pcbnew

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    value=json.loads(path.read_text())
    return value.get("structuredContent",value)
def area(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def nearest(holes,point,diameter,axes=(0,1)):
    candidates=[h for h in holes if abs(h["diameterMm"]-diameter)<0.0001]
    assert candidates,("no matching diameter",diameter,point)
    found=min(candidates,key=lambda h:sum((h["axisOrigin"][i]-point[i])**2 for i in axes))
    error=math.sqrt(sum((found["axisOrigin"][i]-point[i])**2 for i in axes))
    return found,error
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--kind",choices=["oled","pico"],required=True)
    ap.add_argument("--package",type=Path,required=True)
    args=ap.parse_args(); p=args.package.resolve();kind=args.kind
    if kind=="oled":
        evidence=p/"cad/verification/handedness";source=p/"cad/esp32c3-oled-enclosure.kcad.ts"
        pcb=p/"electronics/oled-carrier.kicad_pcb";step=p/"cad/inputs/47111971a61f.step"
        ordered=["J2.1","J2.2","J3.7"];expected_count=18
    else:
        evidence=p/"validation/handedness";source=p/"mechanical/pico-uart-fixture.kcad.ts"
        pcb=p/"electronics/pico-carrier.kicad_pcb";step=p/"cad/pico-carrier.step"
        ordered=["J1.1","J1.2","J2.1"];expected_count=47
    inspection=read(evidence/"native-carrier-inspection.json")
    assert inspection["ok"] and inspection["report"]["solidCount"]==1
    native=inspection["report"]["solids"][0]
    assert native["brepCheck"]=="valid"
    holes=native["holes"];board=pcbnew.LoadBoard(str(pcb));pads=[]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            drill=pad.GetDrillSize();d=pcbnew.ToMM(drill.x)
            if d<=0:continue
            assert abs(drill.x-drill.y)<1,("noncircular pad unsupported",fp.GetReference(),pad.GetNumber())
            pos=pad.GetPosition();x,y=pcbnew.ToMM(pos.x),pcbnew.ToMM(pos.y)
            world=[x,-y,8];hole,error=nearest(holes,world,d)
            assert error<0.0001,(fp.GetReference(),pad.GetNumber(),error)
            pads.append({"pad":fp.GetReference()+"."+pad.GetNumber(),"net":pad.GetNetname(),
                         "editorXY":[x,y],"worldXY":[x,-y],"drillMm":d,
                         "nativeStepAxis":hole["axisOrigin"],"axisXYErrorMm":error})
    pads.sort(key=lambda x:x["pad"]);assert len(pads)==expected_count,len(pads)
    lookup={r["pad"]:r for r in pads}
    signed=area(*(lookup[k]["worldXY"] for k in ordered))
    old_signed=area(*(lookup[k]["editorXY"] for k in ordered))
    assert signed>0 and old_signed<0 and abs(signed+old_signed)<1e-8
    source_text=source.read_text()
    carrier_line=next(l for l in source_text.splitlines() if l.startswith("const carrier="))
    assert ".scale([1,1,1.6/1.51]).translate(0,0,boardZ)" in carrier_line
    assert ".rotate" not in carrier_line and ".reflect" not in carrier_line
    evaluated=read(evidence/"evaluation.json")
    requirements=evaluated["requirements"]["entries"]
    assert evaluated["buildOk"] and evaluated["requirements"]["ok"]
    assert len(requirements)==12 and all(e["status"]=="pass" for e in requirements)
    witnesses=[e for e in requirements if e["name"].startswith("native-") and e["name"]!="native-carrier-size"]
    result={"schemaVersion":1,"kind":kind,"status":"pass","scope":"Native source/STEP coordinate registration; no physical test.",
      "pcbnewVersion":pcbnew.GetBuildVersion(),"worldFrame":{"x":"editor X","y":"negative editor Y","z":"up",
      "nativeBoardPopulatedSide":"+Z","carrierUndersideZMm":8,"carrierFinishedThicknessMm":1.6},
      "inputs":{"nativePcb":{"path":str(pcb.relative_to(p)),"sha256":sha(pcb)},
        "nativeStep":{"path":str(step.relative_to(p)),"sha256":sha(step)},
        "portableCadSource":{"path":str(source.relative_to(p)),"sha256":sha(source)},
        "submittedCadSource":{"path":str((evidence/"submitted-source.kcad.ts").relative_to(p)),"sha256":sha(evidence/"submitted-source.kcad.ts")},
        "nativeInspectionSha256":sha(evidence/"native-carrier-inspection.json"),
        "evaluationSha256":sha(evidence/"evaluation.json"),
        "evaluatedStagedSource":evaluated["evaluationEvidence"]["source"]},
      "nativePadCount":len(pads),"maximumAxisXYErrorMm":max(r["axisXYErrorMm"]for r in pads),"pads":pads,
      "orientationWitness":{"orderedPads":ordered,"signedAreaTwiceMm2":signed,
        "historicalEditorPositiveYWithComponentsUp":old_signed,
        "conclusion":"Keeping populated side +Z requires world Y=-editorY. The historical positive-Y reconstruction reverses this signed orientation."},
      "nativeRequirements":witnesses,"physicalHardwareTested":False}
    if kind=="pico":
        vendor_path=p/"references/raspberry-pi/Pico-R3.step"
        vendor=read(evidence/"native-pico-inspection.json")["report"]
        assert vendor["solidCount"]==17 and all(s["brepCheck"]=="valid" for s in vendor["solids"])
        vendor_holes=vendor["solids"][0]["holes"]
        assembled=read(evidence/"assembly-step-inspection.json")["report"]
        assert assembled["solidCount"]==50 and all(s["brepCheck"]=="valid" for s in assembled["solids"])
        board_solids=[s for s in assembled["solids"] if s["faceCount"]==450 and abs(s["bboxExact"]["min"][0]-19.5)<0.0001]
        assert len(board_solids)==1
        export_holes=board_solids[0]["holes"];matches=[]
        for row,native_x in [("J1",1.61),("J2",19.39)]:
            for index in range(1,21):
                native_point=[native_x,-.5,-49.63+2.54*(index-1)]
                hole,error=nearest(vendor_holes,native_point,1,axes=(0,2))
                assert error<0.0001,(row,index,"native",error)
                # Proper Rx(+90 degrees), then translation. Determinant is +1.
                origin=hole["axisOrigin"];actual=[origin[0]+19.5,-origin[2]-57,origin[1]+21.15]
                expected=lookup[row+"."+str(index)]["worldXY"]
                pin_error=math.dist(actual[:2],expected)
                assert pin_error<0.0001,(row,index,"placement",pin_error)
                exported,export_error=nearest(export_holes,actual,1)
                assert export_error<0.0001,(row,index,"export",export_error)
                matches.append({"carrierPad":row+"."+str(index),"picoPhysicalPin":index if row=="J1" else 41-index,
                    "vendorAxis":origin,"worldAxis":actual,"exportedAxis":exported["axisOrigin"],
                    "carrierAxisErrorMm":pin_error,"exportedAxisErrorMm":export_error})
        assert ".rotateX(90).translate(19.5,-57,moduleMidZ)" in source_text
        assert ".rotateZ(180)" not in source_text
        pos=read(evidence/"registration-positive.json")
        neg=read(evidence/"registration-mirrored-negative.json")
        assert pos["requirements"]["ok"]
        failed=[e for e in neg["requirements"]["entries"] if e["status"]=="fail"]
        assert len(failed)==1 and "led" in failed[0]["name"].lower(),failed
        result["pico"]={"vendorStepSha256":sha(vendor_path),"vendorSolids":17,"assemblySolids":50,
            "rotationMatrix":[[1,0,0],[0,0,-1],[0,1,0]],"rotationDeterminant":1,
            "translationMm":[19.5,-57,21.15],"populatedNormalBefore":[0,1,0],"populatedNormalAfter":[0,0,1],
            "matchedHeaderAxes":matches,"headerAxisCount":len(matches),
            "asymmetricNegativeControl":{"receipt":"registration-mirrored-negative.json","sha256":sha(evidence/"registration-mirrored-negative.json"),
            "failedRequirements":failed,"finding":"The mirrored row swap passes the symmetric hole gauges but fails the native LED position."},
            "historicalPin1":{"worldXY":[38.89,7.37],"carrierJ1Pin1EditorXY":[21.11,7.37],"rowErrorMm":17.78}}
    else:
        neg=read(evidence/"negative-old-carrier.json")
        failed=[e for e in neg["requirements"]["entries"] if e["status"]=="fail" and e["name"].startswith("native-carrier-registration")]
        assert len(failed)==3,len(failed)
        result["historicalCarrierNegativeControl"]={"receipt":"negative-old-carrier.json",
           "sha256":sha(evidence/"negative-old-carrier.json"),"failedRequirements":failed}
    target=evidence/"native-registration.json";target.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"kind":kind,"nativePadCount":len(pads),"maximumAxisXYErrorMm":result["maximumAxisXYErrorMm"],
       "signedAreaTwiceMm2":signed,"headerAxisCount":result.get("pico",{}).get("headerAxisCount"),"receipt":str(target)}))
if __name__=="__main__":main()
