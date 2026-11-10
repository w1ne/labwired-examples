# Historical revision 2 packaging concept

The current assembly is [revision 3](revision-3/README.md), pinned by `../kernelcad-reference.json`. This directory preserves revision 2's source and evidence for reproducibility. Its old USB extension assumption, export counts and interference results do not describe revision 3.

Revision 2 is an evaluated, static packaging concept for the LabWired Game Boy recreation. It is generated from the shared `../design-interfaces.json`, which defines the intended carrier PCB outline, mounting holes, LCD envelope, controls, and connector aperture.

## Model and files

Studio project: https://app.kernelcad.com/p/kQAFdaQs?version=2

The revision-pinned embed URL and model identity are in `kernelcad-reference-v2.json`. The source is `labwired-gameboy.kcad.ts`. Regenerate it with `python3 generate_enclosure.py` after an interface change, then evaluate it through KernelCAD before replacing the saved revision.

The compact Git contribution keeps editable CAD and validation records. Generated STEP, GLB and STL files are omitted. The recorded export set contains 15 bodies: 9 fabrication candidates (front shell, rear shell, service cover, bezel, D-pad, A, B, Start and Select), 5 component envelopes, and 1 active-glass reference. The 6 reference bodies are not fabrication parts.

`enclosure-v2-iso.png` is a deterministic render of the evaluated revision 2 geometry. The screen is a material surface; it does not show live firmware output.

## Geometry

| Item | Value |
| --- | --- |
| Shell | 90 × 148 × 30 mm |
| Overall, including controls | 90 × 148 × 32.3 mm |
| Default wall | 2.4 mm |
| Shell seam gap | 0.25 mm |
| Intended carrier outline | 78 × 132 mm, 1.6 mm thick |
| Carrier mounting holes | Ø2.8 mm at x = ±29 mm, y = 16 and 132 mm |
| Case post clearances in carrier | Radius 4.3 mm at x = ±36 mm, y = 12 and 136 mm |
| Display | Waveshare 2.4-inch ILI9341 module, landscape |
| Display PCB outline | 70.50 × 43.30 mm |
| Display active area | 48.96 × 36.72 mm |

Revision 2 moves the four carrier mounts inward. The minimum planar material gap between a carrier hole and its adjacent case-post notch is 2.362 mm. The top USB opening assumes a panel-mounted extension to the rear-mounted Black Pill; it does not align directly with the board connector.

Coordinates use millimetres. The origin is the rear bottom centre. X points right, Y points toward the top, and Z points toward the front. Display XY dimensions come from the [Waveshare module documentation](https://www.waveshare.com/wiki/2.4inch_LCD_Module). Module height, connector clearance, and screen mounting details require the supplier drawing or measurement before manufacture.

## Recorded results

`evidence-v2.json` contains the revision 2 tool results. `independent-mates.json` records a separate review of the same source: validator solved, 15 parts, 14 fixed mates, one static pose, and zero detected interference. The review reports 28 informational notices because point-based connectors cannot compare hole diameters through feature records. This does not establish fastener engagement or physical fit. KernelCAD design-loop validation passed with no detected static interference. STEP reinspection found 15 valid BREP solids. All 15 exported STL bodies were watertight. The aggregate modeled volume is 142,870.5896 mm³; it includes the component envelopes and is not a plastic usage estimate.

The assembly-path tool run on revision 1 exhausted its work budget and returned unknown results. Assembly sequence, screw selection, fastener engagement, button travel, retention of the service cover, and physical fit are unverified. The battery and speaker are reserved volumes. The rear-mounted Black Pill headers, their solder joints, and the USB extension cable are not represented as solid envelopes in this assembly. Their clearances must be checked against the final carrier and selected parts. A battery circuit has not been established by this mechanical model.

The hosted PCB generator initially returned a different 123 × 88 mm board with a placeholder MCU footprint. That board does not fit this case. Only a carrier derived from `design-interfaces.json` can be compared against this model. Do not report the initial generated PCB as a matched mechanical assembly.

All 17 revision 2 exports were downloaded and checked against the tool-reported byte counts and SHA-256 hashes. `download-verification-v2.json` preserves that evidence; export binaries are omitted here. The raw tool record may contain expiring export URLs. To regenerate exports, evaluate this source in KernelCAD, review its mates and static interference, then export the assembly or selected fabrication bodies.
