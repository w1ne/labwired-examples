/* SPDX-License-Identifier: MIT
 * Host unit fixtures for the datasheet-defined bus contract and fail-closed
 * behavior. These do not emulate a microcontroller or prove a physical bus.
 */
#include "../l6360.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t reg[9], address7, select;
    bool cq, power, fail_write, bad_parity, mismatch, persistent_po;
    bool startup_po, bad_write_parity;
    unsigned writes, reads, pulses, last_pulse_us, delay_us;
    uint8_t config_writes[8];
    unsigned config_count;
} fixture_t;

static uint8_t fixture_parity(const uint8_t *bytes) {
    uint8_t result = 0;
    for (unsigned i = 0; i < 8; ++i) {
        unsigned ones = 0;
        for (unsigned bit = 0; bit < 8; ++bit)
            ones += (bytes[i] >> bit) & 1U;
        result |= (uint8_t)((ones % 2U) << (7U - i));
    }
    return result;
}
/* DS8900 Rev9: lower PARITY bits store parity of received write DATA.
 * Reserved read bits are not the bytes that were received on the bus.
 */
static void store_received_parity(fixture_t *f, unsigned reg, uint8_t data) {
    uint8_t values[8] = {0};
    uint8_t mask = (uint8_t)(1U << (7U - reg));
    values[reg] = data;
    f->reg[8] = (uint8_t)((f->reg[8] & ~mask) | (fixture_parity(values) & mask));
}
static void store_register(fixture_t *f, unsigned reg, uint8_t data) {
    uint8_t mask = reg == 1 ? 0xE0U : (reg == 3 ? 0xBFU : 0xFFU);
    if (reg == 1 && f->config_count < 8)
        f->config_writes[f->config_count++] = data;
    if (!f->mismatch)
        f->reg[reg] = (uint8_t)((f->reg[reg] & ~mask) | (data & mask));
}
static int bus_write(void *user, uint8_t addr, const uint8_t *bytes, size_t len) {
    fixture_t *f = user;
    assert(addr == f->address7);
    ++f->writes;
    if (f->fail_write)
        return -1;
    if (len == 1) {
        assert(bytes[0] == 0);
        f->select = 0;
        return 0;
    }
    if (len == 8) {
        uint8_t values[8] = {0};
        memcpy(values + 1, bytes, 7);
        uint8_t calculated = fixture_parity(values) & 0x7FU;
        f->reg[8] = (uint8_t)((f->reg[8] & 0x80U) | calculated);
        if (calculated != (bytes[7] & 0x7FU) || f->bad_write_parity) {
            f->reg[0] |= L6360_STATUS_PE;
            return 0; /* I2C ACK does not mean the register update was accepted. */
        }
        for (unsigned reg = 1; reg <= 7; ++reg)
            store_register(f, reg, bytes[reg - 1]);
        return 0;
    }
    assert(len == 2);
    const unsigned reg = bytes[1] & 15U;
    assert(reg >= 1 && reg <= 7);
    unsigned p0 = 0, p1 = 0, p2 = 0;
    for (unsigned bit = 0; bit < 8; ++bit) {
        unsigned value = (bytes[0] >> bit) & 1U;
        p0 ^= value;
        if (bit & 1U) p1 ^= value; else p2 ^= value;
    }
    store_received_parity(f, reg, bytes[0]);
    if (((bytes[1] >> 5) & 7U) != (p0 | (p1 << 1) | (p2 << 2)) || f->bad_write_parity) {
        f->reg[0] |= L6360_STATUS_PE;
        return 0;
    }
    store_register(f, reg, bytes[0]);
    return 0;
}
static int bus_read(void *user, uint8_t addr, uint8_t *bytes, size_t len) {
    fixture_t *f = user;
    assert(addr == f->address7);
    ++f->reads;
    f->reg[8] = (uint8_t)((f->reg[8] & 0x7FU) | (fixture_parity(f->reg) & 0x80U));
    if (len == 9)
        memcpy(bytes, f->reg, 9);
    else {
        assert(len == 2);
        bytes[0] = f->reg[0];
        bytes[1] = f->reg[8];
        if (!f->persistent_po)
            f->reg[0] &= (uint8_t)~L6360_STATUS_PO;
    }
    if (f->bad_parity)
        bytes[len - 1] ^= 0x80;
    return 0;
}
static void set_cq(void *user, bool on) { ((fixture_t *)user)->cq = on; }
static void set_power(void *user, bool on) {
    fixture_t *f = user;
    f->power = on;
    if (on && f->startup_po)
        f->reg[0] |= L6360_STATUS_PO;
}
static void delay(void *user, uint32_t us) { ((fixture_t *)user)->delay_us += us; }
static int pulse(void *user, uint32_t us) {
    fixture_t *f = user;
    assert(f->power && !f->cq);
    assert(f->reg[L6360_REG_CONTROL1] == 0xF0);
    f->pulses++;
    f->last_pulse_us = us;
    return 0;
}
static l6360_io_t callbacks(fixture_t *f) {
    return (l6360_io_t){f, bus_write, bus_read, set_cq, set_power, delay, pulse};
}
static fixture_t fixture(uint8_t address) {
    fixture_t f = {0};
    f.address7 = address;
    f.reg[1] = 0x80;
    f.reg[2] = 0x21;
    f.reg[3] = 0x21;
    return f;
}
static void init(l6360_t *d, fixture_t *f) {
    l6360_io_t io = callbacks(f);
    assert(l6360_init(d, &io, f->address7) == 0);
}
static void test_vectors(void) {
    /* Independent fixed vectors from DS8900 Eq.2, DATA then P2/P1/P0+address. */
    assert(l6360_write_check_byte(1, 0xE0) == 0xA1);
    assert(l6360_write_check_byte(1, 0x80) == 0x61);
    assert(l6360_write_check_byte(1, 0x81) == 0xC1);
    assert(l6360_write_check_byte(2, 0xF0) == 0x02);
    assert(l6360_write_check_byte(2, 0xA0) == 0x02);
    assert(l6360_write_check_byte(3, 0x20) == 0x63);
}
static void test_config(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    assert(d.configured && !d.powered && !f.cq && !f.power);
    assert(f.reg[1] == 0xE0 && f.reg[2] == 0xA0 && f.reg[3] == 0x20);
    assert(f.writes == 4 && f.reads == 3); /* status, sequential write/read, PP write/read */
}
static void test_bad_args(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    l6360_io_t io = callbacks(&f);
    assert(l6360_init(&d, &io, 0x20) == L6360_ERR_ARG);
    io.read = NULL;
    assert(l6360_init(&d, &io, 0x60) == L6360_ERR_ARG);
    assert(l6360_write_checked(NULL, 1, 0) == L6360_ERR_ARG);
}
static void test_readback(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    assert(l6360_power(&d, true) == 0);
    f.mismatch = true;
    assert(l6360_write_checked(&d, 2, 0xF0) == L6360_ERR_READBACK);
    assert(!f.cq && !f.power && !d.configured);
}
static void test_parity(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    f.bad_parity = true;
    assert(l6360_read_all(&d) == L6360_ERR_PARITY);
    assert(!f.cq && !f.power && !d.configured);
}
static void test_nack(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    assert(l6360_power(&d, true) == 0);
    assert(l6360_prepare_tx(&d) == 0);
    f.fail_write = true;
    assert(l6360_write_checked(&d, 2, 0xF0) == L6360_ERR_IO);
    assert(!f.cq && !f.power && !d.configured);
}
static void test_startup_po(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    f.startup_po = true;
    assert(l6360_power(&d, true) == 0);
    assert(d.powered && d.startup_status == 0x80 && d.latched_faults == 0);
    assert(f.delay_us == 10000);
}
static void test_persistent_po(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    f.startup_po = true;
    f.persistent_po = true;
    assert(l6360_power(&d, true) == L6360_ERR_FAULT);
    assert(d.latched_faults == 0x80 && !f.power);
}
static void test_fault_and_port_isolation(void) {
    fixture_t a = fixture(0x60), b = fixture(0x61);
    l6360_t da, db;
    init(&da, &a);
    init(&db, &b);
    assert(l6360_power(&da, true) == 0);
    assert(l6360_power(&db, true) == 0);
    assert(l6360_prepare_tx(&da) == 0);
    a.reg[0] = L6360_STATUS_CQOL;
    assert(l6360_poll_faults(&da) == L6360_ERR_FAULT);
    assert(da.latched_faults == L6360_STATUS_CQOL && !a.cq && !a.power);
    assert(db.configured && db.powered && b.power);
    assert(l6360_prepare_tx(&da) == L6360_ERR_FAULT);
}
static void test_active_mode_transition(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    f.config_count = 0;
    assert(l6360_set_mode(&d, L6360_HIGH_SIDE) == 0);
    assert(f.config_count == 2 && f.config_writes[0] == 0x80 && f.config_writes[1] == 0x40);
    assert(!f.cq);
}
static void test_direction(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    assert(l6360_prepare_tx(&d) == L6360_ERR_STATE && !f.cq);
    assert(l6360_power(&d, true) == 0);
    assert(l6360_prepare_tx(&d) == 0 && f.cq);
    assert(l6360_prepare_rx(&d) == 0 && !f.cq && f.power);
    assert(l6360_power(&d, false) == 0 && !f.cq && !f.power);
}
static void test_wake(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    assert(l6360_wake(&d) == L6360_ERR_STATE && f.pulses == 0);
    assert(l6360_power(&d, true) == 0);
    assert(l6360_wake(&d) == 0);
    assert(f.pulses == 1 && f.last_pulse_us == 80 && !f.cq);
    assert(f.reg[2] == 0xA0 && d.configured && d.powered);
}
static void test_reset_parity_contract(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    assert(f.reg[8] == 0 && f.reg[1] == 0x80);
    assert(fixture_parity(f.reg) == 0x40); /* reset PARITY is not recomputed */
    init(&d, &f);
    assert(d.configured && f.reg[8] == 0x50);
}
static void test_unknown_reserved_read_bits(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    f.reg[1] |= 0x1FU;
    f.reg[3] |= 0x40U;
    init(&d, &f);
    assert(f.reg[1] == 0xFF && f.reg[3] == 0x60);
    assert(f.reg[8] == 0x50); /* parity of transmitted E0/A0/20/zero LEDs */
    assert(l6360_read_all(&d) == 0);
}
static void test_initial_status_parity_failure(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    l6360_io_t io = callbacks(&f);
    f.bad_parity = true;
    assert(l6360_init(&d, &io, f.address7) == L6360_ERR_PARITY);
    assert(f.writes == 0 && !f.cq && !f.power && !d.configured);
}
static void test_rejected_sequential_write(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    l6360_io_t io = callbacks(&f);
    f.bad_write_parity = true;
    assert(l6360_init(&d, &io, f.address7) == L6360_ERR_FAULT);
    assert(f.reg[1] == 0x80 && f.reg[2] == 0x21 && f.reg[3] == 0x21);
    assert(d.latched_faults == L6360_STATUS_PE && !f.cq && !f.power);
}
static void test_register_changes_without_parity_refresh(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    f.reg[2] ^= 1U;
    assert(l6360_read_all(&d) == L6360_ERR_READBACK);
    assert(!f.cq && !f.power && !d.configured);
}
static void test_stored_parity_corruption(void) {
    fixture_t f = fixture(0x60);
    l6360_t d;
    init(&d, &f);
    f.reg[8] ^= 0x20U;
    assert(l6360_read_all(&d) == L6360_ERR_PARITY);
    assert(!f.cq && !f.power && !d.configured);
}
int main(void) {
    test_vectors();
    test_reset_parity_contract();
    test_unknown_reserved_read_bits();
    test_initial_status_parity_failure();
    test_rejected_sequential_write();
    test_register_changes_without_parity_refresh();
    test_stored_parity_corruption();
    test_config();
    test_bad_args();
    test_readback();
    test_parity();
    test_nack();
    test_startup_po();
    test_persistent_po();
    test_fault_and_port_isolation();
    test_active_mode_transition();
    test_direction();
    test_wake();
    puts("{\"suite\":\"l6360-datasheet-contract\",\"passed\":18,\"failed\":0,\"scope\":\"host unit "
         "tests; no physical bus or timing measurement\"}");
    return 0;
}
