# Native FC mechanical inputs

These immutable exports come from the repaired OpenFC Lite revision 2-LW1 PCB, SHA-256 `9794ec1a2bfd07f7c33a1332debaf3d785ecb83a07c5866d0d7432cb20ef07db`, with KiCad 10.0.8. The electrical repair evidence is in the parent directory. This checkpoint prepares geometry for the assembly fit check; it does not claim that check has passed.

The native outline is scalloped and 1.0 mm thick. Its four nominal 4 mm mounting cutouts have 30.5 mm center spacing. The export origin is the mounting-pattern center, `(153.0912, 87.1597)` mm in the source board. STEP/STL output keeps KiCad's native millimetre/Z-up coordinates. The component mesh has 47,786 source facets; conversion to binary STL retains each facet and has less than 0.000001 mm float32 coordinate rounding.

All 107 enabled component-model entries resolve. Seventeen standard STEP files are preserved under `../reviewed-models` with exact upstream commits, SHA-256 digests and the KiCad library license. Original custom model references use their matching STEP assets from the unchanged pinned hardware source. The 53 bare solder contacts and four testpoints have no separate component bodies. L1/L2/L3 retain the source-assigned Murata/Changjiang package proxies; these are nominal geometry, not exact manufacturer models for the populated inductors.

`model-resolution-review.json` binds every reference and pose to its asset hash. `export-result.json` retains the exact original tool commands and frozen output hashes. `fc-substrate.step` is the actual board body; `fc-populated.step` includes the assigned component solids; `fc-components.stl` contains only the component mesh. No model was shifted or shrunk to improve a clearance result. The repaired source's explicit Card1 unused-pad omission remains.

OpenFC-derived hardware remains under the parent CERN-OHL-S-2.0 license. The redistributed stock model collection retains its separate KiCad license and attribution.
