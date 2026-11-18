/* SPDX-License-Identifier: MIT
 * STEVAL-IOM001V1 two-port binding for NUCLEO-L476RG.
 * Pin provenance: hardware/master-pin-map.json (UM2414, UM1724, DS10198).
 * Hardware BSP only. The simulator fixture has a different pin assignment.
 */
#ifndef LABWIRED_IOLINK_MASTER_PINMAP_H
#define LABWIRED_IOLINK_MASTER_PINMAP_H

#include "stm32l4xx_hal.h"

#define IOLINK_MASTER_PORT_COUNT 2U
#define IOLINK_MASTER_I2C I2C1
#define IOLINK_MASTER_I2C_AF GPIO_AF4_I2C1
#define IOLINK_MASTER_I2C_SCL_PORT GPIOB
#define IOLINK_MASTER_I2C_SCL_PIN GPIO_PIN_8
#define IOLINK_MASTER_I2C_SDA_PORT GPIOB
#define IOLINK_MASTER_I2C_SDA_PIN GPIO_PIN_9

typedef struct {
    GPIO_TypeDef *port;
    uint16_t pin;
} iolink_gpio_t;

typedef struct {
    USART_TypeDef *uart;
    uint32_t alternate_function;
    iolink_gpio_t tx, rx, cq_enable, lplus_enable, reset_n, irq_n, high_load_enable;
    uint16_t i2c_address_hal;
} iolink_master_pinmap_t;

/* HAL uses the seven-bit address shifted left once: 0x60/0x61 -> 0xC0/0xC2. */
static const iolink_master_pinmap_t IOLINK_MASTER_PINMAP[IOLINK_MASTER_PORT_COUNT] = {
    {USART1,
     GPIO_AF7_USART1,
     {GPIOA, GPIO_PIN_9},
     {GPIOA, GPIO_PIN_10},
     {GPIOC, GPIO_PIN_0},
     {GPIOA, GPIO_PIN_6},
     {GPIOB, GPIO_PIN_5},
     {GPIOA, GPIO_PIN_4},
     {GPIOB, GPIO_PIN_4},
     0xC0U},
    {UART4,
     GPIO_AF8_UART4,
     {GPIOA, GPIO_PIN_0},
     {GPIOA, GPIO_PIN_1},
     {GPIOA, GPIO_PIN_5},
     {GPIOA, GPIO_PIN_8},
     {GPIOC, GPIO_PIN_1},
     {GPIOB, GPIO_PIN_0},
     {GPIOA, GPIO_PIN_7},
     0xC2U}};

#endif
