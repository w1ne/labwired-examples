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

#define CPU_HZ 80000000u
#define CONTROL_HZ 10000u
#define IMU_HZ 100u
#define IMU_TICKS (CONTROL_HZ / IMU_HZ)
#define COMMAND_FRAME_TICKS 100u
#define COMMAND_MASK ((1u<<8)|(1u<<9)|(1u<<10)|(1u<<11))
#define TICKS_PER_SECOND CONTROL_HZ
#define I2C_WAIT_LIMIT 50000u
#define UART_WAIT_LIMIT 10000u
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

// The native stm32l476 descriptor and motor model both declare 80 MHz.
// Configure real L476 MSI(4 MHz) -> PLL(M=1,N=40,R=2) before using that contract.
#define RCC_CR REG(0x40021000)
#define RCC_CFGR REG(0x40021008)
#define RCC_PLLCFGR REG(0x4002100C)
#define PWR_CR1 REG(0x40007000)
#define PWR_SR2 REG(0x40007014)
#define FLASH_ACR REG(0x40022000)
#define CLOCK_WAIT_LIMIT 100000u
#define UART_QUEUE_MASK 511u
static volatile uint32_t control_ticks = 0;
static uint32_t consumed_control_tick = 0;
static volatile uint16_t uart_head = 0, uart_tail = 0;
static volatile uint8_t uart_queue[UART_QUEUE_MASK + 1u];
static volatile uint8_t command_widths[4] = { 0, 0, 0, 0 };
static volatile bool failsafe = false;
static volatile uint32_t failsafe_tick = 0;
static const char * volatile failsafe_reason = 0;
static bool clock_wait(volatile uint32_t *reg, uint32_t mask, uint32_t value) {
  for (uint32_t poll = 0; poll < CLOCK_WAIT_LIMIT; poll++)
    if ((*reg & mask) == value) return true;
  return false;
}
static bool system_clock_80mhz(void) {
  RCC_APB1ENR1 |= 1u << 28;
  PWR_CR1 = (PWR_CR1 & ~(3u << 9)) | (1u << 9);
  if (!clock_wait(&PWR_SR2, 1u << 10, 0)) return false;
  FLASH_ACR = (FLASH_ACR & ~7u) | 4u;
  if (!clock_wait(&FLASH_ACR, 7u, 4u)) return false;
  RCC_CR = (RCC_CR & ~(15u << 4)) | (6u << 4) | (1u << 3) | 1u;
  if (!clock_wait(&RCC_CR, 1u << 1, 1u << 1)) return false;
  RCC_CFGR &= ~3u;
  if (!clock_wait(&RCC_CFGR, 3u << 2, 0)) return false;
  RCC_CR &= ~(1u << 24);
  if (!clock_wait(&RCC_CR, 1u << 25, 0)) return false;
  RCC_PLLCFGR = 1u | (40u << 8) | (1u << 24);
  RCC_CR |= 1u << 24;
  if (!clock_wait(&RCC_CR, 1u << 25, 1u << 25)) return false;
  RCC_CFGR = (RCC_CFGR & ~0xfff3u) | 3u;
  return clock_wait(&RCC_CFGR, 3u << 2, 3u << 2);
}
// Main produces status text; the tick ISR drains at most one UART character.
// Diagnostics cannot busy-wait through a command-sampling deadline.
static void text(const char *s) {
  while (*s) {
    uint16_t next = (uint16_t)((uart_head + 1u) & UART_QUEUE_MASK);
    if (next == uart_tail) return;
    uart_queue[uart_head] = (uint8_t)*s++;
    uart_head = next;
  }
}
static void start_control_clock(void) {
  SYST_CSR = 0;
  control_ticks = 0;
  consumed_control_tick = 0;
  SYST_RVR = CPU_HZ / CONTROL_HZ - 1u;
  SYST_CVR = 0;
  SYST_CSR = (1u << 2) | (1u << 1) | 1u;
}
static uint32_t wait_control_tick(void) {
  for (;;) {
    __asm__ volatile("cpsid i" ::: "memory");
    uint32_t tick = control_ticks;
    if (tick != consumed_control_tick) {
      consumed_control_tick = tick;
      __asm__ volatile("cpsie i" ::: "memory");
      return tick;
    }
    // A pending interrupt wakes WFI while masked, then runs after CPSIE.
    __asm__ volatile("dsb 0xF\nwfi\ncpsie i" ::: "memory");
  }
}
static int32_t abs32(int32_t value) { return value < 0 ? -value : value; }
static void number(int32_t value) {
  char buffer[12]; uint32_t position = sizeof(buffer) - 1u;
  buffer[position] = 0;
  uint32_t magnitude = (uint32_t)(value < 0 ? -value : value);
  do { buffer[--position] = (char)('0' + magnitude % 10u); magnitude /= 10u; } while (magnitude);
  if (value < 0) buffer[--position] = '-';
  text(buffer + position);
}
static int clamp_int(int value, int low, int high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}
static bool wait_stop(void) {
  uint32_t polls = I2C_WAIT_LIMIT;
  while (!(I2C1_ISR & STOPF) && --polls) {}
  if (!polls) return false;
  I2C1_ICR = STOPF;
  return true;
}
static bool i2c_write(uint8_t address, const uint8_t *data, uint32_t count, bool autoend) {
  I2C1_CR2 = SADD(address) | NBYTES(count) | (autoend ? AUTOEND : 0u) | START;
  for (uint32_t index = 0; index < count; index++) {
    uint32_t status = 0;
    uint32_t polls = I2C_WAIT_LIMIT;
    do { status = I2C1_ISR; } while (!(status & (TXIS | NACKF)) && --polls);
    if (!polls || (status & NACKF)) {
      if (status & NACKF) { I2C1_ICR = NACKF; (void)wait_stop(); }
      return false;
    }
    I2C1_TXDR = data[index];
  }
  if (autoend) return wait_stop();
  uint32_t polls = I2C_WAIT_LIMIT;
  while (!(I2C1_ISR & TC) && --polls) {}
  return polls != 0;

}
static bool i2c_reg_write(uint8_t reg, uint8_t value) {
  uint8_t data[2] = { reg, value };
  return i2c_write(0x68, data, 2, true);
}
static bool i2c_read(uint8_t reg, uint8_t *data, uint32_t count) {
  if (!i2c_write(0x68, &reg, 1, false)) return false;
  I2C1_CR2 = SADD(0x68) | RD_WRN | NBYTES(count) | AUTOEND | START;
  for (uint32_t index = 0; index < count; index++) {
    uint32_t polls = I2C_WAIT_LIMIT;
    while (!(I2C1_ISR & (RXNE | NACKF)) && --polls) {}
    if (!polls || (I2C1_ISR & NACKF)) {
      if (I2C1_ISR & NACKF) { I2C1_ICR = NACKF; (void)wait_stop(); }
      return false;
    }
    data[index] = (uint8_t)I2C1_RXDR;
  }
  return wait_stop();
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
// Compute every command pin on every tick. A zero width clears a previously
// high output immediately, including faults in the middle of a PWM frame.
static uint32_t command_high_mask(uint32_t phase, const uint8_t widths[4]) {
  uint32_t high = 0;
  for (uint32_t index = 0; index < 4; index++) {
    if (widths[index] != 0u && phase < widths[index]) high |= 1u << (8u + index);
  }
  return high;
}
static void command_outputs(uint32_t phase, const uint8_t widths[4]) {
  GPIOC_ODR = (GPIOC_ODR & ~COMMAND_MASK) | command_high_mask(phase, widths);
}
// Both the interrupt and main loop can latch a fault. Preserve PRIMASK when
// publishing it so no later main-loop update can briefly reassert an output.
static void latch_disarm(uint32_t tick, const char *reason) {
  uint32_t primask;
  __asm__ volatile("mrs %0, primask\ncpsid i" : "=r"(primask) :: "memory");
  if (!failsafe) {
    failsafe_tick = tick;
    failsafe_reason = reason;
    failsafe = true;
  }
  GPIOC_ODR &= ~COMMAND_MASK;
  __asm__ volatile("msr primask, %0" :: "r"(primask) : "memory");
}
// A frame uses one complete mixer result. The main loop can read the BMI270
// over I2C without disturbing the 10 kHz GPIO command or fault-sampling clock.
void SysTick_Handler(void) {
  static uint32_t phase = 0, health_bad = 0;
  static uint8_t active_widths[4] = { 0, 0, 0, 0 };
  const uint32_t tick = ++control_ticks;
  const uint32_t inputs = GPIOC_IDR;
  if ((inputs & (1u << 4)) != 0u)
    latch_disarm(tick, "FC OPERATOR KILL - ALL ESC DISARM\r\n");
  if (tick == TICKS_PER_SECOND && (inputs & 0x0fu) != 0x0fu)
    latch_disarm(tick, "FC ESC NOT READY - ALL ESC DISARM\r\n");
  if (tick > 25u * TICKS_PER_SECOND / 10u && (inputs & 0x0fu) != 0x0fu) {
    if (++health_bad >= 20u)
      latch_disarm(tick, "FC FAULT DETECTED - ALL ESC DISARM\r\n");
  } else {
    health_bad = 0;
  }
  if (phase == 0u)
    for (uint32_t index = 0; index < 4u; index++)
      active_widths[index] = command_widths[index];
  if (failsafe) GPIOC_ODR &= ~COMMAND_MASK;
  else command_outputs(phase, active_widths);
  if (++phase >= COMMAND_FRAME_TICKS) phase = 0;
  if (uart_tail != uart_head && (USART2_ISR & (1u << 7))) {
    USART2_TDR = uart_queue[uart_tail];
    uart_tail = (uint16_t)((uart_tail + 1u) & UART_QUEUE_MASK);
  }
}
static void publish_commands(const uint8_t widths[4]) {
  uint32_t primask;
  __asm__ volatile("mrs %0, primask\ncpsid i" : "=r"(primask) :: "memory");
  for (uint32_t index = 0; index < 4u; index++)
    command_widths[index] = failsafe ? 0u : widths[index];
  __asm__ volatile("msr primask, %0" :: "r"(primask) : "memory");
}
static uint8_t clamp_width(int value) {
  return (uint8_t)clamp_int(value, 18, 72);
}
static void init(void) {
  SYST_CSR = 0;
  if (!system_clock_80mhz()) for (;;) { __asm__ volatile("wfi"); }
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
  // PC0-3 are ESC health inputs; PC4 is the operator emergency-stop input.
  GPIOC_PUPDR = (GPIOC_PUPDR & ~0x3ffu) | 0x2aau;
  GPIOC_ODR &= ~COMMAND_MASK;
  USART2_BRR = (CPU_HZ + 57600u) / 115200u;
  USART2_CR1 = (1u << 0) | (1u << 3);
  // 80 MHz / (PRESC+1) / (SCLL+SCLH+2) = 400 kHz.
  I2C1_TIMINGR = (9u << 28) | (4u << 20) | (2u << 16) | (9u << 8) | 9u;
  I2C1_CR1 = 1u;
}

int main(void) {
  init();
  for (volatile uint32_t delay = 0; delay < 1000; delay++) {}
  if (!bmi270_init()) {
    text("FC BMI270 INIT FAILED\r\n");
    start_control_clock();
    for (;;) { __asm__ volatile("wfi"); }
  }
  text("FC READY BMI270 ONLINE\r\n");

  uint32_t ticks = 0, last_imu_tick = 0, hover_good = 0, recover_good = 0;
  uint32_t imu_read_failures = 0;
  uint8_t widths[4] = { 0, 0, 0, 0 };
  bool failure_reported = false, takeoff_verified = false, hover_verified = false;
  bool roll_verified = false, pitch_verified = false, yaw_verified = false;
  bool recovery_verified = false, landing_verified = false;
  int32_t roll_raw = 0, pitch_raw = 0, gx_raw = 0, gy_raw = 0, gz_raw = 0;
  int32_t yaw_mdeg = 0, vertical_speed_mm_s = 0;
  int64_t altitude_centi_mm = 0;
  // Preserve sub-mm/s acceleration and sub-mm position between 100 Hz samples.
  // Truncating each delta-v before accumulation biases the inertial estimate.
  int64_t vertical_speed_q16_mm_s = 0, altitude_q16_mm = 0;
  int32_t yaw_remainder = 0;
  start_control_clock();

  for (;;) {
    ticks = wait_control_tick();
    if (failsafe_reason != 0 && !failure_reported) {
      text(failsafe_reason);
      failure_reported = true;
    }
    // BMI270 acquisition and the mixer execute once per 10 ms. SysTick keeps
    // command pulses and fault monitoring running during the I2C transaction.
    if (ticks - last_imu_tick < IMU_TICKS) continue;
    const uint32_t previous_tick = last_imu_tick;
    if (ticks - last_imu_tick >= 2u * IMU_TICKS) {
      latch_disarm(ticks, "FC IMU CONTROL DEADLINE MISSED - ALL ESC DISARM\r\n");
      last_imu_tick = ticks - (ticks % IMU_TICKS);
    } else {
      last_imu_tick += IMU_TICKS;
    }

    // Command markers describe intent. Measurement-based markers below
    // require the same takeoff, hover and attitude thresholds as before.
    if (previous_tick < TICKS_PER_SECOND && ticks >= TICKS_PER_SECOND && !failsafe)
      text("FC ARM COMMAND\r\n");
    if (previous_tick < 2u * TICKS_PER_SECOND && ticks >= 2u * TICKS_PER_SECOND && !failsafe)
      text("FC TAKEOFF COMMAND\r\n");
    if (previous_tick < 5u * TICKS_PER_SECOND && ticks >= 5u * TICKS_PER_SECOND && !failsafe)
      text("FC HOVER SETPOINT\r\n");
    if (previous_tick < 8u * TICKS_PER_SECOND && ticks >= 8u * TICKS_PER_SECOND && !failsafe)
      text("FC ROLL COMMAND\r\n");
    if (previous_tick < 92u * TICKS_PER_SECOND / 10u
        && ticks >= 92u * TICKS_PER_SECOND / 10u && !failsafe)
      text("FC PITCH COMMAND\r\n");
    if (previous_tick < 104u * TICKS_PER_SECOND / 10u
        && ticks >= 104u * TICKS_PER_SECOND / 10u && !failsafe)
      text("FC YAW COMMAND\r\n");
    if (previous_tick < 12u * TICKS_PER_SECOND && ticks >= 12u * TICKS_PER_SECOND && !failsafe)
      text("FC ATTITUDE RECOVERY COMMAND\r\n");

    {
      uint8_t data[12];
      if (i2c_read(0x0C, data, 12)) {
        imu_read_failures = 0;
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
        // g=9806.65 mm/s^2, dt=0.01 s, accelerometer=16384 LSB/g.
        vertical_speed_q16_mm_s += ((int64_t)vertical_accel_raw * 392266LL) / 1000LL;
        if (vertical_speed_q16_mm_s > 6000LL * 65536LL) vertical_speed_q16_mm_s = 6000LL * 65536LL;
        if (vertical_speed_q16_mm_s < -6000LL * 65536LL) vertical_speed_q16_mm_s = -6000LL * 65536LL;
        altitude_q16_mm += vertical_speed_q16_mm_s / IMU_HZ;
        if (altitude_q16_mm < 0) {
          altitude_q16_mm = 0;
          vertical_speed_q16_mm_s = 0;
        }
        if (altitude_q16_mm > 5000LL * 65536LL) {
          altitude_q16_mm = 5000LL * 65536LL;
          if (vertical_speed_q16_mm_s > 0) vertical_speed_q16_mm_s = 0;
        }
        vertical_speed_mm_s = (int32_t)(vertical_speed_q16_mm_s / 65536LL);
        altitude_centi_mm = altitude_q16_mm * 100LL / 65536LL;
        const int32_t yaw_delta = gz_raw * 10 + yaw_remainder;
        yaw_mdeg += yaw_delta / 131;
        yaw_remainder = yaw_delta % 131;
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
        if (failsafe && takeoff_verified && !landing_verified && ticks > failsafe_tick + TICKS_PER_SECOND
            && altitude_mm <= 50) {
          landing_verified = true;
          text("FC ESTIMATED GROUND CONTACT\r\n");
        }
      } else if (++imu_read_failures >= 3u) {
        latch_disarm(ticks, "FC IMU LOST - ALL ESC DISARM\r\n");
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
      // One command tick per 120 mm position error and per 200 mm/s
      // vertical speed. Sum the rational PD terms before rounding so small
      // terms do not disappear independently; round both signs symmetrically.
      const int altitude_pd = (target_altitude_mm - altitude_mm) * 200
        - vertical_speed_mm_s * 120;
      const int altitude_correction = clamp_int(
        (altitude_pd + (altitude_pd >= 0 ? 12000 : -12000)) / 24000, -10, 10);
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
    publish_commands(widths);
    if (last_imu_tick % (TICKS_PER_SECOND / 2u) == 0u) {
      text("FC STATE ms="); number((int32_t)(last_imu_tick / 10u));
      text(" z_mm="); number((int32_t)(altitude_centi_mm / 100));
      text(" vz_mm_s="); number(vertical_speed_mm_s);
      text(" roll_raw="); number(roll_raw); text(" pitch_raw="); number(pitch_raw);
      text(" yaw_mdeg="); number(yaw_mdeg); text(" base="); number(base); text("\r\n");
    }
  }
}
