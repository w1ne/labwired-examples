/* SPDX-License-Identifier: MIT */
#ifndef LABWIRED_IOLINK_BOARD_HAL_H
#define LABWIRED_IOLINK_BOARD_HAL_H
#include "iolinki_master/master.h"
#include <stdint.h>
#define BOARD_PORTS 2U
int board_init(void);
void board_fill_master(iolink_phy_api_t phys[BOARD_PORTS], iolink_master_config_t cfg[BOARD_PORTS]);
void board_poll_faults(void);
uint32_t board_now_us(void);
uint32_t board_now_100us(void);
void board_shutdown(void);
extern volatile uint32_t g_uart_errors[BOARD_PORTS];
extern volatile uint32_t g_rx_overflows[BOARD_PORTS];
extern volatile uint8_t g_phy_faults[BOARD_PORTS];
extern volatile int g_phy_error[BOARD_PORTS];
extern volatile uint32_t g_wake_count[BOARD_PORTS];
#endif
