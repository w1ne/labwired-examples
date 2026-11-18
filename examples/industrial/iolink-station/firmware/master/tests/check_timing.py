#!/usr/bin/env python3
"""Check the authored timer/I2C numbers against timing constraints, not hardware.

References: RM0351 I2C timing, AN4235 sections 2.2.4/2.2.5, and DS8900.
Clock spread +/-5% is a timing-margin perturbation, not a measured clock error
or permission to exceed the MCU rated frequency. Physical clock is 8 MHz MCO.
"""
import itertools,json,re
from pathlib import Path
source=Path(__file__).resolve().parents[1]/'board_hal.c'
text=source.read_text()
timing=int(re.search(r'I2C_FAST_TIMING\s+(0x[0-9A-F]+)U',text)[1],16)
presc=(timing>>28)&15;scldel=(timing>>20)&15;sdadel=(timing>>16)&15
sclh=(timing>>8)&255;scll=timing&255
freqs=[];pulse=[]
for clock,rise,fall,analog in itertools.product([76e6,80e6,84e6],[0,300],[0,300],[50,260]):
    tick=1e9/clock;tp=(presc+1)*tick
    low=(scll+1)*tp+analog+2*tick
    high=(sclh+1)*tp+analog+2*tick
    assert low>=1300 and high>=600
    assert (scldel+1)*tp>=rise+100
    assert sdadel*tp>=max(0,fall-50-3*tick)
    assert sdadel*tp<=900-rise-260-4*tick
    hz=1e9/(low+high+rise+fall);assert hz<=400000;freqs.append(hz)
    # 1 MHz nominal timer, PWM2 CCR=1 and ARR=80: (ARR+1-CCR)=80 ticks.
    us=80*80e6/clock;assert 75<=us<=85;pulse.append(us)
assert 500+(32000000+38400-1)//38400==1334
# HAL UART uses 9-bit word length with parity for eight data bits. Baud divider
# nearest 80 MHz/38400 is 2083; nominal divider error is independent of RC drift.
actual_baud=80e6/round(80e6/38400)
print(json.dumps({'scope':'analytical timing bounds; no measured bus/waveform',
 'i2c_timing_hex':hex(timing),'clock_bound_hz':[76e6,84e6],
 'i2c_frequency_range_hz':[min(freqs),max(freqs)],
 'wake_pulse_range_us':[min(pulse),max(pulse)],
 'nominal_com2_actual_baud':actual_baud,
 'nominal_com2_divider_error_ppm':(actual_baud/38400-1)*1e6,
 'master_frequency_acceptance_hz':[38400*.999,38400*1.001],'wake_to_test_min_us':1334,'result':'PASS'},indent=2))
