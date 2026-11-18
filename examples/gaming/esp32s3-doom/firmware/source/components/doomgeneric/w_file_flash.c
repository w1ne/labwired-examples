//
// Memory-mapped WAD access for the ESP32-S3.
//
// This replaces upstream w_file_stdc.c. The IWAD lives in its own raw flash
// partition, mapped into the data address space by main.c, so a lump is just a
// pointer into flash: W_CacheLumpNum takes the `mapped` fast path in w_wad.c
// and never copies the lump into PSRAM.
//
// The symbol is still called `stdc_wad_file` because w_file.c reaches for that
// name by default (it only tries the other classes under -mmap).
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "doomtype.h"
#include "w_file.h"

// Published by main.c once esp_partition_mmap has succeeded.
const unsigned char *doom_wad_base = NULL;
unsigned int doom_wad_length = 0;

extern wad_file_class_t stdc_wad_file;

typedef struct
{
    wad_file_t wad;
} flash_wad_file_t;

static wad_file_t *W_Flash_OpenFile(char *path)
{
    flash_wad_file_t *file;

    (void)path;

    // Nothing is mapped -> report failure the way a missing file would, so
    // D_DoomMain prints its own "IWAD not found" rather than faulting on NULL.
    if (doom_wad_base == NULL || doom_wad_length == 0)
    {
        return NULL;
    }

    file = calloc(1, sizeof(flash_wad_file_t));

    if (file == NULL)
    {
        return NULL;
    }

    file->wad.file_class = &stdc_wad_file;
    file->wad.mapped = (byte *)doom_wad_base;
    file->wad.length = doom_wad_length;

    return &file->wad;
}

static void W_Flash_CloseFile(wad_file_t *wad)
{
    free(wad);
}

// Only reached for the non-mapped paths in w_wad.c (header and directory
// reads). Flash is byte-addressable through the cache, so this is a memcpy.
static size_t W_Flash_Read(wad_file_t *wad, unsigned int offset,
                           void *buffer, size_t buffer_len)
{
    size_t available;

    if (offset >= wad->length)
    {
        return 0;
    }

    available = wad->length - offset;

    if (buffer_len > available)
    {
        buffer_len = available;
    }

    memcpy(buffer, wad->mapped + offset, buffer_len);

    return buffer_len;
}

wad_file_class_t stdc_wad_file =
{
    W_Flash_OpenFile,
    W_Flash_CloseFile,
    W_Flash_Read,
};
