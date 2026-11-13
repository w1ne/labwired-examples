#!/usr/bin/env python3
"""Render a paced LabWired quadrotor demo from source-bound real recordings.

Video shots are the accepted KernelCAD/LabWired browser capture and R4-02
LabWired mixed-signal run. Video edits only: zoom/crop, captions, fade, timing.
No synthesized telemetry or simulated flight is implied by this cut.

Source ESC board derives from OpenDrone OpenESC-30x30, CERN-OHL-S-2.0.
See ../hardware/esc-4in1/README.md and the retained license file.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H, FPS = 1600, 900, 30
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SOURCES = {
    'design': HERE / 'quadrotor-engineering-preview.mp4',
    'instruments': HERE / 'source/quadrotor-universal-instruments-r4-02.webm',
}
OUTPUT = HERE / 'labwired-quadrotor-focused-demo.mp4'
# Each scene retains natural-time movement; no time compression or invented frames.
# Crops enlarge actual interface evidence and avoid the legacy third-party title.
SCENES = [
    dict(name='01-cad', src='design', start=9, seconds=10, crop=(1250,703,175,100),
         title='QUADCOPTER / PARAMETRIC CAD', sub='Inspect the complete mechanical assembly', foot='Actual KernelCAD design capture'),
    dict(name='02-pcb', src='design', start=30.2, seconds=6.3, crop=(1300,731,150,80),
         title='NATIVE PCB / DESIGN REVIEW', sub='6 layers | 222 footprints | 1,067 pads', foot='Native ESC source and validation evidence retained'),
    dict(name='03-firmware', src='design', start=37.0, seconds=9.0, crop=(1250,703,210,95),
         title='FOUR CONTROLLERS / ONE TWIN', sub='Compiled STM32 firmware drives four BLDC motor models', foot='Deterministic simulation, not aircraft flight'),
    dict(name='04-analog', src='instruments', start=106.4, seconds=8.0, crop=(790,445,20,250),
         title='LIVE OSCILLOSCOPE', sub='Read motor current and speed from the running simulation', foot='Actual R4-02 captured signals - enlarged 2x'),
    dict(name='05-logic', src='instruments', start=107.0, seconds=8.0, crop=(790,445,790,250),
         title='LIVE LOGIC ANALYZER', sub='Inspect PWM, drive, fault and enable signals', foot='Actual R4-02 captured signals - enlarged 2x'),
    dict(name='06-fault', src='instruments', start=206.4, seconds=10.0, crop=(1430,804,85,50),
         title='INJECT A MOTOR-DRIVER FAULT', sub='Watch PWM gating and inverter shutdown', foot='Native four-channel fault test - recorded at original speed'),
    dict(name='07-verify', src='design', start=49.0, seconds=10.0, crop=(1250,703,210,95),
         title='OBSERVE THE SAFETY RESPONSE', sub='M1 stops; M2-M4 continue | pause and inspect', foot='Four-channel motor bench, not flight-control validation'),
    dict(name='08-close', src='design', start=70.5, seconds=4.0, crop=(1250,703,175,100),
         title='BUILD. SIMULATE. VERIFY.', sub='LabWired | labwired.com', foot='Evidence and open-source hardware provenance in the project repository'),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def esc(text: str) -> str:
    return text.replace('\\','\\\\').replace(':','\\:').replace("'", '')


def render_scene(scene: dict, target: Path) -> None:
    duration = scene['seconds']
    w,h,x,y = scene['crop']
    title,sub,foot = map(esc,(scene['title'],scene['sub'],scene['foot']))
    vf = ','.join([
        f'crop={w}:{h}:{x}:{y}',
        f'scale={W}:{H}:flags=lanczos',
        f'fps={FPS}',
        'setsar=1',
        'drawbox=x=0:y=0:w=iw:h=122:color=0x07111a@0.94:t=fill',
        'drawbox=x=0:y=840:w=iw:h=60:color=0x07111a@0.90:t=fill',
        'drawbox=x=44:y=25:w=8:h=69:color=0x4fc3f7:t=fill',
        f'drawtext=fontfile={BOLD}:text=\'{title}\':fontcolor=white:fontsize=41:x=70:y=15',
        f'drawtext=fontfile={FONT}:text=\'{sub}\':fontcolor=0xc9d7e8:fontsize=25:x=70:y=74',
        f'drawtext=fontfile={FONT}:text=\'{foot}\':fontcolor=0xc7d2df:fontsize=21:x=70:y=856',
        'fade=t=in:st=0:d=0.42',
        f'fade=t=out:st={duration-0.44:.2f}:d=0.44',
        'format=yuv420p',
    ])
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                    '-ss',str(scene['start']),'-t',str(duration),'-i',str(SOURCES[scene['src']]),
                    '-vf',vf,'-t',str(duration),'-an','-c:v','libx264','-threads','4',
                    '-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
                    '-r',str(FPS),'-video_track_timescale','30000', str(target)], check=True)


def main():
    for name,src in SOURCES.items():
        if not src.is_file():
            raise FileNotFoundError(f'{name}: {src}')
    with tempfile.TemporaryDirectory(prefix='labwired-quad-rec-') as tmp:
        root=Path(tmp)
        parts=[]
        for s in SCENES:
            path=root/f"{s['name']}.mp4"
            render_scene(s,path)
            parts.append(path)
            print(f"rendered {s['name']}, {s['seconds']} s",flush=True)
        lst=root/'concat.txt'
        lst.write_text(''.join(f"file '{p}'\n" for p in parts))
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                        '-f','concat','-safe','0','-i',str(lst), '-an', '-c','copy',
                        '-movflags','+faststart','-metadata','title=LabWired quadrotor - design simulate verify',
                        '-metadata','comment=Real captured LabWired mixed-signal motor test and KernelCAD assembly; derivative open-source ESC documented in repository; no flight validation.',str(OUTPUT)], check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
                 'format=duration,size:stream=codec_name,width,height,avg_frame_rate',
                 '-of','json',str(OUTPUT)],text=True))
    audit={'date':'2026-11-13','renderer':Path(__file__).name,
           'summary':'Readable paced cut; 8 long shots with zoomed real analog/digital captures; no OpenDrone schematic scene.',
           'shots':SCENES,'inputs':{k:{'path':str(p.relative_to(HERE)),'sha256':sha256(p)} for k,p in SOURCES.items()},
           'output':{'path':OUTPUT.name,'sha256':sha256(OUTPUT),'ffprobe':probe},
           'limits':['The ESC PCB is derived from OpenDrone OpenESC-30x30 under CERN-OHL-S-2.0; source attribution stays in the project.',
                     'The analog and digital instruments show accepted four-controller R4-02 bench telemetry.',
                     'The video does not show full flight, structural validation, or transistor-level power simulation.',
                     'Zoom crops and scene fades are editorial; no telemetry is synthesized.']}
    (HERE/'labwired-quadrotor-focused-demo.provenance.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'output':str(OUTPUT),'sha256':sha256(OUTPUT),'probe':probe},indent=2),flush=True)

if __name__=='__main__': main()
