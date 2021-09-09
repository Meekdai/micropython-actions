#define MICROPY_HW_BOARD_NAME       "GRAPEPI"
#define MICROPY_HW_MCU_NAME         "STM32H750"

#define MICROPY_HW_ENABLE_RTC       (1)
#define MICROPY_HW_ENABLE_RNG       (1)
#define MICROPY_HW_ENABLE_ADC       (1)
#define MICROPY_HW_ENABLE_DAC       (1)
#define MICROPY_HW_ENABLE_USB       (1)
#define MICROPY_HW_ENABLE_SDCARD    (1)
#define MICROPY_HW_HAS_SWITCH       (1)
#define MICROPY_HW_HAS_FLASH        (1)

#define MICROPY_HW_FLASH_FS_LABEL "GrapePi"

#define MICROPY_BOARD_EARLY_INIT    GRAPEPI_LITE_board_early_init
void GRAPEPI_LITE_board_early_init(void);

// // The board has an 8MHz HSE, the following gives 400MHz CPU speed
// #define MICROPY_HW_CLK_PLLM (4)
// #define MICROPY_HW_CLK_PLLN (400)
// #define MICROPY_HW_CLK_PLLP (2)
// #define MICROPY_HW_CLK_PLLQ (4)
// #define MICROPY_HW_CLK_PLLR (2)

// // The USB clock is set using PLL3
// #define MICROPY_HW_CLK_PLL3M (4)
// #define MICROPY_HW_CLK_PLL3N (120)
// #define MICROPY_HW_CLK_PLL3P (2)
// #define MICROPY_HW_CLK_PLL3Q (5)
// #define MICROPY_HW_CLK_PLL3R (2)

// // The board has an 12MHz HSE, the following gives 480MHz CPU speed
#define MICROPY_HW_CLK_PLLM (3)
#define MICROPY_HW_CLK_PLLN (240)
#define MICROPY_HW_CLK_PLLP (2)
#define MICROPY_HW_CLK_PLLQ (20)
#define MICROPY_HW_CLK_PLLR (2)

// // The USB clock is set using PLL3
#define MICROPY_HW_CLK_PLL3M (3)
#define MICROPY_HW_CLK_PLL3N (240)
#define MICROPY_HW_CLK_PLL3P (2)
#define MICROPY_HW_CLK_PLL3Q (20)
#define MICROPY_HW_CLK_PLL3R (2)

// 4 wait states
#define MICROPY_HW_FLASH_LATENCY    FLASH_LATENCY_4

// UART config
#define MICROPY_HW_UART4_TX         (pin_A0)
#define MICROPY_HW_UART4_RX         (pin_A1)
#define MICROPY_HW_UART_REPL        PYB_UART_4
#define MICROPY_HW_UART_REPL_BAUD   115200

// I2C busses
#define MICROPY_HW_I2C2_SCL         (pin_B10)
#define MICROPY_HW_I2C2_SDA         (pin_B11)
#define MICROPY_HW_I2C4_SCL         (pin_D12)
#define MICROPY_HW_I2C4_SDA         (pin_D13)

// SPI
// #define MICROPY_HW_SPI1_NSS         (pin_A4)
#define MICROPY_HW_SPI1_SCK         (pin_B3)
#define MICROPY_HW_SPI1_MISO        (pin_B4)
#define MICROPY_HW_SPI1_MOSI        (pin_B5)

// #define MICROPY_HW_SPI2_NSS         (pin_A4)
#define MICROPY_HW_SPI2_SCK         (pin_B13)
#define MICROPY_HW_SPI2_MISO        (pin_B14)
#define MICROPY_HW_SPI2_MOSI        (pin_B15)

// USRSW is pulled low. Pressing the button makes the input go high.
#define MICROPY_HW_USRSW_PIN        (pin_A5)
#define MICROPY_HW_USRSW_PULL       (GPIO_PULLUP)
#define MICROPY_HW_USRSW_EXTI_MODE  (GPIO_MODE_IT_FALLING)
#define MICROPY_HW_USRSW_PRESSED    (0)

// LEDs
#define MICROPY_HW_LED1             (pin_C0)    // red
#define MICROPY_HW_LED2             (pin_C1)    // green
#define MICROPY_HW_LED3             (pin_C2)   // blue
#define MICROPY_HW_LED_ON(pin)      (mp_hal_pin_high(pin))
#define MICROPY_HW_LED_OFF(pin)     (mp_hal_pin_low(pin))

// USB config
#define MICROPY_HW_USB_FS              (1)
#define MICROPY_HW_USB_VBUS_DETECT_PIN (pin_A9)
#define MICROPY_HW_USB_OTG_ID_PIN      (pin_A10)

// SD card detect switch
#define MICROPY_HW_SDCARD_DETECT_PIN        (pin_D15)
#define MICROPY_HW_SDCARD_DETECT_PULL       (GPIO_PULLUP)
#define MICROPY_HW_SDCARD_DETECT_PRESENT    (GPIO_PIN_RESET)


// Bootloader configuration (only needed if Mboot is used)
// #define MBOOT_VFS_FAT (1)
// #define MBOOT_FSLOAD (1)
// #define MBOOT_SPIFLASH_ADDR (0x80000000) 
// #define MBOOT_SPIFLASH_BYTE_SIZE (16 * 1024 * 1024) 
// #define MBOOT_SPIFLASH_LAYOUT "/0x80000000/16*04Kg" 
// #define MBOOT_SPIFLASH_ERASE_BLOCKS_PER_PAGE (16 / 4) 
// #define MBOOT_SPIFLASH_SPIFLASH (&spi_bdev.spiflash) 
// #define MBOOT_SPIFLASH_CONFIG (&spiflash_config)

// SPI flash #1, for R/W storage
#define MICROPY_HW_ENABLE_INTERNAL_FLASH_STORAGE (0)
#define MICROPY_HW_SPIFLASH_SIZE_BITS (128 * 1024 * 1024)
#define MICROPY_HW_SPIFLASH_CS      (pin_E11)
#define MICROPY_HW_SPIFLASH_SCK     (pin_B2)
#define MICROPY_HW_SPIFLASH_IO0     (pin_E7)
#define MICROPY_HW_SPIFLASH_IO1     (pin_E8)
#define MICROPY_HW_SPIFLASH_IO2     (pin_E9)
#define MICROPY_HW_SPIFLASH_IO3     (pin_E10)

// SPI flash #1, block device config
extern const struct _mp_spiflash_config_t spiflash_config;
extern struct _spi_bdev_t spi_bdev;
#define MICROPY_HW_BDEV_IOCTL(op, arg) ( \
    (op) == BDEV_IOCTL_NUM_BLOCKS ? (MICROPY_HW_SPIFLASH_SIZE_BITS / 8 / FLASH_BLOCK_SIZE) : \
    (op) == BDEV_IOCTL_INIT ? spi_bdev_ioctl(&spi_bdev, (op), (uint32_t)&spiflash_config) : \
    spi_bdev_ioctl(&spi_bdev, (op), (arg)) \
)
#define MICROPY_HW_BDEV_READBLOCKS(dest, bl, n) spi_bdev_readblocks(&spi_bdev, (dest), (bl), (n))
#define MICROPY_HW_BDEV_WRITEBLOCKS(src, bl, n) spi_bdev_writeblocks(&spi_bdev, (src), (bl), (n))
#define MICROPY_HW_BDEV_SPIFLASH_EXTENDED (&spi_bdev) // for extended block protocol
