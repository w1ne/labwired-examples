//
// Display backend + the remaining doomgeneric hooks.
//
// Two modes, selected by DOOM_LCD_ENABLED in doom_lcd_pins.h:
//
//   0 - no panel. Every frame is still measured: frame rate, an FNV-1a hash of
//       the pixels, the lit-pixel fraction, and a periodic ASCII thumbnail. A
//       hash that changes frame to frame with a plausible ink fraction is proof
//       Doom is really rendering, and it needs no hardware at all.
//   1 - 8080 parallel panel over the S3 LCD_CAM peripheral, DMA fed.
//
// Doom renders 320x200 into a 320x240 panel, so the image is centred with a
// 20-line black band above and below rather than stretched.
//

#include <string.h>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "doom_esp32.h"
#include "doom_lcd_pins.h"

#if DOOM_LCD_ENABLED
#include "driver/gpio.h"
#include "esp_lcd_panel_io.h"
#if DOOM_LCD_BUS == DOOM_LCD_BUS_SPI
#include "driver/spi_master.h"
#endif
#endif

static const char *TAG = "doom_video";

#define STATS_EVERY_FRAMES 60
#define THUMBNAIL_EVERY_FRAMES 300

#define THUMB_COLS 64
#define THUMB_ROWS 24

static uint32_t s_frames;
static int64_t s_last_stats_us;

#if DOOM_LCD_ENABLED
static esp_lcd_panel_io_handle_t s_io;
static uint16_t *s_rgb565;   // DMA-capable 320x200 scratch, PSRAM
static bool s_panel_up;      // false -> serial-only, Doom still runs
#endif

// --- frame measurement ------------------------------------------------------

static uint32_t fnv1a(const void *data, size_t len)
{
    const uint8_t *p = (const uint8_t *)data;
    uint32_t hash = 0x811c9dc5u;

    for (size_t i = 0; i < len; ++i)
    {
        hash ^= p[i];
        hash *= 0x01000193u;
    }

    return hash;
}

// Fraction of pixels that are not pure black, in tenths of a percent. A frame
// that hashes differently every time but is 100% black is a renderer writing
// nothing useful - the ink figure is what separates those two cases.
static uint32_t ink_permille(const uint32_t *argb, int count)
{
    int lit = 0;

    for (int i = 0; i < count; ++i)
    {
        if ((argb[i] & 0x00ffffffu) != 0)
        {
            ++lit;
        }
    }

    return (uint32_t)((int64_t)lit * 1000 / count);
}

static void log_thumbnail(const uint32_t *argb, int width, int height)
{
    static const char ramp[] = " .:-=+*#%@";
    char line[THUMB_COLS + 1];

    ESP_LOGI(TAG, "frame %" PRIu32 ":", s_frames);

    for (int row = 0; row < THUMB_ROWS; ++row)
    {
        int sy = row * height / THUMB_ROWS;

        for (int col = 0; col < THUMB_COLS; ++col)
        {
            int sx = col * width / THUMB_COLS;
            uint32_t px = argb[sy * width + sx];
            uint32_t r = (px >> 16) & 0xff;
            uint32_t g = (px >> 8) & 0xff;
            uint32_t b = px & 0xff;

            // Rec. 601 luma, integer only.
            uint32_t luma = (r * 77 + g * 150 + b * 29) >> 8;

            line[col] = ramp[(luma * (sizeof(ramp) - 2)) / 255];
        }

        line[THUMB_COLS] = '\0';
        ESP_LOGI(TAG, "|%s|", line);
    }
}

// --- panel ------------------------------------------------------------------

#if DOOM_LCD_ENABLED

static void lcd_cmd(uint8_t cmd, const uint8_t *params, size_t len)
{
    ESP_ERROR_CHECK(esp_lcd_panel_io_tx_param(s_io, cmd, params, len));
}

static void ili9341_init(void)
{
    vTaskDelay(pdMS_TO_TICKS(120));

    lcd_cmd(0x01, NULL, 0);                       // software reset
    vTaskDelay(pdMS_TO_TICKS(120));

    lcd_cmd(0xcf, (const uint8_t[]){0x00, 0x83, 0x30}, 3);
    lcd_cmd(0xed, (const uint8_t[]){0x64, 0x03, 0x12, 0x81}, 4);
    lcd_cmd(0xe8, (const uint8_t[]){0x85, 0x01, 0x79}, 3);
    lcd_cmd(0xcb, (const uint8_t[]){0x39, 0x2c, 0x00, 0x34, 0x02}, 5);
    lcd_cmd(0xf7, (const uint8_t[]){0x20}, 1);
    lcd_cmd(0xea, (const uint8_t[]){0x00, 0x00}, 2);
    lcd_cmd(0xc0, (const uint8_t[]){0x26}, 1);    // power control 1
    lcd_cmd(0xc1, (const uint8_t[]){0x11}, 1);    // power control 2
    lcd_cmd(0xc5, (const uint8_t[]){0x35, 0x3e}, 2);
    lcd_cmd(0xc7, (const uint8_t[]){0xbe}, 1);
    lcd_cmd(0x36, (const uint8_t[]){0x28}, 1);    // MADCTL: landscape, BGR
    lcd_cmd(0x3a, (const uint8_t[]){0x55}, 1);    // 16 bit/pixel
    lcd_cmd(0xb1, (const uint8_t[]){0x00, 0x1b}, 2);
    lcd_cmd(0xb6, (const uint8_t[]){0x0a, 0x82, 0x27, 0x00}, 4);
    lcd_cmd(0x11, NULL, 0);                       // sleep out
    vTaskDelay(pdMS_TO_TICKS(120));
    lcd_cmd(0x29, NULL, 0);                       // display on
}

static void set_window(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1)
{
    uint8_t col[] = {x0 >> 8, x0 & 0xff, x1 >> 8, x1 & 0xff};
    uint8_t page[] = {y0 >> 8, y0 & 0xff, y1 >> 8, y1 & 0xff};

    lcd_cmd(0x2a, col, sizeof(col));
    lcd_cmd(0x2b, page, sizeof(page));
}

// RST and BL are plain firmware-driven outputs, not part of the i80 bus.
static void panel_gpio_init(void)
{
#if DOOM_LCD_BUS == DOOM_LCD_BUS_SPI
    const int rst_pin = DOOM_LCD_SPI_RST;
    const uint64_t pins = 1ULL << DOOM_LCD_SPI_RST;
#else
    const int rst_pin = DOOM_LCD_RST;
    const uint64_t pins = (1ULL << DOOM_LCD_RST) | (1ULL << DOOM_LCD_BL);
#endif

    gpio_config_t io = {
        .pin_bit_mask = pins,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };

    ESP_ERROR_CHECK(gpio_config(&io));

    // Hardware reset pulse: the ILI9341 needs RST low for >10 us and ~120 ms
    // of settling before it will accept commands.
    gpio_set_level(rst_pin, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(rst_pin, 0);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(rst_pin, 1);
    vTaskDelay(pdMS_TO_TICKS(120));

#if DOOM_LCD_BUS == DOOM_LCD_BUS_I80
    gpio_set_level(DOOM_LCD_BL, 1);
#endif
}

#if DOOM_LCD_BUS == DOOM_LCD_BUS_SPI

/// 4-wire SPI bring-up. Same ILI9341 on the far side, so ili9341_init() and
/// the frame push below are untouched — only how bytes reach the panel differs.
static esp_err_t panel_bus_init(void)
{
    esp_err_t err;

    spi_bus_config_t buscfg = {
        .sclk_io_num = DOOM_LCD_SPI_SCLK,
        .mosi_io_num = DOOM_LCD_SPI_MOSI,
        .miso_io_num = -1,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = DOOMGENERIC_RESX * DOOMGENERIC_RESY * sizeof(uint16_t),
    };

    err = spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO);
    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "spi_bus_initialize failed: %s", esp_err_to_name(err));
        return err;
    }

    esp_lcd_panel_io_spi_config_t io_config = {
        .dc_gpio_num = DOOM_LCD_SPI_DC,
        .cs_gpio_num = DOOM_LCD_SPI_CS,
        .pclk_hz = 40 * 1000 * 1000,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
        .spi_mode = 0,
        .trans_queue_depth = 10,
    };

    err = esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI2_HOST, &io_config, &s_io);
    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "esp_lcd_new_panel_io_spi failed: %s", esp_err_to_name(err));
    }
    return err;
}

#else

static esp_err_t panel_bus_init(void)
{
    esp_lcd_i80_bus_handle_t bus = NULL;
    esp_err_t err;

    esp_lcd_i80_bus_config_t bus_config = {
        .clk_src = LCD_CLK_SRC_DEFAULT,
        .dc_gpio_num = DOOM_LCD_DC,
        .wr_gpio_num = DOOM_LCD_WR,
        .data_gpio_nums = {
            DOOM_LCD_D0, DOOM_LCD_D1, DOOM_LCD_D2, DOOM_LCD_D3,
            DOOM_LCD_D4, DOOM_LCD_D5, DOOM_LCD_D6, DOOM_LCD_D7,
            DOOM_LCD_D8, DOOM_LCD_D9, DOOM_LCD_D10, DOOM_LCD_D11,
            DOOM_LCD_D12, DOOM_LCD_D13, DOOM_LCD_D14, DOOM_LCD_D15,
        },
        .bus_width = 16,
        .max_transfer_bytes = DOOMGENERIC_RESX * DOOMGENERIC_RESY * sizeof(uint16_t),
        .psram_trans_align = 64,
        .sram_trans_align = 4,
    };
    err = esp_lcd_new_i80_bus(&bus_config, &bus);

    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "esp_lcd_new_i80_bus failed: %s", esp_err_to_name(err));
        return err;
    }

    esp_lcd_panel_io_i80_config_t io_config = {
        .cs_gpio_num = DOOM_LCD_CS,
        .pclk_hz = DOOM_LCD_PCLK_HZ,
        .trans_queue_depth = 4,
        .dc_levels = {
            .dc_idle_level = 0,
            .dc_cmd_level = 0,
            .dc_dummy_level = 0,
            .dc_data_level = 1,
        },
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
    };
    err = esp_lcd_new_panel_io_i80(bus, &io_config, &s_io);

    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "esp_lcd_new_panel_io_i80 failed: %s", esp_err_to_name(err));
    }
    return err;
}

#endif // DOOM_LCD_BUS

static esp_err_t panel_init(void)
{
    esp_err_t err;

    panel_gpio_init();

    err = panel_bus_init();
    if (err != ESP_OK)
    {
        return err;
    }

    ili9341_init();

    return ESP_OK;
}

#endif // DOOM_LCD_ENABLED

// --- doomgeneric hooks ------------------------------------------------------

void doom_display_init(void)
{
#if DOOM_LCD_ENABLED
    const size_t fb_bytes = DOOMGENERIC_RESX * DOOMGENERIC_RESY * sizeof(uint16_t);

    if (panel_init() != ESP_OK)
    {
        ESP_LOGW(TAG, "panel did not come up - serial-only measurement");
        return;
    }

    s_rgb565 = heap_caps_malloc(fb_bytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_DMA);

    if (s_rgb565 == NULL)
    {
        s_rgb565 = heap_caps_malloc(fb_bytes, MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA);
    }

    if (s_rgb565 == NULL)
    {
        ESP_LOGE(TAG, "no DMA-capable memory for the %u B frame buffer",
                 (unsigned)fb_bytes);
        return;
    }

    s_panel_up = true;

#if DOOM_LCD_BUS == DOOM_LCD_BUS_SPI
    ESP_LOGI(TAG, "panel up: %dx%d ILI9341 over SPI2", DOOM_LCD_H_RES, DOOM_LCD_V_RES);
#else
    ESP_LOGI(TAG, "panel up: %dx%d i80 16-bit at %d Hz",
             DOOM_LCD_H_RES, DOOM_LCD_V_RES, DOOM_LCD_PCLK_HZ);
#endif
#else
    ESP_LOGW(TAG, "no panel configured - measuring frames over serial only");
#endif
}

void doom_display_frame(const uint32_t *argb, int width, int height)
{
    int64_t now = esp_timer_get_time();

    ++s_frames;

#if DOOM_LCD_ENABLED
    // ARGB8888 -> RGB565, then one DMA push of the whole 320x200 image into
    // the centred window.
    if (s_panel_up)
    {
    for (int i = 0; i < width * height; ++i)
    {
        uint32_t px = argb[i];
        s_rgb565[i] = (uint16_t)(((px >> 8) & 0xf800) |
                                 ((px >> 5) & 0x07e0) |
                                 ((px >> 3) & 0x001f));
    }

    {
        uint16_t y0 = (DOOM_LCD_V_RES - height) / 2;

        set_window(0, y0, width - 1, y0 + height - 1);
        esp_lcd_panel_io_tx_color(s_io, 0x2c, s_rgb565,
                                  width * height * sizeof(uint16_t));
    }
    }
#endif

    // Report the very first frame as well as every STATS_EVERY_FRAMES-th.
    // Waiting 60 frames for the first evidence is fine at 30 fps on silicon
    // and painful in a simulator, where 60 frames is billions of instructions
    // — and "did it ever render once" is the question that actually matters.
    if (s_frames == 1 || s_frames % STATS_EVERY_FRAMES == 0)
    {
        int64_t elapsed_us = now - s_last_stats_us;
        uint32_t hash = fnv1a(argb, (size_t)width * height * sizeof(uint32_t));
        uint32_t ink = ink_permille(argb, width * height);
        uint32_t mfps = elapsed_us > 0
            ? (uint32_t)((int64_t)STATS_EVERY_FRAMES * 1000000000LL / elapsed_us)
            : 0;

        ESP_LOGI(TAG, "frame %" PRIu32 "  %" PRIu32 ".%03" PRIu32 " fps  "
                      "hash 0x%08" PRIx32 "  ink %" PRIu32 ".%" PRIu32 "%%",
                 s_frames, mfps / 1000, mfps % 1000, hash, ink / 10, ink % 10);

        s_last_stats_us = now;
    }

    if (s_frames == 1 || s_frames % THUMBNAIL_EVERY_FRAMES == 0)
    {
        log_thumbnail(argb, width, height);
    }
}

void DG_Init(void)
{
    s_last_stats_us = esp_timer_get_time();
    ESP_LOGI(TAG, "DG_Init: %dx%d", DOOMGENERIC_RESX, DOOMGENERIC_RESY);
}

void DG_DrawFrame(void)
{
    extern uint32_t *DG_ScreenBuffer;

    doom_display_frame(DG_ScreenBuffer, DOOMGENERIC_RESX, DOOMGENERIC_RESY);
}

void DG_SleepMs(uint32_t ms)
{
    vTaskDelay(pdMS_TO_TICKS(ms));
}

uint32_t DG_GetTicksMs(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000);
}

void DG_SetWindowTitle(const char *title)
{
    ESP_LOGI(TAG, "title: %s", title);
}
