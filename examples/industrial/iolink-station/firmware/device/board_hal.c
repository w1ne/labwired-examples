/* SPDX-License-Identifier: MIT
 * NUCLEO-L476RG + STEVAL-IOD003V1 + native SN74HC165 input board.
 * L6362A logic/protection semantics remain in pinned iolinki/phy_l6362a.c.
 * IN1=GND: remove R102, fit R112=100 ohm. Move IN2 R101 -> R111 (PA9).
 */
#include "board_hal.h"
#include "iolinki/phy_l6362a.h"
#include "iolinki/time_utils.h"
#include "station_clock.h"
#include "stm32l4xx_hal.h"
#include <limits.h>

#define RX_SIZE 128U
#define TX_PIN GPIO_PIN_9
#define RX_PIN GPIO_PIN_10
#define EN_PIN GPIO_PIN_7       /* PC7, R109=100 ohm, board R10=330 ohm */
#define OL_PIN GPIO_PIN_6       /* PA6, R105=100 ohm, active low */
#define DIAG_PIN GPIO_PIN_4     /* PA4, R104=100 ohm, IC side of EN resistor */
#define INPUT_CLOCK GPIO_PIN_13 /* PB13, CN10.30 */
#define INPUT_DATA GPIO_PIN_14  /* PB14, CN10.28 */
#define INPUT_LOAD GPIO_PIN_6   /* PC6, CN10.4 */

static UART_HandleTypeDef uart;
static iolink_l6362a_ctx_t l6362;
static iolink_phy_api_t phy;
static volatile uint16_t head, tail;
static uint8_t rx_byte, ring[RX_SIZE];
static uint32_t rx_observed_us[RX_SIZE], last_consumed_rx_us;
static bool last_consumed_rx_valid, response_sample_valid;
static iolink_phy_response_timing_t response_sample;
static volatile bool rx_error, wake_pending;
volatile uint32_t g_uart_errors, g_rx_overflows, g_wake_events, g_overload_edges;
volatile int g_phy_error;
volatile uint32_t g_tx_deadline_errors;

static void output(GPIO_TypeDef *port, uint16_t pin, bool high) {
    HAL_GPIO_WritePin(port, pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
    GPIO_InitTypeDef g = {0};
    g.Pin = pin;
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(port, &g);
}
static int arm_rx(void) {
    if (uart.RxState == HAL_UART_STATE_BUSY_RX)
        return 0;
    return HAL_UART_Receive_IT(&uart, &rx_byte, 1) == HAL_OK ? 0 : -1;
}
static int flush_rx(void) {
    if (HAL_UART_AbortReceive(&uart) != HAL_OK)
        return -1;
    const uint32_t mask = __get_PRIMASK();
    __disable_irq();
    tail = head;
    rx_error = false;
    __HAL_UART_CLEAR_FLAG(&uart,
                          UART_CLEAR_PEF | UART_CLEAR_FEF | UART_CLEAR_NEF | UART_CLEAR_OREF);
    __HAL_UART_SEND_REQ(&uart, UART_RXDATA_FLUSH_REQUEST);
    __set_PRIMASK(mask);
    return 0;
}
static int phy_init(void *user) {
    (void)user;
    output(GPIOC, EN_PIN, false);
    output(GPIOA, TX_PIN, false);
    GPIO_InitTypeDef g = {0};
    g.Pin = DIAG_PIN;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = OL_PIN;
    g.Mode = GPIO_MODE_IT_FALLING;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &g);
    /* Board R5/D5/R4 provide the OL pull-up path. No invented dedicated WAKE pin. */
    wake_pending = false;
    HAL_NVIC_SetPriority(EXTI9_5_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);
    return 0;
}
static void enable(void *user, bool high) {
    (void)user;
    HAL_GPIO_WritePin(GPIOC, EN_PIN, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}
static void set_sio(void *user, bool high) {
    (void)user;
    if (uart.Instance != NULL)
        (void)HAL_UART_AbortReceive(&uart);
    output(GPIOA, TX_PIN, high);
    /* IN1=0 means C/Q follows IN2 in SIO (DS027660 Table 14). */
}
static int configure_uart(void *user, uint32_t baud) {
    (void)user;
    if (baud != 38400U)
        return -1;
    enable(0, false);
    uart.Instance = USART1;
    (void)HAL_UART_AbortReceive(&uart);
    uart.Init.BaudRate = baud;
    uart.Init.WordLength = UART_WORDLENGTH_9B;
    uart.Init.StopBits = UART_STOPBITS_1;
    uart.Init.Parity = UART_PARITY_EVEN;
    uart.Init.Mode = UART_MODE_TX_RX;
    uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    uart.Init.OverSampling = UART_OVERSAMPLING_16;
    uart.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    /* IN1=0 makes BOTH L6362A paths noninverting (Tables 14/15).
     * IO-Link C/Q is inverse of conventional UART logic: enable HAL's pin
     * inversion for TX and RX. This preserves start/parity/stop bits too;
     * complementing payload bytes would not implement the wire protocol. */
    uart.AdvancedInit.AdvFeatureInit =
        UART_ADVFEATURE_TXINVERT_INIT | UART_ADVFEATURE_RXINVERT_INIT;
    uart.AdvancedInit.TxPinLevelInvert = UART_ADVFEATURE_TXINV_ENABLE;
    uart.AdvancedInit.RxPinLevelInvert = UART_ADVFEATURE_RXINV_ENABLE;
    GPIO_InitTypeDef g = {0};
    g.Pin = TX_PIN | RX_PIN;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF7_USART1;
    HAL_GPIO_Init(GPIOA, &g);
    if (HAL_UART_Init(&uart) != HAL_OK || flush_rx() != 0)
        return -1;
    return arm_rx();
}
static int send_complete(void *user, const uint8_t *data, size_t n) {
    (void)user;
    response_sample_valid = false;
    if (!data || !n || n > UINT16_MAX || !last_consumed_rx_valid)
        return -1;
    /* RX IRQ observation can precede the end of the stop bit. A 40 us guard
     * exceeds one COM2 bit plus half a stop bit (39.063 us). These software
     * observations detect scheduling faults; only a C/Q capture qualifies t_A. */
    uint64_t now = station_now_us64();
    const uint64_t rx_end_estimate = now - (uint32_t)((uint32_t)now - last_consumed_rx_us);
    while (station_now_us64() - rx_end_estimate < 40U) {
    }
    if (station_now_us64() - rx_end_estimate > 250U) {
        ++g_tx_deadline_errors;
        return -1;
    }
    if (HAL_UART_AbortReceive(&uart) != HAL_OK)
        return -1;
    const uint32_t timeout = (uint32_t)((n * 11000U + 38399U) / 38400U) + 3U;
    response_sample.rx_end_us = rx_end_estimate;
    response_sample.tx_start_us = station_now_us64();
    response_sample.quality = IOLINK_PHY_TIMING_ESTIMATED;
    const bool ok = HAL_UART_Transmit(&uart, (uint8_t *)data, (uint16_t)n, timeout) == HAL_OK;
    /* HAL waits for TC. Drop local echo and rearm before the shared driver
     * releases EN after this callback returns. */
    if (flush_rx() != 0 || arm_rx() != 0)
        return -1;
    response_sample_valid = ok;
    return ok ? (int)n : -1;
}
static int response_timing(void *user, iolink_phy_response_timing_t *timing) {
    (void)user;
    if (!timing || !response_sample_valid)
        return 0;
    *timing = response_sample;
    response_sample_valid = false; /* Samples cannot be replayed by a second call. */
    return 1;
}
static int receive(void *user, uint8_t *value) {
    (void)user;
    if (!value)
        return -1;
    const uint32_t mask = __get_PRIMASK();
    __disable_irq();
    int result = 0;
    if (rx_error) {
        rx_error = false;
        tail = head;
        last_consumed_rx_valid = false;
        response_sample_valid = false;
        result = -1;
    } else if (tail != head) {
        *value = ring[tail];
        last_consumed_rx_us = rx_observed_us[tail];
        last_consumed_rx_valid = true;
        response_sample_valid = false;
        tail = (tail + 1U) % RX_SIZE;
        result = 1;
    }
    __set_PRIMASK(mask);
    return result;
}
static int consume_wake(void *user) {
    (void)user;
    const uint32_t mask = __get_PRIMASK();
    __disable_irq();
    const bool event = wake_pending;
    wake_pending = false;
    __set_PRIMASK(mask);
    if (event)
        ++g_wake_events;
    return event ? 1 : 0;
}
static bool read_ol(void *user) {
    (void)user;
    return HAL_GPIO_ReadPin(GPIOA, OL_PIN) == GPIO_PIN_SET;
}
static bool read_diag(void *user) {
    (void)user;
    return HAL_GPIO_ReadPin(GPIOA, DIAG_PIN) == GPIO_PIN_SET;
}
static bool read_fault(void *user) {
    const iolink_l6362a_ctx_t *d = user;
    return iolink_phy_l6362a_overload(d) > 0 || iolink_phy_l6362a_fault(d) > 0;
}
int device_board_init(void) {
    if (station_clock_init() != 0)
        return -1;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    RCC_PeriphCLKInitTypeDef clk = {0};
    clk.PeriphClockSelection = RCC_PERIPHCLK_USART1;
    clk.Usart1ClockSelection = RCC_USART1CLKSOURCE_PCLK2;
    if (HAL_RCCEx_PeriphCLKConfig(&clk) != HAL_OK)
        return -1;
    HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    output(GPIOB, INPUT_CLOCK, false);
    output(GPIOC, INPUT_LOAD, true);
    GPIO_InitTypeDef input = {0};
    input.Pin = INPUT_DATA;
    input.Mode = GPIO_MODE_INPUT;
    input.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &input);
    const iolink_l6362a_io_t io = {.user = 0,
                                   .init = phy_init,
                                   .set_enable = enable,
                                   .set_in2 = set_sio,
                                   .uart_configure = configure_uart,
                                   .uart_send_complete = send_complete,
                                   .uart_recv = receive,
                                   .consume_wakeup = consume_wake,
                                   .read_ol = read_ol,
                                   .read_diag = read_diag,
                                   .get_response_timing = response_timing};
    if (iolink_phy_l6362a_init(&l6362, &io) != 0)
        return -1;
    phy = *iolink_phy_l6362a_get(&l6362);
    phy.is_short_circuit = read_fault;
    return 0;
}
const iolink_phy_api_t *device_board_phy(void) { return &phy; }
uint8_t device_board_inputs(void) {
    g_phy_error = l6362.error;
    HAL_GPIO_WritePin(GPIOB, INPUT_CLOCK, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOC, INPUT_LOAD, GPIO_PIN_RESET);
    station_delay_us(1);
    HAL_GPIO_WritePin(GPIOC, INPUT_LOAD, GPIO_PIN_SET);
    station_delay_us(1);
    uint8_t result = 0;
    for (unsigned i = 0; i < 8; ++i) {
        /* QH starts with H. Sample before shifting, then clock H->G->...->A.
         * Result bit 7 is input H; bit 0 is input A. */
        result = (uint8_t)((result << 1) | (HAL_GPIO_ReadPin(GPIOB, INPUT_DATA) == GPIO_PIN_SET));
        HAL_GPIO_WritePin(GPIOB, INPUT_CLOCK, GPIO_PIN_SET);
        station_delay_us(1);
        HAL_GPIO_WritePin(GPIOB, INPUT_CLOCK, GPIO_PIN_RESET);
        station_delay_us(1);
    }
    return result;
}
void USART1_IRQHandler(void) { HAL_UART_IRQHandler(&uart); }
void EXTI9_5_IRQHandler(void) { HAL_GPIO_EXTI_IRQHandler(OL_PIN); }
void HAL_GPIO_EXTI_Callback(uint16_t pin) {
    if (pin == OL_PIN) {
        ++g_overload_edges;
        /* OL is aggregate overload, not a dedicated WAKE output. Accept its
         * edge as a wake request only in driven SIO with DIAG healthy.
         * UVLO/cutoff/thermal assertions do not become synthetic wake events. */
        if (l6362.initialized && l6362.enabled && l6362.mode == IOLINK_PHY_MODE_SIO && read_diag(0))
            wake_pending = true;
    }
}
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *handle) {
    if (handle != &uart)
        return;
    const uint16_t next = (head + 1U) % RX_SIZE;
    if (next == tail) {
        ++g_rx_overflows;
        rx_error = true;
    } else {
        ring[head] = rx_byte;
        rx_observed_us[head] = station_now_us();
        head = next;
    }
    if (arm_rx() != 0)
        rx_error = true;
}
void HAL_UART_ErrorCallback(UART_HandleTypeDef *handle) {
    if (handle != &uart)
        return;
    ++g_uart_errors;
    rx_error = true;
    (void)arm_rx();
}
uint32_t iolink_time_get_ms(void) { return HAL_GetTick(); }
uint64_t iolink_time_get_us(void) { return station_now_us64(); }
