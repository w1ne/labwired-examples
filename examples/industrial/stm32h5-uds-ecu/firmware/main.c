/* SPDX-License-Identifier: MIT
 * NUCLEO-H563ZI physical UDS ECU. STM32Cube HAL/CMSIS owns clocks, pins,
 * FDCAN message RAM and the millisecond SysTick. Simulator fixture is separate.
 */
#include "stm32h5xx_hal.h"
#include "uds/uds_core.h"
#include "uds/uds_isotp.h"
#include "uds_ecu_app.h"
#include <string.h>
#include <stdbool.h>
FDCAN_HandleTypeDef hfdcan1;
static UART_HandleTypeDef uart;
static uds_isotp_ctx_t iso;
static uint8_t tx_sdu[768], rx_sdu[128], response[768];
void SystemClock_Config(void);
void Error_Handler(void) { __disable_irq(); for (;;) {} }
void SysTick_Handler(void) { HAL_IncTick(); }
void HAL_FDCAN_MspInit(FDCAN_HandleTypeDef *h) {
    (void)h;
    RCC_PeriphCLKInitTypeDef clock = {0};
    clock.PeriphClockSelection = RCC_PERIPHCLK_FDCAN;
    clock.FdcanClockSelection = RCC_FDCANCLKSOURCE_PLL1Q;
    if (HAL_RCCEx_PeriphCLKConfig(&clock) != HAL_OK) Error_Handler();
    __HAL_RCC_FDCAN_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    gpio.Mode = GPIO_MODE_AF_PP; gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH; gpio.Alternate = GPIO_AF9_FDCAN1;
    HAL_GPIO_Init(GPIOD, &gpio);
}
static void uart_init(void) {
    __HAL_RCC_GPIOD_CLK_ENABLE(); __HAL_RCC_USART3_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_8 | GPIO_PIN_9; gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL; gpio.Speed = GPIO_SPEED_FREQ_LOW;
    gpio.Alternate = GPIO_AF7_USART3; HAL_GPIO_Init(GPIOD, &gpio);
    uart.Instance = USART3; uart.Init.BaudRate = 115200;
    uart.Init.WordLength = UART_WORDLENGTH_8B; uart.Init.StopBits = UART_STOPBITS_1;
    uart.Init.Parity = UART_PARITY_NONE; uart.Init.Mode = UART_MODE_TX_RX;
    uart.Init.HwFlowCtl = UART_HWCONTROL_NONE; uart.Init.OverSampling = UART_OVERSAMPLING_16;
    uart.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    if (HAL_UART_Init(&uart) != HAL_OK) Error_Handler();
}
void uds_ecu_app_log(const char *s) {
    (void)HAL_UART_Transmit(&uart, (const uint8_t *)s, (uint16_t)strlen(s), 100u);
}
static void fdcan_init(void) {
    hfdcan1.Instance = FDCAN1;
    hfdcan1.Init.ClockDivider = FDCAN_CLOCK_DIV1;
    hfdcan1.Init.FrameFormat = FDCAN_FRAME_FD_BRS;
    hfdcan1.Init.Mode = FDCAN_MODE_NORMAL;
    hfdcan1.Init.AutoRetransmission = ENABLE;
    hfdcan1.Init.TransmitPause = ENABLE;
    hfdcan1.Init.ProtocolException = DISABLE;
    /* PLL1Q = 250 MHz from ST's 8 MHz ST-LINK MCO clock recipe.
     * Nominal: 250 MHz / 2 / (1 + 187 + 62) = 500 kbit/s, 75.2% SP.
     * Data:    250 MHz / 5 / (1 + 19 + 5) = 2 Mbit/s, 80% SP.
     */
    hfdcan1.Init.NominalPrescaler = 2;
    hfdcan1.Init.NominalSyncJumpWidth = 62;
    hfdcan1.Init.NominalTimeSeg1 = 187; hfdcan1.Init.NominalTimeSeg2 = 62;
    hfdcan1.Init.DataPrescaler = 5;
    hfdcan1.Init.DataSyncJumpWidth = 5;
    hfdcan1.Init.DataTimeSeg1 = 19; hfdcan1.Init.DataTimeSeg2 = 5;
    hfdcan1.Init.StdFiltersNbr = 1; hfdcan1.Init.ExtFiltersNbr = 0;
    hfdcan1.Init.TxFifoQueueMode = FDCAN_TX_FIFO_OPERATION;
    if (HAL_FDCAN_Init(&hfdcan1) != HAL_OK) Error_Handler();
    FDCAN_FilterTypeDef filter = {0};
    filter.IdType = FDCAN_STANDARD_ID; filter.FilterIndex = 0;
    filter.FilterType = FDCAN_FILTER_MASK; filter.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    filter.FilterID1 = 0x7E0u; filter.FilterID2 = 0x7FFu;
    if (HAL_FDCAN_ConfigFilter(&hfdcan1, &filter) != HAL_OK ||
        HAL_FDCAN_ConfigGlobalFilter(&hfdcan1, FDCAN_REJECT, FDCAN_REJECT,
                                    FDCAN_REJECT_REMOTE, FDCAN_REJECT_REMOTE) != HAL_OK ||
        HAL_FDCAN_Start(&hfdcan1) != HAL_OK) Error_Handler();
}
static const uint32_t dlc[] = {
 FDCAN_DLC_BYTES_0,FDCAN_DLC_BYTES_1,FDCAN_DLC_BYTES_2,FDCAN_DLC_BYTES_3,
 FDCAN_DLC_BYTES_4,FDCAN_DLC_BYTES_5,FDCAN_DLC_BYTES_6,FDCAN_DLC_BYTES_7,
 FDCAN_DLC_BYTES_8,FDCAN_DLC_BYTES_12,FDCAN_DLC_BYTES_16,FDCAN_DLC_BYTES_20,
 FDCAN_DLC_BYTES_24,FDCAN_DLC_BYTES_32,FDCAN_DLC_BYTES_48,FDCAN_DLC_BYTES_64};
static const uint8_t lengths[] = {0,1,2,3,4,5,6,7,8,12,16,20,24,32,48,64};
static int can_send(uint32_t id, const uint8_t *data, uint8_t len) {
    if (id > 0x7FFu || len > 64u || !HAL_FDCAN_GetTxFifoFreeLevel(&hfdcan1)) return -1;
    unsigned i = 0; while (lengths[i] < len) ++i;
    /* Zero padding prevents exposing adjacent memory when DLC rounds upward. */
    uint8_t frame[64] = {0}; memcpy(frame, data, len);
    FDCAN_TxHeaderTypeDef h = {0};
    h.Identifier = id; h.IdType = FDCAN_STANDARD_ID; h.TxFrameType = FDCAN_DATA_FRAME;
    h.DataLength = dlc[i]; h.ErrorStateIndicator = FDCAN_ESI_ACTIVE;
    h.FDFormat = len > 8u ? FDCAN_FD_CAN : FDCAN_CLASSIC_CAN;
    h.BitRateSwitch = len > 8u ? FDCAN_BRS_ON : FDCAN_BRS_OFF;
    h.TxEventFifoControl = FDCAN_NO_TX_EVENTS;
    return HAL_FDCAN_AddMessageToTxFifoQ(&hfdcan1, &h, frame) == HAL_OK ? 0 : -1;
}
static int isotp_send(struct uds_ctx *ctx, const uint8_t *data, uint16_t len) {
    (void)ctx; return uds_isotp_send(&iso, data, len);
}
static bool tx_complete(struct uds_ctx *ctx) {
    (void)ctx;
    return !HAL_FDCAN_IsTxBufferMessagePending(&hfdcan1,
        FDCAN_TX_BUFFER0 | FDCAN_TX_BUFFER1 | FDCAN_TX_BUFFER2);
}
int main(void) {
    HAL_Init(); SystemClock_Config(); uart_init(); fdcan_init();
    uds_ecu_app_log("H563-UDS-ECU PHYSICAL HAL 500K/2M FD\r\n");
    uds_tp_isotp_init(&iso, can_send, 0x7E8u, 0x7E0u, tx_sdu, sizeof tx_sdu);
    uds_tp_isotp_set_fd(&iso, true);
    uds_config_t cfg = {
      .ecu_address=0x10u, .get_time_ms=HAL_GetTick, .fn_tp_send=isotp_send,
      .rx_buffer=rx_sdu, .rx_buffer_size=sizeof rx_sdu,
      .tx_buffer=response, .tx_buffer_size=sizeof response,
      .p2_ms=50u, .p2_star_ms=2000u, .fn_tx_complete=tx_complete, .reset_tx_wait_ms=20u
    };
    uds_ecu_app_fill_config(&cfg, "LABWIRED-H563-UDS");
    uds_ctx_t ctx; if (uds_init(&ctx, &cfg) != UDS_OK) Error_Handler();
    uds_ecu_app_log("ECU_READY\r\n");
    for (;;) {
      while (HAL_FDCAN_GetRxFifoFillLevel(&hfdcan1, FDCAN_RX_FIFO0)) {
        FDCAN_RxHeaderTypeDef h; uint8_t data[64];
        if (HAL_FDCAN_GetRxMessage(&hfdcan1, FDCAN_RX_FIFO0, &h, data) != HAL_OK) break;
        for (unsigned i=0; i<16; ++i) if (dlc[i] == h.DataLength) {
          uds_isotp_rx_callback(&iso, &ctx, h.Identifier, data, lengths[i]); break;
        }
      }
      uds_process(&ctx); uds_tp_isotp_process(&iso, HAL_GetTick());
    }
}
