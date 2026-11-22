#!/usr/bin/env python3
"""Recompute the mass budget and limited static-aerodynamic reference.

Uses recorded kernelCAD BREP measurements. Does not create a flight simulation,
assign mass to installation envelopes, or treat missing measurements as zero.
Run: python3 calculate-mass-stability.py [--measurements measured-mass-inputs.json]
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
def read(name):
    return json.loads((HERE / name).read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def aggregate(rows):
    total = sum(r["mass_g"] for r in rows)
    first = [sum(r["mass_g"] * r["com_mm"][i] for r in rows) for i in range(3)]
    if not math.isfinite(total) or total <= 0 or not all(math.isfinite(v) for v in first):
        raise ValueError("Aggregate mass must be positive and mass moments must be finite")
    return {"mass_g": total, "first_moment_g_mm": first,
            "com_mm": [v / total for v in first]}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--measurements", type=Path)
parser.add_argument("--output", type=Path, default=HERE / "mass-stability-review.json")
args = parser.parse_args()
geometry = read("mass-geometry-components.json")
source = (HERE / "pathfinder-extended.kcad.ts").read_text()
if sha(HERE / "pathfinder-extended.kcad.ts") != geometry["source_sha256"]:
    raise ValueError("Actual CAD source hash differs from the recorded geometry")
pcb_sha256 = sha(HERE / "routing/pathfinder-routed.kicad_pcb")
drill_projection = read("pcb-cad-drill-parity-review.json")
if (drill_projection.get("source_sha256") != geometry["source_sha256"]
        or drill_projection.get("pcb_sha256") != pcb_sha256):
    raise ValueError("Drill projection review must bind this exact CAD and native PCB")
if (drill_projection.get("one_to_one") is not True
        or drill_projection.get("counts") != {"pad": 100, "cutout": 8, "via": 65}
        or drill_projection["max_tuple_delta_mm"] > 0.0005 + 1e-12):
    raise ValueError("Drill projection exceeds its reviewed 0.0005 mm coordinate bound")
assert geometry["all_other_shape_constructions_byte_identical"] is True
stats = read("mass-geometry-part-stats.json")["inspection"]["parts"]
nominal = []
for row in geometry["geometry_rows"]:
    m = row["response"]["massProperties"]
    assert row["response"]["ok"] and m["mass"] > 0 and not m["densityDefaulted"]
    nominal.append({"name": row["name"], "volume_mm3": m["volume"],
                    "density_kg_m3_assumed": m["density"],
                    "mass_g": m["mass"] * 1000, "com_mm": m["com"]})
assert len(nominal) == 17 and len({r["name"] for r in nominal}) == 17
raw_nominal = aggregate(nominal)

# The original bulkhead solids fuse a plywood disk with a rod-shaped attachment
# placeholder. Keep only the disk in the material budget; actual metal hardware
# remains an independent unknown. Never count the rod as 680 kg/m3 plywood.
disk_volume = math.pi * 19**2 * 4
budget = [dict(r) for r in nominal]
for row in budget:
    if row["name"] in ("bulkhead-aft", "bulkhead-fwd"):
        row.update(volume_mm3=disk_volume, mass_g=disk_volume * 680 / 1e6,
                   com_mm=[0., 0., 232. if row["name"] == "bulkhead-aft" else 478.])
        row["scope"] = "Plywood disk only; attachment hardware excluded."
base = aggregate(budget)

# Exact external 24-segment nose profile used by this CAD source. Its internal
# hollow and shoulder do not affect this external displaced-volume calculation.
assert "const L = 160" in source and "i <= 24" in source
assert ".lineTo(R, 95).lineTo(R + 40, 55).lineTo(R + 40, 10)" in source
diameter, radius, nose_length, tip_z = 42., 21., 160., 800.
rho = (radius**2 + nose_length**2) / (2 * radius)
profile = [(nose_length * i / 24,
            max(math.sqrt(rho**2 - (nose_length - nose_length * i / 24)**2)
                + radius - rho, 0.)) for i in range(25)]
outer_volume = sum(math.pi * (x1-x0) * (r0*r0 + r0*r1 + r1*r1) / 3
                   for (x0,r0),(x1,r1) in zip(profile, profile[1:]))
nose_cp_from_tip = nose_length - outer_volume / (math.pi * radius**2)
nose_cp_z = tip_z - nose_cp_from_tip
root_chord, tip_chord, span, sweep, fin_count = 90.,45.,40.,40.,3
half_chord_length = math.hypot(span, sweep + (tip_chord-root_chord)/2)
fin_slope_alone = 4*fin_count*(span/diameter)**2 / (
    1 + math.sqrt(1+(2*half_chord_length/(root_chord+tip_chord))**2))
interference = 1 + radius / (span+radius)
fin_slope = fin_slope_alone * interference
fin_cp_from_root_le = sweep/3*(root_chord+2*tip_chord)/(root_chord+tip_chord) + (
    root_chord**2+tip_chord**2+root_chord*tip_chord)/(6*(root_chord+tip_chord))
fin_cp_z = 95 - fin_cp_from_root_le
reference_cp_z = (2*nose_cp_z + fin_slope*fin_cp_z)/(2+fin_slope)
# Algebraic limiting checks independent of the CAD mass calculation.
assert math.isclose(nose_length - (math.pi*radius**2*nose_length/3) /
                    (math.pi*radius**2), 2*nose_length/3, abs_tol=1e-10)
assert math.isclose(fin_cp_from_root_le, 35.27777777777778, abs_tol=1e-10)
targets = [{"margin_cal": c, "required_cg_z_mm": reference_cp_z+c*diameter}
           for c in (1.,1.5,2.)]
aft_budgets = [
    {"target_margin_cal": t["margin_cal"], "added_point_mass_z_mm": z,
     "maximum_added_point_mass_g": base["mass_g"] *
       (base["com_mm"][2]-t["required_cg_z_mm"]) / (t["required_cg_z_mm"]-z)}
    for t in targets for z in (0.,43.5)
]
modelled_names = {r["name"] for r in nominal}
service_names = {"battery-pigtail-service-envelope", "power-harness-service-envelope"}
excluded_names = modelled_names | service_names | {"launch-pad-rail"}
purchased = [p for p in stats if p["name"] not in excluded_names]
assert len(purchased) == 46
# Reflect the final moved R1 envelope; no mass is inferred from this box.
envelopes = json.loads(re.search(r"^const envelopes=(.*);$", source, re.M).group(1))
by_name = {e[0]:e for e in envelopes}
inputs = [{"name":r["name"], "category":"fabricated part",
           "mass_g":None, "com_mm":None, "measured":False, "source":None,
           "nominal_geometry_estimate":{"mass_g":r["mass_g"],"com_mm":r["com_mm"]}}
          for r in budget]
for p in purchased:
    bb = p["bbox"]
    if p["name"] == "pcb-r_vbat_hi":
        e = by_name[p["name"]]
        bb = {"min":[e[1],0,e[3]], "max":[e[2],e[5],e[4]]}
    entry = {"name":p["name"],"category":"purchased part or assembly",
             "mass_g":None,"com_mm":None,"measured":False,"source":None,
             "installation_bounds_mm":bb,
             "bounds_are_not_mass_or_centroid_measurements":True}
    if p["name"] == "battery-tattu-450mah-envelope":
        entry["catalog_nominal_mass_g"] = 12
        entry["catalog_source"] = "battery-current-review.json"
    inputs.append(entry)
for name in ("actual battery pigtail and connector", "actual power and signal harness",
             "aft bulkhead attachment hardware", "forward bulkhead attachment hardware",
             "PCB copper, via plating, solder and finishes",
             "other adhesives, fasteners and retention parts"):
    inputs.append({"name":name,"category":"unmodelled installed material",
                   "mass_g":None,"com_mm":None,"measured":False,"source":None})
template = {"source_sha256":geometry["source_sha256"],
            "datum":"mm; z=0 at aft body-tube end; +z points to tip at 800 mm",
            "notes":["Measure installed assemblies without counting the same part twice.",
                     "PCB module masses must include their fitted headers and storage card.",
                     "State loaded and burned-out motor mass/CG in separate measurement files.",
                     "Zero mass requires a source explaining why that item is absent.",
                     "Density-derived CAD estimates are not populated as measurements."],
            "entries":inputs}
template_path = HERE / "mass-inputs.template.json"
if not template_path.exists():
    template_path.write_text(json.dumps(template,indent=2)+"\n")
physical = {"mass_g":None, "com_mm":None,"reference_static_margin_cal":None,
            "status":"incomplete: installed mass and centroid inputs are unmeasured"}
if args.measurements:
    measured = json.loads(args.measurements.read_text())
    if not isinstance(measured, dict) or measured.get("source_sha256") != geometry["source_sha256"]:
        raise ValueError("Measurement source hash must match the CAD source")
    items = measured.get("entries")
    expected_names = {r["name"] for r in inputs}
    if (not isinstance(items, list) or len(items) != len(inputs)
            or not all(isinstance(r, dict) and isinstance(r.get("name"), str) for r in items)
            or {r["name"] for r in items} != expected_names):
        raise ValueError("Duplicate, missing or unknown mass-budget entries")
    for r in items:
        mass = r.get("mass_g")
        if type(mass) not in (int, float) or not math.isfinite(mass) or mass < 0:
            raise ValueError(r["name"] + ": mass_g must be a finite nonnegative number, not a boolean")
        com = r.get("com_mm")
        if (not isinstance(com, list) or len(com) != 3
                or not all(type(v) in (int, float) and math.isfinite(v) for v in com)):
            raise ValueError(r["name"] + ": com_mm needs three finite numbers, not booleans")
        if type(r.get("measured")) is not bool:
            raise ValueError(r["name"] + ": measured must be a JSON boolean")
        if not isinstance(r.get("source"), str) or not r["source"].strip():
            raise ValueError(r["name"] + ": each mass/centroid needs nonempty text provenance")
    totals = aggregate(items)
    physical = {**totals,
                "reference_static_margin_cal":(totals["com_mm"][2]-reference_cp_z)/diameter,
                "status":"measured inputs" if all(r["measured"] is True for r in items) else "input estimates",
                "measurement_status_basis":"Caller-declared boolean flags and per-entry provenance; measurements are not independently verified by this calculator.",
                "measurement_file_sha256":sha(args.measurements)}
report = {
 "status":"geometry-derived budget complete; physical mass and full-airframe stability open",
 "source_sha256":geometry["source_sha256"],
 "pcb_sha256":pcb_sha256,
 "routed_via_count":65,
 "pcb_cad_drill_projection":{"pad_holes":100,"cutouts":8,"vias":65,"one_to_one":True,
   "max_center_rounding_difference_mm":0.0005,
   "scope":"All 173 drill/cutout shapes map one-to-one. Ten J3/J4/J6 pad-hole centers differ by 0.0005 mm between the CAD and native coordinates; do not claim exact coordinate parity.",
   "receipt":"pcb-cad-drill-parity-review.json"},
 "datum":template["datum"],
 "raw_nominal_17_solid_CAD_estimate_not_flight_mass":raw_nominal,
 "fabricated_material_estimate_excluding_attachment_placeholders":base,
 "fabricated_material_rows":budget,
 "physical_assembly":physical,
 "mass_budget":{"unmeasured_purchased_bodies":46,"measurement_entries":len(inputs),
   "excluded_massless_geometry":["launch-pad-rail",*sorted(service_names)],
   "template":"mass-inputs.template.json",
   "formula":"CG = (sum of nominal material first moments + sum(m_i * r_i)) / (nominal material mass + sum(m_i)); replace every nominal term with measured values for a physical result.",
   "limitations":["1000 kg/m3 tube, 680 kg/m3 plywood, 1850 kg/m3 substrate, 1380 kg/m3 PETG and 2700 kg/m3 aluminium are inherited model assumptions.",
     "PETG density does not specify slicer infill, print voids, coatings or actual material density.",
     "Motor, camera, switch, parachute and cord density stand-ins are excluded from the physical budget.",
     "Installation envelopes provide space; no density or mass is assigned to them.",
     "Via holes remove 0.0845057008 g from the nominal substrate. Copper and via plating are separate unknown mass."]},
 "static_aerodynamics_reference":{"method":"Barrowman low-Mach, small-angle reference for the axisymmetric body and 3 uncanted fins only",
   "body_diameter_mm":diameter,"nose_external_displaced_volume_mm3":outer_volume,
   "nose_cp_from_tip_mm":nose_cp_from_tip,"nose_cp_z_mm":nose_cp_z,"nose_normal_force_slope_per_rad":2,
   "fin_root_chord_mm":root_chord,"fin_tip_chord_mm":tip_chord,"fin_span_mm":span,
   "fin_sweep_mm":sweep,"fin_count":fin_count,"fin_body_interference_factor":interference,
   "fin_normal_force_slope_per_rad":fin_slope,"fin_cp_z_mm":fin_cp_z,
   "reference_cp_z_mm":reference_cp_z,
   "margin_formula":"(CG_z - reference_CP_z) / 42",
   "cg_targets_reference_only":targets,
   "aft_point_mass_sensitivity_reference_only":aft_budgets,
   "sensitivity_scope":"Illustrative extra point mass applied to the nominal fabricated-material baseline, with all other unknown masses omitted; not a permitted payload or motor selection.",
   "full_airframe_cp_mm":None,
   "limitations":["The side-mounted camera pod violates axial symmetry; its aerodynamic force, moment and interference are not qualified.",
     "Rail buttons, switch, gaps, surface finish, wind and finite angle-of-attack effects are omitted.",
     "Body lift and CP shift with flight condition can change the result; this is not a dynamic-stability or rail-exit check.",
     "Loaded and burnout mass distributions, lateral CG, motor thrust curve and actual aerodynamic inputs remain unmeasured."]},
 "flight_acceptance":{"accepted":False,"mass_and_CG_measured":physical["status"] == "measured inputs",
    "complete_airframe_aerodynamics_qualified":False,"new_trajectory_computed":False,
    "historical_flight_fixture_applies":False,
    "historical_values_not_carried_forward":["351 g launch mass","320 mm launch CG",
        "2.55/3.17 caliber launch/burnout margins","364 m apogee and 15 m/s rail exit"]},
 "sources":[
   {"url":"https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/rocket-center-of-gravity/","use":"mass-weighted center of gravity and empirical balance"},
   {"url":"https://www.nasa.gov/wp-content/uploads/2023/11/sl-video-instruction-book.pdf","use":"pages 41-43: small-angle/axial-symmetry assumptions, fin equations and static-margin definition"},
   {"url":"https://openrocket.sourceforge.net/techdoc.pdf","edition":"2013-05-10","use":"equations 3.28-3.29, 3.34 and 3.55-3.56: displaced-volume nose CP, coefficient-weighted CP, fin location and body-interference correction"},
   {"url":"https://github.com/w1ne/kernelCAD-web/blob/9a73bbd3603217aa51d09789ef32c5fff6411fa2/src/shared/materials/materialCatalog.ts","use":"provenance of inherited kernel material defaults; not production-material measurements"}],
 "evidence":{"geometry_components_sha256":sha(HERE/"mass-geometry-components.json"),
             "historical_part_stats_sha256":sha(HERE/"mass-geometry-part-stats.json"),
             "calculator_sha256":sha(Path(__file__)),
             "drill_projection_review_sha256":sha(HERE/"pcb-cad-drill-parity-review.json")}}
args.output.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"report":str(args.output),"nominal_material_mass_g":base["mass_g"],
                  "nominal_material_cg_mm":base["com_mm"],
                  "axisymmetric_reference_cp_z_mm":reference_cp_z,
                  "physical_mass_g":physical["mass_g"],"flight_accepted":False},indent=2))
