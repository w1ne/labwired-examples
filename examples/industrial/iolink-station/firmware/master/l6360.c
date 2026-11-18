/* SPDX-License-Identifier: MIT
 * Protocol and register values: ST L6360 DS8900 Rev 9, September 2023.
 * Current write: section 7.2 equation 2 (DATA then parity/register byte).
 * Random read: section 7.2 figure 34 (address-write STOP, then read START).
 * The implementation never uses HAL_I2C_Mem_Write: this is not that protocol.
 */
#include "l6360.h"
#include <string.h>

/* ENCGQ=1; 220 mA cut-off; 100 us cut-off delay; no receiver debounce.
 * No debounce permits COM3 as well as the package's nominal COM2 rate.
 */
#define CONTROL1_COMMUNICATION 0xA0U
/* ENCGQ=1; 580 mA cut-off; 200 us delay; no receiver debounce.
 * The 80 us pulse ends before this delay. Protection remains enabled.
 */
#define CONTROL1_WAKE 0xF0U
/* C/Q input current 5.5 mA, L+ cut-off enabled at 500 us, 64 ms restart.
 * Unused I/Q pull-down is off. No input debounce.
 */
#define CONTROL2_COMMUNICATION 0x20U

static uint8_t parity(uint8_t value) {
    value ^= value >> 4;
    value ^= value >> 2;
    value ^= value >> 1;
    return value & 1U;
}

uint8_t l6360_write_check_byte(uint8_t address, uint8_t data) {
    /* DS8900 equation 2. P1 covers D7/D5/D3/D1; P2 D6/D4/D2/D0. */
    return (uint8_t)((parity(data) << 5) | (parity(data & 0xAAU) << 6) |
                     (parity(data & 0x55U) << 7) | (address & 0x0FU));
}

void l6360_shutdown(l6360_t *dev) {
    if (!dev)
        return;
    if (dev->io.cq_enable)
        dev->io.cq_enable(dev->io.user, false);
    if (dev->io.lplus_enable)
        dev->io.lplus_enable(dev->io.user, false);
    dev->powered = false;
}

static int fail(l6360_t *dev, int error) {
    l6360_shutdown(dev);
    dev->configured = false;
    dev->last_error = error;
    return error;
}

static int write_bytes(l6360_t *dev, const uint8_t *data, size_t length) {
    if (dev->io.write(dev->io.user, dev->address7, data, length) != 0)
        return fail(dev, L6360_ERR_IO);
    return L6360_OK;
}

static int read_bytes(l6360_t *dev, uint8_t *data, size_t length) {
    if (dev->io.read(dev->io.user, dev->address7, data, length) != 0)
        return fail(dev, L6360_ERR_IO);
    return L6360_OK;
}

int l6360_read_all(l6360_t *dev) {
    uint8_t start = L6360_REG_STATUS;
    uint8_t data[9], expected = 0;
    if (!dev || !dev->io.write || !dev->io.read)
        return L6360_ERR_ARG;
    if (write_bytes(dev, &start, 1) || read_bytes(dev, data, sizeof(data)))
        return dev->last_error;
    for (unsigned i = 0; i < 8; ++i)
        expected |= (uint8_t)(parity(data[i]) << (7U - i));
    if (expected != data[L6360_REG_PARITY])
        return fail(dev, L6360_ERR_PARITY);
    memcpy(dev->registers, data, sizeof(data));
    if (data[L6360_REG_STATUS] & L6360_STATUS_FAULTS) {
        dev->latched_faults |= data[L6360_REG_STATUS] & L6360_STATUS_FAULTS;
        return fail(dev, L6360_ERR_FAULT);
    }
    return L6360_OK;
}

static uint8_t writable_mask(uint8_t address) {
    if (address == L6360_REG_CONFIG)
        return 0xE0U;
    if (address == L6360_REG_CONTROL2)
        return 0xBFU; /* bit 6 is unused */
    return 0xFFU;
}

int l6360_write_checked(l6360_t *dev, uint8_t address, uint8_t data) {
    uint8_t bytes[2] = {data, l6360_write_check_byte(address, data)};
    if (!dev || address < L6360_REG_CONFIG || address > L6360_REG_LED2_L)
        return L6360_ERR_ARG;
    if (dev->last_error != L6360_OK)
        return dev->last_error;
    if (write_bytes(dev, bytes, sizeof(bytes)) || l6360_read_all(dev))
        return dev->last_error;
    if (((dev->registers[address] ^ data) & writable_mask(address)) != 0)
        return fail(dev, L6360_ERR_READBACK);
    return L6360_OK;
}

static bool active(uint8_t mode) { return mode != L6360_OFF && mode != L6360_TRISTATE; }

int l6360_set_mode(l6360_t *dev, l6360_mode_t mode) {
    uint8_t current;
    if (!dev || !dev->io.cq_enable)
        return L6360_ERR_ARG;
    dev->io.cq_enable(dev->io.user, false);
    if (dev->last_error != L6360_OK)
        return dev->last_error;
    if (mode != L6360_OFF && mode != L6360_LOW_SIDE && mode != L6360_HIGH_SIDE &&
        mode != L6360_PUSH_PULL && mode != L6360_TRISTATE)
        return L6360_ERR_ARG;
    current = dev->registers[L6360_REG_CONFIG] & 0xE0U;
    /* DS8900 p23: changing between active bridge modes requires OFF/tri-state. */
    if (current != (uint8_t)mode && active(current) && active((uint8_t)mode)) {
        int ret = l6360_write_checked(dev, L6360_REG_CONFIG, L6360_TRISTATE);
        if (ret)
            return ret;
    }
    if (current == (uint8_t)mode)
        return L6360_OK;
    return l6360_write_checked(dev, L6360_REG_CONFIG, (uint8_t)mode);
}

static int current_status(l6360_t *dev, bool allow_startup_po) {
    uint8_t data[2], faults;
    if (read_bytes(dev, data, sizeof(data)))
        return dev->last_error;
    if (parity(data[0]) != ((data[1] >> 7) & 1U))
        return fail(dev, L6360_ERR_PARITY);
    dev->registers[L6360_REG_STATUS] = data[0];
    dev->registers[L6360_REG_PARITY] = data[1];
    faults = data[0] & L6360_STATUS_FAULTS;
    if (allow_startup_po) {
        /* DS8900 p17: ENL+ rising edge sets PO; a successful current read clears
         * the historical flag only when the supply has crossed its threshold.
         * The next read must be clean. No other status bit is exempted.
         */
        dev->startup_status = data[0];
        faults &= (uint8_t)~L6360_STATUS_PO;
    }
    if (faults) {
        dev->latched_faults |= faults;
        return fail(dev, L6360_ERR_FAULT);
    }
    return L6360_OK;
}

int l6360_poll_faults(l6360_t *dev) {
    if (!dev || !dev->io.read)
        return L6360_ERR_ARG;
    if (dev->last_error != L6360_OK)
        return dev->last_error;
    return current_status(dev, false);
}

int l6360_init(l6360_t *dev, const l6360_io_t *io, uint8_t address7) {
    if (!dev || !io || !io->write || !io->read || !io->cq_enable || !io->lplus_enable ||
        !io->delay_us || !io->pulse || address7 < 0x60U || address7 > 0x67U)
        return L6360_ERR_ARG;
    memset(dev, 0, sizeof(*dev));
    dev->io = *io;
    dev->address7 = address7;
    l6360_shutdown(dev);
    if (l6360_read_all(dev) || l6360_set_mode(dev, L6360_TRISTATE) ||
        l6360_write_checked(dev, L6360_REG_CONTROL1, CONTROL1_COMMUNICATION) ||
        l6360_write_checked(dev, L6360_REG_CONTROL2, CONTROL2_COMMUNICATION) ||
        l6360_set_mode(dev, L6360_PUSH_PULL))
        return dev->last_error;
    dev->configured = true;
    return L6360_OK;
}

int l6360_power(l6360_t *dev, bool enabled) {
    if (!dev || !dev->io.lplus_enable || !dev->io.cq_enable)
        return L6360_ERR_ARG;
    if (!enabled) {
        l6360_shutdown(dev);
        return L6360_OK;
    }
    if (!dev->configured || dev->last_error != L6360_OK)
        return dev->last_error ? dev->last_error : L6360_ERR_STATE;
    dev->io.cq_enable(dev->io.user, false);
    dev->io.lplus_enable(dev->io.user, true);
    dev->io.delay_us(dev->io.user, 10000U);
    if (current_status(dev, true) || current_status(dev, false))
        return dev->last_error;
    dev->powered = true;
    return L6360_OK;
}

int l6360_prepare_tx(l6360_t *dev) {
    if (!dev || !dev->io.cq_enable)
        return L6360_ERR_ARG;
    if (!dev->configured || !dev->powered || dev->last_error != L6360_OK ||
        (dev->registers[L6360_REG_CONFIG] & 0xE0U) != L6360_PUSH_PULL) {
        dev->io.cq_enable(dev->io.user, false);
        return dev->last_error ? dev->last_error : L6360_ERR_STATE;
    }
    dev->io.cq_enable(dev->io.user, true);
    return L6360_OK;
}

int l6360_prepare_rx(l6360_t *dev) {
    if (!dev || !dev->io.cq_enable)
        return L6360_ERR_ARG;
    dev->io.cq_enable(dev->io.user, false);
    return dev->last_error;
}

int l6360_wake(l6360_t *dev) {
    if (!dev || !dev->configured || !dev->powered)
        return L6360_ERR_STATE;
    if (l6360_prepare_rx(dev) || l6360_set_mode(dev, L6360_PUSH_PULL) ||
        l6360_write_checked(dev, L6360_REG_CONTROL1, CONTROL1_WAKE))
        return dev->last_error;
    if (dev->io.pulse(dev->io.user, 80U) != 0)
        return fail(dev, L6360_ERR_IO);
    dev->io.cq_enable(dev->io.user, false);
    if (l6360_write_checked(dev, L6360_REG_CONTROL1, CONTROL1_COMMUNICATION))
        return dev->last_error;
    return L6360_OK;
}
