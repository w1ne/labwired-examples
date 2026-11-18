/* SPDX-License-Identifier: MIT */
#ifndef LABWIRED_IOLINK_DEVICE_BOARD_H
#define LABWIRED_IOLINK_DEVICE_BOARD_H
#include "iolinki/phy.h"
#include <stdint.h>
int device_board_init(void);
const iolink_phy_api_t *device_board_phy(void);
uint8_t device_board_inputs(void);
extern volatile uint32_t g_uart_errors, g_rx_overflows, g_wake_events, g_overload_edges;
extern volatile int g_phy_error;
#endif
