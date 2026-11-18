# Immediate-compare gate candidate

These four sources compiled through the authenticated LabWired compiler. `compile-identities.json` records the source and downloaded ELF hashes. Each source is 6,371 bytes and each ELF is 83,636 bytes. Compilation is not runtime acceptance.

The firmware retains the 4 MHz simulation clock, 20 kHz PWM and 10 kHz control tick. It clears compare preload, uses immediate updates, and holds the selected N-only low side on for its commutation sector with CCR equal to ARR + 1. Inactive phases have both outputs disabled. There is no complementary dead-time-insertion claim for this configuration.

The canonical circuit saves motor current, speed, PA8 PWM and PC0 Hall A on the universal oscilloscope. The four-lane universal logic analyzer saves PA8, PB13, PB7 fault and PB0 enable. Phase pairs can be selected in separate capture windows.

Native motor integration, native complementary-pad observation, unchanged firmware execution during both instrument source changes, isolated fault coast-down, hosted verification and public deployment still require final acceptance. No public readiness or final video is established by these compile receipts.

## Later runtime acceptance

The exact images in this compile receipt subsequently passed the [R4-02 native and UI acceptance](../20261112-universal-instruments/). Earlier pending statements describe the compile-only candidate stage. Hosted project verification and public deployment remain pending; the compiler receipt is unchanged.
