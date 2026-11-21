# Project library provenance

The included .kicad_sym files are exact snapshots of the final schematic embedded definitions, produced by the existing LabWired projectLibraryFiles helper. The A1_Native and A1_Native_C10 footprint libraries are exact KiCad exports of the native board footprints. Their geometry remains unchanged; local library namespaces were added for portable resolution. The underlying KiCad community libraries are documented at https://gitlab.com/kicad/libraries/kicad-symbols and https://gitlab.com/kicad/libraries/kicad-footprints . The library license and design exception are included in KICAD_SYMBOLS_LICENSE.md.

## Upstream LabWired symbol attribution

# Vendored KiCad symbols

`kicad-symbols.generated.ts` holds symbols copied verbatim from the KiCad symbol
library (https://gitlab.com/kicad/libraries/kicad-symbols), tag 10.0.6,
commit 7800d91437ce44e2ed0928f2ad31a287457b8a68. They remain under the library's license, CC-BY-SA 4.0 with the KiCad
design exception; see `KICAD_SYMBOLS_LICENSE.md` in this directory. Only the
library-id prefix of each symbol name was changed (`R` -> `Device:R`), which is
what a schematic's `lib_symbols` requires.

Vendored (37):

- Device: R, C, L, LED, D, D_Zener, Buzzer, R_Potentiometer, R_Photo, Thermistor_NTC
- Transistor_BJT: Q_NPN_BCE, Q_PNP_BCE, Q_NPN_EBC, Q_PNP_EBC, Q_NPN_BEC, Q_PNP_BEC
- Transistor_FET: Q_NMOS_GDS, Q_PMOS_GDS
- Switch: SW_Push
- Relay: SANYOU_SRD_Form_C
- LED: WS2812B
- Amplifier_Operational: LM358, drawn from LM2904 (the symbol LM358 extends)
- Comparator: LM393, drawn from LM2903 (the symbol LM393 extends)
- 74xx: 74HC595, 74HC4051; 74HC00, 74HC04, 74HC08, 74HC32 and 74HC125 drawn from the 74LS symbols they extend
- power: GND, +3V3, +5V, VCC, VDD, +12V, PWR_FLAG

