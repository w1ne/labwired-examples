# Physical target; no simulator-specific peripheral shortcuts.
CUBE_DIR ?= deps/STM32CubeH5
UDSLIB_DIR ?= deps/udslib
CC := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy
TARGET := build/h563-uds-physical
HAL := $(CUBE_DIR)/Drivers/STM32H5xx_HAL_Driver
CMSIS := $(CUBE_DIR)/Drivers/CMSIS
DEVICE := $(CMSIS)/Device/ST/STM32H5xx
VENDOR := $(CUBE_DIR)/Projects/NUCLEO-H563ZI/Examples/FDCAN/FDCAN_Com_Polling
CPU := -mcpu=cortex-m33 -mthumb -mfloat-abi=soft
CFLAGS := $(CPU) -Os -g3 -ffunction-sections -fdata-sections -Wall -Wextra  -DSTM32H563xx -DUSE_HAL_DRIVER -I. -I$(HAL)/Inc -I$(CMSIS)/Include  -I$(DEVICE)/Include -I$(UDSLIB_DIR)/include -I$(UDSLIB_DIR)/src/core
HAL_NAMES := hal hal_cortex hal_rcc hal_rcc_ex hal_gpio hal_fdcan hal_uart hal_uart_ex hal_pwr hal_pwr_ex hal_flash hal_flash_ex hal_dma
HAL_SRC := $(addprefix $(HAL)/Src/stm32h5xx_,$(addsuffix .c,$(HAL_NAMES)))
UDS_SRC := $(UDSLIB_DIR)/src/core/uds_core.c $(wildcard $(UDSLIB_DIR)/src/services/*.c) $(UDSLIB_DIR)/src/transport/uds_tp_isotp.c
STARTUP := $(DEVICE)/Source/Templates/gcc/startup_stm32h563xx.s
SOURCE := main.c clock.c uds_ecu_app.c $(DEVICE)/Source/Templates/system_stm32h5xx.c $(HAL_SRC) $(UDS_SRC) $(STARTUP)
all: check-deps $(TARGET).elf $(TARGET).bin
check-deps:
	python3 verify-deps.py $(CUBE_DIR) $(UDSLIB_DIR)
$(TARGET).elf: $(SOURCE) stm32h563.ld
	@mkdir -p build
	$(CC) $(CFLAGS) $(SOURCE) -Tstm32h563.ld --specs=nano.specs --specs=nosys.specs 	  -Wl,--gc-sections,-Map=$(TARGET).map -o $@
	arm-none-eabi-size $@
$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@
.PHONY: all check-deps
