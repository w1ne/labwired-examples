/* SPDX-License-Identifier: MIT
 * L6360 protocol driver, derived from ST DS8900 Rev 9, sections 6.8/6.9/7.2/8.
 * This is application source, not STSW-IOM001 or a replacement MCU HAL.
 */
#ifndef LABWIRED_L6360_H
#define LABWIRED_L6360_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    L6360_REG_STATUS = 0,
    L6360_REG_CONFIG = 1,
    L6360_REG_CONTROL1 = 2,
    L6360_REG_CONTROL2 = 3,
    L6360_REG_LED1_H = 4,
    L6360_REG_LED1_L = 5,
    L6360_REG_LED2_H = 6,
    L6360_REG_LED2_L = 7,
    L6360_REG_PARITY = 8
};
enum {
    L6360_STATUS_PO = 0x80,
    L6360_STATUS_OVT = 0x20,
    L6360_STATUS_CQOL = 0x10,
    L6360_STATUS_LOL = 0x08,
    L6360_STATUS_REGLN = 0x02,
    L6360_STATUS_PE = 0x01,
    L6360_STATUS_FAULTS = 0xBB
};
typedef enum {
    L6360_OFF = 0x00,
    L6360_LOW_SIDE = 0x20,
    L6360_HIGH_SIDE = 0x40,
    L6360_PUSH_PULL = 0xE0,
    L6360_TRISTATE = 0x80
} l6360_mode_t;
typedef enum {
    L6360_OK = 0,
    L6360_ERR_ARG = -1,
    L6360_ERR_IO = -2,
    L6360_ERR_PARITY = -3,
    L6360_ERR_READBACK = -4,
    L6360_ERR_FAULT = -5,
    L6360_ERR_STATE = -6
} l6360_result_t;

/* Each I2C callback is one complete START...STOP transaction.
 * Address is seven-bit here; the ST HAL adapter shifts it exactly once.
 * pulse() must generate a timed 80 us drive opposite to the current C/Q state,
 * then release ENCQ. It returns only after the output has been released.
 */
typedef struct {
    void *user;
    int (*write)(void *user, uint8_t address7, const uint8_t *data, size_t length);
    int (*read)(void *user, uint8_t address7, uint8_t *data, size_t length);
    void (*cq_enable)(void *user, bool enabled);
    void (*lplus_enable)(void *user, bool enabled);
    void (*delay_us)(void *user, uint32_t us);
    int (*pulse)(void *user, uint32_t us);
} l6360_io_t;

typedef struct {
    l6360_io_t io;
    uint8_t address7;
    uint8_t registers[9];
    uint8_t latched_faults;
    uint8_t startup_status;
    int last_error;
    bool configured;
    bool powered;
} l6360_t;

uint8_t l6360_write_check_byte(uint8_t address, uint8_t data);
int l6360_init(l6360_t *dev, const l6360_io_t *io, uint8_t address7);
int l6360_read_all(l6360_t *dev);
int l6360_write_checked(l6360_t *dev, uint8_t address, uint8_t data);
int l6360_set_mode(l6360_t *dev, l6360_mode_t mode);
int l6360_power(l6360_t *dev, bool enabled);
int l6360_poll_faults(l6360_t *dev);
int l6360_prepare_tx(l6360_t *dev);
int l6360_prepare_rx(l6360_t *dev);
int l6360_wake(l6360_t *dev);
void l6360_shutdown(l6360_t *dev);
#endif
