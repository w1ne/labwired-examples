#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

static const uint32_t X_STEP = PB0;
static const uint32_t X_DIR = PB1;
static const uint32_t Y_STEP = PB3;
static const uint32_t Y_DIR = PB4;
static const uint32_t Z_STEP = PB5;
static const uint32_t Z_DIR = PB8;
static const uint32_t E_STEP = PB9;
static const uint32_t E_DIR = PB10;
static const uint32_t STEPPER_EN = PB12;

static const uint32_t X_MIN = PA8;
static const uint32_t Y_MIN = PC13;
static const uint32_t Z_MIN = PC14;
static const uint32_t START_PIN = PA15;
static const uint32_t STOP_PIN = PB2;

static const uint32_t HOTEND_PWM = PB13;
static const uint32_t BED_PWM = PB14;
static const uint32_t FAN_PWM = PB15;
static const uint32_t HOT_ADC = PA4;
static const uint32_t BED_ADC = PA1;
// Fault LED on the controller board: 3V3 - 1k - LED - PA10, so LOW lights it.
static const uint32_t STATUS_LED = PA10;

static const uint8_t OLED_ADDRESS = 0x3c;
static const uint32_t STEP_PIN[4] = {X_STEP, Y_STEP, Z_STEP, E_STEP};
static const uint32_t DIR_PIN[4] = {X_DIR, Y_DIR, Z_DIR, E_DIR};
static const uint32_t LIMIT_PIN[3] = {X_MIN, Y_MIN, Z_MIN};
static const int32_t STEPS_PER_MM[4] = {5, 5, 25, 100};

enum class State : uint8_t { IDLE, HOME, HEATING, PRINTING, DONE, FAULT };
static State state = State::IDLE;

static uint8_t oledFrame[1024];
static bool oledOk = true;
static int hotC = 25;
static int bedC = 25;
static uint16_t hotAdc = 0;
static int32_t axisSteps[4] = {0, 0, 0, 0};
static uint32_t stepRiseCount[4] = {0, 0, 0, 0};

static uint8_t hotDuty = 0;
static uint8_t bedDuty = 0;
static uint32_t thermalAt = 0;
static uint32_t reportedAt = 0;
static uint32_t heatWatchAt = 0;
static int heatWatchHot = 25;
static int heatWatchBed = 25;

static uint8_t homeAxis = 0;
static uint32_t homeCount = 0;
static uint32_t stateAt = 0;
static uint32_t stepAt = 0;
static uint32_t pulseAt = 0;
static uint8_t pulseMask = 0;

static bool rawStart = false;
static bool stableStart = false;
static uint32_t startChangedAt = 0;

static uint8_t segment = 0;
static uint32_t majorSteps = 0;
static uint32_t stepsTaken = 0;
static uint32_t stepIntervalUs = 0;
static int32_t deltaSteps[4] = {0, 0, 0, 0};
static int32_t ddaError[4] = {0, 0, 0, 0};
static int8_t stepSign[4] = {1, 1, 1, 1};

static const int32_t PATH[][4] = {
  {0, 0, 25, 0},
  {150, 150, 25, 0},
  {450, 150, 25, 100},
  {450, 450, 25, 200},
  {150, 450, 25, 300},
  {150, 150, 25, 400},
  {450, 450, 25, 500},
  {150, 150, 25, 600}
};

static const uint16_t NTC_ADC[] = {
  32,47,69,99,140,195,265,355,466,600,758,939,1140,1357,1585,1817,
  2048,2270,2481,2676,2854,3014,3155,3280,3388,3482,3563,3633,3694,
  3745,3790,3828,3861,3889,3914,3935,3953,3969,3983,3995,4006,4015
};
static const int16_t NTC_TEMP[] = {
  -55,-50,-45,-40,-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,
  35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,
  130,135,140,145,150
};

static const uint8_t GLYPHS[][5] = {
 {0x3e,0x51,0x49,0x45,0x3e},{0,0x42,0x7f,0x40,0},{0x42,0x61,0x51,0x49,0x46},
 {0x21,0x41,0x45,0x4b,0x31},{0x18,0x14,0x12,0x7f,0x10},{0x27,0x45,0x45,0x45,0x39},
 {0x3c,0x4a,0x49,0x49,0x30},{1,0x71,9,5,3},{0x36,0x49,0x49,0x49,0x36},
 {6,0x49,0x49,0x29,0x1e},
 {0x7e,0x11,0x11,0x11,0x7e},{0x7f,0x49,0x49,0x49,0x36},{0x3e,0x41,0x41,0x41,0x22},
 {0x7f,0x41,0x41,0x22,0x1c},{0x7f,0x49,0x49,0x49,0x41},{0x7f,9,9,9,1},
 {0x3e,0x41,0x49,0x49,0x7a},{0x7f,8,8,8,0x7f},{0,0x41,0x7f,0x41,0},
 {0x20,0x40,0x41,0x3f,1},{0x7f,8,0x14,0x22,0x41},{0x7f,0x40,0x40,0x40,0x40},
 {0x7f,2,0x0c,2,0x7f},{0x7f,4,8,0x10,0x7f},{0x3e,0x41,0x41,0x41,0x3e},
 {0x7f,9,9,9,6},{0x3e,0x41,0x51,0x21,0x5e},{0x7f,9,0x19,0x29,0x46},
 {0x46,0x49,0x49,0x49,0x31},{1,1,0x7f,1,1},{0x3f,0x40,0x40,0x40,0x3f},
 {0x1f,0x20,0x40,0x20,0x1f},{0x3f,0x40,0x38,0x40,0x3f},{0x63,0x14,8,0x14,0x63},
 {7,8,0x70,8,7},{0x61,0x51,0x49,0x45,0x43}
};

static void serialEvent(const char *name) {
  Serial.print(name);
  Serial.print(" t_us=");
  Serial.println(micros());
}

static void setPixel(uint8_t x, uint8_t y) {
  if (x < 128 && y < 64) {
    oledFrame[(y >> 3) * 128 + x] |= uint8_t(1U << (y & 7));
  }
}

static void drawText(uint8_t x, uint8_t y, const char *text) {
  while (*text && x < 123) {
    char c = *text++;
    int8_t index = -1;
    if (c >= '0' && c <= '9') index = c - '0';
    else if (c >= 'A' && c <= 'Z') index = c - 'A' + 10;
    for (uint8_t col = 0; col < 5; ++col) {
      uint8_t bits = index >= 0 ? GLYPHS[index][col] : 0;
      for (uint8_t row = 0; row < 7; ++row) {
        if (bits & (1U << row)) setPixel(x + col, y + row);
      }
    }
    x += 6;
  }
}

static void oledCommand(const uint8_t *bytes, size_t count) {
  Wire.beginTransmission(OLED_ADDRESS);
  Wire.write(uint8_t(0));
  Wire.write(bytes, count);
  if (Wire.endTransmission() != 0) oledOk = false;
}

static void flushDisplay() {
  const uint8_t addressWindow[] = {0x21,0,127,0x22,0,7};
  oledCommand(addressWindow, sizeof(addressWindow));
  for (size_t offset = 0; offset < sizeof(oledFrame); offset += 16) {
    Wire.beginTransmission(OLED_ADDRESS);
    Wire.write(uint8_t(0x40));
    Wire.write(oledFrame + offset, 16);
    if (Wire.endTransmission() != 0) oledOk = false;
  }
}

static void showScreen(const char *status) {
  memset(oledFrame, 0, sizeof(oledFrame));
  drawText(0, 2, "A1 MINI");
  drawText(0, 18, status);
  drawText(0, 34, "HOT 140C");
  drawText(0, 48, "BED 60C");
  flushDisplay();
  Serial.print("DISPLAY ");
  Serial.println(status);
}

static void initDisplay() {
  const uint8_t initBytes[] = {
    0xae,0xd5,0x80,0xa8,0x3f,0xd3,0x00,0x40,0x8d,0x14,0x20,0x00,
    0xa1,0xc8,0xda,0x12,0x81,0x7f,0xd9,0xf1,0xdb,0x20,0xa4,0xa6,0x2e,0xaf
  };
  oledCommand(initBytes, sizeof(initBytes));
  showScreen("PRESS START");
}

static int decodeBedTemperature(uint16_t adc) {
  const size_t count = sizeof(NTC_ADC) / sizeof(NTC_ADC[0]);
  for (size_t i = 1; i < count; ++i) {
    if (adc <= NTC_ADC[i]) {
      const int32_t span = int32_t(NTC_ADC[i] - NTC_ADC[i - 1]);
      const int32_t offset = int32_t(adc - NTC_ADC[i - 1]);
      return NTC_TEMP[i - 1] +
        int((offset * (NTC_TEMP[i] - NTC_TEMP[i - 1]) + span / 2) / span);
    }
  }
  return 200;
}

// 100K NTC (beta 3950) from 3V3A to PA4, 100K pulldown on the board:
// Rntc = 100K * (4095 - adc) / adc, then the beta equation.
static bool readHotendTemperature(int &temperatureC) {
  hotAdc = uint16_t(analogRead(HOT_ADC));
  if (hotAdc < 40 || hotAdc > 4090) return false;
  const float rNtc = 100000.0f * float(4095 - hotAdc) / float(hotAdc);
  const float invT = 1.0f / 298.15f + logf(rNtc / 100000.0f) / 3950.0f;
  temperatureC = int(1.0f / invT - 273.15f + 0.5f);
  return temperatureC >= 0 && temperatureC <= 500;
}

static bool readTemperatures() {
  int measuredHot = 0;
  const bool hotValid = readHotendTemperature(measuredHot);
  const uint16_t bedAdc = uint16_t(analogRead(BED_ADC));
  const int measuredBed = decodeBedTemperature(bedAdc);

  hotC = measuredHot;
  bedC = measuredBed;
  return hotValid && bedAdc > 40 && bedAdc < 4088 && bedC >= 0 && bedC <= 150;
}

static uint8_t dutyFor(int target, int actual) {
  const int error = target - actual;
  if (error <= 0) return 0;
  if (error >= 25) return 100;
  return uint8_t(error * 4);
}

static void writePowerOutputs(uint32_t nowUs) {
  const uint8_t phase = uint8_t((nowUs % 100000UL) / 1000UL);
  digitalWrite(HOTEND_PWM, phase < hotDuty ? HIGH : LOW);
  digitalWrite(BED_PWM, phase < bedDuty ? HIGH : LOW);
}

static void disableOutputs() {
  hotDuty = 0;
  bedDuty = 0;
  digitalWrite(HOTEND_PWM, LOW);
  digitalWrite(BED_PWM, LOW);
  digitalWrite(FAN_PWM, LOW);
  digitalWrite(STEPPER_EN, HIGH);
  for (uint8_t axis = 0; axis < 4; ++axis) digitalWrite(STEP_PIN[axis], LOW);
  pulseMask = 0;
}

static void fail(const char *reason) {
  if (state == State::FAULT) return;
  state = State::FAULT;
  disableOutputs();
  digitalWrite(STATUS_LED, LOW);
  Serial.print("FAULT ");
  serialEvent(reason);
  showScreen(reason);
}

static void serviceThermal(uint32_t nowUs) {
  if (uint32_t(nowUs - thermalAt) < 10000UL) return;
  thermalAt = nowUs;

  if (!readTemperatures()) {
    fail("SENSOR_FAULT");
    return;
  }

  if (uint32_t(nowUs - reportedAt) >= 100000UL) {
    reportedAt = nowUs;
    Serial.print("TEMP hot=");
    Serial.print(hotC);
    Serial.print(" bed=");
    Serial.print(bedC);
    Serial.print(" hot_adc=");
    Serial.println(hotAdc);
  }

  // The twin's NTC model spans -55..150 C, so the simulated hotend profile
  // is a 140 C setpoint with a 148 C hard limit (a real A1 runs hotter).
  if (hotC > 148 || bedC > 90) {
    fail("OVERTEMP");
    return;
  }

  const bool fanOn = state != State::FAULT &&
    (hotC > 50 || state == State::PRINTING);
  digitalWrite(FAN_PWM, fanOn ? HIGH : LOW);

  if (state == State::HEATING || state == State::PRINTING) {
    hotDuty = dutyFor(140, hotC);
    bedDuty = dutyFor(60, bedC);

    if (uint32_t(nowUs - heatWatchAt) >= 8000000UL) {
      if ((hotDuty > 80 && hotC < heatWatchHot + 2) ||
          (bedDuty > 80 && bedC < heatWatchBed + 2)) {
        fail("HEAT_NO_RISE");
        return;
      }
      heatWatchHot = hotC;
      heatWatchBed = bedC;
      heatWatchAt = nowUs;
    }
  } else {
    hotDuty = 0;
    bedDuty = 0;
  }
}

static void beginPulse(uint8_t mask, uint32_t nowUs) {
  for (uint8_t axis = 0; axis < 4; ++axis) {
    if (mask & (1U << axis)) {
      digitalWrite(STEP_PIN[axis], HIGH);
      ++stepRiseCount[axis];
    }
  }
  pulseMask = mask;
  pulseAt = nowUs;
}

static void endPulse(uint32_t nowUs) {
  if (pulseMask == 0 || uint32_t(nowUs - pulseAt) < 5UL) return;
  for (uint8_t axis = 0; axis < 4; ++axis) {
    if (pulseMask & (1U << axis)) digitalWrite(STEP_PIN[axis], LOW);
  }
  pulseMask = 0;
}

static bool endstopPressed(uint8_t axis) {
  return digitalRead(LIMIT_PIN[axis]) == LOW;
}

static void startHoming(uint32_t nowUs) {
  state = State::HOME;
  homeAxis = 0;
  homeCount = 0;
  stateAt = nowUs;
  stepAt = nowUs;
  digitalWrite(STEPPER_EN, LOW);
  for (uint8_t axis = 0; axis < 4; ++axis) digitalWrite(DIR_PIN[axis], LOW);
  serialEvent("HOME_START");
  showScreen("HOMING XYZ");
}

static void serviceHoming(uint32_t nowUs) {
  if (endstopPressed(homeAxis)) {
    axisSteps[homeAxis] = 0;
    serialEvent(homeAxis == 0 ? "HOME_X" : homeAxis == 1 ? "HOME_Y" : "HOME_Z");
    ++homeAxis;
    homeCount = 0;
    stateAt = nowUs;
    stepAt = nowUs;

    if (homeAxis == 3) {
      serialEvent("ALL_HOMED");
      state = State::HEATING;
      stateAt = nowUs;
      heatWatchAt = nowUs;
      heatWatchHot = hotC;
      heatWatchBed = bedC;
      showScreen("HEATING");
    }
    return;
  }

  const uint32_t timeoutUs = homeAxis == 2 ? 10000000UL : 2200000UL;
  if (uint32_t(nowUs - stateAt) > timeoutUs ||
      homeCount > uint32_t(185 * STEPS_PER_MM[homeAxis])) {
    fail("HOME_TIMEOUT");
    return;
  }

  if (pulseMask == 0 && uint32_t(nowUs - stepAt) >= 2000UL) {
    stepAt = nowUs;
    beginPulse(uint8_t(1U << homeAxis), nowUs);
    --axisSteps[homeAxis];
    ++homeCount;
  }
}

static void reportPosition(const char *prefix) {
  Serial.print(prefix);
  for (uint8_t axis = 0; axis < 4; ++axis) {
    Serial.print(" ");
    Serial.print(axisSteps[axis]);
  }
  Serial.println();
}

static void beginSegment(uint32_t nowUs) {
  majorSteps = 0;
  stepsTaken = 0;
  for (uint8_t axis = 0; axis < 4; ++axis) {
    const int32_t signedDelta = PATH[segment][axis] - axisSteps[axis];
    stepSign[axis] = signedDelta >= 0 ? 1 : -1;
    deltaSteps[axis] = signedDelta >= 0 ? signedDelta : -signedDelta;
    if (uint32_t(deltaSteps[axis]) > majorSteps) majorSteps = uint32_t(deltaSteps[axis]);
    ddaError[axis] = 0;
    digitalWrite(DIR_PIN[axis], stepSign[axis] > 0 ? HIGH : LOW);
  }
  stepIntervalUs = majorSteps ? 25000UL / majorSteps : 25000UL;
  if (stepIntervalUs < 20UL) stepIntervalUs = 20UL;
  stepAt = nowUs;
  Serial.print("SEGMENT ");
  Serial.println(segment);
}

static void finishPrint() {
  state = State::DONE;
  disableOutputs();
  serialEvent("PRINT_DONE");
  reportPosition("POSITION_STEPS");
  Serial.print("STEP_RISE_COUNTS");
  for (uint8_t axis = 0; axis < 4; ++axis) {
    Serial.print(" ");
    Serial.print(stepRiseCount[axis]);
  }
  Serial.println();
  Serial.println("OUTPUTS_SAFE EN=1 HOT=0 BED=0 FAN=0");
  showScreen("PATH COMPLETE");
}

static void servicePrint(uint32_t nowUs) {
  if (pulseMask != 0) return;

  if (stepsTaken >= majorSteps) {
    reportPosition("MOTION_POSITION");
    ++segment;
    if (segment >= sizeof(PATH) / sizeof(PATH[0])) {
      finishPrint();
    } else {
      beginSegment(nowUs);
    }
    return;
  }

  if (uint32_t(nowUs - stepAt) < stepIntervalUs) return;
  stepAt = nowUs;

  uint8_t mask = 0;
  for (uint8_t axis = 0; axis < 4; ++axis) {
    ddaError[axis] += deltaSteps[axis];
    if (ddaError[axis] >= int32_t(majorSteps)) {
      ddaError[axis] -= int32_t(majorSteps);
      axisSteps[axis] += stepSign[axis];
      mask |= uint8_t(1U << axis);
    }
  }
  if (mask) beginPulse(mask, nowUs);
  ++stepsTaken;
}

static void serviceStartButton(uint32_t nowUs) {
  const bool pressed = digitalRead(START_PIN) == LOW;
  if (pressed != rawStart) {
    rawStart = pressed;
    startChangedAt = nowUs;
  }
  if (pressed == stableStart || uint32_t(nowUs - startChangedAt) < 18000UL) return;

  stableStart = pressed;
  if (!stableStart) return;

  if (state == State::IDLE || state == State::DONE) {
    startHoming(nowUs);
  } else if (state == State::FAULT && digitalRead(STOP_PIN) == HIGH) {
    state = State::IDLE;
    digitalWrite(STATUS_LED, HIGH);
    showScreen("PRESS START");
    serialEvent("RESET_TO_IDLE");
  }
}

void setup() {
  Serial.begin(115200);

  for (uint8_t axis = 0; axis < 4; ++axis) {
    pinMode(STEP_PIN[axis], OUTPUT);
    pinMode(DIR_PIN[axis], OUTPUT);
    digitalWrite(STEP_PIN[axis], LOW);
    digitalWrite(DIR_PIN[axis], LOW);
  }
  pinMode(STEPPER_EN, OUTPUT);
  pinMode(HOTEND_PWM, OUTPUT);
  pinMode(BED_PWM, OUTPUT);
  pinMode(FAN_PWM, OUTPUT);
  pinMode(HOT_ADC, INPUT_ANALOG);
  pinMode(STATUS_LED, OUTPUT);
  pinMode(X_MIN, INPUT_PULLUP);
  pinMode(Y_MIN, INPUT_PULLUP);
  pinMode(Z_MIN, INPUT_PULLUP);
  pinMode(START_PIN, INPUT_PULLUP);
  pinMode(STOP_PIN, INPUT_PULLUP);
  pinMode(BED_ADC, INPUT_ANALOG);

  digitalWrite(STATUS_LED, HIGH);
  disableOutputs();

  analogReadResolution(12);

  Wire.setSCL(PB6);
  Wire.setSDA(PB7);
  Wire.begin();
  Wire.setClock(400000UL);

  initDisplay();
  Serial.println("A1_REFERENCE_BOOT");
  serialEvent("READY");
  thermalAt = micros();
  startChangedAt = thermalAt;
}

void loop() {
  const uint32_t nowUs = micros();

  endPulse(nowUs);

  if (digitalRead(STOP_PIN) == LOW && state != State::FAULT) {
    fail("EMERGENCY_STOP");
  }

  serviceStartButton(nowUs);
  serviceThermal(nowUs);
  writePowerOutputs(nowUs);

  if (state == State::HOME) {
    serviceHoming(nowUs);
  } else if (state == State::HEATING) {
    if (hotC >= 138 && hotC <= 142 && bedC >= 58 && bedC <= 62) {
      state = State::PRINTING;
      segment = 0;
      serialEvent("MOTION_START");
      showScreen("PRINTING");
      beginSegment(nowUs);
    } else if (uint32_t(nowUs - stateAt) > 20000000UL) {
      fail("HEAT_TIMEOUT");
    }
  } else if (state == State::PRINTING) {
    servicePrint(nowUs);
  }
}
