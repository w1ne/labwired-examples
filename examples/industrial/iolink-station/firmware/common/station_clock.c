/* SPDX-License-Identifier: MIT
 * Pinned ST HAL clock/timer setup shared by all three NUCLEO-L476RG nodes.
 * Require ST-LINK 8 MHz MCO: SB16/SB50/SB54 ON, SB55 OFF, R35/R37 absent.
 */
#include "station_clock.h"
#include "stm32l4xx_hal.h"
#include <stdint.h>
static TIM_HandleTypeDef clock_timer;
int station_clock_init(void) {
    HAL_Init();
    __HAL_RCC_PWR_CLK_ENABLE();
    if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK)
        return -1;
    /* UM1724 section 7.9.1: ST-LINK crystal-derived MCO feeds PH0/HSE.
     * MSI auto-trim's +/-0.25% specification is insufficient for the Master's
     * +/-0.1% transmission-rate requirement (IO-Link v1.1.4 Table 9).
     * 8 MHz /2 *40 /2 = 80 MHz. Missing MCO is an initialization failure;
     * no runtime/internal-RC fallback is provided for communication timing. */
    RCC_OscInitTypeDef osc = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_BYPASS;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLM = 2;
    osc.PLL.PLLN = 40;
    osc.PLL.PLLR = 2;
    osc.PLL.PLLP = 7;
    osc.PLL.PLLQ = 4;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
        return -1;
    RCC_ClkInitTypeDef clk = {0};
    clk.ClockType =
        RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV1;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_4) != HAL_OK)
        return -1;
    __HAL_RCC_TIM5_CLK_ENABLE();
    clock_timer.Instance = TIM5;
    clock_timer.Init.Prescaler = 79;
    clock_timer.Init.CounterMode = TIM_COUNTERMODE_UP;
    clock_timer.Init.Period = UINT32_MAX;
    clock_timer.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    clock_timer.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&clock_timer) != HAL_OK || HAL_TIM_Base_Start(&clock_timer) != HAL_OK)
        return -1;
    return 0;
}
uint32_t station_now_us(void) { return __HAL_TIM_GET_COUNTER(&clock_timer); }
uint64_t station_now_us64(void) {
    /* Main-loop-only reader, called at least once per 32-bit timer period.
     * Extend TIM5 before conversion so its 71.6-minute wrap loses no time. */
    static uint32_t previous;
    static uint64_t elapsed;
    const uint32_t current = station_now_us();
    elapsed += (uint32_t)(current - previous);
    previous = current;
    return elapsed;
}
uint32_t station_now_100us(void) { return (uint32_t)(station_now_us64() / 100U); }
void station_delay_us(uint32_t duration) {
    const uint32_t start = station_now_us();
    while ((uint32_t)(station_now_us() - start) < duration) {
    }
}
void SysTick_Handler(void) { HAL_IncTick(); }
