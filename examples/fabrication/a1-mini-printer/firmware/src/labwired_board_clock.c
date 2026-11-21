#include "pins_arduino.h"

#if !defined(STM32F411xE)
#error "The STM32F411 HSE8 profile requires STM32F411xE"
#endif
#if HSE_VALUE != 8000000U
#error "The STM32F411 HSE8 profile requires HSE_VALUE=8000000U"
#endif
#if defined(USBCON)
#error "The STM32F411 HSE8 100MHz profile does not provide a 48MHz USB clock"
#endif

/* STM32F411: 8MHz crystal / 8 * 200 / 2 = 100MHz.
 * The upstream generic Arduino variant uses HSI at 96MHz regardless of F_CPU.
 * A strong definition replaces that weak default, without carrier pin aliases.
 * PLLQ is unused: 200MHz / 4 = 50MHz is not a USB clock. */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef osc = {0};
  RCC_ClkInitTypeDef clocks = {0};
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
  osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  osc.HSEState = RCC_HSE_ON;
  osc.PLL.PLLState = RCC_PLL_ON;
  osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  osc.PLL.PLLM = 8;
  osc.PLL.PLLN = 200;
  osc.PLL.PLLP = RCC_PLLP_DIV2;
  osc.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&osc) != HAL_OK) Error_Handler();

  clocks.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
  clocks.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  clocks.AHBCLKDivider = RCC_SYSCLK_DIV1;
  clocks.APB1CLKDivider = RCC_HCLK_DIV2;
  clocks.APB2CLKDivider = RCC_HCLK_DIV1;
  if (HAL_RCC_ClockConfig(&clocks, FLASH_LATENCY_3) != HAL_OK) Error_Handler();
}
