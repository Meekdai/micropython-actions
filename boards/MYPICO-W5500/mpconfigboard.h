// Board config for Wiznet W5500-EVB-Pico.

// Board and hardware specific configuration
#define MICROPY_HW_BOARD_NAME             "MYPICO-W5500"
#define MICROPY_HW_FLASH_STORAGE_BYTES    (1408 * 1024)

#define MICROPY_HW_FLASH_FS_LABEL "MYPICO"

// Enable networking.
#define MICROPY_PY_NETWORK                (1)

// Wiznet HW config.
#define MICROPY_HW_WIZNET_SPI_ID          (0)
#define MICROPY_HW_WIZNET_SPI_BAUDRATE    (20 * 1000 * 1000)
#define MICROPY_HW_WIZNET_SPI_SCK         (18)
#define MICROPY_HW_WIZNET_SPI_MOSI        (19)
#define MICROPY_HW_WIZNET_SPI_MISO        (16)
#define MICROPY_HW_WIZNET_PIN_CS          (17)
#define MICROPY_HW_WIZNET_PIN_RST         (20)
// Connecting the INTN pin enables RECV interrupt handling of incoming data.
#define MICROPY_HW_WIZNET_PIN_INTN        (21)

// Enable USB Mass Storage with FatFS filesystem.
#define MICROPY_HW_USB_MSC  (1)
