idf_component_register(
    SRCS
        "main.c"
        "doom_vfs.c"
        "doom_input.c"
        "doom_display.c"
        "board_led.c"
    INCLUDE_DIRS "."
    REQUIRES
        doomgeneric
        driver
        esp_lcd
        esp_timer
        esp_partition
        vfs
        spi_flash
        esp_driver_rmt
)

# This package builds the 34-pin I80 panel for both hardware and the twin.
# Keep the upstream optional SPI mode available but disabled in sdkconfig.
if(CONFIG_DOOM_LCD_BUS_SPI)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE DOOM_LCD_BUS=2)
endif()
