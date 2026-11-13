#!/usr/bin/env python3
"""Assemble a source-bound native PCB routing + hosted mixed-signal review film."""
import json, subprocess, tempfile, hashlib
from pathlib import Path
M=Path(__file__).resolve().parent
E=M/'evidence/native-routing-mixed-signal-20261113'
OUT=M/'labwired-quadcopter-routing-mixed-signal-32s.mp4'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
shots=[
    ('native_pcb_route',E/'native-pcb-route-operation-7s.mp4',0,7.0,None),
    ('populated_pcb',M/'pcb-3d-orbit.mp4',0,4.0,'PCB ASSEMBLY|Populated, source-derived 3D model'),
    ('hosted_test',E/'hosted-mixed-signal-fault-14s.mp4',0,14.0,None),
    ('motor_twin',M/'quadrotor-engineering-preview.mp4',37,7.0,'FIRMWARE + MOTOR TWIN|Compiled MCU and reduced-order BLDC models'),
]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()
with tempfile.TemporaryDirectory(prefix='quad-final-cut-') as tmp:
    tmp=Path(tmp)
    clips=[]
    for i,(id,p,start,duration,caption) in enumerate(shots):
        assert p.is_file(),p
        dest=tmp/f'{i:02d}.mp4'
        filters=[]
        if id=='motor_twin':filters+=['crop=1300:732:150:88']
        filters+=['scale=1600:900:flags=lanczos','fps=30','setsar=1']
        if caption:
            title,sub=caption.split('|')
            filters += [
                'drawbox=x=0:y=0:w=iw:h=103:color=0x0b1724@0.93:t=fill',
                'drawbox=x=43:y=18:w=7:h=63:color=0x63d5f0:t=fill',
                f"drawtext=fontfile={font}:text='{title}':fontcolor=white:fontsize=36:x=66:y=9",
                f"drawtext=fontfile={regular}:text='{sub}':fontcolor=0xb4cedc:fontsize=23:x=68:y=61"
            ]
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
         '-ss',str(start),'-t',str(duration),'-i',str(p),'-vf',','.join(filters),
         '-an','-t',str(duration),'-r','30','-c:v','libx264','-threads','4',
         '-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
        clips.append(dest)
        print('SHOT',id,'SECONDS',duration,'bytes',dest.stat().st_size,flush=True)
    concat=tmp/'concat.txt'
    concat.write_text(''.join(f"file '{p}'\n" for p in clips))
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0',
         '-i',str(concat),'-c','copy','-an','-movflags','+faststart',
         '-metadata','title=Quadrotor: PCB routing and mixed-signal verification',
         '-metadata','comment=KiCad 10 scripted route reconstruction and independently checked DRC; actual hosted STM32 GPIO and virtual motor current/fault traces; no new autorouter or physical-flight claim.',
         str(OUT)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
    'format=duration,size:stream=width,height,avg_frame_rate,codec_name',
    '-of','json',str(OUT)],text=True))
assert abs(float(probe['format']['duration'])-32.0)<0.08,probe
assert probe['streams'][0]['width']==1600 and probe['streams'][0]['height']==900
assert probe['streams'][0]['avg_frame_rate']=='30/1'
receipt={
    'date':'2026-11-13',
    'video':OUT.name, 'sha256':sha(OUT), 'ffprobe':probe,
    'scenes':[{'name':id,'source':str(p.relative_to(M)),'source_sha256':sha(p),
               'start_seconds':start,'duration_seconds':dur}
              for id,p,start,dur,_ in shots],
    'real_routing_evidence':'Four native KiCad10 scripted segment-add stages on a disposable copy of a six-layer ESC PCB; 29 segments for 12 nets restored. DRC open connections 12,9,6,3,0; zero other violations. No autorouter succeeded.',
    'real_simulation_evidence':'One hosted STM32L476 six-step ESC and virtual BLDC run, actual PWM GPIO edges, Hall edges, analog model current and motor speed; injected driver fault and measured inverter disable.',
    'limits':['Not a record of a successful autorouter','Restores preapproved PCB routing, not an original route computation',
             'Physical 4S AT32F421 ESC circuit differs from the functional 24V STM32L476 motor bench',
             'No transistor-level MOSFET model, no validated motor power electronics or flight dynamics',
             'Analog motor current is an executable model, not physical measurement',
             'Mechanical twin motion is a separate prior recording, not frame-synchronized to the hosted fault trace'],
}
(M/'labwired-quadcopter-routing-mixed-signal-32s.provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('FINAL',OUT,'duration',probe['format']['duration'],'SHA256',sha(OUT),flush=True)
