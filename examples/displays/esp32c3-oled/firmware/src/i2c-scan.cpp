// Bring-up only. Reflash the clock environment after confirming address0x3C.
#include <Arduino.h>
#include <Wire.h>

void setup() {
  Serial.begin(115200);
  Wire.begin(4, 5); // XIAO D2=SDA and D3=SCL, matching the carrier.
}

void loop() {
  unsigned found = 0;
  for (uint8_t address = 1; address < 127; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.printf("I2C_ACK 0x%02X\n", address);
      ++found;
    }
  }
  Serial.printf("I2C_SCAN_DONE devices=%u\n", found);
  delay(2000);
}
