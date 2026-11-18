#ifndef DOOM_LCD_PINS_H
#define DOOM_LCD_PINS_H

//
// Pin map for a 34-pin 3.2" 320x240 panel on an 8080 (i80) parallel bus.
//
// QDtech/LCDWiki MRB3205, 16-bit I80 mode (R16 fitted, R8 open), J1
// closed for 3.3 V supply bypass. ESP32-S3-DevKitC-1-N16R8 PCB v1.0:
//   - GPIO26-32 are the SPI flash, GPIO33-37 are the octal PSRAM: gone.
//   - GPIO19/20 are native USB D-/D+, GPIO43/44 are UART0.
//   - GPIO0, 45 and 46 are left free. GPIO3 is also a strapping pin;
//     it drives DB2 only after reset, with no external pull on this carrier.
//

// Panel path built in. If the bus never comes up the firmware falls back to
// serial-only measurement instead of refusing to boot.
#define DOOM_LCD_ENABLED 1

// Which bus drives the panel.
//
//   I80 — the 34-pin parallel module on the physical board. 16 data lines
//         through LCD_CAM + GDMA. Fast, and what the hardware actually has.
//   SPI — retained as an upstream alternative. This package builds I80
//         for the physical carrier and the LCD_CAM/GDMA LabWired twin.
//
// Same panel controller either way — only the bus differs, so the init
// sequence and the frame push are shared.
#define DOOM_LCD_BUS_I80 1
#define DOOM_LCD_BUS_SPI 2

#ifndef DOOM_LCD_BUS
#define DOOM_LCD_BUS DOOM_LCD_BUS_I80
#endif

// SPI pin map. Matches examples/esp32s3-doomlike-lab/system.yaml so the lab
// circuit that already exists in the catalog drives this firmware unchanged.
#define DOOM_LCD_SPI_SCLK 12
#define DOOM_LCD_SPI_MOSI 13
#define DOOM_LCD_SPI_CS 10
#define DOOM_LCD_SPI_DC 11
#define DOOM_LCD_SPI_RST 14

// Data bus. DB0..DB7 first, then DB8..DB15.
#define DOOM_LCD_D0  1
#define DOOM_LCD_D1  2
#define DOOM_LCD_D2  3
#define DOOM_LCD_D3  4
#define DOOM_LCD_D4  5
#define DOOM_LCD_D5  6
#define DOOM_LCD_D6  7
#define DOOM_LCD_D7  8
#define DOOM_LCD_D8  9
#define DOOM_LCD_D9  10
#define DOOM_LCD_D10 11
#define DOOM_LCD_D11 12
#define DOOM_LCD_D12 13
#define DOOM_LCD_D13 14
#define DOOM_LCD_D14 15
#define DOOM_LCD_D15 16

// Control lines. RD is pulled high on the carrier: we never read the panel back.
#define DOOM_LCD_WR  17
#define DOOM_LCD_DC  18
#define DOOM_LCD_CS  21
#define DOOM_LCD_RST 38
#define DOOM_LCD_BL  39

// 16 data bits at 10 MHz give a nominal 160 Mbit/s bus data rate before
// command and transfer overhead. Keep 10 MHz until physical signal integrity
// is measured on the carrier and specified ribbon cable.
#define DOOM_LCD_PCLK_HZ (10 * 1000 * 1000)

#define DOOM_LCD_H_RES 320
#define DOOM_LCD_V_RES 240

#endif // DOOM_LCD_PINS_H
