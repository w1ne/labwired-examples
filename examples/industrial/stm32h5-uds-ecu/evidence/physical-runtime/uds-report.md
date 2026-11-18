# UDS evidence report: test

**Verdict: PASS** · 3/3 run assertions passed · 16/16 UDS steps passed

## Firmware and setup

| Item | Value |
|---|---|
| Firmware | `runtime/../firmware/h563-uds-physical.elf` |
| Firmware sha256 | `d78d30a8ae57835c237e21c99104b56e1fcf50fcd8872440c986132eba67275f` |
| System | `runtime/./system.yaml` |
| Chip | stm32h563 |
| Core clock | 250000000 Hz |
| Tester `uds-tester` | on `fdcan1`, request 0x7E0, reply 0x7E8, FlowControl `30 00 00` |

## Tool versions

| Tool | Version |
|---|---|
| labwired-cli / labwired-core | 0.26.0 |
| firmware compiler (ELF .comment) | GCC: (15:13.2.rel1-2) 13.2.1 20231009 |

## Assertions (executed)

| # | Assertion | Result |
|---|---|---|
| 1 | `uart_contains: H563-UDS-ECU PHYSICAL HAL 500K/2M FD` | PASS |
| 2 | `uart_ordered: ["ECU_READY", "H563-UDS-ECU PHYSICAL HAL", "ECU_READY"]` | PASS |
| 3 | `uds_tester: uds-tester result=Done` | PASS |

## UDS exchanges: tester `uds-tester` (done, 16/16 steps)

| Step | Request at (ms) | Service | Request | Expected | Response | ISO-TP frames | Latency (µs) | Result |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.021 | ReadDataByIdentifier | `22 F1 90` | `62 F1 90` | `62 F1 90 4C 41 42 57 49 52 45 44 2D … (20 B)` | 1 | 15.2 | PASS |
| 1 | 0.036 | ReadDataByIdentifier | `22 F1 A0` | `62 F1 A0 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F 40 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E 4F 50 51 52 53 54 55 56 57 58 59 5A 5B 5C 5D 5E 5F 60 61 62 63 64 65 66 67 68 69 6A 6B 6C 6D 6E 6F 70 71 72 73 74 75 76 77 78 79 7A 7B 7C 7D 7E 7F 80 81 82 83 84 85 86 87 88 89 8A 8B 8C 8D 8E 8F 90 91 92 93 94 95 96 97 98 99 9A 9B 9C 9D 9E 9F A0 A1 A2 A3 A4 A5 A6 A7 A8 A9 AA AB AC AD AE AF B0 B1 B2 B3 B4 B5 B6 B7 B8 B9 BA BB BC BD BE BF C0 C1 C2 C3 C4 C5 C6 C7 C8 C9 CA CB CC CD CE CF D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 DA DB DC DD DE DF E0 E1 E2 E3 E4 E5 E6 E7 E8 E9 EA EB EC ED EE EF F0 F1 F2 F3 F4 F5 F6 F7 F8 F9 FA FB FC FD FE FF 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F 40 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E 4F 50 51 52 53 54 55 56 57 58 59 5A 5B 5C 5D 5E 5F 60 61 62 63 64 65 66 67 68 69 6A 6B 6C 6D 6E 6F 70 71 72 73 74 75 76 77 78 79 7A 7B 7C 7D 7E 7F 80 81 82 83 84 85 86 87 88 89 8A 8B 8C 8D 8E 8F 90 91 92 93 94 95 96 97 98 99 9A 9B 9C 9D 9E 9F A0 A1 A2 A3 A4 A5 A6 A7 A8 A9 AA AB AC AD AE AF B0 B1 B2 B3 B4 B5 B6 B7 B8 B9 BA BB BC BD BE BF C0 C1 C2 C3 C4 C5 C6 C7 C8 C9 CA CB CC CD CE CF D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 DA DB DC DD DE DF E0 E1 E2 E3 E4 E5 E6 E7 E8 E9 EA EB EC ED EE EF F0 F1 F2 F3 F4 F5 F6 F7 F8 F9 FA FB FC FD FE FF 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F 40 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E 4F 50 51 52 53 54 55 56 57` | `62 F1 A0 00 01 02 03 04 05 06 07 08 … (603 B)` | 10 | 51.2 | PASS |
| 2 | 0.087 | WriteDataByIdentifier | `2E 01 23 DE AD BE EF` | `NRC 7F 2E 31` | `7F 2E 31` | 1 | 4.4 | PASS |
| 3 | 0.092 | DiagnosticSessionControl | `10 03` | `50 03` | `50 03 00 32 00 C8` | 1 | 3.8 | PASS |
| 4 | 0.095 | TesterPresent | `3E 00` | `7E 00` | `7E 00` | 1 | 4.1 | PASS |
| 5 | 0.099 | WriteDataByIdentifier | `2E 01 23 DE AD BE EF` | `6E 01 23` | `6E 01 23` | 1 | 4.5 | PASS |
| 6 | 0.104 | ReadDataByIdentifier | `22 01 23` | `62 01 23 DE AD BE EF` | `62 01 23 DE AD BE EF` | 1 | 4.3 | PASS |
| 7 | 0.108 | ReadDTCInformation | `19 01 09` | `59 01` | `59 01 00 00 00 01` | 1 | 4.1 | PASS |
| 8 | 0.112 | ClearDiagnosticInformation | `14 FF FF FF` | `54` | `54` | 1 | 3.8 | PASS |
| 9 | 0.116 | RoutineControl | `31 01 02 03` | `71 01 02 03` | `71 01 02 03 00` | 1 | 4.3 | PASS |
| 10 | 0.121 | InputOutputControlByIdentifier | `2F A0 01 03 01` | `6F A0 01` | `6F A0 01 01` | 1 | 4.8 | PASS |
| 11 | 0.125 | CommunicationControl | `28 00 01` | `68 00` | `68 00` | 1 | 4.1 | PASS |
| 12 | 0.129 | ECUReset | `11 01` | `51 01` | `51 01` | 1 | 3.7 | PASS |
| 13 | 1.133 | ReadDataByIdentifier | `22 F1 90` | `62 F1 90` | `62 F1 90 4C 41 42 57 49 52 45 44 2D … (20 B)` | 1 | 5.0 | PASS |
| 14 | 1.138 | WriteDataByIdentifier | `2E 01 23 DE AD BE EF` | `NRC 7F 2E 31` | `7F 2E 31` | 1 | 4.4 | PASS |
| 15 | 1.142 | DiagnosticSessionControl | `10 03` | `50 03` | `50 03 00 32 00 C8` | 1 | 3.8 | PASS |

## CAN frame timeline (ISO-TP and UDS decoded)

| # | t (ms) | Cycle | Direction | CAN ID | Type | ISO-TP | UDS | Data |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.021 | 5172 | tester->ecu | 0x7E0 | classic | SF len=3 | ReadDataByIdentifier | `03 22 F1 90` |
| - | 0.021 | 5344 | firmware uart3 | | | | console | `H563-UDS-ECU PHYSICAL HAL 500K/2M FD` |
| - | 0.030 | 7421 | firmware uart3 | | | | console | `ECU_READY` |
| 2 | 0.036 | 8982 | ecu->tester | 0x7E8 | FD+BRS | SF(FD) len=20 | ReadDataByIdentifier positive response | `00 14 62 F1 90 4C 41 42 57 49 52 45 44 2D 48 35 … (24 B)` |
| 3 | 0.036 | 8983 | tester->ecu | 0x7E0 | classic | SF len=3 | ReadDataByIdentifier | `03 22 F1 A0` |
| 4 | 0.053 | 13151 | ecu->tester | 0x7E8 | FD+BRS | FF len=603 | ReadDataByIdentifier positive response | `12 5B 62 F1 A0 00 01 02 03 04 05 06 07 08 09 0A … (64 B)` |
| 5 | 0.053 | 13152 | tester->ecu | 0x7E0 | classic | FC CTS BS=0 STmin=0 |  | `30 00 00` |
| 6 | 0.057 | 14279 | ecu->tester | 0x7E8 | FD+BRS | CF SN=1 |  | `21 3B 3C 3D 3E 3F 40 41 42 43 44 45 46 47 48 49 … (64 B)` |
| 7 | 0.061 | 15228 | ecu->tester | 0x7E8 | FD+BRS | CF SN=2 |  | `22 7A 7B 7C 7D 7E 7F 80 81 82 83 84 85 86 87 88 … (64 B)` |
| 8 | 0.065 | 16172 | ecu->tester | 0x7E8 | FD+BRS | CF SN=3 |  | `23 B9 BA BB BC BD BE BF C0 C1 C2 C3 C4 C5 C6 C7 … (64 B)` |
| 9 | 0.068 | 17121 | ecu->tester | 0x7E8 | FD+BRS | CF SN=4 |  | `24 F8 F9 FA FB FC FD FE FF 00 01 02 03 04 05 06 … (64 B)` |
| 10 | 0.072 | 18070 | ecu->tester | 0x7E8 | FD+BRS | CF SN=5 |  | `25 37 38 39 3A 3B 3C 3D 3E 3F 40 41 42 43 44 45 … (64 B)` |
| 11 | 0.076 | 19019 | ecu->tester | 0x7E8 | FD+BRS | CF SN=6 |  | `26 76 77 78 79 7A 7B 7C 7D 7E 7F 80 81 82 83 84 … (64 B)` |
| 12 | 0.080 | 19963 | ecu->tester | 0x7E8 | FD+BRS | CF SN=7 |  | `27 B5 B6 B7 B8 B9 BA BB BC BD BE BF C0 C1 C2 C3 … (64 B)` |
| 13 | 0.084 | 20912 | ecu->tester | 0x7E8 | FD+BRS | CF SN=8 |  | `28 F4 F5 F6 F7 F8 F9 FA FB FC FD FE FF 00 01 02 … (64 B)` |
| 14 | 0.087 | 21775 | ecu->tester | 0x7E8 | FD+BRS | CF SN=9 |  | `29 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F 40 41 … (48 B)` |
| 15 | 0.087 | 21776 | tester->ecu | 0x7E0 | classic | SF len=7 | WriteDataByIdentifier | `07 2E 01 23 DE AD BE EF` |
| 16 | 0.092 | 22884 | ecu->tester | 0x7E8 | classic | SF len=3 | NegativeResponse WriteDataByIdentifier NRC 0x31 requestOutOfRange | `03 7F 2E 31 CC CC CC CC` |
| 17 | 0.092 | 22885 | tester->ecu | 0x7E0 | classic | SF len=2 | DiagnosticSessionControl | `02 10 03` |
| 18 | 0.095 | 23830 | ecu->tester | 0x7E8 | classic | SF len=6 | DiagnosticSessionControl positive response | `06 50 03 00 32 00 C8 CC` |
| 19 | 0.095 | 23831 | tester->ecu | 0x7E0 | classic | SF len=2 | TesterPresent | `02 3E 00` |
| 20 | 0.099 | 24865 | ecu->tester | 0x7E8 | classic | SF len=2 | TesterPresent positive response | `02 7E 00 CC CC CC CC CC` |
| 21 | 0.099 | 24866 | tester->ecu | 0x7E0 | classic | SF len=7 | WriteDataByIdentifier | `07 2E 01 23 DE AD BE EF` |
| 22 | 0.104 | 25999 | ecu->tester | 0x7E8 | classic | SF len=3 | WriteDataByIdentifier positive response | `03 6E 01 23 CC CC CC CC` |
| 23 | 0.104 | 26000 | tester->ecu | 0x7E0 | classic | SF len=3 | ReadDataByIdentifier | `03 22 01 23` |
| 24 | 0.108 | 27062 | ecu->tester | 0x7E8 | classic | SF len=7 | ReadDataByIdentifier positive response | `07 62 01 23 DE AD BE EF` |
| 25 | 0.108 | 27063 | tester->ecu | 0x7E0 | classic | SF len=3 | ReadDTCInformation | `03 19 01 09` |
| 26 | 0.112 | 28099 | ecu->tester | 0x7E8 | classic | SF len=6 | ReadDTCInformation positive response | `06 59 01 00 00 00 01 CC` |
| 27 | 0.112 | 28100 | tester->ecu | 0x7E0 | classic | SF len=4 | ClearDiagnosticInformation | `04 14 FF FF FF` |
| 28 | 0.116 | 29059 | ecu->tester | 0x7E8 | classic | SF len=1 | ClearDiagnosticInformation positive response | `01 54 CC CC CC CC CC CC` |
| 29 | 0.116 | 29060 | tester->ecu | 0x7E0 | classic | SF len=4 | RoutineControl | `04 31 01 02 03` |
| 30 | 0.121 | 30134 | ecu->tester | 0x7E8 | classic | SF len=5 | RoutineControl positive response | `05 71 01 02 03 00 CC CC` |
| 31 | 0.121 | 30135 | tester->ecu | 0x7E0 | classic | SF len=5 | InputOutputControlByIdentifier | `05 2F A0 01 03 01` |
| 32 | 0.125 | 31322 | ecu->tester | 0x7E8 | classic | SF len=4 | InputOutputControlByIdentifier positive response | `04 6F A0 01 01 CC CC CC` |
| 33 | 0.125 | 31323 | tester->ecu | 0x7E0 | classic | SF len=3 | CommunicationControl | `03 28 00 01` |
| 34 | 0.129 | 32340 | ecu->tester | 0x7E8 | classic | SF len=2 | CommunicationControl positive response | `02 68 00 CC CC CC CC CC` |
| 35 | 0.129 | 32341 | tester->ecu | 0x7E0 | classic | SF len=2 | ECUReset | `02 11 01` |
| 36 | 0.133 | 33264 | ecu->tester | 0x7E8 | classic | SF len=2 | ECUReset positive response | `02 51 01 CC CC CC CC CC` |
| - | 0.155 | 38815 | firmware uart3 | | | | console | `H563-UDS-ECU PHYSICAL HAL 500K/2M FD` |
| - | 0.164 | 40892 | firmware uart3 | | | | console | `ECU_READY` |
| 37 | 1.133 | 283265 | tester->ecu | 0x7E0 | classic | SF len=3 | ReadDataByIdentifier | `03 22 F1 90` |
| 38 | 1.138 | 284505 | ecu->tester | 0x7E8 | FD+BRS | SF(FD) len=20 | ReadDataByIdentifier positive response | `00 14 62 F1 90 4C 41 42 57 49 52 45 44 2D 48 35 … (24 B)` |
| 39 | 1.138 | 284506 | tester->ecu | 0x7E0 | classic | SF len=7 | WriteDataByIdentifier | `07 2E 01 23 DE AD BE EF` |
| 40 | 1.142 | 285607 | ecu->tester | 0x7E8 | classic | SF len=3 | NegativeResponse WriteDataByIdentifier NRC 0x31 requestOutOfRange | `03 7F 2E 31 CC CC CC CC` |
| 41 | 1.142 | 285608 | tester->ecu | 0x7E0 | classic | SF len=2 | DiagnosticSessionControl | `02 10 03` |
| 42 | 1.146 | 286553 | ecu->tester | 0x7E8 | classic | SF len=6 | DiagnosticSessionControl positive response | `06 50 03 00 32 00 C8 CC` |

## What is modelled and what is not

- Times are simulated CPU time (engine cycle / core clock) at which a frame entered or left the CAN controller model. CAN bit timing, arbitration, ACK, error frames and bus load are not simulated: a frame takes zero wire time, so the latencies below measure firmware processing time, not bus time.
- The tester is a host-side scripted CAN node serviced once per engine tick, not a second MCU. It sends classic CAN frames (8 bytes max); it checks ISO-TP framing, ConsecutiveFrame sequence numbers and the UDS response bytes. It enforces a per-step tick budget, not the ISO 14229-2 P2/P2* or ISO 15765-2 N_Bs/N_Cr timers in real time.
- The ECU firmware, its UDS stack and its ISO-TP layer run unmodified as machine code on the simulated core. ECUReset is the firmware's own reset request (SCB AIRCR.SYSRESETREQ); the simulated core reboots through its vector table and the tester re-connects over the same bus.
- A system reset restarts the core only: peripheral registers (including the CAN controller and its RX FIFO) and RAM keep their state until the rebooted firmware re-initializes them. On silicon, SYSRESETREQ also resets the peripherals, so a frame queued at the moment of reset is lost. The scenario therefore waits before its first post-reset request, as a real tester does.
- Not covered by this scenario: the physical layer and transceiver, bus-off and error confinement, other bus participants, and security access.
- STM32H5 FDCAN: acceptance filters are not modelled (frames follow RXGFC.ANFS into RX FIFO0), RX FIFO1 routing and dedicated RX buffers are not modelled, FDCAN2 and interrupt line 1 are not modelled. DBTP/NBTP are stored with their silicon reset values but do not change timing.

## Reproduce

```sh
labwired test --script runtime/test.yaml --output-dir <dir>
# this run wrote /data/work-evidence/labwired-industrial-packages-20261118/physical-core-probes/uds-portable
```
