#ifndef DOOM_ESP32_H
#define DOOM_ESP32_H

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// The IWAD, memory-mapped out of its raw flash partition. Defined in
// components/doomgeneric/w_file_flash.c, filled in by main.c at boot.
extern const unsigned char *doom_wad_base;
extern unsigned int doom_wad_length;

// Clears the DevKit's addressable RGB LED, which otherwise holds whatever
// colour the previous firmware left latched in it.
void board_led_off(void);

// Read-only VFS exposing the mapped WAD as a real path for fopen()/stat().
esp_err_t doom_vfs_register(void);
const char *doom_vfs_iwad_path(void);

// Serial keyboard: turns bytes arriving on the console UART into Doom key
// events, synthesising a key-up a short time after each key-down.
void doom_input_init(void);

// Display backend. doom_display_init() is a no-op build when the panel is
// not enabled, so the port can be proven over serial before 21 bus lines are
// soldered.
void doom_display_init(void);
void doom_display_frame(const uint32_t *argb, int width, int height);

#ifdef __cplusplus
}
#endif

#endif // DOOM_ESP32_H
