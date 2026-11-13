// LabWired quadrotor flight controller.
// Five-controller closed-loop twin: BMI270 attitude/inertial altitude feedback,
// four independent ESC commands, deterministic maneuver and all-motor failsafe.
#include <stdint.h>
#include <stdbool.h>

#define REG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define RCC_AHB2ENR REG(0x4002104C)
#define RCC_APB1ENR1 REG(0x40021058)
#define GPIOA_MODER REG(0x48000000)
#define GPIOA_AFRL REG(0x48000020)
#define GPIOB_MODER REG(0x48000400)
#define GPIOB_OTYPER REG(0x48000404)
#define GPIOB_PUPDR REG(0x4800040C)
#define GPIOB_AFRL REG(0x48000420)
#define GPIOC_MODER REG(0x48000800)
#define GPIOC_PUPDR REG(0x4800080C)
#define GPIOC_IDR REG(0x48000810)
#define GPIOC_ODR REG(0x48000814)
#define USART2_CR1 REG(0x40004400)
#define USART2_BRR REG(0x4000440C)
#define USART2_ISR REG(0x4000441C)
#define USART2_TDR REG(0x40004428)
#define I2C1_CR1 REG(0x40005400)
#define I2C1_CR2 REG(0x40005404)
#define I2C1_TIMINGR REG(0x40005410)
#define I2C1_ISR REG(0x40005418)
#define I2C1_ICR REG(0x4000541C)
#define I2C1_RXDR REG(0x40005424)
#define I2C1_TXDR REG(0x40005428)
#define SYST_CSR REG(0xE000E010)
#define SYST_RVR REG(0xE000E014)
#define SYST_CVR REG(0xE000E018)

#define CPU_HZ 4000000u
#define CONTROL_HZ 10000u
#define IMU_HZ 100u
#define IMU_TICKS (CONTROL_HZ / IMU_HZ)
#define COMMAND_FRAME_TICKS 100u
#define COMMAND_MASK ((1u<<8)|(1u<<9)|(1u<<10)|(1u<<11))
#define TICKS_PER_SECOND CONTROL_HZ
#define TXIS (1u<<1)
#define RXNE (1u<<2)
#define NACKF (1u<<4)
#define STOPF (1u<<5)
#define TC (1u<<6)
#define START (1u<<13)
#define AUTOEND (1u<<25)
#define RD_WRN (1u<<10)
#define NBYTES(n) ((uint32_t)(n)<<16)
#define SADD(a) ((uint32_t)(a)<<1)

static void text(const char *s) {
  while (*s) {
    while (!(USART2_ISR & (1u << 7))) {}
    USART2_TDR = (uint8_t)*s++;
  }
}
static int32_t abs32(int32_t value) { return value < 0 ? -value : value; }
static int clamp_int(int value, int low, int high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}
static void wait_stop(void) {
  while (!(I2C1_ISR & STOPF)) {}
  I2C1_ICR = STOPF;
}
static bool i2c_write(uint8_t address, const uint8_t *data, uint32_t count, bool autoend) {
  I2C1_CR2 = SADD(address) | NBYTES(count) | (autoend ? AUTOEND : 0u) | START;
  for (uint32_t index = 0; index < count; index++) {
    uint32_t status;
    do { status = I2C1_ISR; } while (!(status & (TXIS | NACKF)));
    if (status & NACKF) {
      I2C1_ICR = NACKF;
      wait_stop();
      return false;
    }
    I2C1_TXDR = data[index];
  }
  if (autoend) wait_stop();
  else while (!(I2C1_ISR & TC)) {}
  return true;
}
static bool i2c_reg_write(uint8_t reg, uint8_t value) {
  uint8_t data[2] = { reg, value };
  return i2c_write(0x68, data, 2, true);
}
static bool i2c_read(uint8_t reg, uint8_t *data, uint32_t count) {
  if (!i2c_write(0x68, &reg, 1, false)) return false;
  I2C1_CR2 = SADD(0x68) | RD_WRN | NBYTES(count) | AUTOEND | START;
  for (uint32_t index = 0; index < count; index++) {
    while (!(I2C1_ISR & (RXNE | NACKF))) {}
    if (I2C1_ISR & NACKF) {
      I2C1_ICR = NACKF;
      wait_stop();
      return false;
    }
    data[index] = (uint8_t)I2C1_RXDR;
  }
  wait_stop();
  return true;
}
static int16_t le16(const uint8_t *data) {
  return (int16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8));
}
static bool bmi270_init(void) {
  uint8_t chip_id = 0;
  if (!i2c_read(0x00, &chip_id, 1) || chip_id != 0x24) return false;
  // Upload one config byte to open the deterministic model's init gate.
  if (!i2c_reg_write(0x7C, 0x00)) return false;
  if (!i2c_reg_write(0x5E, 0x00)) return false;
  if (!i2c_reg_write(0x59, 0x01)) return false;
  // Accelerometer ±2 g; gyroscope ±250 degrees/s.
  if (!i2c_reg_write(0x41, 0x00)) return false;
  if (!i2c_reg_write(0x43, 0x03)) return false;
  return i2c_reg_write(0x7D, 0x06);
}
static void command_outputs(uint32_t phase, const uint8_t widths[4]) {
  uint32_t set = 0, clear = 0;
  for (uint32_t index = 0; index < 4; index++) {
    const uint32_t bit = 1u << (8u + index);
    if (phase == 0 && widths[index]) set |= bit;
    if (phase == widths[index]) clear |= bit;
  }
  GPIOC_ODR = (GPIOC_ODR | set) & ~clear;
}
static uint8_t clamp_width(int value) {
  return (uint8_t)clamp_int(value, 18, 72);
}
static void init(void) {
  RCC_AHB2ENR |= 7u;
  RCC_APB1ENR1 |= (1u << 17) | (1u << 21);
  GPIOA_MODER = (GPIOA_MODER & ~(3u << 4)) | (2u << 4);
  GPIOA_AFRL = (GPIOA_AFRL & ~(15u << 8)) | (7u << 8);
  GPIOB_MODER = (GPIOB_MODER & ~((3u << 12) | (3u << 14))) | (2u << 12) | (2u << 14);
  GPIOB_OTYPER |= (1u << 6) | (1u << 7);
  GPIOB_PUPDR = (GPIOB_PUPDR & ~(0x0fu << 12)) | (1u << 12) | (1u << 14);
  GPIOB_AFRL = (GPIOB_AFRL & ~(0xffu << 24)) | (0x44u << 24);
  GPIOC_MODER = (GPIOC_MODER & ~(0xffu | (0xffu << 16)))
    | (1u << 16) | (1u << 18) | (1u << 20) | (1u << 22);
  GPIOC_PUPDR = (GPIOC_PUPDR & ~0xffu) | 0xaau;
  GPIOC_ODR &= ~COMMAND_MASK;
  USART2_BRR = (CPU_HZ + 57600u) / 115200u;
  USART2_CR1 = (1u << 0) | (1u << 3);
  I2C1_TIMINGR = (4u << 20) | (2u << 16) | (15u << 8) | 15u;
  I2C1_CR1 = 1u;
  SYST_RVR = CPU_HZ / CONTROL_HZ - 1u;
  SYST_CVR = 0;
  SYST_CSR = (1u << 2) | 1u;
}

int main(void) {
  init();
  for (volatile uint32_t delay = 0; delay < 1000; delay++) {}
  if (!bmi270_init()) {
    text("FC BMI270 INIT FAILED\r\n");
    for (;;) {}
  }
  text("FC READY BMI270 ONLINE\r\n");

  uint32_t ticks = 0, phase = 0, health_bad = 0, hover_good = 0, recover_good = 0;
  uint32_t failsafe_tick = 0;
  uint8_t widths[4] = { 0, 0, 0, 0 };
  bool failsafe = false, takeoff_verified = false, hover_verified = false;
  bool roll_verified = false, pitch_verified = false, yaw_verified = false;
  bool recovery_verified = false, landing_verified = false;
  int32_t roll_raw = 0, pitch_raw = 0, gx_raw = 0, gy_raw = 0, gz_raw = 0;
  int32_t yaw_mdeg = 0, vertical_speed_mm_s = 0;
  int64_t altitude_centi_mm = 0;

  for (;;) {
    if ((SYST_CSR & (1u << 16)) == 0) continue;
    ticks++;

    if (ticks == 1u * TICKS_PER_SECOND) text("FC ARM\r\n");
    if (ticks == 2u * TICKS_PER_SECOND) text("FC TAKEOFF\r\n");
    if (ticks == 5u * TICKS_PER_SECOND) text("FC HOVER HOLD\r\n");
    if (ticks == 8u * TICKS_PER_SECOND) text("FC ROLL COMMAND\r\n");
    if (ticks == 92u * TICKS_PER_SECOND / 10u) text("FC PITCH COMMAND\r\n");
    if (ticks == 104u * TICKS_PER_SECOND / 10u) text("FC YAW COMMAND\r\n");
    if (ticks == 12u * TICKS_PER_SECOND) text("FC ATTITUDE RECOVERY\r\n");

    if (ticks > 25u * TICKS_PER_SECOND / 10u && (GPIOC_IDR & 0x0fu) != 0x0fu) {
      if (++health_bad >= 20 && !failsafe) {
        failsafe = true;
        failsafe_tick = ticks;
        text("FC FAULT DETECTED - ALL ESC DISARM\r\n");
      }
    } else {
      health_bad = 0;
    }

    if ((ticks % IMU_TICKS) == 0u) {
      uint8_t data[12];
      if (i2c_read(0x0C, data, 12)) {
        const int32_t ax_raw = (int32_t)le16(&data[0]);
        const int32_t ay_raw = (int32_t)le16(&data[2]);
        const int32_t az_raw = (int32_t)le16(&data[4]);
        roll_raw = ay_raw;
        pitch_raw = -ax_raw;
        gx_raw = (int32_t)le16(&data[6]);
        gy_raw = (int32_t)le16(&data[8]);
        gz_raw = (int32_t)le16(&data[10]);

        const int64_t horizontal_square = (int64_t)ax_raw * ax_raw + (int64_t)ay_raw * ay_raw;
        const int32_t expected_gravity_z = 16384 - (int32_t)(horizontal_square / 32768);
        const int32_t vertical_accel_raw = az_raw - expected_gravity_z;
        vertical_speed_mm_s += (vertical_accel_raw * 98) / 16384;
        vertical_speed_mm_s = clamp_int(vertical_speed_mm_s, -6000, 6000);
        altitude_centi_mm += vertical_speed_mm_s;
        if (altitude_centi_mm < 0) {
          altitude_centi_mm = 0;
          vertical_speed_mm_s = 0;
        }
        if (altitude_centi_mm > 500000) {
          altitude_centi_mm = 500000;
          if (vertical_speed_mm_s > 0) vertical_speed_mm_s = 0;
        }
        yaw_mdeg += (gz_raw * 10) / 131;
        while (yaw_mdeg > 180000) yaw_mdeg -= 360000;
        while (yaw_mdeg < -180000) yaw_mdeg += 360000;

        const int32_t altitude_mm = (int32_t)(altitude_centi_mm / 100);
        if (!takeoff_verified && altitude_mm > 500) {
          takeoff_verified = true;
          text("FC TAKEOFF VERIFIED\r\n");
        }
        if (ticks >= 5u * TICKS_PER_SECOND && ticks < 8u * TICKS_PER_SECOND
            && abs32(altitude_mm - 1000) <= 150
            && abs32(roll_raw) <= 1430 && abs32(pitch_raw) <= 1430) {
          if (++hover_good >= IMU_HZ && !hover_verified) {
            hover_verified = true;
            text("FC HOVER VERIFIED\r\n");
          }
        } else {
          hover_good = 0;
        }
        if (!roll_verified && ticks >= 8u * TICKS_PER_SECOND
            && ticks < 92u * TICKS_PER_SECOND / 10u && roll_raw > 1000) {
          roll_verified = true;
          text("FC ROLL TRACK VERIFIED\r\n");
        }
        if (!pitch_verified && ticks >= 92u * TICKS_PER_SECOND / 10u
            && ticks < 104u * TICKS_PER_SECOND / 10u && pitch_raw > 900) {
          pitch_verified = true;
          text("FC PITCH TRACK VERIFIED\r\n");
        }
        if (!yaw_verified && ticks >= 104u * TICKS_PER_SECOND / 10u
            && ticks < 12u * TICKS_PER_SECOND && yaw_mdeg > 8000) {
          yaw_verified = true;
          text("FC YAW TRACK VERIFIED\r\n");
        }
        if (ticks >= 13u * TICKS_PER_SECOND && !failsafe
            && abs32(altitude_mm - 1000) <= 150
            && abs32(roll_raw) <= 900 && abs32(pitch_raw) <= 900 && abs32(yaw_mdeg) <= 5000) {
          if (++recover_good >= IMU_HZ / 2u && !recovery_verified) {
            recovery_verified = true;
            text("FC RECOVERY VERIFIED\r\n");
          }
        } else {
          recover_good = 0;
        }
        if (failsafe && !landing_verified && ticks > failsafe_tick + TICKS_PER_SECOND
            && altitude_mm <= 50) {
          landing_verified = true;
          text("FC SAFE LANDING VERIFIED\r\n");
        }
      }
    }

    int target_altitude_mm = 0;
    if (ticks >= 2u * TICKS_PER_SECOND && ticks < 5u * TICKS_PER_SECOND) {
      target_altitude_mm = (int)(((uint64_t)(ticks - 2u * TICKS_PER_SECOND) * 1000u)
        / (3u * TICKS_PER_SECOND));
    } else if (ticks >= 5u * TICKS_PER_SECOND) {
      target_altitude_mm = 1000;
    }
    int desired_roll_raw = 0, desired_pitch_raw = 0, desired_yaw_mdeg = 0;
    if (ticks >= 8u * TICKS_PER_SECOND && ticks < 92u * TICKS_PER_SECOND / 10u) {
      desired_roll_raw = 2200;
    } else if (ticks >= 92u * TICKS_PER_SECOND / 10u
        && ticks < 104u * TICKS_PER_SECOND / 10u) {
      desired_pitch_raw = 2000;
    } else if (ticks >= 104u * TICKS_PER_SECOND / 10u && ticks < 12u * TICKS_PER_SECOND) {
      desired_yaw_mdeg = 20000;
    }

    int base = 0;
    if (ticks >= 1u * TICKS_PER_SECOND && ticks < 2u * TICKS_PER_SECOND) {
      base = 22;
    } else if (ticks >= 2u * TICKS_PER_SECOND) {
      const int altitude_mm = (int)(altitude_centi_mm / 100);
      const int altitude_correction = clamp_int((target_altitude_mm - altitude_mm) / 120
        - vertical_speed_mm_s / 350, -10, 10);
      base = 60 + altitude_correction;
    }
    const int roll = clamp_int((desired_roll_raw - roll_raw) / 700 - gx_raw / 700, -7, 7);
    const int pitch = clamp_int((desired_pitch_raw - pitch_raw) / 700 - gy_raw / 700, -7, 7);
    const int yaw = clamp_int((desired_yaw_mdeg - yaw_mdeg) / 2500 - gz_raw / 1800, -6, 6);

    if (failsafe || base == 0) {
      for (int index = 0; index < 4; index++) widths[index] = 0;
    } else {
      widths[0] = clamp_width(base + roll - pitch + yaw);
      widths[1] = clamp_width(base - roll - pitch - yaw);
      widths[2] = clamp_width(base + roll + pitch - yaw);
      widths[3] = clamp_width(base - roll + pitch + yaw);
    }
    command_outputs(phase, widths);
    if (++phase >= COMMAND_FRAME_TICKS) phase = 0;
  }
}
