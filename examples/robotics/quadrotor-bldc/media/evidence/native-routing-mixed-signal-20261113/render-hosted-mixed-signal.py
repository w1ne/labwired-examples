#!/usr/bin/env python3
"""Render an actual LabWired hosted PWM/analog single-run trace with fault injection."""
import json, math, bisect, hashlib, statistics, subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
D=Path('/home/andrii/scratch/quad-routing-live-20261113')
O=D/'output'
ev=json.loads((O/'hosted-mixed-signal-trace.json').read_text())
w0,w1=ev['window']
hz=ev['simulation_clock_hz']; assert hz==80_000_000
PWM=ev['traces']; analog=ev['analog']
fault=next(c for c,v in PWM['gpiob:7']['edges'] if v==1)
off=next(c for c,v in PWM['gpiob:0']['edges'] if v==0)
assert (fault,off)==(2500001,2656181)
for key in ['gpioa:8','gpioa:9','gpioa:10']:
    assert not any(c>off and v==1 for c,v in PWM[key]['edges']),key
rises=[c for c,v in PWM['gpioa:8']['edges'] if v==1]
periods=[b-a for a,b in zip(rises,rises[1:]) if 3900<=b-a<=4100]
assert periods and statistics.median(periods)==4000,periods[:10]
fall=[c for c,v in PWM['gpioa:8']['edges'] if v==0]
highs=[next((f-r for f in fall if f>r),0) for r in rises]
highs=[h for h in highs if 2300<=h<=2500]
assert highs and statistics.median(highs)==2400,highs[:10]
assert any(p[2]>.25 for p in analog['motor.rotor1.current_a'] if p[0]<fault)
assert any(p[1]<-.2 for p in analog['motor.rotor1.current_a'] if p[0]<fault)
W,H,FPS,N=1600,900,30,420
FONT='/usr/share/fonts/truetype/dejavu'
ft32=ImageFont.truetype(FONT+'/DejaVuSans-Bold.ttf',32)
ft26=ImageFont.truetype(FONT+'/DejaVuSans-Bold.ttf',26)
ft22=ImageFont.truetype(FONT+'/DejaVuSans.ttf',22)
ft18=ImageFont.truetype(FONT+'/DejaVuSans.ttf',18)
ft15=ImageFont.truetype(FONT+'/DejaVuSans.ttf',15)
xmin,xmax=275,1540
def X(c):return xmin+round((c-w0)/(w1-w0)*(xmax-xmin))
def Tms(c):return (c/hz)*1000
def txt(d,xy,t,font=ft18,c='#d2e2ee'):d.text(xy,str(t),font=font,fill=c)
base=Image.new('RGB',(W,H),'#081420');d=ImageDraw.Draw(base)
d.rectangle((0,0,W,94),fill='#102331')
txt(d,(36,17),'MIXED-SIGNAL TEST',ft32,'#f6f8fb')
txt(d,(37,58),'ONE COMPILED ESC + VIRTUAL BLDC  /  SHARED SIMULATION CLOCK',ft18,'#a8c8da')
txt(d,(1140,27),'20.0 kHz PWM  |  60% ON',ft22,'#91e7d9')
for i in range(16):
    c=w0+i*40000
    x=X(c)
    d.line((x,132,x,826),fill='#223949',width=1)
    txt(d,(x-20,106),f'{Tms(c):.1f}',ft15,'#8ba9bc')
txt(d,(38,107),'TIME (ms)',ft18,'#9ebbc9')
xf,xo=X(fault),X(off)
d.rectangle((xf,134,xo,825),fill='#34283b')
for x,col in [(xf,'#f2af68'),(xo,'#f47a8a')]:
    d.line((x,130,x,825),fill=col,width=2)
txt(d,(xf+6,140),'FAULT INPUT',ft15,'#f2af68')
txt(d,(xo+6,162),'INVERTER OFF',ft15,'#ff9da6')
rows=[('PA8 PWM-A','gpioa:8',184,213,'#5cd0ed'),
      ('PA9 PWM-B','gpioa:9',253,282,'#e7c681'),
      ('PA10 PWM-C','gpioa:10',322,351,'#b1a0fb')]
def draw_logic(key,hi,lo,color,label):
    v=PWM[key];ed=v['edges'];cur=v['initial'];xlast=xmin
    d.line((xmin,lo+15,xmax,lo+15),fill='#2c414e',width=1)
    for cyc,lev in ed+[[w1,cur]]:
        x=X(cyc)
        if x<xlast:continue
        d.line((xlast,hi if cur else lo,x,hi if cur else lo),fill=color,width=3)
        if cyc<w1:d.line((x,hi if cur else lo,x,hi if lev else lo),fill=color,width=2)
        xlast=x;cur=lev
    txt(d,(38,hi+7),label,ft22,color)
for label,key,hi,lo,col in rows:draw_logic(key,hi,lo,col,label)
# Hall state from the three independent input-edge traces.
hc=[('gpioc:0',1),('gpioc:1',2),('gpioc:2',4)]
events=[];state=0
for k,bit in hc:
    if PWM[k]['initial']:state|=bit
    for c,v in PWM[k]['edges']:events.append((c,bit,v))
events.sort()
hall_segments=[(w0,state)]
for c,bit,v in events:
    state=(state|bit) if v else (state&~bit)
    hall_segments.append((c,state))
hall_segments.append((w1,state))
for j in range(len(hall_segments)-1):
    x0=X(hall_segments[j][0]);x1=X(hall_segments[j+1][0]);s=hall_segments[j][1]
    y=422-round((s/7)*28)
    d.line((x0,y,x1,y),fill='#75dfb0',width=3)
    d.line((x0,436,x1,436),fill='#243b47')
    if x1-x0>42:txt(d,(x0+5,438),str(s),ft15,'#8bdab9')
txt(d,(38,398),'HALL CODE',ft22,'#78dfb3')
txt(d,(38,428),'PC2..PC0',ft15,'#80b39c')
# Analog-current trace. Bars are true min/max of 500-cycle bins, not fabricated interpolations.
curve=analog['motor.rotor1.current_a'];IY=548;SCALE=68
for ax in [-1,0,1,2]:
    yy=IY-round(ax*SCALE)
    d.line((xmin,yy,xmax,yy),fill='#284354',width=1)
    txt(d,(196,yy-10),f'{ax} A',ft15,'#83a8b8')
prior=None
for c,lo,hi,mean,n in curve:
    xx=X(c);ylo=IY-round(lo*SCALE);yhi=IY-round(hi*SCALE);ym=IY-round(mean*SCALE)
    d.line((xx,ylo,xx,yhi),fill='#40bece',width=2)
    if prior and xx>prior[0]:d.line((prior[0],prior[1],xx,ym),fill='#8bf2e3',width=2)
    prior=(xx,ym)
txt(d,(38,515),'MOTOR CURRENT',ft22,'#8bf2e3')
txt(d,(38,544),'modeled A',ft18,'#82afb9')
# Speed trend: only observations from the same captured analog series.
speed=analog['motor.rotor1.speed_rpm'];last=None
for c,lo,hi,mean,n in speed:
    x=X(c);y=691-round(mean/60)
    if last:d.line((last[0],last[1],x,y),fill='#8fa6e9',width=2)
    last=x,y
d.line((xmin,694,xmax,694),fill='#294153')
txt(d,(38,670),'MOTOR SPEED',ft22,'#b6c2f6')
txt(d,(38,699),'model RPM',ft18,'#99a6c7')
draw_logic('gpiob:7',748,772,'#f2ae68','PB7 FAULT')
draw_logic('gpiob:0',796,820,'#e5869a','PB0 ENABLE')
d.rectangle((0,850,W,900),fill='#0f2431')
txt(d,(35,862),'Actual STM32 TIM1 GPIO edges + BLDC model current; no MOSFET transient or physical-flight validation',ft18,'#a4becd')
out=O/'hosted-mixed-signal-fault-14s.mp4'
proc=subprocess.Popen(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo',
'-pixel_format','rgb24','-video_size','1600x900','-framerate','30','-i','-','-an','-c:v','libx264','-threads','4',
'-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
try:
  for i in range(N):
    c=w0+(w1-w0)*(i/(N-1))
    frame=base.copy();dd=ImageDraw.Draw(frame)
    x=X(c)
    dd.line((x,131,x,826),fill='#f5f7fa',width=2)
    dd.polygon([(x-7,127),(x+7,127),(x,137)],fill='#f5f7fa')
    state='RUNNING' if c<fault else 'DRIVER FAULT' if c<off else 'INVERTER DISABLED'
    col='#8feac5' if c<fault else '#f3cb81' if c<off else '#ff9d9f'
    # Live event readout does not replace source traces.
    dd.rectangle((928,54,1560,90),fill='#132d3a')
    txt(dd,(947,60),state,ft18,col)
    txt(dd,(1340,60),f't = {Tms(c):.3f} ms',ft18,'#eaf5fa')
    if proc.stdin is None:raise RuntimeError('ffmpeg closed')
    proc.stdin.write(frame.tobytes())
  proc.stdin.close()
  if proc.wait()!=0:raise RuntimeError('ffmpeg error')
except:
  proc.kill();raise
receipt={
 'run_id':ev['run_id'],'snapshot_id':ev['snapshot_id'],
 'source':'Single hosted LabWired run, actual TIM1 PWM GPIO edges and reduced-order BLDC motor analog series',
 'simulation_clock_hz':hz,
 'gpio_pwm_period_cycles_median':statistics.median(periods),
 'pwm_high_cycles_median':statistics.median(highs),
 'pwm_frequency_hz':hz/statistics.median(periods),
 'pwm_duty':statistics.median(highs)/statistics.median(periods),
 'fault_assert_cycle':fault,'inverter_enable_low_cycle':off,
 'fault_to_disable_cycles':off-fault,'fault_to_disable_ms':(off-fault)/hz*1000,
 'analog_current_sample_bins':len(curve),'analog_speed_sample_bins':len(speed),
 'unpowered_rail_assumed':True,'outputs_not_validated':'physical MOSFET, real AT32F421 ESC, flight controller, thermal and actual propulsion',
 'video_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'source_trace_sha256':hashlib.sha256((O/'hosted-mixed-signal-trace.json').read_bytes()).hexdigest(),
}
(O/'hosted-mixed-signal-fault-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('RENDERED',out,round(out.stat().st_size/1048576,2),'MiB',receipt)
