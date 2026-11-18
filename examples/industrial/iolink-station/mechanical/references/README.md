# Purchased-board geometry references

`mb1136-milled-board.step` is the native KiCad 10 export of the common ST
MB1136 reference PCB with its factory milling profile restored. It contains
only the board substrate and drilled/milled openings. It is not a populated
NUCLEO-L476RG model or a replacement manufacturing package.

The untouched ST archive is identified in `../../hardware/vendor-sources.json`.
Its `MB1136C/Altium_Designer/MB1136.PcbDoc` has 179 native footprint placements
and no embedded component 3D bodies. KiCad's initial import puts a 70 x 83 mm
bounding rectangle on Edge.Cuts. The real milling geometry remains on
Mechanical 1: 70 x 82.5 mm, with rounded corners, lower tab and ST-LINK
breakaway slots. This matches UM1724 Rev 17, Figure 5. The conversion retains
the three existing 3.2 mm mounting holes and the native 1.59112 mm stack.
The board-only STEP contains the 1.50000 mm substrate. The fitted assembly
uses an explicit positive Z scale of 1.59112/1.5 for the finished-stack
mechanical envelope; it retains native X/Y and the populated-side +Z normal.
The independent native inspection and scaled evaluation are in the evidence
directory. The scale is not a fabricated copper or component model.

`../tools/prepare-mb1136-reference.py` moves those factory milling entities to
Edge.Cuts. It drops one zero-length marker and trims a 0.030 mm line overrun at
the existing lower-tab intersection. The full original coordinates, identities,
repair values, native pad locations, hashes and KiCad version are recorded in
`../../evidence/mechanical/mb1136-native-conversion.json`. The native source
and all electrical placements remain unchanged. No DRC or electrical validation
is asserted for this mechanical reference conversion.

From the package directory, after fetching and unpacking the verified archive:

```sh
kicad-cli pcb import --format altium --output /tmp/mb1136-import.kicad_pcb \
  /path/to/MB1136C/Altium_Designer/MB1136.PcbDoc
/usr/bin/python3 mechanical/tools/prepare-mb1136-reference.py \
  /tmp/mb1136-import.kicad_pcb \
  mechanical/references/mb1136-mechanical-reference.kicad_pcb \
  --receipt evidence/mechanical/mb1136-native-conversion.json
kicad-cli pcb export step --board-only --user-origin 113.5011x64.0036mm \
  --output mechanical/references/mb1136-milled-board.step \
  mechanical/references/mb1136-mechanical-reference.kicad_pcb
```

The STEP uses KiCad's right-handed export frame: X follows factory X and Y is
opposite PCB-editor Y. The source origin is the actual milled top-left corner.
The assembly source must apply the recorded transform explicitly.

ST's original notice is retained in `ST-MB1136-NOTICE.txt`. The ST-derived
reference files remain under their source terms and are not relicensed as MIT.
The authored conversion script uses the repository license. Purchased-board
variant, connector-height and as-built tolerances require their own evidence.

## IO-Link shield references

`iom-factory-board` and `iod-factory-board` retain the eight factory outline
segments and all 264/185 drill centres from the paired ST fabrication archives.
Every plated drill centre is cross-checked against its factory TOP copper
flash. The adjacent geometry JSON records the member hashes, coordinate
format, counts, thickness source and calculated volume. Both drawings specify
a 1.67 mm reference full stack. `../tools/extract-shield-geometry.py` generates
the editable KernelCAD sources from the verified extracted Gerbers.

These are purchased-board mechanical references. They do not claim a
reconstructed routed PCB or a manufacturer-supplied populated 3D model. Their
KernelCAD exports re-import as valid single solids; measured volume matches
the factory polygon area minus all drill bores. The final station must add
source-qualified connector bodies and preserve native coordinate handedness.
