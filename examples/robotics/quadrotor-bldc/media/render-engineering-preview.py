#!/usr/bin/env python3
"""Edit actual CAD, native KiCad exports and an audited runtime screen capture.

Requires ffmpeg and DejaVu Sans. No graphics, motion or telemetry are fabricated.
The CAD review clips are time-compressed. All runtime clips play at real speed.
"""
import argparse
import json
import subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--capture-dir',required=True,type=Path)
p.add_argument('--runtime-video',required=True,type=Path)
p.add_argument('--reuse-existing',action='store_true')
p.add_argument('--output',required=True,type=Path)
a=p.parse_args()
B=a.capture_dir; O=B/'video'/'edit'; O.mkdir(parents=True,exist_ok=True)
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';FB=F.replace('Sans.ttf','Sans-Bold.ttf')
order=[]
def run(args):
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*args],check=True)
def text(s):
 return s.replace('\\','\\\\').replace(':','\\:').replace("'",'')
def footer(title,sub):
 return ','.join(['drawbox=x=0:y=806:w=1600:h=94:color=0x09121f@0.96:t=fill',f"drawtext=fontfile={FB}:text='{text(title)}':fontcolor=white:fontsize=29:x=42:y=823",f"drawtext=fontfile={F}:text='{text(sub)}':fontcolor=0x9eafc3:fontsize=18:x=43:y=863"])
def video(name,src,start,end,duration,title,sub,extra='',reuse=True):
 out=O/(name+'.mp4');order.append(out)
 if reuse and a.reuse_existing and out.exists():return
 ratio=duration/(end-start)
 vf=f'setpts={ratio:.8f}*(PTS-STARTPTS),fps=30,scale=1600:900:flags=lanczos,{footer(title,sub)}'
 if extra:vf+=','+extra
 vf+=f',fade=t=in:st=0:d=0.18,fade=t=out:st={duration-.2:.3f}:d=0.2'
 run(['-ss',str(start),'-t',str(end-start),'-i',str(src),'-vf',vf,'-t',str(duration),'-an','-c:v','libx264','-threads','2','-preset','faster','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(out)])
 print('Rendered',name,flush=True)
def still(name,path,duration,title,sub):
 out=O/(name+'.mp4');order.append(out)
 if a.reuse_existing and out.exists():return
 vf=f"scale=1600:900:force_original_aspect_ratio=decrease,pad=1600:900:(ow-iw)/2:(oh-ih)/2:color=white,zoompan=z='min(1.025,1+on*0.0001)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1600x900:fps=30,{footer(title,sub)},fade=t=in:st=0:d=0.2,fade=t=out:st={duration-.2}:d=0.2"
 run(['-loop','1','-framerate','30','-i',str(path),'-t',str(duration),'-vf',vf,'-an','-c:v','libx264','-threads','2','-preset','faster','-crf','24','-pix_fmt','yuv420p',str(out)])
 print('Rendered',name,flush=True)
scenes={s['name']:s for s in json.loads((B/'video'/'cad-scenes.json').read_text())}
def cad_file(s):return B/'video'/Path(s['file']).name
s=scenes['03-hero'];video('00-intro',cad_file(s),s['start']+1,s['end']-1,5,'LABWIRED + KERNELCAD','Quadrotor co-design | Engineering preview | Actual application recording',f"drawbox=x=0:y=0:w=1600:h=125:color=0x09121f@0.85:t=fill,drawtext=fontfile={FB}:text='DESIGN. ASSEMBLE. TEST.':fontcolor=white:fontsize=47:x=42:y=42")
s=scenes['01-design'];video('01-design',cad_file(s),s['start'],s['end']-.5,8,'01 / DESIGN THE MECHANICS','226 mm OpenFrame-5F | Revision 3 | Editable parametric source')
s=scenes['02-assembly'];video('02-assembly',cad_file(s),s['start'],s['end']-.5,10,'02 / INSPECT THE ASSEMBLY','36 modeled parts | Four rotor joints | Exploded view')
still('03a-schematic',B/'pcb/schematic-overview.png',3,'03 / CONNECT THE ELECTRONICS','Native OpenESC schematic | Four AT32F421 channels | 210 nets')
still('03b-power-stage',B/'pcb/schematic-channel.png',4,'TRACE EACH MOTOR POWER STAGE','Gate driver + three half bridges | Native schematic ERC passes')
still('04-pcb',B/'pcb/esc-isometric.png',7,'04 / REVIEW THE REAL PCB','Six layers | 222 footprints | 1,067 pads | ERC 0 / DRC 0')
video('05-live',a.runtime_video,35.5,43.5,8,'05 / RUN THE ELECTRONICS + CAD','Candidate build | Real STM32 C firmware | Four measured motor angles and speeds',reuse=False)
video('06-fault-action',a.runtime_video,52,57,5,'06 / APPLY FAULT 1','Actual circuit input | Independent firmware channels | 24 V reduced-order plants',reuse=False)
video('07-fault-result',a.runtime_video,80,87,7,'ONE CHANNEL STOPS. THREE CONTINUE.','M1 inverter off | M2-M4 running | CAD poses follow observed shaft positions',reuse=False)
video('08-pause',a.runtime_video,95,102,7,'07 / PAUSE THE SYSTEM','All four measured poses hold | Telemetry is marked Last observed',reuse=False)
video('09-reset',a.runtime_video,115,121,6,'08 / RESET THE SYSTEM','Four controllers reinitialize | All four observed motor samples clear',reuse=False)
s=scenes['03-hero'];video('10-end',cad_file(s),s['start']+5,s['end']-1,5,'CO-DESIGN ENGINEERING PREVIEW','Native PCB + 24 V STM32 bench | Physical board simulation and flight control remain open',reuse=False)
concat=O/'concat.txt';concat.write_text(''.join("file '"+str(x.resolve()).replace("'","'\\''")+"'\n" for x in order))
a.output.parent.mkdir(parents=True,exist_ok=True)
run(['-f','concat','-safe','0','-i',str(concat),'-an','-c:v','libx264','-threads','2','-preset','faster','-crf','25','-pix_fmt','yuv420p','-movflags','+faststart','-metadata','title=Quadrotor co-design engineering preview','-metadata','comment=Actual application footage and native KiCad exports. Candidate 24 V STM32 propulsion bench; physical board simulation and flight control remain incomplete.',str(a.output)])
print('Final',a.output,flush=True)
