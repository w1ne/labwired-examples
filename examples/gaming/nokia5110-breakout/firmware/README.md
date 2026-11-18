# Nokia Breakout firmware

This is the physical STM32L476 firmware used by the existing Nokia Breakout Lab. It targets an intact NUCLEO-L476RG, a Joy-IT SBC-LCD84x48 REVISION 2 display, and an Adafruit 3942 HC-SR04 through this package's carrier.

## Build and program

Run `./build.sh` from this directory. The pinned Rust toolchain is 1.95.0, the target is thumbv7em-none-eabihf, and Cargo.lock pins the dependencies. The build also needs arm-none-eabi-objcopy on PATH. The script produces build/nokia-breakout.elf and build/nokia-breakout.bin. Released copies are under artifacts/. The release manifest records their hashes and the exact source hashes.

Use the Nucleo's integrated ST-LINK over its Mini-B connector to program the ELF. If the programmer requires a raw binary, load nokia-breakout.bin at **0x08000000**, as defined in memory.x. Verify the programmed bytes and reset the target. The ST-LINK section remains attached; this enclosure is not for a snapped-off Nucleo board.

## Hardware and timing contract

The MCU runs from its reset MSI clock at **4 MHz**. TIM2 counts at **1 MHz** (PSC = 3). TRIG is held low for 2 microseconds and high for 12 microseconds. Both the wait for ECHO and the pulse-width measurement have 30 millisecond timeouts. Ranging transactions start at least 70 milliseconds apart. SPI1 uses mode 0 at 1 MHz.

The accepted sensor pulse range is 80 to 25,000 microseconds. The gameplay range is 10 to 50 cm: a near hand moves the paddle right; a far hand moves it left; 30 cm is the center. Valid distances outside that gameplay range clamp to the corresponding end. A median-of-three filter and a one-quarter exponential update reduce movement noise. Missing or stuck-high ECHO centers the paddle, resets the distance filter, and leaves the game running.

The physical HC-SR04 uses **5 V**. Its ECHO passes through R1 = 10 kilohms and R2 = 18 kilohms before PB10. The LCD uses **3.3 V**. The full pad-level map is in ../README.md and ../hardware-interface.json.

## Simulator configuration

system.yaml uses the existing built-in **stm32l476** descriptor. It carries the physical 4 MHz CPU and sensor calibration rate, and an explicit maximum peripheral tick interval of **32 cycles**. At 4 MHz, that interval is 8 microseconds. A nominal 2 cm pulse is about 116 microseconds; a 1024-cycle interval would span 256 microseconds and could erase the pulse. The generic manifest cap limits such a caller request to 32 cycles.

An 8 microsecond pulse-width grid corresponds to about **0.138 cm** at the model's nominal 58 microseconds per centimetre. This is a simulation time-quantization figure, not a sensor-accuracy specification.

Run the packaged clean-run baseline with a LabWired CLI containing the timing change:

```sh
labwired test --script io-smoke.yaml --no-key --output-dir build/smoke
```

That baseline proves a clean 5-million-step run only. The seven stronger existing core oracles are recorded in ../validation/firmware-behavior.json and firmware-behavior.log. They cover the rendered splash, minimum-distance ECHO, near/far paddle motion, the requested 1024-cycle interval, missing and stuck-high ECHO, and walk-mode parity. No assertion was weakened for this package.

The simulator ELF and the physical programming ELF are the same artifact. These receipts are simulated behavior; a fabricated, powered device has not yet been qualified.
