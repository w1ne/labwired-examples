# Five-controller native flight acceptance — 22 November 2026

**The native candidate passes takeoff, hover, roll, pitch, yaw, attitude recovery and all five fault cases.** Five independently compiled STM32L476 ELFs execute in the existing native `WasmWorld`. The production flight runtime converts actual motor RPM into body forces and writes the resulting BMI270 observations back into the FC's native I²C sensor. The FC commands four real ESC firmware instances through GPIO PWM links.

This bundle preserves the exact WASM, five ELFs, C sources, body/motor traces and an independent reader. App integration is [PR #3967](https://github.com/w1ne/labwired/pull/3967); native drag and L476 EXTI routing landed through [core PR #2155](https://github.com/w1ne/labwired-core/pull/2155). Saved-project promotion and hosted/browser flight proof remain separate gates. Physical-aircraft validation remains open.

## Observed nominal result

The oracle reads quaternion-derived body angles and altitude from captured observations. It does not accept firmware success markers as flight proof. All 11 nominal checks pass.

| Measurement | Required bound | 5,000 World rounds/poll | 1,000 rounds/poll |
| --- | --- | --- | --- |
| Native duration | Complete 15 s | 15.000 s | 15.000 s |
| Hover, within 5–8 s | Altitude 0.85–1.15 m, roll/pitch ≤5.007°, continuous ≥1.00 s | 2.68 s, 5.31–7.99 s | 2.69 s, 5.30–7.99 s |
| Positive roll, 8–9.2 s | >3.499° | 7.376° | 7.337° |
| Positive pitch, 9.2–10.4 s | >3.149° | 6.818° | 6.771° |
| Positive yaw, 10.4–12 s | >8° | 24.447° | 24.466° |
| Recovery, after 13 s | Altitude 0.85–1.15 m, roll/pitch ≤3.149°, yaw ≤5°, continuous ≥0.50 s | 1.87 s | 1.88 s |
| Maximum observed altitude | Reported, no substituted target | 1.101109 m | 1.085838 m |
| Final observed altitude | Reported | 1.035756 m | 1.040973 m |

The smaller-poll run keeps every source, ELF, WASM byte and oracle limit fixed. Its peak altitude differs by 15.27 mm and its final altitude by 5.22 mm. Both runs pass. See the [nominal oracle](oracles/nominal-damping-oracle.json), [convergence oracle](oracles/nominal-convergence-oracle.json) and [machine-readable acceptance](acceptance.json).

## Fault acceptance

Each case starts a separate World, takes off, then injects the named channel on rotor 1 at native time 6.000 s. A clear is attempted at 6.100 s. Every case passes 14 checks, including airborne motion before injection, the specific firmware fault path, all-rotor shutdown, every post-attempt output observation, and sustained ground contact.

| Injected input | First observed all-inverter-off | First observed all speeds <1 RPM | Clear result | Post-attempt output samples |
| --- | --- | --- | --- | --- |
| External `fault1` button | ≤50 ms | ≤160 ms | Input cleared; firmware stays latched | 391/391 off |
| Native `inverter_fault` | ≤50 ms | ≤160 ms | Input cleared; firmware stays latched | 391/391 proven off |
| Native `overcurrent_fault` | ≤50 ms | ≤160 ms | Clear rejected by native sticky latch | 391/391 off |
| Native `undervoltage_fault` | ≤50 ms | ≤160 ms | Input cleared; firmware stays latched | 391/391 off |
| Native `stall` | ≤90 ms | ≤200 ms | Input cleared; firmware stays latched | 391/391 off |

These are upper bounds from 10 ms trace samples. The response is latched shutdown followed by rotor decay and model ground contact. It does not establish controlled landing or impact survivability. Native overcurrent was **not cleared**: the existing input contract accepts assertion only, and the rejected zero write is retained in the result.

The candidate adds the missing native fault-output wires on each ESC: `INVERTER_FAULT` → PC6, `OVERCURRENT_FAULT` → PB6, and `UNDERVOLTAGE_FAULT` → PC7. The original external button remains on PB7. The corresponding native fault appears in the motor snapshot and the actual ELF reports its named fault before the FC disarms all motors.

### Inverter clear-boundary observation

The native snapshot retains the label `fault:inverter` until its next motor service after a clear. A label-only reader cannot prove that boundary observation is off. The original label-only audit remains a recorded **FAIL**.

A second run adds read-only GPIO and timer register observations. Before injection, at 5.990 s, every channel reports PB0=1, TIM1 BDTR=0x8030 and CCER=0x14. At the clear attempt, rotor 1 reports PB0=0, BDTR=0x30 and CCER=0: external enable, MOE and all six phase-enable bits are disabled. The reader accepts that ambiguous label only when all three native disable conditions are observed.

All 1,003 body/motor/event records are identical between the two runs after removing only wall time and the added registers. See [register positive control](inverter-gate-positive-control.json), [observer equivalence](inverter-gate-observer-equivalence.json), and [the accepted inverter oracle](oracles/fault-inverter-gates-oracle.json).

## Source and model identity

| Item | Identity |
| --- | --- |
| App source | `3157a536da36051d5b1eec9a7c5dff6a720833b6` |
| Minimal core source | `7c0825e7bbcae493b710c5ffeb0d848b4ddd4fa0` |
| Core source tree | `586fec760c60a604cdccb7703ba2db4f81e6205e` |
| Native WASM SHA-256 | `4c45fb97b6af9e0a93407a7cc20b9e5d95eb769e653938ab8b284ecf6a5925d7` |
| Candidate diagram SHA-256 | `4198c3afa92c801f179dcfa96a43990c69ce328390d8317f0ebacbe5af100cc6` |
| Original saved-project content hash | `1c89a2f856b3759d7c51e4a9b5080ba60acd63a2c53890e147a4cd23f1524ecc` |

The diagram hash is canonical sorted UTF-8 JSON; it is not a server-issued saved revision. The candidate has no claimed saved verification hash. [Compiler receipts](compiles.json), [source hashes](candidate-source-receipt.json), [build provenance](candidate-runtime-build.json), [vector-table verification](vector-receipt.json) and [final app/plan equivalence](final-app-plan-equivalence.json) bind the run to its inputs. `artifacts.json` hashes every archived file, including compressed and uncompressed byte identities.

The existing body uses 0.55 kg mass, declared inertia and aerodynamic coefficients. Its yaw coefficient of `1e-8 N m/RPM²` gives a per-motor quadratic shaft coefficient of `9.118906527810402e-7 N m/(rad/s)²` through `k_rad = k_RPM × (60/(2π))²`. The native shaft integrator evaluates the resisting torque continuously. The body requires acknowledgement from all four native motors before accepting their samples; a missing or changed coefficient invalidates the run.

The firmware configures and uses the declared 80 MHz clock. Real SysTick interrupts and WFI preserve 10 kHz command/fault sampling, a 1 kHz speed controller, 100 Hz FC/IMU control and 20 kHz PWM. Hall commutation uses both EXTI edge polarities and wrap-safe TIM2 timestamps. The native L476 SYSCFG model implements the EXTICR mux only; other SYSCFG configuration fields remain explicitly unmodeled.

The five sources are in [firmware/flight-native](../../../firmware/flight-native/). They remain separate from the published four-channel bench sources.

## Retained failed candidates

| Candidate | Hover | Recovery | Cause and correction |
| --- | --- | --- | --- |
| Coupled governor | 0.30 s | 0.00 s | Integer inertial accumulation discarded sub-unit velocity/altitude increments. |
| Inertial precision | 0.60 s | 0.32 s | The position estimate improved; polled Hall timing and weak damping remained. |
| Hall IRQ with native mux | 0.92 s | 1.90 s | Actual IRQs worked; the separately truncated altitude PD terms left too little vertical damping. |
| Final rounded PD | 2.68 s | 1.87 s | Position gain stays one output tick per 120 mm. Velocity damping becomes one tick per 200 mm/s, with one sign-correct rounding after summation and the same ±10 saturation. |

The failed EXTI smoke with a stubbed SYSCFG model also remains archived: all four vector tables were correct but Hall IRQ counters stayed zero. The native mux fix produced 1,166 real ISR edges per ESC by firmware time 2.520 s. No aircraft constants, clock rates, maneuver schedules or pass thresholds were changed to turn those failures into passes.

## Recompute the evidence without simulation

From this directory:

```sh
python3 audit.py
```

The reader verifies archived file and source hashes, decompresses the recorded traces into a temporary directory, and independently recomputes all seven final and four negative outcomes. Expected output includes `passingScenarios: 7`, `preservedNegativeScenarios: 4` and `inverterObserverEquivalent: true`. It does not compile or execute firmware.

The repository CI test is `python3 -m unittest scripts.test_quadrotor_native_flight -v`.

## Replay the actual native runtime

Use a LabWired app checkout at the exact app commit above, with its pinned core, normal Node dependencies, and a built `packages/board-config` workspace. The WASM and all five ELFs are archived here; they are read directly, with no synthetic RPM samples or alternate plant.

```sh
export LABWIRED_APP=/absolute/path/to/labwired
export LABWIRED_EVIDENCE_OUT=/absolute/path/to/new-replay-output
node --import "$LABWIRED_APP/node_modules/tsx/dist/loader.mjs" \
  replay-native-world.mts 15 Infinity nominal  button 5000
python3 capture/analyze-flight.py "$LABWIRED_EVIDENCE_OUT/nominal-result.json"
```

Arguments are native duration, fault time, output tag, fault kind, and World rounds per poll. Use `10 6 fault-inverter inverter_fault 5000` for the native inverter case, or `15 Infinity nominal-fine button 1000` for the smaller-poll nominal case. Supported fault kinds are `button`, `inverter_fault`, `overcurrent_fault`, `undervoltage_fault` and `stall`.

The replay driver rejects a different app/core commit, changed production runtime source, or a resolved five-MCU plan that differs from the accepted plan. The original capture drivers are preserved under `capture/`; the portable driver uses the same existing runtime APIs and includes the read-only gate observations. The portable driver reproduced all 1,501 nominal body/motor/event records exactly against the qualified app commit, excluding wall time and added register observations; see [portable replay equivalence](portable-replay-equivalence.json). The later main refresh changes only the equivalent board-selection helper; [integration equivalence](app-integration-equivalence.json) records its separate commit.

## Model limits

The proof covers this declared native model. The body has bounded six-degree-of-freedom motion and a simplified BMI270 feedback mapping. The electrical target is the ideal 24 V STM32L476/BLDC plant. Measured motor/propeller calibration, battery sag, transistor switching, the physical AT32F421/RP2354 aircraft electronics, copper-to-model equivalence and physical flight remain unvalidated. The existing checkpoint API also does not provide full motor-state restoration.
