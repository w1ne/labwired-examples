/* SPDX-License-Identifier: MIT
 * Physical two-port IO-Link master. GPL iolinki-master is linked separately.
 */
#include "board_hal.h"
#include "stm32l4xx_hal.h"
volatile uint8_t g_master_state[BOARD_PORTS] = {0xff, 0xff};
volatile uint8_t g_master_pd[BOARD_PORTS] = {0xff, 0xff};
volatile int g_master_tick_result[BOARD_PORTS];
volatile int g_startup_error;
static iolink_master_controller_t controller;
static iolink_master_port_t ports[BOARD_PORTS];
static iolink_phy_api_t phys[BOARD_PORTS];
static iolink_master_config_t configs[BOARD_PORTS];
void _init(void) {}
void _fini(void) {}
static void halt(int error) {
    g_startup_error = error;
    board_shutdown();
    for (;;)
        __WFI();
}
int main(void) {
    int result = board_init();
    if (result != 0)
        halt(result);
    board_fill_master(phys, configs);
    result = iolink_master_controller_init(&controller, ports, BOARD_PORTS, phys, configs);
    if (result != 0)
        halt(result);
    /* Each USB-powered device gets its full boot interval after L+ appears. */
    HAL_Delay(500);
    for (;;) {
        board_poll_faults();
        for (uint8_t i = 0; i < BOARD_PORTS; ++i) {
            iolink_master_port_t *p = 0;
            if (iolink_master_controller_get_port(&controller, i, &p) != 0 || !p)
                halt(-20);
            /* Refresh real time per port: a blocking UART transfer on one
             * port must not give the second port a stale controller timestamp. */
            const uint32_t now = board_now_100us();
            iolink_master_timing_t timing;
            if (iolink_master_get_timing(p, &timing) != 0)
                halt(-21);
            const bool expired =
                timing.awaiting_response && (int32_t)(now - timing.response_deadline_100us) >= 0;
            g_master_tick_result[i] = iolink_master_tick_at(
                p, expired ? IOLINK_MASTER_TICK_RESPONSE_TIMEOUT : IOLINK_MASTER_TICK_CYCLE_DUE,
                now);
            g_master_state[i] = (uint8_t)iolink_master_get_state(p);
            uint8_t data[1], length = 0;
            if (iolink_master_get_pd_in(p, data, sizeof(data), &length) == 0 && length == 1)
                g_master_pd[i] = data[0];
        }
    }
}
