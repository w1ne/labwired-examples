//
// See dg_psram_statics.h. Compiled to nothing unless DOOM_STATICS_ON_HEAP is
// defined, which only the Arduino/PlatformIO build does — the ESP-IDF build
// does not even list this file, and its arrays stay in .bss.
//
// GPLv2, following doomgeneric.
//

#include "dg_psram_statics.h"

#ifdef DOOM_STATICS_ON_HEAP

#include <stdlib.h>
#include <string.h>

#if defined(ESP_PLATFORM)
#include "esp_heap_caps.h"
#endif

// Each converted module allocates its own arrays, because the sizes are
// #defines local to that file and are better left there.
extern boolean R_AllocPlanes(void);

void *DG_AllocLarge(size_t bytes)
{
    void *p = NULL;

#if defined(ESP_PLATFORM)
    // Ask for external RAM by name rather than trusting the heap's size
    // heuristic: CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL only routes allocations
    // above its threshold, and not every array here is above it.
    p = heap_caps_malloc(bytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
#endif

    if (p == NULL)
    {
        p = malloc(bytes);
    }

    if (p != NULL)
    {
        // .bss is zero at start-up; these have to look the same.
        memset(p, 0, bytes);
    }

    return p;
}

boolean DG_AllocStatics(void)
{
    static boolean done = false;

    if (done)
    {
        return true;
    }

    if (!R_AllocPlanes())
    {
        return false;
    }

    done = true;
    return true;
}

#endif // DOOM_STATICS_ON_HEAP
