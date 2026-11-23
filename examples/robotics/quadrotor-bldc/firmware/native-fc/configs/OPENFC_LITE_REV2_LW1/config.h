/*
 * This file is part of Betaflight.
 *
 * Betaflight is free software. You can redistribute this software
 * and/or modify this software under the terms of the GNU General
 * Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later
 * version.
 *
 * Betaflight is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public
 * License along with this software.
 *
 * If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#define FC_TARGET_MCU        RP2350B
#define BOARD_NAME           OPENFC_LITE_REV2_LW1
#define MANUFACTURER_ID      OPDR

// LabWired OpenFC-Lite rev2-LW1 native derivative: RP2354B, 2 MiB flash.
// Exact PCB/netlist authority is hardware/flight-controller-openfc-lite-rev2-lw1.
// This package selects a 4S pack. It does not inherit the rev3.3 voltage rating.
// Base pin definitions: OpenDrone-hw/betaflight-config dd0e3200b27f43b581f4559574ddc5d12e6040f0.
// Historical rev2 repaired-board GPIO remaps do not apply to this routed PCB.

// UART0: digital VTX connector (U8) and TX1/RX1 pads
#define UART0_TX_PIN         PA0
#define UART0_RX_PIN         PA1

// PIO UART0: native CN1 receiver, pin3 RX (receiver TX), pin4 TX (receiver RX).
#define PIOUART0_TX_PIN      PA2
#define PIOUART0_RX_PIN      PA3

// UART1: TX2/RX2 auxiliary pads. The packaged CRSF receiver uses CN1.
#define UART1_TX_PIN         PA22
#define UART1_RX_PIN         PA21
#define DEFAULT_RX_FEATURE   FEATURE_RX_SERIAL
#define SERIALRX_PROVIDER    SERIALRX_CRSF
#define SERIALRX_UART        SERIAL_PORT_PIOUART0

// PIO UART1: TX4/RX4 pads
#define PIOUART1_TX_PIN      PA26
#define PIOUART1_RX_PIN      PA27

// I2C0 pads
#define I2C0_SDA_PIN         PA16
#define I2C0_SCL_PIN         PA17

// Analog OSD (framebuffer OSD, PIO2)
#define ENABLE_FB_OSD        1
#define DEFAULT_FEATURES     (FEATURE_OSD)
#define DEFAULT_OSD_DISPLAYPORT_DEVICE OSD_DISPLAYPORT_DEVICE_FBOSD
#define DEFAULT_VIDEO_SYSTEM VIDEO_SYSTEM_AUTO // digital VTX users set vcd_video_system = HD
// MSP DisplayPort on the digital VTX connector by default, so going digital only takes vcd_video_system = HD
#define MSP_DISPLAYPORT_UART SERIAL_PORT_UART0
#define OSD_W_PIN            PA4
#define OSD_EN_PIN           PA5
#define OSD_SYNC_PIN         PA6

// Beeper pad (N-MOS low-side)
#define USE_BEEPER
#define BEEPER_PIN           PA7
// Q1 is a low-side N-MOS switch. The pinned driver uses INVERTED for
// active-high push-pull, with low at the off state.
#define BEEPER_INVERTED

// 10V VTX/cam rail enable (U6 EN), active high. Inverted so pinioInit drives
// it high at boot.
#define PINIO1_PIN           PA11
#define PINIO1_CONFIG        (PINIO_CONFIG_MODE_OUT_PP | PINIO_CONFIG_OUT_INVERTED)

// Status LED
#define LED0_PIN             PA12
// GPIO12 -> R15/R16 -> D1 anode, D1 cathode -> GND: active high.
// ledSet uses INVERTED to select that physical polarity.
#define LED0_INVERTED

// Gyro+acc on SPI0: exact populated U9 is BMI270.
#define USE_GYRO
#define USE_ACC
#define USE_ACCGYRO_BMI270
#define SPI0_SCK_PIN         PA18
#define SPI0_SDO_PIN         PA19
#define SPI0_SDI_PIN         PA20
#define GYRO_1_CS_PIN        PA14
#define GYRO_1_EXTI_PIN      PA13
#define GYRO_1_SPI_INSTANCE  SPI0

// Source31066 has no ENABLE_BMI270_ALIGN_AS_ICM consumer. Use its native,
// supported board-alignment transform for this specific populated placement.
// Bosch DS000-08 section8.2 + native pad1: sensor +X is CAD +Y, +Y is CAD -X.
// The assembly camera is at -Y. CW180 maps output X forward, Y left, Z up.
// Bench axis-direction qualification remains required; see axes.md.
#define GYRO_1_ALIGN         CW180_DEG

// LED strip pad. Its WS2812 program goes on PIO1 (with the PIO UARTs): the
// default PIO2 is shared with the FB OSD, whose 31-instruction program then
// no longer fits and the OSD stays blank.
#define LED_STRIP_PIN        PA23
#define PIO_LEDSTRIP_INDEX   1
// No LED_STRIP_INVERTED: Q2 (gate on 3.3V, source on the GPIO, 2.4k to 4.5V) is a non-inverting level shifter

// Motors (PIO0 DShot), silk M1-M4 = GPIO31..28
#define MOTOR1_PIN           PA31
#define MOTOR2_PIN           PA30
#define MOTOR3_PIN           PA29
#define MOTOR4_PIN           PA28

// Four native AM32 signal wires carry bidirectional DShot. ESC J1.4 is NC;
// do not enable a serial ESC sensor or assign ESC_SENSOR_UART to that wire.
#define DEFAULT_MOTOR_PROTOCOL MOTOR_PROTOCOL_DSHOT600
#define DEFAULT_DSHOT_TELEMETRY DSHOT_TELEMETRY_ON

// Blackbox: microSD on SPI1
#define USE_SDCARD
#define USE_SDCARD_SPI
#define SPI1_SCK_PIN         PA42
#define SPI1_SDO_PIN         PA43
#define SPI1_SDI_PIN         PA44
#define SDCARD_SPI_CS_PIN    PA46
#define SDCARD_SPI_INSTANCE  SPI1
#define DEFAULT_BLACKBOX_DEVICE  BLACKBOX_DEVICE_SDCARD

// ADC (each input via 1k + 100nF RC)
#define USE_ADC
#define ADC_CURR_PIN         PA40
#define ADC_VBAT_PIN         PA41
#define ADC_RSSI_PIN         PA45
#define ADC_EXTERNAL1_PIN    PA47
#define DEFAULT_VOLTAGE_METER_SOURCE  VOLTAGE_METER_ADC
#define DEFAULT_VOLTAGE_METER_SCALE   110 // 100k:10k divider
#define DEFAULT_CURRENT_METER_SOURCE  CURRENT_METER_ADC
#define DEFAULT_CURRENT_METER_SCALE   100  // mV/10A: native ESC INA186A3 gain100, two 0.2mOhm shunts in parallel; calibrate physically
