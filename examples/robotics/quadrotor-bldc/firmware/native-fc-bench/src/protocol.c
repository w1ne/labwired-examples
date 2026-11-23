// SPDX-License-Identifier: GPL-3.0-or-later
// DShot inverted checksum and GCR/RLL decoding. Algorithm source:
// OpenDrone-hw/betaflight 31066c0f, src/platform/PICO/dshot_bidir_pico.c.
// This implementation scans bits without undefined shifts or calibration.
// The PIO samples every18 clocks at75MHz; nominal reply bit is100 clocks.
#include "protocol.h"

uint16_t dshot_frame(uint16_t throttle) {
    uint16_t data = (uint16_t)((throttle & 2047u) << 1); // request bit0; bidir replies are automatic
    uint16_t crc = (uint16_t)(~(data ^ (data >> 4) ^ (data >> 8)) & 15u);
    return (uint16_t)((data << 4) | crc);
}

static bool sample(const uint32_t words[4], unsigned bit) {
    return ((words[bit / 32u] >> (31u - bit % 32u)) & 1u) != 0;
}

telemetry_result_t telemetry_decode(const uint32_t words[4], uint16_t *payload) {
    static const uint8_t decode[32] = {
        255,255,255,255,255,255,255,255,255,9,10,11,255,13,14,15,
        255,255,2,3,255,5,6,7,255,0,8,1,255,4,12,255
    };
    if (sample(words, 0)) return TELEMETRY_START;
    bool level = false;
    unsigned run = 0, bits = 0, edges = 0;
    uint32_t gcr = 0;
    for (unsigned i = 0; i < 128u; ++i) {
        bool next = sample(words, i);
        if (next == level) { ++run; continue; }
        unsigned length = (run * 18u + 50u) / 100u;
        if (length < 1u || length > 3u || bits + length > 21u) return TELEMETRY_LENGTH;
        gcr = (gcr << length) | (1u << (length - 1u));
        bits += length; ++edges;
        level = next; run = 1;
    }
    if (edges < 2u || bits < 18u || bits > 21u || !level) return TELEMETRY_LENGTH;
    // High data bits cannot be separated from final idle-high samples.
    unsigned padding = 21u - bits;
    gcr <<= padding;
    if (padding) gcr |= 1u << (padding - 1u);
    uint16_t raw = 0;
    for (int shift = 15; shift >= 0; shift -= 5) {
        uint8_t nibble = decode[(gcr >> (unsigned)shift) & 31u];
        if (nibble > 15u) return TELEMETRY_GCR;
        raw = (uint16_t)((raw << 4) | nibble);
    }
    if (((raw ^ (raw >> 4) ^ (raw >> 8) ^ (raw >> 12)) & 15u) != 15u) return TELEMETRY_CRC;
    *payload = raw >> 4;
    return TELEMETRY_OK;
}

bool telemetry_is_erpm(uint16_t payload) {
    // AM32 normalizes nonzero exponents with mantissa bit8 set. Reserved
    // non-normalized encodings carry EDT data, not a motor period.
    return payload > 0 && payload <= 0xfff
        && (payload < 0x200u || (payload & 0x100u));
}
uint32_t telemetry_period_us(uint16_t payload) {
    if (!telemetry_is_erpm(payload) || payload == 0xfffu) return 0; // protocol stopped indication
    return (uint32_t)(payload & 0x1ffu) << (payload >> 9);
}
uint32_t telemetry_erpm(uint16_t payload) {
    uint32_t period = telemetry_period_us(payload);
    return period ? (60000000u + period / 2u) / period : 0;
}
