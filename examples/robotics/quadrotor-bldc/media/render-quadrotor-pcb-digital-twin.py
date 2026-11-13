#!/usr/bin/env python3
"""Make the short LabWired 5-scene quadcopter video from recorded evidence.

Real clips: KernelCAD quadcopter, KiCad-10 source routing-layer visualization,
real populated PCB GLB turntable, quadrotor universal instruments and digital twin.
Do not imply recorded autorouter execution or completed aircraft flight.
"""
import hashlib,json,subprocess,tempfile
from pathlib import Path
M=Path(__file__).resolve().parent
OUT=M/'labwired-quadrotor-pcb-digital-twin-32s.mp4'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
INPUTS={
    'cad':M/'quadrotor-engineering-preview.mp4',
    'routing':M/'pcb-routing-animation.mp4',
    '3d':M/'pcb-3d-orbit.mp4',
    'instruments':M/'source/quadrotor-universal-instruments-r4-02.webm',
    'twin':M/'quadrotor-engineering-preview.mp4',
}
SHOTS=[
    {'id':'01-cad','src':'cad','start':10.0,'duration':5.5,'title':'QUADCOPTER CAD',
     'sub':'Parametric mechanical design'},
    {'id':'02-routing','src':'routing','start':0,'duration':7.0,'title':'PCB ROUTING',
     'sub':'Six copper layers; actual segment and via geometry'},
    {'id':'03-pcb3d','src':'3d','start':0,'duration':4.4,'title':'3D PCB',
     'sub':'Rotating populated board'},
    {'id':'04-instruments','src':'instruments','start':109.4,'duration':7.5,
     'title':'LIVE OSCILLOSCOPE + LOGIC ANALYZER','sub':'Analog and digital signals from one running simulation'},
    {'id':'05-twin','src':'twin','start':37.0,'duration':8.0,'title':'DIGITAL TWIN',
     'sub':'Firmware and motor simulation with linked 3D model'},
]
assert abs(sum(s['duration'] for s in SHOTS)-32.4)<1e-6
for p in INPUTS.values():
    if not p.exists():raise FileNotFoundError(p)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def shell(*args):
    subprocess.run(args,check=True)

def overlay(title,sub):
    txt=lambda s: s.replace('\\','\\\\').replace(":",r'\:').replace("'",'')
    return (f'drawbox=x=0:y=0:w=iw:h=106:color=0x07111c@0.94:t=fill,'
            f'drawbox=x=38:y=24:w=7:h=60:color=0x50c7eb:t=fill,'
            f"drawtext=fontfile={FONT}:text='{txt(title)}':fontcolor=white:fontsize=37:x=65:y=13,"
            f"drawtext=fontfile={FONT_REG}:text='{txt(sub)}':fontcolor=0xc5d6e1:fontsize=22:x=67:y=66")

with tempfile.TemporaryDirectory(prefix='labwired-quadcopter-video-',dir='/data/tmp' if Path('/data/tmp').is_dir() else None) as tmp:
    clips=[]
    for item in SHOTS:
        src=INPUTS[item['src']]
        dest=Path(tmp)/f"{item['id']}.mp4"
        name=item['id']
        if name=='01-cad':
            vf='crop=1280:720:160:95,scale=1600:900:flags=lanczos,'+overlay(item['title'],item['sub'])
        elif name=='02-routing':
            vf='scale=1600:900:flags=lanczos' # source already has the correct PCB ROUTING header
        elif name=='03-pcb3d':
            vf='scale=1600:900:flags=lanczos,'+overlay(item['title'],item['sub'])
        elif name=='04-instruments':
            vf=('[0:v]split=2[a][b];'
                '[a]crop=780:620:10:155,scale=800:636:flags=lanczos[l];'
                '[b]crop=780:620:810:155,scale=800:636:flags=lanczos[r];'
                '[l][r]hstack=inputs=2,pad=1600:900:0:126:color=0x07111c,'
                +overlay(item['title'],item['sub'])+'[out]')
        elif name=='05-twin':
            vf='crop=1300:732:150:88,scale=1600:900:flags=lanczos,'+overlay(item['title'],item['sub'])
        argv=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
              '-ss',str(item['start']),'-t',str(item['duration']),'-i',str(src)]
        if name=='04-instruments':argv+=['-filter_complex',vf,'-map','[out]']
        else:argv+=['-vf',vf]
        argv+=['-t',str(item['duration']),'-an','-r','30','-c:v','libx264',
               '-threads','4','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',
               '-movflags','+faststart',str(dest)]
        shell(*argv);clips.append(dest)
        print('SCENE',name,item['duration'],'sec',flush=True)
    playlist=Path(tmp)/'clips.txt';playlist.write_text(''.join(f"file '{p}'\n" for p in clips))
    shell('ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
        '-f','concat','-safe','0','-i',str(playlist),'-c','copy','-an',
        '-movflags','+faststart','-metadata','title=LabWired quadcopter - PCB routing and digital twin',
        '-metadata','comment=Source-bound design, completed PCB route layer visualization, actual PCB GLB turntable and recorded mixed-signal twin; not an autorouting-process recording or validated flight.',str(OUT))
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
    'format=duration,size:stream=codec_name,width,height,avg_frame_rate','-of','json',str(OUT)],text=True))
provenance={
 'date':'2026-11-13','type':'short demonstration','video':OUT.name,'sha256':sha(OUT),
 'frame_info':probe,'shots':SHOTS,
 'source_hashes':{key:sha(p) for key,p in INPUTS.items()},
 'routing':{'generator':'render-pcb-routing.py','source':'../hardware/esc-4in1/4in1.kicad_pcb',
            'exporter':'KiCad 10.0.8','copper_layers':6,'segments_rendered':1198,'vias_rendered':1716,
            'note':'Progressive reveal of physical routed segments; not capture of an autorouter running.'},
 'board_3d':{'source':'../hardware/esc-4in1/fabrication-review/esc-board-populated.glb',
             'renderer':'render-pcb-turntable.py','mesh_count':214,
             'note':'The camera rotates around the actual exported board geometry. Solder-mask color was corrected for visibility.'},
 'instruments':{'source':'quadrotor-universal-instruments-r4-02.webm',
                'note':'Both displayed panels are synchronized crops of the same accepted LabWired browser recording.'},
 'limits':['The ESC electrical source derives from OpenDrone OpenESC-30x30 under CERN-OHL-S-2.0; attribution retained in hardware/esc-4in1/README.md.',
           'The firmware/BLDC plant footage is a digital-twin demonstration, not calibrated flight validation.',
           'No circuit routing was performed during the video; the animation presents completed source PCB segments and vias.']}
(M/'labwired-quadrotor-pcb-digital-twin-32s.provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('FINAL VIDEO',OUT,'SECONDS',probe['format']['duration'],'SHA256',sha(OUT),flush=True)
