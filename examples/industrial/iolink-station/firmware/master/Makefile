# SPDX-License-Identifier: MIT
# Externally fetched vendor sources are pinned by dependencies.json.
CUBE ?= .deps/STM32CubeL4
IOLINKI ?= .deps/iolinki
MASTER ?= .deps/labwired-core/third_party/iolinki-master
CROSS ?= arm-none-eabi-
CC := $(CROSS)gcc
BUILD := build
HAL := $(CUBE)/Drivers/STM32L4xx_HAL_Driver
DEVICE := $(CUBE)/Drivers/CMSIS/Device/ST/STM32L4xx
TEMPLATE := $(CUBE)/Projects/NUCLEO-L476RG/Templates
CPU := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CPPFLAGS := -DSTM32L476xx -DUSE_HAL_DRIVER -I. -I../common -I$(HAL)/Inc -I$(DEVICE)/Include -I$(CUBE)/Drivers/CMSIS/Include -I$(MASTER)/include -I$(IOLINKI)/include
CFLAGS := $(CPU) -std=c11 -Os -g3 -Wall -Wextra -ffunction-sections -fdata-sections
HAL_NAMES := hal hal_cortex hal_dma hal_flash hal_flash_ex hal_gpio hal_i2c hal_i2c_ex hal_pwr hal_pwr_ex hal_rcc hal_rcc_ex hal_tim hal_tim_ex hal_uart hal_uart_ex
SOURCES := main.c board_hal.c l6360.c ../common/station_clock.c $(addprefix $(HAL)/Src/stm32l4xx_,$(addsuffix .c,$(HAL_NAMES))) $(DEVICE)/Source/Templates/system_stm32l4xx.c $(wildcard $(MASTER)/src/*.c) $(IOLINKI)/src/frame.c $(IOLINKI)/src/crc.c
STARTUP := $(DEVICE)/Source/Templates/gcc/startup_stm32l476xx.s
LD := $(TEMPLATE)/STM32CubeIDE/STM32L476RGTX_FLASH.ld
OBJECTS := $(addprefix $(BUILD)/,$(notdir $(SOURCES:.c=.o))) $(BUILD)/startup.o
vpath %.c . $(sort $(dir $(SOURCES)))
.PHONY: all test clean verify-deps
all: verify-deps $(BUILD)/iolink-master.elf $(BUILD)/iolink-master.bin
verify-deps:
	python3 verify-deps.py $(CUBE) $(IOLINKI) $(MASTER)
$(OBJECTS): Makefile dependencies.json | verify-deps
$(BUILD):
	mkdir -p $@
$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@
$(BUILD)/startup.o: $(STARTUP) | $(BUILD)
	$(CC) $(CPU) -g3 -x assembler-with-cpp -c $< -o $@
$(BUILD)/iolink-master.elf: $(OBJECTS) $(LD)
	$(CC) $(CPU) -nostartfiles --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections,-Map=$(BUILD)/iolink-master.map -T$(LD) $(OBJECTS) -o $@
	$(CROSS)size $@
$(BUILD)/iolink-master.bin: $(BUILD)/iolink-master.elf
	$(CROSS)objcopy -O binary $< $@
test: | $(BUILD)
	$(HOSTCC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined l6360.c tests/test_l6360.c -o $(BUILD)/test_l6360
	$(BUILD)/test_l6360
	python3 tests/check_timing.py
clean:
	rm -rf $(BUILD)
HOSTCC ?= cc
-include $(OBJECTS:.o=.d)
