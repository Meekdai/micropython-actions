#include "py/mphal.h"

void GRAPEPI_LITE_board_early_init(void) {
    // output 8MHz to the PA8 output
    HAL_RCC_MCOConfig(RCC_MCO1, RCC_MCO1SOURCE_HSI48, RCC_MCODIV_1);
/* redirect to:       source RCC_MCOSource:       prescaler RCC_MCODiv:
 * RCC_MCO1: PA8      RCC_MCO1SOURCE_HSI          RCC_MCODIV_1
 * RCC_MCO2: PC9      RCC_MCO1SOURCE_LSE          RCC_MCODIV_2
 *                    RCC_MCO1SOURCE_HSE          RCC_MCODIV_3
 *                    RCC_MCO1SOURCE_PLLCLK       RCC_MCODIV_4
 *                    RCC_MCO2SOURCE_SYSCLK       RCC_MCODIV_5
 *                    RCC_MCO2SOURCE_PLLI2SCLK
 *                    RCC_MCO2SOURCE_I2SCLK
 *                    RCC_MCO2SOURCE_HSE
 *                    RCC_MCO2SOURCE_PLLCLK
**/

}