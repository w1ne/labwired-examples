# OLED revision 2: ordered path follow-up

All **39 ordered removal stages** pass nominal geometric checks for the unchanged **41-part** revision 2 assembly. This evidence was recorded after the candidate 2 package checkpoint. The immutable candidate 2 archive, firmware, PCB, CAD source, model revision and exports are unchanged. The complete raw receipt retains original mesh hashes, transforms, the remaining obstacles at every stage, mesh-check findings and native swept-volume measurements.

| Phase | Stages | Result |
| --- | --- | --- |
| Device on held base | 30 | Remove lid screws, the complete lid/OLED module, carrier and retained pins, and mounting hardware. Base remains as fixture. |
| Lid held on bench | 9 | Remove display screws/nuts, then the purchased OLED PCB/glass module. Lid remains as fixture. |

The reverse sequence provides a nominal insertion path. The PCB and glass remain together as a purchased OLED module. Every moving body is checked against all geometry still present. The source parts are not simplified, shrunk or discarded. Conservative native BREP envelopes resolve mesh ambiguity at nominally seated surfaces; the receipt preserves the original mesh findings. The conservative envelope must contain the complete actual source body, and all remaining-obstacle intersections must measure exactly zero. Unknown measurements fail closed.

**Thirteen helper controls pass**, covering actual-part positives, a later obstacle, wrong movement directions, a shifted fastener, an enlarged tool, a source protrusion beyond its envelope and unknown measurements. The final complete run adds a 0.2 mm shifted-screw negative; it blocks with **2.9968 mm³** overlap. The run took **379.861 seconds** on the recorded runtime. The source, runtime and executed helper hashes are in the raw receipts and provenance file.

## Holds, tools and physical limits

The support calculation treats the base and lid as held fixtures. It reports additional holds for the OLED and display screws during device assembly, and the OLED and display nuts during the lid-bench phase. Hold the module and loose hardware until their fasteners engage. The calculation is a mesh support projection; it does not simulate friction, clamping, torque, hand access or counterholding.

The declared 6 mm cylindrical nut driver clears the nominal 6 mm opening with **zero dimensional margin**. The 6.2 mm negative control blocks. A physical driver, its tolerance and access for counterholding still need qualification. The existing cable, USB overmold, spacer engagement, component revision and print-tolerance checks remain open. No physical prototype or print has been tested.

## Acceptance and reproduction

This is independent geometric evidence. The hosted assembly-path tool has not yet accepted the complete assembly and its older blocked/budget receipts remain in the package. These helpers are not integrated into that tool. The result does not grant a hosted verification badge or physical acceptance.

The exact executed harness and BREP helpers use private runtime internals and are retained in the [private measured-evidence commit](https://github.com/w1ne/kernelCAD-server/tree/940e3bce72384399c885a7d14b8b110aeffcf70d/docs/measured-evidence/oled-ordered-path-20261118). The four complete result/control files are included here. `provenance.json` pins every receipt to the unchanged source and model revision.
