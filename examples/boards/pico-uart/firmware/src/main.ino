#include <Arduino.h>

// Raspberry Pi Pico / Pico H (RP2040), not Pico W or Pico 2.
// UART0 is the physical console on GP0 (TX) / GP1 (RX), 115200 8N1.
// Power through the Pico micro-USB socket. A USB-TTL adapter is 3.3 V logic;
// leave its red 5 V power wire disconnected.
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial1.begin(115200);
  Serial1.print("RP2040_SMOKE_OK\n");
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial1.print("PICO_LED=1\n");
  delay(100);
  digitalWrite(LED_BUILTIN, LOW);
  Serial1.print("PICO_LED=0\n");
  delay(100);
}
