// SPDX-License-Identifier: GPL-3.0-or-later
// Physical OpenFC-Lite rev2-LW1 / RP2354B four-motor commissioning bench.
#include <errno.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/binary_info.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "hardware/uart.h"
#include "hardware/sync.h"
#include "dshot.pio.h"
#include "protocol.h"

_Static_assert(PICO_RP2350 && !PICO_RP2350A, "Native QFN80 RP2354B required");
_Static_assert(PICO_FLASH_SIZE_BYTES == 2097152, "Native stacked flash is2MiB");
bi_decl(bi_1pin_with_name(31, "Motor1 bidirectional DShot600 / P1.5"));
bi_decl(bi_1pin_with_name(30, "Motor2 bidirectional DShot600 / P1.6"));
bi_decl(bi_1pin_with_name(29, "Motor3 bidirectional DShot600 / P1.7"));
bi_decl(bi_1pin_with_name(28, "Motor4 bidirectional DShot600 / P1.8"));
bi_decl(bi_1pin_with_name(0, "Host UART0 TX /115200 baud"));
bi_decl(bi_1pin_with_name(1, "Host UART0 RX /115200 baud"));

#define MOTORS 4u
#define RELEASE_US 750000u
#define ZERO_FRAMES_REQUIRED 1250u
#define VALID_REPLIES_REQUIRED 128u
#define FRAME_US 1000u
#define REPLY_TIMEOUT_US 200u
#define COMMAND_TIMEOUT_US 500000u
static const uint motor_pin[MOTORS] = {31, 30, 29, 28};
static PIO const motor_pio = pio0;
static int tx_dma[MOTORS], rx_dma[MOTORS];
static uint program_offset;
static uint32_t tx_word[MOTORS];
static volatile uint32_t rx_word[MOTORS][4];
static uint64_t last_valid_us[MOTORS];
static bool inflight;
static uint64_t receive_deadline, command_deadline;

// Read-only observability ABI for a debugger or native integration test.
// Only this physical firmware updates these fields, from real DMA results.
struct bench_state {
    uint32_t abi_version, phase, armed, zero_frames, missed_deadlines;
    uint32_t submitted[MOTORS], valid[MOTORS], timeout[MOTORS], invalid[MOTORS];
    uint32_t requested[MOTORS], last_payload[MOTORS], period_us[MOTORS], erpm[MOTORS];
    uint32_t command_ok, command_error, watchdog_stops, telemetry_stops, log_dropped;
};
volatile struct bench_state g_bench = {.abi_version = 1};

// Nonblocking console: status output cannot hold up the1kHz frame schedule.
static char console_ring[2048];
static unsigned console_head, console_tail;
static void console_printf(const char *fmt, ...) {
    char text[240]; va_list ap; va_start(ap, fmt);
    int count = vsnprintf(text, sizeof text, fmt, ap); va_end(ap);
    if (count < 0 || (unsigned)count >= sizeof text) { ++g_bench.log_dropped; return; }
    unsigned free = (console_tail + sizeof console_ring - console_head - 1u) % sizeof console_ring;
    if ((unsigned)count > free) { ++g_bench.log_dropped; return; }
    for (int i = 0; i < count; ++i) {
        console_ring[console_head] = text[i];
        console_head = (console_head + 1u) % sizeof console_ring;
    }
}
static void console_line(const char *text) { console_printf("%s\n", text); }
static void console_poll(void) {
    for (unsigned budget = 0; budget < 16u && console_tail != console_head; ++budget) {
        if (!uart_is_writable(uart0)) break;
        uart_putc_raw(uart0, console_ring[console_tail]);
        console_tail = (console_tail + 1u) % sizeof console_ring;
    }
}

static void stop(void) {
    for (uint i = 0; i < MOTORS; ++i) g_bench.requested[i] = 0;
    g_bench.armed = 0;
    g_bench.zero_frames = 0;
    command_deadline = 0;
}

static void status(void) {
    console_printf("BENCH phase=%lu armed=%lu zero=%lu missed=%lu\n",
        (unsigned long)g_bench.phase, (unsigned long)g_bench.armed,
        (unsigned long)g_bench.zero_frames, (unsigned long)g_bench.missed_deadlines);
    for (uint i = 0; i < MOTORS; ++i) {
        console_printf("M%u pin=%u value=%lu submitted=%lu valid=%lu timeout=%lu invalid=%lu raw=%03lx period_us=%lu erpm=%lu\n",
            i + 1, motor_pin[i], (unsigned long)g_bench.requested[i],
            (unsigned long)g_bench.submitted[i], (unsigned long)g_bench.valid[i],
            (unsigned long)g_bench.timeout[i], (unsigned long)g_bench.invalid[i],
            (unsigned long)g_bench.last_payload[i], (unsigned long)g_bench.period_us[i],
            (unsigned long)g_bench.erpm[i]);
    }
}

static void recover_motor(uint i) {
    pio_sm_set_enabled(motor_pio, i, false);
    dma_channel_abort((uint)tx_dma[i]);
    dma_channel_abort((uint)rx_dma[i]);
    pio_sm_clear_fifos(motor_pio, i);
    pio_sm_restart(motor_pio, i);
    pio_sm_exec(motor_pio, i, pio_encode_jmp(program_offset));
    pio_sm_set_pins_with_mask(motor_pio, i, 1u << motor_pin[i], 1u << motor_pin[i]);
    pio_sm_set_pindirs_with_mask(motor_pio, i, 0, 1u << motor_pin[i]);
    pio_sm_set_enabled(motor_pio, i, true);
}

static void init_motor(uint i) {
    const uint pin = motor_pin[i];
    pio_sm_claim(motor_pio, i);
    pio_sm_config c = dshot_600_bidir_program_get_default_config(program_offset);
    sm_config_set_set_pins(&c, pin, 1);
    sm_config_set_in_pins(&c, pin);
    sm_config_set_jmp_pin(&c, pin);
    sm_config_set_out_shift(&c, false, false, 32);
    sm_config_set_in_shift(&c, false, true, 32);
    // Native150MHz clock /2 =75MHz;125PIO clocks per DShot600 bit.
    sm_config_set_clkdiv_int_frac(&c, 2, 0);
    pio_gpio_init(motor_pio, pin);
    pio_sm_init(motor_pio, i, program_offset, &c);
    pio_sm_set_pins_with_mask(motor_pio, i, 1u << pin, 1u << pin);
    pio_sm_set_consecutive_pindirs(motor_pio, i, pin, 1, false);
    gpio_set_pulls(pin, true, false);
    tx_dma[i] = dma_claim_unused_channel(true);
    rx_dma[i] = dma_claim_unused_channel(true);
    dma_channel_config tx = dma_channel_get_default_config((uint)tx_dma[i]);
    channel_config_set_transfer_data_size(&tx, DMA_SIZE_32);
    channel_config_set_read_increment(&tx, false);
    channel_config_set_write_increment(&tx, false);
    channel_config_set_dreq(&tx, pio_get_dreq(motor_pio, i, true));
    dma_channel_configure((uint)tx_dma[i], &tx, &motor_pio->txf[i], &tx_word[i], 1, false);
    dma_channel_config rx = dma_channel_get_default_config((uint)rx_dma[i]);
    channel_config_set_transfer_data_size(&rx, DMA_SIZE_32);
    channel_config_set_read_increment(&rx, false);
    channel_config_set_write_increment(&rx, true);
    channel_config_set_dreq(&rx, pio_get_dreq(motor_pio, i, false));
    dma_channel_configure((uint)rx_dma[i], &rx, rx_word[i], &motor_pio->rxf[i], 4, false);
    pio_sm_set_enabled(motor_pio, i, true);
}

static void begin_frame(uint64_t now) {
    uint32_t rx_mask = 0, tx_mask = 0;
    bool all_zero = true;
    for (uint i = 0; i < MOTORS; ++i) {
        tx_word[i] = dshot_frame((uint16_t)g_bench.requested[i]);
        all_zero = all_zero && g_bench.requested[i] == 0;
        dma_channel_set_write_addr((uint)rx_dma[i], rx_word[i], false);
        dma_channel_set_trans_count((uint)rx_dma[i], 4, false);
        dma_channel_set_read_addr((uint)tx_dma[i], &tx_word[i], false);
        dma_channel_set_trans_count((uint)tx_dma[i], 1, false);
        rx_mask |= 1u << (uint)rx_dma[i];
        tx_mask |= 1u << (uint)tx_dma[i];
        ++g_bench.submitted[i];
    }
    __dmb();
    dma_start_channel_mask(rx_mask);
    dma_start_channel_mask(tx_mask);
    if (all_zero) ++g_bench.zero_frames; else g_bench.zero_frames = 0;
    receive_deadline = now + REPLY_TIMEOUT_US;
    inflight = true;
}

static bool replies_complete(void) {
    for (uint i = 0; i < MOTORS; ++i)
        if (dma_channel_is_busy((uint)rx_dma[i])) return false;
    return true;
}

static void finish_frame(uint64_t now) {
    for (uint i = 0; i < MOTORS; ++i) {
        if (dma_channel_is_busy((uint)rx_dma[i])) {
            ++g_bench.timeout[i];
            recover_motor(i);
            continue;
        }
        uint16_t payload = 0;
        __dmb();
        uint32_t samples[4];
        for (uint j = 0; j < 4; ++j) samples[j] = rx_word[i][j];
        telemetry_result_t result = telemetry_decode(samples, &payload);
        if (result == TELEMETRY_OK && telemetry_is_erpm(payload)) {
            ++g_bench.valid[i];
            last_valid_us[i] = now;
            g_bench.last_payload[i] = payload;
            g_bench.period_us[i] = telemetry_period_us(payload);
            g_bench.erpm[i] = telemetry_erpm(payload);
        } else {
            ++g_bench.invalid[i];
        }
    }
    inflight = false;
}

static bool replies_fresh(uint64_t now) {
    for (uint i = 0; i < MOTORS; ++i)
        if (!last_valid_us[i] || now - last_valid_us[i] > 100000u) return false;
    return true;
}

static bool ready_to_arm(uint64_t now) {
    if (g_bench.phase != 2 || g_bench.zero_frames < ZERO_FRAMES_REQUIRED) return false;
    for (uint i = 0; i < MOTORS; ++i)
        if (g_bench.valid[i] < VALID_REPLIES_REQUIRED) return false;
    return replies_fresh(now);
}

static bool number(char **cursor, unsigned long max, unsigned long *out) {
    char *s = *cursor;
    while (*s == ' ') ++s;
    if (*s < '0' || *s > '9') return false;
    char *end; errno = 0;
    unsigned long n = strtoul(s, &end, 10);
    if (errno || end == s || n > max) return false;
    *cursor = end; *out = n;
    return true;
}
static bool end_of_command(char *s) {
    while (*s == ' ') ++s;
    return *s == 0;
}
static void command(char *line, uint64_t now) {
    if (!strcmp(line, "status")) { status(); ++g_bench.command_ok; return; }
    if (!strcmp(line, "stop")) { stop(); console_line("OK stopped"); ++g_bench.command_ok; return; }
    if (!strcmp(line, "arm")) {
        if (!ready_to_arm(now)) { console_line("ERR not-ready"); ++g_bench.command_error; return; }
        g_bench.armed = 1; command_deadline = now + COMMAND_TIMEOUT_US;
        console_line("OK bench-armed"); ++g_bench.command_ok; return;
    }
    bool all = !strncmp(line, "all ", 4);
    bool one = !strncmp(line, "set ", 4);
    char *cursor = line + (all || one ? 4 : 0);
    unsigned long motor = 0, value = 0;
    if ((!all && !one) || (one && (!number(&cursor, MOTORS, &motor) || motor < 1))
        || !number(&cursor, 2047, &value) || !end_of_command(cursor)
        || (value != 0 && value < 48)) {
        console_line("ERR command"); ++g_bench.command_error; return;
    }
    if (value && !g_bench.armed) { console_line("ERR arm-required"); ++g_bench.command_error; return; }
    if (all && !value) { stop(); } else {
        for (uint i = 0; i < MOTORS; ++i) if (all || i + 1 == motor) g_bench.requested[i] = (uint32_t)value;
        command_deadline = now + COMMAND_TIMEOUT_US;
    }
    console_line("OK value"); ++g_bench.command_ok;
}

static void serial_input(uint64_t now) {
    static char line[64]; static unsigned used; static bool overflow;
    for (unsigned budget = 0; budget < 32; ++budget) {
        if (!uart_is_readable(uart0)) break;
        int ch = uart_getc(uart0);
        if (ch == '\r') continue;
        if (ch == '\n') {
            line[used] = 0;
            if (overflow) { console_line("ERR line-too-long"); ++g_bench.command_error; }
            else if (used) command(line, now);
            used = 0; overflow = false;
        } else if (used + 1 < sizeof line && !overflow) line[used++] = (char)ch;
        else overflow = true;
    }
}

int main(void) {
    // Keep reset high-Z intact. AM32 PB4 bootloader must see its own pull-down.
    for (uint i = 0; i < MOTORS; ++i) { gpio_init(motor_pin[i]); gpio_set_dir(motor_pin[i], GPIO_IN); gpio_disable_pulls(motor_pin[i]); }
    uart_init(uart0, 115200);
    gpio_set_function(0, GPIO_FUNC_UART); gpio_set_function(1, GPIO_FUNC_UART);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_fifo_enabled(uart0, true);
    gpio_init(12); gpio_set_dir(12, GPIO_OUT); gpio_put(12, false);
    g_bench.phase = 1;
    console_line("OPENFC_NATIVE_MOTOR_BENCH v1 RP2354B release=750ms DShot600-bidir UART0=0/1");
    uint64_t release_until = time_us_64() + RELEASE_US;
    while (time_us_64() < release_until) { console_poll(); serial_input(time_us_64()); sleep_ms(1); }
    if (clock_get_hz(clk_sys) != 150000000u) { console_line("FATAL clock-contract"); while (true) { console_poll(); tight_loop_contents(); } }
    program_offset = pio_add_program(motor_pio, &dshot_600_bidir_program);
    for (uint i = 0; i < MOTORS; ++i) init_motor(i);
    sleep_us(1000); // physical idle-high after the released startup interval
    g_bench.phase = 2;
    console_line("BENCH zero-qualification");
    uint64_t next_frame = time_us_64();
    uint64_t next_status = next_frame + 1000000u;
    while (true) {
        uint64_t now = time_us_64();
        serial_input(now);
        console_poll();
        gpio_put(12, g_bench.armed || ((now / 500000u) & 1u));
        if (g_bench.armed && now >= command_deadline) { stop(); ++g_bench.watchdog_stops; console_line("STOP command-timeout"); }
        if (g_bench.armed && !replies_fresh(now)) { stop(); ++g_bench.telemetry_stops; console_line("STOP telemetry-timeout"); }
        if (inflight && (replies_complete() || now >= receive_deadline)) finish_frame(now);
        if (now >= next_frame) {
            if (inflight) finish_frame(now);
            begin_frame(now);
            next_frame += FRAME_US;
            if (next_frame <= now) { ++g_bench.missed_deadlines; next_frame = now + FRAME_US; }
        }
        if (now >= next_status) { status(); next_status = now + 1000000u; }
        // PIO/DMA owns wire timing. A25us poll bounds console and receive
        // service latency without occupying the CPU between deadlines.
        sleep_us(25);
    }
}
