/* SPDX-License-Identifier: MIT
 * Physical NUCLEO-L476RG + two STEVAL-IOM001V1 adapter.
 * MCU peripherals use ST STM32CubeL4 v1.18.2 HAL, not simulator registers.
 * See hardware/master-pin-map.json and README for board solder bridges.
 */
#include "board_hal.h"
#include "board_pinmap.h"
#include "l6360.h"
#include "station_clock.h"
#include "station_profile.h"
#include <limits.h>
#include <string.h>

#define RX_SIZE 128U
#define COM2_BAUD 38400U
/* RM0351 I2C timing; 80 MHz kernel, analog filter ON, DNF=0.
 * PRESC=2,SCLDEL=15,SDADEL=7,SCLH=27,SCLL=39. Fast mode <=400 kHz,
 * rise/fall <=300 ns. The conservative clock/filter corner analysis is in
 * tests/check_timing.py. The shield/header bus must meet those edge limits. */
#define I2C_FAST_TIMING 0x20F71B27U
/* 500 us T_REN + ceil(32 bit times at COM2), measured AFTER wake release.
 * This physical guard remains valid if I2C readback delays the callback. */
#define WAKE_TO_TEST_US (500U + (32000000U + COM2_BAUD - 1U) / COM2_BAUD)

typedef struct {
    unsigned index;
    UART_HandleTypeDef uart;
    TIM_HandleTypeDef pulse_timer;
    uint32_t pulse_channel;
    l6360_t phy;
    volatile uint16_t head, tail;
    uint8_t rx_byte, rx[RX_SIZE];
    volatile bool rx_error;
    bool wake_guard;
    uint32_t wake_released_us;
} port_t;

static I2C_HandleTypeDef i2c;
static port_t ports[BOARD_PORTS];
volatile uint32_t g_uart_errors[BOARD_PORTS];
volatile uint32_t g_rx_overflows[BOARD_PORTS];
volatile uint8_t g_phy_faults[BOARD_PORTS];
volatile int g_phy_error[BOARD_PORTS];
volatile uint32_t g_wake_count[BOARD_PORTS];

static const iolink_master_pinmap_t *pins(const port_t *p) {
    return &IOLINK_MASTER_PINMAP[p->index];
}
static void write_pin(iolink_gpio_t p, bool high) {
    HAL_GPIO_WritePin(p.port, p.pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}
static void output_pin(iolink_gpio_t p, bool high) {
    GPIO_InitTypeDef g = {0};
    write_pin(p, high);
    g.Pin = p.pin;
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(p.port, &g);
}
static void input_pin(iolink_gpio_t p, uint32_t pull) {
    GPIO_InitTypeDef g = {0};
    g.Pin = p.pin;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = pull;
    HAL_GPIO_Init(p.port, &g);
}
static void alternate_pin(iolink_gpio_t p, uint32_t af) {
    GPIO_InitTypeDef g = {0};
    g.Pin = p.pin;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = af;
    HAL_GPIO_Init(p.port, &g);
}
uint32_t board_now_us(void) { return station_now_us(); }
uint32_t board_now_100us(void) { return station_now_100us(); }
static void delay_us(void *user, uint32_t us) {
    (void)user;
    station_delay_us(us);
}
static void cq_enable(void *user, bool enabled) {
    port_t *p = user;
    write_pin(pins(p)->cq_enable, enabled);
}
static void lplus_enable(void *user, bool enabled) {
    port_t *p = user;
    write_pin(pins(p)->lplus_enable, enabled);
}
static int i2c_write(void *user, uint8_t addr, const uint8_t *data, size_t n) {
    (void)user;
    if (!data || !n || n > UINT16_MAX)
        return -1;
    return HAL_I2C_Master_Transmit(&i2c, (uint16_t)addr << 1, (uint8_t *)data, (uint16_t)n, 10) ==
                   HAL_OK
               ? 0
               : -1;
}
static int i2c_read(void *user, uint8_t addr, uint8_t *data, size_t n) {
    (void)user;
    if (!data || !n || n > UINT16_MAX)
        return -1;
    return HAL_I2C_Master_Receive(&i2c, (uint16_t)addr << 1, data, (uint16_t)n, 10) == HAL_OK ? 0
                                                                                              : -1;
}
static int rx_arm(port_t *p) {
    if (p->uart.RxState == HAL_UART_STATE_BUSY_RX)
        return 0;
    return HAL_UART_Receive_IT(&p->uart, &p->rx_byte, 1) == HAL_OK ? 0 : -1;
}
static int flush(port_t *p) {
    if (HAL_UART_AbortReceive(&p->uart) != HAL_OK)
        return -1;
    const uint32_t mask = __get_PRIMASK();
    __disable_irq();
    p->tail = p->head;
    p->rx_error = false;
    __HAL_UART_CLEAR_FLAG(&p->uart,
                          UART_CLEAR_PEF | UART_CLEAR_FEF | UART_CLEAR_NEF | UART_CLEAR_OREF);
    __HAL_UART_SEND_REQ(&p->uart, UART_RXDATA_FLUSH_REQUEST);
    __set_PRIMASK(mask);
    return rx_arm(p);
}
static int uart_configure(port_t *p, iolink_baudrate_t baud) {
    /* This release is explicitly COM2. Unsupported rates return an error;
     * no successful no-op callback and no unqualified automatic scan. */
    if (baud != IOLINK_BAUDRATE_COM2)
        return -1;
    cq_enable(p, false);
    p->uart.Instance = pins(p)->uart;
    (void)HAL_UART_AbortReceive(&p->uart);
    p->uart.Init.BaudRate = COM2_BAUD;
    p->uart.Init.WordLength = UART_WORDLENGTH_9B; /* eight data bits + parity */
    p->uart.Init.StopBits = UART_STOPBITS_1;
    p->uart.Init.Parity = UART_PARITY_EVEN;
    p->uart.Init.Mode = UART_MODE_TX_RX;
    p->uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    p->uart.Init.OverSampling = UART_OVERSAMPLING_16;
    p->uart.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    p->uart.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    alternate_pin(pins(p)->tx, pins(p)->alternate_function);
    alternate_pin(pins(p)->rx, pins(p)->alternate_function);
    if (HAL_UART_Init(&p->uart) != HAL_OK)
        return -1;
    return flush(p);
}
static int pulse(void *user, uint32_t width_us) {
    port_t *p = user;
    TIM_HandleTypeDef *t = &p->pulse_timer;
    if (width_us != 80U)
        return -1;
    cq_enable(p, false);
    if (HAL_UART_AbortReceive(&p->uart) != HAL_OK)
        return -1;
    const bool rx_high = HAL_GPIO_ReadPin(pins(p)->rx.port, pins(p)->rx.pin) == GPIO_PIN_SET;
    /* L6360 RX=NOT C/Q while ENCQ=0; C/Q=NOT INCQ while transmitting.
     * PWM2 idles at the sampled RX level and drives its opposite for 80 us.
     * TIM1_CH2 is PA9 AF1; TIM2_CH1 is PA0 AF1 (DS10198 Table 17). */
    t->Instance = p->index == 0U ? TIM1 : TIM2;
    t->Init.Prescaler = 79U;
    t->Init.CounterMode = TIM_COUNTERMODE_UP;
    t->Init.Period = 80U;
    t->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    t->Init.RepetitionCounter = 0;
    t->Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_OnePulse_Init(t, TIM_OPMODE_SINGLE) != HAL_OK)
        return -1;
    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode = TIM_OCMODE_PWM2;
    oc.Pulse = 1U;
    oc.OCPolarity = rx_high ? TIM_OCPOLARITY_LOW : TIM_OCPOLARITY_HIGH;
    oc.OCNPolarity = TIM_OCNPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    oc.OCIdleState = rx_high ? TIM_OCIDLESTATE_SET : TIM_OCIDLESTATE_RESET;
    oc.OCNIdleState = TIM_OCNIDLESTATE_RESET;
    if (HAL_TIM_PWM_ConfigChannel(t, &oc, p->pulse_channel) != HAL_OK)
        return -1;
    __HAL_TIM_SET_COUNTER(t, 0);
    __HAL_TIM_CLEAR_FLAG(t, TIM_FLAG_UPDATE);
    alternate_pin(pins(p)->tx, p->index == 0U ? GPIO_AF1_TIM1 : GPIO_AF1_TIM2);
    /* OnePulse_Start enables the output, but does not start the counter.
     * Establish idle first; enable C/Q; then HAL_Base_Start starts the pulse.
     * Hardware returns to idle at update even if an IRQ delays this thread. */
    int result = -1;
    if (HAL_TIM_OnePulse_Start(t, p->pulse_channel) == HAL_OK) {
        cq_enable(p, true);
        if (HAL_TIM_Base_Start(t) == HAL_OK) {
            const uint32_t start = board_now_us();
            while (__HAL_TIM_GET_FLAG(t, TIM_FLAG_UPDATE) == RESET &&
                   (uint32_t)(board_now_us() - start) < 1000U) {
            }
            if (__HAL_TIM_GET_FLAG(t, TIM_FLAG_UPDATE) != RESET)
                result = 0;
        }
    }
    cq_enable(p, false);
    p->wake_released_us = board_now_us();
    p->wake_guard = result == 0;
    (void)HAL_TIM_Base_Stop(t);
    (void)HAL_TIM_OnePulse_Stop(t, p->pulse_channel);
    alternate_pin(pins(p)->tx, pins(p)->alternate_function);
    if (flush(p) != 0)
        result = -1;
    if (result == 0)
        ++g_wake_count[p->index];
    return result;
}
static int phy_init(void *user) {
    port_t *p = user;
    const iolink_master_pinmap_t *pm = pins(p);
    cq_enable(p, false);
    lplus_enable(p, false);
    write_pin(pm->high_load_enable, false);
    write_pin(pm->reset_n, false);
    delay_us(p, 1000);
    write_pin(pm->reset_n, true);
    delay_us(p, 1000);
    const l6360_io_t io = {p, i2c_write, i2c_read, cq_enable, lplus_enable, delay_us, pulse};
    int result = l6360_init(&p->phy, &io, (uint8_t)(pm->i2c_address_hal >> 1));
    if (result == 0)
        result = uart_configure(p, IOLINK_BAUDRATE_COM2);
    if (result == 0)
        result = l6360_power(&p->phy, true);
    g_phy_error[p->index] = result;
    return result;
}
static int mode(port_t *p, iolink_phy_mode_t value) {
    cq_enable(p, false);
    if (value == IOLINK_PHY_MODE_INACTIVE)
        return l6360_set_mode(&p->phy, L6360_TRISTATE);
    if (value == IOLINK_PHY_MODE_SDCI)
        return l6360_set_mode(&p->phy, L6360_PUSH_PULL);
    return -1; /* SIO outputs are not part of this master release. */
}
static int prepare_tx(port_t *p) {
    if (p->wake_guard) {
        while ((uint32_t)(board_now_us() - p->wake_released_us) < WAKE_TO_TEST_US) {
        }
        p->wake_guard = false;
    }
    if (HAL_UART_AbortReceive(&p->uart) != HAL_OK)
        return -1;
    return l6360_prepare_tx(&p->phy);
}
static int prepare_rx(port_t *p) {
    /* Arm UART before releasing the PHY: device can answer immediately. */
    if (rx_arm(p) != 0) {
        l6360_shutdown(&p->phy);
        return -1;
    }
    return l6360_prepare_rx(&p->phy);
}
static int send_bytes(void *user, const uint8_t *data, size_t n) {
    port_t *p = user;
    if (!data || !n || n > UINT16_MAX)
        return -1;
    /* HAL's blocking transmit waits for TC, including the final stop bit.
     * 11 bits/byte (8E1), bounded timeout even for a 66-byte stack frame. */
    const uint32_t timeout = (uint32_t)((n * 11000U + COM2_BAUD - 1U) / COM2_BAUD) + 3U;
    if (HAL_UART_Transmit(&p->uart, (uint8_t *)data, (uint16_t)n, timeout) != HAL_OK) {
        l6360_shutdown(&p->phy);
        g_phy_error[p->index] = -1;
        return -1;
    }
    return (int)n;
}
static int receive_byte(void *user, uint8_t *byte) {
    port_t *p = user;
    if (!byte)
        return -1;
    const uint32_t mask = __get_PRIMASK();
    __disable_irq();
    int result = 0;
    if (p->rx_error) {
        p->rx_error = false;
        p->tail = p->head;
        result = -1;
    } else if (p->tail != p->head) {
        *byte = p->rx[p->tail];
        p->tail = (p->tail + 1U) % RX_SIZE;
        result = 1;
    }
    __set_PRIMASK(mask);
    return result;
}
static void set_mode_legacy(void *user, iolink_phy_mode_t v) {
    port_t *p = user;
    g_phy_error[p->index] = mode(p, v);
}
static void set_baud_legacy(void *user, iolink_baudrate_t v) {
    port_t *p = user;
    g_phy_error[p->index] = uart_configure(p, v);
}
static bool fault(void *user) {
    const port_t *p = user;
    return p->phy.last_error != 0 || p->phy.latched_faults != 0;
}

#define PORT_CALLBACKS(N)                                                                          \
    static int mode_##N(iolink_phy_mode_t v) { return mode(&ports[N], v); }                        \
    static int baud_##N(iolink_baudrate_t v) { return uart_configure(&ports[N], v); }              \
    static int flush_##N(void) { return flush(&ports[N]); }                                        \
    static int tx_##N(void) { return prepare_tx(&ports[N]); }                                      \
    static int rx_##N(void) { return prepare_rx(&ports[N]); }                                      \
    static int wake_##N(void) { return l6360_wake(&ports[N].phy); }
PORT_CALLBACKS(0)
PORT_CALLBACKS(1)
void board_fill_master(iolink_phy_api_t phys[BOARD_PORTS],
                       iolink_master_config_t cfg[BOARD_PORTS]) {
    for (unsigned i = 0; i < BOARD_PORTS; ++i) {
        phys[i] = (iolink_phy_api_t){.user = &ports[i],
                                     .init = phy_init,
                                     .set_mode = set_mode_legacy,
                                     .set_baudrate = set_baud_legacy,
                                     .send = send_bytes,
                                     .recv_byte = receive_byte,
                                     .is_short_circuit = fault};
        cfg[i] = (iolink_master_config_t){
            .port_mode = IOLINK_MASTER_PORT_MODE_IOLINK,
            .m_seq_type = STATION_MASTER_MSEQ_TYPE,
            .baudrate = STATION_BAUDRATE,
            /* Pinned master implementation consumes this field in 100 us units;
             * its header's raw-octet comment is inconsistent with master_port.c. */
            .min_cycle_time = STATION_CYCLE_100US,
            .pd_in_len = STATION_PD_INPUT_BYTES,
            .pd_out_len = STATION_PD_OUTPUT_BYTES,
            .auto_baudrate = false,
            .response_timeout_100us = 50U};
    }
    cfg[0].set_mode_checked = mode_0;
    cfg[0].set_baudrate_checked = baud_0;
    cfg[0].flush_rx = flush_0;
    cfg[0].prepare_tx = tx_0;
    cfg[0].prepare_rx = rx_0;
    cfg[0].wake_up = wake_0;
    cfg[1].set_mode_checked = mode_1;
    cfg[1].set_baudrate_checked = baud_1;
    cfg[1].flush_rx = flush_1;
    cfg[1].prepare_tx = tx_1;
    cfg[1].prepare_rx = rx_1;
    cfg[1].wake_up = wake_1;
}
void board_poll_faults(void) {
    static uint32_t last;
    const uint32_t now = board_now_us();
    if ((uint32_t)(now - last) < 20000U)
        return;
    last = now;
    for (unsigned i = 0; i < BOARD_PORTS; ++i) {
        port_t *p = &ports[i];
        if (p->phy.configured)
            (void)l6360_poll_faults(&p->phy);
        g_phy_faults[i] = p->phy.latched_faults;
        g_phy_error[i] = p->phy.last_error;
    }
}
void board_shutdown(void) {
    for (unsigned i = 0; i < BOARD_PORTS; ++i) {
        cq_enable(&ports[i], false);
        lplus_enable(&ports[i], false);
    }
}
void USART1_IRQHandler(void) { HAL_UART_IRQHandler(&ports[0].uart); }
void UART4_IRQHandler(void) { HAL_UART_IRQHandler(&ports[1].uart); }
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *uart) {
    for (unsigned i = 0; i < BOARD_PORTS; ++i)
        if (uart == &ports[i].uart) {
            port_t *p = &ports[i];
            const uint16_t next = (p->head + 1U) % RX_SIZE;
            if (next == p->tail) {
                ++g_rx_overflows[i];
                p->rx_error = true;
            } else {
                p->rx[p->head] = p->rx_byte;
                p->head = next;
            }
            if (rx_arm(p) != 0)
                p->rx_error = true;
            return;
        }
}
void HAL_UART_ErrorCallback(UART_HandleTypeDef *uart) {
    for (unsigned i = 0; i < BOARD_PORTS; ++i)
        if (uart == &ports[i].uart) {
            ++g_uart_errors[i];
            ports[i].rx_error = true;
            (void)rx_arm(&ports[i]);
            return;
        }
}
int board_init(void) {
    if (station_clock_init() != 0)
        return -1;
    RCC_PeriphCLKInitTypeDef peripheral = {0};
    peripheral.PeriphClockSelection =
        RCC_PERIPHCLK_I2C1 | RCC_PERIPHCLK_USART1 | RCC_PERIPHCLK_UART4;
    peripheral.I2c1ClockSelection = RCC_I2C1CLKSOURCE_SYSCLK;
    peripheral.Usart1ClockSelection = RCC_USART1CLKSOURCE_PCLK2;
    peripheral.Uart4ClockSelection = RCC_UART4CLKSOURCE_PCLK1;
    if (HAL_RCCEx_PeriphCLKConfig(&peripheral) != HAL_OK)
        return -1;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_I2C1_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_UART4_CLK_ENABLE();
    __HAL_RCC_TIM1_CLK_ENABLE();
    __HAL_RCC_TIM2_CLK_ENABLE();
    for (unsigned i = 0; i < BOARD_PORTS; ++i) {
        port_t *p = &ports[i];
        p->index = i;
        p->pulse_channel = i == 0U ? TIM_CHANNEL_2 : TIM_CHANNEL_1;
        const iolink_master_pinmap_t *pm = pins(p);
        output_pin(pm->cq_enable, false);
        output_pin(pm->lplus_enable, false);
        output_pin(pm->high_load_enable, false);
        output_pin(pm->reset_n, false);
        input_pin(pm->irq_n, GPIO_PULLUP);
    }
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_8 | GPIO_PIN_9;
    gpio.Mode = GPIO_MODE_AF_OD;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    gpio.Alternate = GPIO_AF4_I2C1;
    HAL_GPIO_Init(GPIOB, &gpio);
    i2c.Instance = I2C1;
    i2c.Init.Timing = I2C_FAST_TIMING;
    i2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    i2c.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    i2c.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
    i2c.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    i2c.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&i2c) != HAL_OK ||
        HAL_I2CEx_ConfigAnalogFilter(&i2c, I2C_ANALOGFILTER_ENABLE) != HAL_OK ||
        HAL_I2CEx_ConfigDigitalFilter(&i2c, 0) != HAL_OK)
        return -1;
    HAL_NVIC_SetPriority(USART1_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_NVIC_SetPriority(UART4_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(UART4_IRQn);
    return 0;
}
