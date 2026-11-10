# Third-party notices

## Peanut-GB

Source: https://github.com/deltabeard/Peanut-GB/blob/master/peanut_gb.h

The exact included header is identified by its SHA-256 in `source-provenance.json`; no release version is inferred from the branch name. Its full MIT license remains at the top of `firmware/peanut_gb.h` and in the amalgamated `firmware/gameboy.c`.

Copyright (c) 2018–2023 Mahyar Koshkouei. The header also retains its MIT-licensed SameBoy code notice, Copyright (c) 2015–2019 Lior Halphon.

## WeAct Black Pill footprint and symbol

Source: https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/tree/master/Hardware/KiCAD

The upstream README explicitly permits copying or vendoring the KiCad folder into a project. It does not state a named license in that folder, and the repository root LICENSE URL returned 404 at retrieval. Do not treat these vendor files as covered by the example's MIT license. Their source URLs and content hashes are recorded in `source-provenance.json`.

The KiCad 9-compatible footprint changes the file version and removes one KiCad 10-only field. Pad geometry and numbering remain unchanged. The original vendor footprint and symbol are included for reference.

## KiCad footprint libraries

The PCB embeds the standard KiCad JST PH 8-pin connector, 6 mm through-hole switch, and 0603/0805 capacitor footprints. KiCad libraries use CC BY-SA 4.0 with a design exception that permits designs made with the libraries to be distributed under the designer's chosen terms. Source and license: https://www.kicad.org/libraries/license/

## Original example

Wire Runner, its ROM generator, STM32 integration, carrier generator/router, and the authored enclosure sources use the MIT license in `LICENSE`. No Nintendo software or assets are included.
