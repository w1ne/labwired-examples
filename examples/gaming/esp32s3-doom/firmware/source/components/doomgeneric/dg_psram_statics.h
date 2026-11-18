//
// Doom's largest static arrays, off internal DRAM.
//
// Shareware Doom carries ~240 kB of .bss. On an ESP32-S3 that does not fit in
// internal DRAM alongside a framework, and there are two ways out:
//
//   ESP-IDF   a linker fragment (linker.lf) maps the whole archive's .bss into
//             the 8 MB octal PSRAM. Zero source changes. This is what
//             ../../main builds with.
//
//   Arduino   no equivalent exists. The framework's sections.ld sends
//             .ext_ram.bss into internal DRAM, and no Arduino-ESP32 variant
//             defines CONFIG_SPIRAM_ALLOW_BSS_SEG_EXTERNAL_MEMORY, so there is
//             nothing to aim a linker fragment at. The biggest arrays are
//             allocated at start-up instead.
//
// Only the Arduino path is affected: every conversion is guarded by
// DOOM_STATICS_ON_HEAP, which only library.json defines. With the macro unset
// this file compiles to nothing and the arrays are plain .bss, exactly as
// upstream and exactly as the ESP-IDF build has always linked them.
//
// A converted array becomes a pointer to the same storage, so every use site
// - indexing, pointer arithmetic, comparison against the end - is unchanged.
// The one thing that would break is sizeof(), which none of the converted
// arrays are subject to.
//

#ifndef DG_PSRAM_STATICS_H
#define DG_PSRAM_STATICS_H

#include <stddef.h>

#include "doomtype.h"

#ifdef DOOM_STATICS_ON_HEAP

// Zeroed, and off the internal heap wherever the platform can tell the
// difference. Never freed: these live as long as the game does.
void *DG_AllocLarge(size_t bytes);

// Fills in every converted array. Idempotent, and called from
// doomgeneric_Create() before anything can touch them, so a backend does not
// have to remember to call it.
boolean DG_AllocStatics(void);

#endif // DOOM_STATICS_ON_HEAP

#endif // DG_PSRAM_STATICS_H
