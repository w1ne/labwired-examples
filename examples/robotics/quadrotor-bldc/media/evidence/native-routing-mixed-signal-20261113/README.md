# Native routing and hosted mixed-signal evidence — 13 November 2026

The quadcopter review film is ../../labwired-quadcopter-routing-mixed-signal-32s.mp4.

## Native six-layer PCB

The source is the checked-in hardware/esc-4in1/4in1.kicad_pcb, a derivative of OpenDrone OpenESC-30x30 under CERN-OHL-S-2.0.

A disposable copy had 29 copper segments removed across 12 ESC nets. The included create_route_input.py generated this interrupted KiCad 10 board and DSN. The included restore_native_routes.py actually edited KiCad PCB_TRACK objects in four successive revisions, using source-approved geometry. The original board was untouched.

KiCad 10.0.8 independently checked every saved revision using the source design rules. Open connections: 12, 9, 6, 3, 0. Other DRC violations: 0 at every stage, within configured checks. Raw DRC reports, SHA-256 identifiers, code and manifests are preserved in this directory.

No autorouter succeeded. Separate Freerouting 2.5.0 attempts reported about 17,014 conflicting fixed-geometry cases, performed unnecessary fanout and did not finish within 180 seconds. Its numbers are not native KiCad DRC findings. The video depicts real KiCad scripted copper restoration, NOT an independently computed novel route.

## Single hosted fault-injection simulation

The source is one real LabWired hosted run of the exact firmware/channels/ctrl1.c STM32L476 six-step firmware and an executable reduced-order 24 V BLDC plant. It is not the physical AT32F421/AM32 four-in-one ESC, and no real transistor-level or flight physics are validated.

Run ID: f069cc33-a945-4f96-84a9-a85ab3315e2d
Snapshot ID: c037dba7fc14da6d2b1748438037e24c

Actual observed GPIO transitions: PWM-A median period 4,000 cycles (20,000 Hz on the 80 MHz model clock) and high duration 2,400 cycles (60%). Fault PB7 asserted at cycle 2,500,001. Inverter enable PB0 went low at cycle 2,656,181. Delay: 156,180 cycles, or 1.95225 ms. Serial output reported HALL LOCKED, FAULT DRIVER and INVERTER OFF.

PWM PA8/PA9/PA10, Hall PC0/PC1/PC2, fault PB7, enable PB0, model current and RPM came from the SAME simulation snapshot. Input waveform JSON and metrics receipt are retained. The motor-current measurements are from the simulation model, NOT physical test equipment. An ideal 3.3-V MCU rail is assumed; power-on and brown-out are not covered.

The 14-second video is a diagnostic visualization of these actual simulator results. No synthetic analog current curve was generated. It does not verify power electronics, PCB functional equivalence, current density, thermal limits, EMI, flight or manufacturing.

## Reproduction

From the parent media directory, run:
    python3 render-native-quad-review-32s.py

The assembler uses four committed MP4 sources and asserts duration and dimensions. To reproduce PCB edits, run the saved source scripts in KiCad 10.0.8 with the board source mounted read-only at /source and scratch mounted writable at /work, then run KiCad 10 DRC on each exported revision with the source .kicad_pro and .kicad_dru.

The video ends with prior recorded motor-twin motion from a SEPARATE browser run, not a synchronized flight recording. The PCB turntable is a saved populated digital geometry model, not an assembled manufactured board.
