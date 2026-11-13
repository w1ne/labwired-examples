#!/usr/bin/env python3
import os,json,math,re,subprocess,hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
D=Path('/home/andrii/scratch/quad-routing-live-20261113')
O=D/'output'
SRC=Path('/data/worktrees/labwired-examples-quad-story-20261113/examples/robotics/quadrotor-bldc/hardware/esc-4in1/4in1.kicad_pcb')
m=json.loads((O/'route-input-manifest.json').read_text())
stages=json.loads((O/'native-route-stages.json').read_text())['stages']
assert [int(re.search(r'Found (\d+) unconnected', (O/f'esc-route-stage-{i}.drc.txt').read_text()).group(1)) for i in range(5)]==[12,9,6,3,0]
assert all('Found 0 DRC violations' in (O/f'esc-route-stage-{i}.drc.txt').read_text() for i in range(5))
assert [x['segments'] for x in stages]==[1169,1177,1184,1191,1198]
pat=r'\(segment\s+\(start\s+([.\d-]+)\s+([.\d-]+)\)\s+\(end\s+([.\d-]+)\s+([.\d-]+)\)\s+\(width\s+([.\d-]+)\)\s+\(layer\s+"([^"]+)"\)'
data=SRC.read_text()
all_segs=[dict(x0=float(a),y0=float(b),x1=float(c),y1=float(e),width_mm=float(w),layer=layer)
          for a,b,c,e,w,layer in re.findall(pat,data)]
selected=m['selected_nets'];actual=m['removed_segments']
def key(s):
    return (round(s['x0'],4),round(s['y0'],4),round(s['x1'],4),round(s['y1'],4),s['layer'],round(s['width_mm'],4))
remove_keys=set(map(key,actual))
bg=[s for s in all_segs if key(s) not in remove_keys]
assert len(bg)==1169,(len(bg),len(all_segs))
ordered=sorted(actual,key=lambda s:(selected.index(s['net']),s['x0'],s['y0']))
W,H,FPS,N=1600,900,30,210
fdir='/usr/share/fonts/truetype/dejavu'
f40=ImageFont.truetype(fdir+'/DejaVuSans-Bold.ttf',39)
f30=ImageFont.truetype(fdir+'/DejaVuSans-Bold.ttf',28)
f24=ImageFont.truetype(fdir+'/DejaVuSans.ttf',24)
f20=ImageFont.truetype(fdir+'/DejaVuSans.ttf',20)
f16=ImageFont.truetype(fdir+'/DejaVuSans.ttf',16)
SCALE=17.1;OX=135;OY=117;bx=53.2;by=25.5
def xy(x,y):return (int(OX+(x-bx)*SCALE),int(OY+(y-by)*SCALE))
def drseg(draw,s,color,width=None):
    a=xy(s['x0'],s['y0']);b=xy(s['x1'],s['y1'])
    d=max(2,int(s['width_mm']*SCALE)) if width is None else width
    draw.line((a,b), fill=color,width=d,joint='curve')
    r=max(1,d//2);draw.ellipse((a[0]-r,a[1]-r,a[0]+r,a[1]+r),fill=color)
via_blocks=re.findall(r'^\t\(via\b(.*?)^\t\)',data,re.M|re.S)
vias=[]
for v in via_blocks:
    a=re.search(r'\(at\s+([.\d-]+)\s+([.\d-]+)\)',v)
    if a:vias.append((float(a.group(1)),float(a.group(2))))
assert len(vias)==1716
base=Image.new('RGB',(W,H),'#08121e');dr=ImageDraw.Draw(base)
dr.rounded_rectangle((105,101,895,849),radius=47,fill='#102834',outline='#34515e',width=3)
for seg in bg:drseg(dr,seg,'#365865',1)
for a,b in vias:
    x,y=xy(a,b);dr.ellipse((x-2,y-2,x+2,y+2),fill='#52696e')
for a,b in [(59.2,31),(90.7,31),(59.2,64.0),(90.7,64.0)]:
    x,y=xy(a,b);dr.ellipse((x-19,y-19,x+19,y+19),fill='#08121e',outline='#52717b',width=3)
dr.rectangle((962,95,1555,842),fill='#0d1d2a')
dr.rectangle((962,95,1555,99),fill='#42b9d8')
def add(draw,pos,t,font,col):draw.text(pos,t,font=font,fill=col)
GROUP_COLORS=['#51d5f3','#f4c76b','#b8a0ff','#85dfb1']
groups=[ordered[i*0:] for i in []] # groups assembled from the actual net inventory
group_segs=[[s for s in ordered if s['net'] in selected[k*3:(k+1)*3]] for k in range(4)]
assert list(map(len,group_segs))==[8,7,7,7]
out=O/'native-pcb-route-operation-7s.mp4'
proc=subprocess.Popen(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
'-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-',
'-an','-c:v','libx264','-threads','4','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
try:
    for i in range(N):
        t=i/(N-1);stagef=min(4, t*4.05);completed=min(4,int(stagef));active=min(3, int(stagef))
        frame=base.copy();dd=ImageDraw.Draw(frame)
        for k,g in enumerate(group_segs):
            # Replay additions produced by KiCad-native PCB_TRACK edits.
            n=len(g) if k<completed else max(0,min(len(g),math.floor((stagef-k)*len(g)))) if k==active else 0
            for seg in g[:n]:drseg(dd,seg,GROUP_COLORS[k],max(5,round(seg['width_mm']*SCALE)+3))
        # These counts refer to completed native KiCad DRC stages, not interpolated frames.
        openings=[12,9,6,3,0][completed]
        add(dd,(1000,125),'PCB ROUTING',f40,'#f3f6fa')
        add(dd,(1000,185),'NATIVE KiCad 10 EDITS',f24,'#adbfca')
        add(dd,(1000,231),'6 copper layers  |  12 ESC nets',f20,'#b7d0db')
        add(dd,(1000,294),'Actual copper added',f24,'#b7d0db')
        add(dd,(1000,333),f'{sum(len(g) for g in group_segs[:completed]) + (max(0,min(len(group_segs[active]),math.floor((stagef-active)*len(group_segs[active])))) if completed<4 else 0):02d} / 29 segments',f30,'#f5f7fa')
        add(dd,(1000,399),'LAST KiCad DRC',f20,'#a7c1cf')
        add(dd,(1000,440),f'{openings} open connections',f30,'#7fe0b5' if openings==0 else '#ffd18a')
        add(dd,(1000,481),'0 other violations',f24,'#b3c8d5')
        add(dd,(1000,533),f'ESC GROUP {min(4,active+1)} / COPPER DETAIL',f20,GROUP_COLORS[active])
        for k in range(4):
            x=1000+k*125
            dd.rounded_rectangle((x,578,x+107,587),radius=4,fill='#273b48')
            fraction=max(0,min(1,stagef-k))
            if fraction:dd.rounded_rectangle((x,578,x+max(1,round(107*fraction)),587),radius=4,fill=GROUP_COLORS[k])
        # Live digital magnification of the actual PCB geometry and stage tracks.
        focus=group_segs[active]
        cx=sum((s['x0']+s['x1'])/2 for s in focus)/len(focus)
        cy=sum((s['y0']+s['y1'])/2 for s in focus)/len(focus)
        px,py=xy(cx,cy)
        crop=frame.crop((max(0,px-127),max(0,py-48),min(W,px+127),min(H,py+48)))
        inset=crop.resize((540,205),Image.Resampling.BICUBIC)
        frame.paste(inset,(993,606))
        dd=ImageDraw.Draw(frame)
        dd.rectangle((993,606,1533,811),outline=GROUP_COLORS[active],width=3)
        add(dd,(1000,820),'Native copper edits  /  KiCad DRC checked',f16,'#b7ccd6')
        if proc.stdin is None:raise RuntimeError('ffmpeg input closed')
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('ffmpeg failed')
except:
    proc.kill();raise
(O/'native-route-video-provenance.json').write_text(json.dumps(
 {'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
  'route_stage_manifest_sha256':hashlib.sha256((O/'native-route-stages.json').read_bytes()).hexdigest(),
  'proof':'5 native KiCad 10.0.8 PCB states and DRC reports','unconnected_by_stage':[12,9,6,3,0],
  'drc_other_violations':0,'routed_nets':selected,'source_route_segments_restored':len(ordered),
  'no_autorouter_claim':True,'output':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n')
print('RENDERED',out,round(out.stat().st_size/1048576,2),'MiB')
