/* SPDX-License-Identifier: MIT */
#include "board_hal.h"
#include "iolinki/device.h"
#include "iolinki/iolink.h"
#include "station_clock.h"
#include "station_profile.h"
#include "stm32l4xx_hal.h"
#include <string.h>
volatile uint8_t g_device_state = 0xff;
volatile uint8_t g_device_pd;
volatile int g_startup_error;
static iolink_device_ctx_t device;
static char serial_number[17];
static iolink_device_info_t identity = {
    .vendor_name = "LabWired",
    .vendor_text = "Educational bench example",
    .product_name = "Eight-bit input station",
    .product_id = "L476-L6362A-DI8",
    .product_text = "SN74HC165 parallel input carrier",
    .serial_number = serial_number,
    .hardware_revision = "A",
    .firmware_revision = "A",
    .application_tag = "DI8",
    .vendor_id = 0xFFFFU, /* Unassigned bench identity, not a registered Vendor ID. */
    .device_id = 0x000001U,
    /* Direct Parameter page uses raw B.1.3 code: 6.4 + 9*0.4 = 10 ms.
     * This is separate from stack.min_cycle_time's 100-us API unit. */
    .min_cycle_time = STATION_MIN_CYCLE_RAW,
    .revision_id = 0x11U,
};
static void make_serial_number(void) {
    /* Encode all 96 UID bits in 16 printable characters without truncation. */
    const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    const uint32_t words[3] = {HAL_GetUIDw0(), HAL_GetUIDw1(), HAL_GetUIDw2()};
    uint8_t bytes[12];
    for (unsigned w = 0; w < 3; ++w)
        for (unsigned b = 0; b < 4; ++b)
            bytes[4 * w + b] = (uint8_t)(words[w] >> (24U - 8U * b));
    for (unsigned i = 0; i < 4; ++i) {
        const uint32_t value =
            ((uint32_t)bytes[3 * i] << 16) | ((uint32_t)bytes[3 * i + 1] << 8) | bytes[3 * i + 2];
        for (unsigned c = 0; c < 4; ++c)
            serial_number[4 * i + c] = alphabet[(value >> (18U - 6U * c)) & 63U];
    }
    serial_number[16] = 0;
}
void _init(void) {}
void _fini(void) {}
int main(void) {
    g_startup_error = device_board_init();
    if (g_startup_error != 0)
        for (;;)
            __WFI();
    iolink_device_config_t config;
    memset(&config, 0, sizeof(config));
    make_serial_number();
    /* This pinned stack's direct page still reads the legacy identity context.
     * A physical MCU has one device; bind both public contexts to the same data. */
    iolink_device_info_init(&identity);
    config.device_info = &identity;
    config.phy = *device_board_phy();
    config.stack.m_seq_type = STATION_DEVICE_MSEQ_TYPE;
    config.stack.min_cycle_time = STATION_CYCLE_100US; /* Public API unit: 100 us; 10 ms cycle. */
    config.stack.pd_in_len = STATION_PD_INPUT_BYTES;
    config.stack.pd_out_len = STATION_PD_OUTPUT_BYTES;
    config.stack.t_pd_us = 0;
    g_startup_error = iolink_device_init(&device, &config);
    if (g_startup_error != 0)
        for (;;)
            __WFI();
    iolink_device_set_timing_enforcement(&device, true);
    uint32_t last_input = station_now_us() - 1000U;
    for (;;) {
        const uint32_t now = station_now_us();
        if ((uint32_t)(now - last_input) >= 1000U) {
            last_input = now;
            g_device_pd = device_board_inputs();
            uint8_t input = g_device_pd;
            iolink_device_pd_input_update(&device, &input, 1, true);
        }
        iolink_device_process(&device);
        g_device_state = (uint8_t)iolink_device_get_state(&device);
    }
}
