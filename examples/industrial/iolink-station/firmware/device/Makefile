# SPDX-License-Identifier: MIT
# Externally fetched vendor sources are pinned by dependencies.json.
CUBE ?= ../master/.deps/STM32CubeL4
IOLINKI ?= ../master/.deps/iolinki
MASTER ?= ../master/.deps/labwired-core/third_party/iolinki-master
CROSS ?= arm-none-eabi-
CC := $(CROSS)gcc
BUILD := build
HAL := $(CUBE)/Drivers/STM32L4xx_HAL_Driver
DEVICE := $(CUBE)/Drivers/CMSIS/Device/ST/STM32L4xx
TEMPLATE := $(CUBE)/Projects/NUCLEO-L476RG/Templates
CPU := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CPPFLAGS := -DSTM32L476xx -DUSE_HAL_DRIVER -I. -I../common -I../master -I$(HAL)/Inc -I$(DEVICE)/Include -I$(CUBE)/Drivers/CMSIS/Include -I$(MASTER)/include -I$(IOLINKI)/include
CFLAGS := $(CPU) -std=c11 -Os -g3 -Wall -Wextra -ffunction-sections -fdata-sections
HAL_NAMES := hal hal_cortex hal_dma hal_flash hal_flash_ex hal_gpio hal_i2c hal_i2c_ex hal_pwr hal_pwr_ex hal_rcc hal_rcc_ex hal_tim hal_tim_ex hal_uart hal_uart_ex
SOURCES := main.c board_hal.c ../common/station_clock.c $(addprefix $(HAL)/Src/stm32l4xx_,$(addsuffix .c,$(HAL_NAMES))) $(DEVICE)/Source/Templates/system_stm32l4xx.c $(addprefix $(IOLINKI)/src/,device.c phy_l6362a.c crc.c dll.c isdu.c events.c platform.c params.c data_storage.c device_info.c platform_stubs.c)
STARTUP := $(DEVICE)/Source/Templates/gcc/startup_stm32l476xx.s
LD := $(TEMPLATE)/STM32CubeIDE/STM32L476RGTX_FLASH.ld
OBJECTS := $(addprefix $(BUILD)/,$(notdir $(SOURCES:.c=.o))) $(BUILD)/startup.o
vpath %.c . $(sort $(dir $(SOURCES)))
.PHONY: all test clean verify-deps
all: verify-deps $(BUILD)/iolink-device.elf $(BUILD)/iolink-device.bin
verify-deps:
	python3 ../master/verify-deps.py $(CUBE) $(IOLINKI) $(MASTER)
$(OBJECTS): Makefile ../master/dependencies.json | verify-deps
$(BUILD):
	mkdir -p $@
$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@
$(BUILD)/startup.o: $(STARTUP) | $(BUILD)
	$(CC) $(CPU) -g3 -x assembler-with-cpp -c $< -o $@
$(BUILD)/iolink-device.elf: $(OBJECTS) $(LD)
	$(CC) $(CPU) -nostartfiles --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections,-Map=$(BUILD)/iolink-device.map -T$(LD) $(OBJECTS) -o $@
	$(CROSS)size $@
$(BUILD)/iolink-device.bin: $(BUILD)/iolink-device.elf
	$(CROSS)objcopy -O binary $< $@
clean:
	rm -rf $(BUILD)
HOSTCC ?= cc
-include $(OBJECTS:.o=.d)
