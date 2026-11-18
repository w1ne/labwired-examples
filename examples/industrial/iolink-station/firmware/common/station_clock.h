/* SPDX-License-Identifier: MIT */
#ifndef LABWIRED_STATION_CLOCK_H
#define LABWIRED_STATION_CLOCK_H
#include <stdint.h>
int station_clock_init(void);
uint32_t station_now_us(void);
uint64_t station_now_us64(void);
uint32_t station_now_100us(void);
void station_delay_us(uint32_t duration);
#endif
