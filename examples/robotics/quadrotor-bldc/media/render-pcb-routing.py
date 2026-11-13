#!/usr/bin/env python3
"""Animate exact KiCad 10 routed segment/via geometry as a layer reveal.

This is a visualization of a completed PCB, not a recording of an autorouter.
KiCad 10.0.8 is used to independently export all six physical copper layers.
"""
import math, os, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'hardware/esc-4in1/4in1.kicad_pcb'
OUTPUT=Path(os.environ.get('LABWIRED_PCB_ROUTING_OUTPUT', str(Path(__file__).resolve().parent/'pcb-routing-animation.mp4')))
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
s=SOURCE.read_text()
pat=r'\(segment\s+\(start\s+([.\d-]+)\s+([.\d-]+)\)\s+\(end\s+([.\d-]+)\s+([.\d-]+)\)\s+\(width\s+([.\d-]+)\)\s+\(layer\s+"([^"]+)"\)'
segments=[(float(x),float(y),float(x2),float(y2),float(w),layer) for x,y,x2,y2,w,layer in re.findall(pat,s)]
# Include microvias with the optional `micro` qualifier before the position.
via_blocks=re.findall(r'^\t\(via\b(.*?)^\t\)',s,re.M|re.S)
vias=[]
for block in via_blocks:
    pt=re.search(r'\(at\s+([.\d-]+)\s+([.\d-]+)\)',block)
    diam=re.search(r'\(size\s+([.\d-]+)\)',block)
    assert pt and diam,block[:150]
    vias.append((float(pt.group(1)),float(pt.group(2)),float(diam.group(1))))
assert len(vias)==1716,len(vias)
assert len(segments)==1198,(len(segments),SOURCE)
assert len(vias)>1700,len(vias)
COLORS={'B.Cu':(53,161,227),'In1.Cu':(230,203,94),'In2.Cu':(147,119,237),'In3.Cu':(104,212,163),'In4.Cu':(233,125,123),'F.Cu':(246,173,86)}
# draw at 1280x720 to keep per-frame processing bounded.
W,H,FPS,DURATION=1280,720,24,7
SCALE=13.25; origin=(235,85); board_x0=53.2;board_y0=25.5
def xy(x,y):return (round(origin[0]+(x-board_x0)*SCALE),round(origin[1]+(y-board_y0)*SCALE))
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f_title=ImageFont.truetype(bold,31); f_body=ImageFont.truetype(font,21); f_small=ImageFont.truetype(font,18)
# Group by actual physical copper layer; within each layer, keep source-file ordering.
order=['B.Cu','In3.Cu','In2.Cu','In4.Cu','F.Cu','In1.Cu']
ordered=[seg for layer in order for seg in segments if seg[-1]==layer]
assert len(ordered)==len(segments)
base=Image.new('RGB',(W,H),(7,13,23))
d=ImageDraw.Draw(base)
# Board outline is stylized; the route segments and via coordinates are exact.
box=(xy(54.3,26.4),xy(96.1,68.7)); rect=[box[0][0],box[0][1],box[1][0],box[1][1]]
d.rounded_rectangle(rect,radius=40,fill=(12,37,44),outline=(61,104,109),width=3)
for bx,by in [(59.2,31),(90.7,31),(59.2,64.0),(90.7,64.0)]:
    px,py=xy(bx,by)
    d.ellipse((px-22,py-22,px+22,py+22),fill=(7,13,23),outline=(102,119,125),width=4)
d.rounded_rectangle((40,22,1240,84),radius=18,fill=(13,26,39))
d.text((58,35),'PCB ROUTING',font=f_title,fill=(245,247,250))
d.text((842,137),'6 COPPER LAYERS',font=f_body,fill=(225,233,239))
d.text((842,175),f'{len(segments):,} routed segments',font=f_small,fill=(156,187,201))
d.text((842,205),f'{len(vias):,} vias',font=f_small,fill=(156,187,201))
for i,lay in enumerate(order):
    y=283+i*49
    d.rounded_rectangle((841,y+2,861,y+22),radius=4,fill=COLORS[lay])
    d.text((880,y-1),lay.replace('.Cu',''),font=f_body,fill=(221,229,235))
d.text((840,625),'KICAD 10',font=f_small,fill=(183,202,211))
d.text((840,657),'Actual routed geometry',font=f_small,fill=(183,202,211))

proc=subprocess.Popen(['ffmpeg','-y','-nostdin','-hide_banner','-loglevel','error','-f','rawvideo',
                        '-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
                        '-an','-c:v','libx264','-threads','4','-preset','veryfast','-crf','20',
                        '-pix_fmt','yuv420p','-movflags','+faststart',str(OUTPUT)],stdin=subprocess.PIPE)
try:
    N=FPS*DURATION
    for i in range(N):
        frame=base.copy(); dr=ImageDraw.Draw(frame)
        t=i/(N-1)
        # First two seconds establish board, then smoothly draw all routed segments.
        reveal=min(1,max(0,(t-0.08)/0.79))
        count=round(len(ordered)*reveal)
        for (a,b,c,e,w,layer) in ordered[:count]:
            thickness=max(2,round(w*SCALE))
            dr.line((xy(a,b),xy(c,e)),fill=COLORS[layer],width=thickness,joint='curve')
        # The actual via coordinates appear as the routed layers are revealed.
        via_count=round(len(vias)*reveal)
        for a,b,w in vias[:via_count]:
            cx,cy=xy(a,b); rad=max(2,round(w*SCALE*.38))
            dr.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=(216,192,110),outline=(40,66,84),width=1)
        # Timeline and progress indicator.
        dr.rounded_rectangle((840,592,1210,602),radius=4,fill=(34,58,73))
        dr.rounded_rectangle((840,592,840+round(370*reveal),602),radius=4,fill=(82,203,232))
        dr.text((840,566),'COPPER ROUTE VIEW',font=f_small,fill=(146,188,206))
        assert proc.stdin is not None
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    code=proc.wait()
    if code:raise RuntimeError(f'ffmpeg exited {code}')
except Exception:
    proc.kill();raise
print(f'ROUTING VIDEO {OUTPUT} segments={len(segments)} vias={len(vias)} secs={DURATION}',flush=True)
