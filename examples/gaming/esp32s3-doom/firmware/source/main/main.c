//
// Doom on an ESP32-S3-N16R8.
//
// 16 MB flash holds the shareware IWAD in its own raw partition; 8 MB octal
// PSRAM holds Doom's zone heap and the 320x200 frame buffer. The WAD is
// memory-mapped, so lumps are read in place through the flash cache.
//

#include <string.h>

#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_partition.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "doom_esp32.h"

extern void doomgeneric_Create(int argc, char **argv);
extern void doomgeneric_Tick(void);

static const char *TAG = "doom";

// Doom recurses through the BSP tree; the default task stack is nowhere near
// enough. Measured headroom is reported after the first frames.
#define DOOM_TASK_STACK_BYTES (48 * 1024)

// Zone heap, in MiB, taken from PSRAM. Shareware Doom is comfortable in 4.
#define DOOM_ZONE_MB "4"

// Which core runs the game. Doom is single-threaded, so on a dual-core build
// it gets core 1 to itself and the system keeps core 0. A unicore build has no
// core 1 at all, and asking for one is a FreeRTOS assert, not a fallback.
#if CONFIG_FREERTOS_UNICORE
#define DOOM_TASK_CORE 0
#else
#define DOOM_TASK_CORE 1
#endif

static esp_partition_mmap_handle_t s_wad_map;

static void log_hardware(void)
{
    esp_chip_info_t chip;
    uint32_t flash_size = 0;

    esp_chip_info(&chip);
    esp_flash_get_size(NULL, &flash_size);

    ESP_LOGI(TAG, "ESP32-S3 rev v%d.%d, %d core(s), %" PRIu32 " MB flash",
             chip.revision / 100, chip.revision % 100, chip.cores,
             flash_size / (1024 * 1024));
    ESP_LOGI(TAG, "internal free %u B, PSRAM free %u B",
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
}

static esp_err_t map_wad(void)
{
    const esp_partition_t *part;
    const void *mapped = NULL;
    esp_err_t err;

    part = esp_partition_find_first(ESP_PARTITION_TYPE_DATA,
                                    (esp_partition_subtype_t)0x40, "wad");

    if (part == NULL)
    {
        ESP_LOGE(TAG, "no 'wad' partition in the table");
        return ESP_ERR_NOT_FOUND;
    }

    err = esp_partition_mmap(part, 0, part->size, ESP_PARTITION_MMAP_DATA,
                             &mapped, &s_wad_map);

    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "esp_partition_mmap failed: %s", esp_err_to_name(err));
        return err;
    }

    // A blank partition reads as 0xFF, which would otherwise reach Doom as a
    // corrupt directory much later and much less legibly.
    if (memcmp(mapped, "IWAD", 4) != 0 && memcmp(mapped, "PWAD", 4) != 0)
    {
        ESP_LOGE(TAG, "no WAD at 0x%" PRIx32 " (first bytes %02x %02x %02x %02x)",
                 part->address,
                 ((const uint8_t *)mapped)[0], ((const uint8_t *)mapped)[1],
                 ((const uint8_t *)mapped)[2], ((const uint8_t *)mapped)[3]);
        return ESP_ERR_INVALID_STATE;
    }

    // Lump count and directory offset are the two 32-bit fields after the
    // magic; the directory offset is the honest end of the WAD's payload.
    {
        uint32_t num_lumps;
        uint32_t dir_offset;

        memcpy(&num_lumps, (const uint8_t *)mapped + 4, 4);
        memcpy(&dir_offset, (const uint8_t *)mapped + 8, 4);

        doom_wad_base = (const unsigned char *)mapped;
        doom_wad_length = dir_offset + num_lumps * 16;

        ESP_LOGI(TAG, "IWAD mapped at %p: %" PRIu32 " lumps, %u bytes",
                 mapped, num_lumps, doom_wad_length);
    }

    return ESP_OK;
}

static void doom_task(void *arg)
{
    char *argv[] = {
        "doom",
        "-iwad", (char *)doom_vfs_iwad_path(),
        "-mb", DOOM_ZONE_MB,
    };

    (void)arg;

    ESP_LOGI(TAG, "starting doomgeneric with %s", doom_vfs_iwad_path());

    // doomgeneric_Create only *initialises* Doom: its D_DoomMain returns once
    // the WAD, renderer and playloop are up, and the host is expected to drive
    // the game one tic at a time. Every upstream backend has this loop in its
    // main(); ours lives here.
    doomgeneric_Create(sizeof(argv) / sizeof(argv[0]), argv);

    ESP_LOGI(TAG, "doom initialised, entering tick loop");

    for (;;)
    {
        doomgeneric_Tick();
    }
}

void app_main(void)
{
    log_hardware();
#ifndef DOOM_SKIP_LED
    board_led_off();
#endif

    ESP_ERROR_CHECK(map_wad());
    ESP_ERROR_CHECK(doom_vfs_register());

    doom_display_init();
    doom_input_init();

    xTaskCreatePinnedToCore(doom_task, "doom", DOOM_TASK_STACK_BYTES, NULL,
                            5, NULL, DOOM_TASK_CORE);
}
