// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <stdbool.h>
#include <stdint.h>

typedef enum { TELEMETRY_OK, TELEMETRY_START, TELEMETRY_LENGTH, TELEMETRY_GCR, TELEMETRY_CRC } telemetry_result_t;
uint16_t dshot_frame(uint16_t throttle);
telemetry_result_t telemetry_decode(const uint32_t samples[4], uint16_t *payload);
bool telemetry_is_erpm(uint16_t payload);
uint32_t telemetry_period_us(uint16_t payload);
uint32_t telemetry_erpm(uint16_t payload);
