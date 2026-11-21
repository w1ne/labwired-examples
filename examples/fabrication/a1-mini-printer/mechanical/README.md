# A1 reference mechanical integration

This directory contains original A1-inspired reference geometry and drawing-checked package data. It is not OEM Bambu geometry or a physical sample qualification.

## Package qualification

- U10/U11/U12/U13: A4988SETTR-T ET QFN28. The existing KiCad body had a correct3.15mm exposed pad despite its3.35mm filename. Contact heels were extended from0.40mm to the primary drawing0.55mm. Body5×5×0.92mm;28contacts,0.50mm pitch.
- U20: LMR36520ADDAR DDA8. The KiCad2.29×3.00mm exposed-pad variant lies within TI DDA0008B dimensions. The previous3.81mm pad-length model did not.
- J20: USB4216-03-A. Original clearance model derived from GCT revA2; dimensional shell, mounting and mating interface. This is not a supplier native STEP. Undimensioned springs, forming details and0.50mm peg depth remain nominal.

## Connector correction

The GCT recommended layout specifies3.925mm shell-pad center pitch,3.30mm from lower shell center to pegs, and4.00mm from lower shell center to signal-pad inner edge. Signal pads remain at y93.320mm. Correct centers are shell y93.970/97.895mm and pegs y94.595mm. The inherited footprint had shell pitch4.030mm.

## Fit study input

`a1-populated-fit-baseline.step` is a native populated KiCad STEP exported from the existing copper baseline after mechanical corrections. It is a mechanical fit input, not a final routed or fabrication-approved board. The final copper release must retain these package/pad corrections and rerun native DRC under its original rules.

## Primary sources

- Allegro A4988 datasheet, package and pinout pp18–19: https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf
- TI LMR36520 datasheet, pinout p4 and DDA0008B appended package drawing: https://www.ti.com/lit/ds/symlink/lmr36520.pdf
- GCT USB4216 drawing revA2,28July2025: https://www.mouser.lt/datasheet/3/1507/1/usb4216.pdf

Downloaded drawing hashes and exact model dimensions are in the JSON records. PDFs are retained in the working evidence directory; they are not redistributed in this repository. Model source licenses are preserved in the STEP headers.

## Reproduce

Install cadquery-ocp==8.0.1.1.0 and use the provided OCCT geometry scripts with KiCad standard STEP libraries installed. The scripts resolve their model output directory relative to the script and retain explicit source provenance. `apply_mechanical_patch.py INPUT OUTPUT --models-dir ../pcb/models --model-prefix \\${KIPRJMOD}/models` writes a separate native board, preserves signal pads, and records exact allowed changes. Refill zones and run original-rule DRC after this patch.
