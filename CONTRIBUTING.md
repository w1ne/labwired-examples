# Contributing examples

Each example must have:

1. A concrete existing device or engineering task and the behavior it tests.
2. Firmware source and target MCU. Never call a host-side mock real firmware.
3. Circuit JSON with genuine LabWired catalog IDs.
4. At least one observable acceptance oracle and a driven input stimulus when needed.
5. Actual observed results with limitations and proof class.
6. When mechanical, editable KernelCAD CAD, a saved Studio revision and independent mate validation.
7. Media captured from the real environment. No invented flight, thermal, power-stage, hardware-in-loop, or manufacturer compliance claims.

Examples stay here. Engine/model/SimInput improvements and regressions belong in w1ne/labwired-core with native tests. Use bounded CI workloads.
