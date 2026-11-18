# Physical device firmware in the digital core

The package's unchanged device ELF passes a bounded boot, input-scan, wake-up
and TYPE0 request/reply test on core commit
`e2908774da4d254e1244dfdf9e5fb7bf6cdf4cf1`, with the production
`event-scheduler` feature. The exact source, image, invocation, network trace
and results are in [the receipt manifest](../evidence/physical-runtime-device/manifest.json).

The image executes the ST HAL clock, GPIO, EXTI and UART paths. The test
observes an 80 MHz clock, four correct input patterns (00/FF/A5/3C), one
80 microsecond opposed-line wake event, a real OL falling-edge interrupt,
and a checksum-valid `A2 00` -> `49 06` exchange. `0x49` encodes the
package's 10 ms minimum cycle. UART BRR is 2083 and TXINV/RXINV are both set.
There are zero UART, overflow, network framing or network parity errors.

[physical-device-probe.yaml](physical-device-probe.yaml) records the exact
model wiring used in the test. The test also sets the existing peripheral
tick interval to one cycle and uses the existing `Machine::timed_uart_sync`
seam after the controlled peer publishes its request. It adds no second
serial engine or firmware substitute.

## Reproduce the probe

Use a checkout of the recorded core commit and the packaged ELF. From the
core checkout, set absolute paths and run:

```sh
IOLINK_L476_DEVICE_ELF=/absolute/package/firmware/release/iolink-device.elf \
IOLINK_L476_DEVICE_REPORT=/absolute/output/device-probe.json \
cargo test --locked -p labwired-core --features event-scheduler \
  --test stm32 stm32_iolink_physical:: -- --ignored --nocapture
```

The test rejects an ELF whose SHA-256 differs from the pinned physical
image. Its ignore annotation records the external immutable ELF/report
requirement; the recorded invocation explicitly ran the test. The ordinary
STM32 suite passed 174 tests and the timed UART group passed eight tests on
the same commit.

## Scope and remaining integration

This proof uses one physical device image and a controlled digital master
line. It does not execute the physical master image or the complete
three-node station. Those are separate required integration steps. The
current L6360 review also exposed a master startup parity/reset assumption
that must be fixed in the physical driver and host fixture before its
image is accepted.

The L6362A model represents explicit digital enable, inversion, opposition,
fault and line-state scenarios. It does not calculate analog voltage,
current, slew, clamp energy or thermal behavior. Its overload delay uses
the sourced typical scenario; the 5 ms cutoff/80 ms retry are declared
scenarios. EN settling and physical timing qualification remain outside
this receipt. The component probe uses a synthetic UID reset value;
a full station must declare distinct node identities.

The published canonical Lab keeps its existing firmware until the matching
physical master and both device images pass together.
