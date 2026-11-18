#!/usr/bin/env python3
"""Finish the existing 18-second CAD movie with the requested short brand ending.

The 59-part geometry and true framebuffer movie are reused without a new render.
The only new imagery is precise typography on a continuous neutral background.
"""
import argparse, hashlib, json, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
PREVIOUS=BASE.parent/'promo-v3'
W,H,FPS=1920,1080,60
DURATION=20.0
BRAND='LabWired'
TAGLINE='The easy way to make hardware with agents.'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def card(output_dir, font_dir):
    yy,xx=np.mgrid[:H,:W]
    radius=np.clip(((xx-W*.5)/(W*.8))**2+((yy-H*.47)/(H*1.0))**2,0,1)
    center=np.array([246.,248.,249.]);edge=np.array([235.,240.,243.])
    pixels=(center[None,None,:]*(1-radius[:,:,None])+edge[None,None,:]*radius[:,:,None]).astype(np.uint8)
    im=Image.fromarray(pixels,'RGB');d=ImageDraw.Draw(im)
    brand_font=ImageFont.truetype(str(font_dir/'DejaVuSans-Bold.ttf'),112)
    tagline_font=ImageFont.truetype(str(font_dir/'DejaVuSans.ttf'),40)
    d.text((W/2,478),BRAND,font=brand_font,fill='#212e3b',anchor='mm')
    d.text((W/2,603),TAGLINE,font=tagline_font,fill='#51606d',anchor='mm')
    im.save(output_dir/'end-card.png')
    return {'brand':BRAND,'tagline':TAGLINE,'font':'DejaVu Sans / Bold','wordmark_px':112,'tagline_px':40,'decorative_lines':False}

def score(audio, output_dir):
    with wave.open(str(audio),'rb') as f:
        assert f.getnchannels()==2 and f.getsampwidth()==2 and f.getframerate()==48000
        sr=f.getframerate();src=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float64)/32768.
    n=round(sr*DURATION);mix=np.zeros((n,2),dtype=np.float64)
    # Keep the existing original cue through the action. Its final bar begins
    # at 28.125s (bar15 at128BPM) and contains the authored tonic resolution.
    # Place that existing closing bar at18.0s, as the brand card becomes opaque.
    times=np.arange(n)/sr
    first=np.minimum(np.arange(n),len(src)-1)
    mix[:round(18.04*sr)]=src[first[:round(18.04*sr)]]
    valid=(times>=17.96)&(times<19.875)
    idx=np.rint((times[valid]+10.125)*sr).astype(int)
    tail=src[np.minimum(idx,len(src)-1)]
    a=np.clip((times[valid]-17.96)/.08,0,1)
    blend=.5-.5*np.cos(np.pi*a)
    mix[valid]=mix[valid]*(1-blend[:,None])+tail*blend[:,None]
    # Original score already has its composed closing decay. Silence follows
    # the complete ending; nothing is time-stretched or pitched.
    mix[times>=19.875]=0
    fadein=np.clip(times/.08,0,1)
    mix*=((.5-.5*np.cos(np.pi*fadein))*10**(-2/20))[:,None]
    pcm=np.rint(np.clip(mix,-1,1)*32767).astype('<i2')
    out=output_dir/'ending-score.wav'
    with wave.open(str(out),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes(pcm.tobytes())
    return {'source':str(audio),'source_sha256':sha(audio),'source_bpm':128,'closing_bar_source_seconds':[28.125,30.0],'closing_bar_output_seconds':[18.0,19.875],'splice_crossfade_seconds':[17.96,18.04],'output_duration_seconds':20,'sample_peak_dbfs':float(20*np.log10(np.max(np.abs(mix)))),'ending_silence_seconds':.125,'provenance':'Original synthesized melody and score; same authored tonic ending repositioned, no external media.'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',type=Path,default=PREVIOUS/'build/motion/geometry-master.mp4')
    parser.add_argument('--captions',type=Path,default=BASE/'promo.ass')
    parser.add_argument('--audio',type=Path,default=PREVIOUS/'build/audio/wire-runner-original-30s.wav')
    parser.add_argument('--output',type=Path,default=BASE/'build/LabWired-KernelCAD-BrickBreaker.mp4')
    parser.add_argument('--work-dir',type=Path,help='Generated assets and reports; defaults to the output movie directory')
    parser.add_argument('--font-dir',type=Path,default=Path('/usr/share/fonts/truetype/dejavu'),help='Directory containing DejaVuSans.ttf and DejaVuSans-Bold.ttf')
    parser.add_argument('--assets-only',action='store_true')
    args=parser.parse_args()
    output_dir=(args.work_dir or args.output.parent).resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    visual=card(output_dir,args.font_dir);music=score(args.audio,output_dir)
    # Clear the action captions just as the closing dissolve starts.
    ass=args.captions.read_text().replace('0:00:18.00','0:00:17.65')
    (output_dir/'promo.ass').write_text(ass)
    provenance={'video_input':str(args.video),'video_input_sha256':sha(args.video),'card':visual,'score':music,'duration_seconds':20,'fps':60,'frames':1200,'transition':{'kind':'dissolve','start_seconds':17.6,'duration_seconds':.4,'frames':24},'full_card_seconds':[18,20],'geometry_rerendered':False,'scope':'Offline CAD footage with real ROM framebuffer, followed by a typographic brand card; not realtime UI capture.'}
    if args.assets_only:
        (output_dir/'ending-provenance.json').write_text(json.dumps(provenance,indent=2));print('ASSETS_READY');return
    cap=str((output_dir/'promo.ass').resolve()).replace('\\','\\\\').replace(':','\\:').replace("'","\\'")
    filters=f"[0:v]subtitles=filename='{cap}',format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS,fps=60[film];[1:v]format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS,fps=60[card];[film][card]xfade=transition=fade:duration=0.4:offset=17.6,format=yuv420p[v]"
    with (output_dir/'encode.log').open('w') as log:
        subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(args.video),'-loop','1','-framerate','60','-t','2.4','-i',str(output_dir/'end-card.png'),'-i',str(output_dir/'ending-score.wav'),'-filter_complex_threads','2','-filter_complex',filters,'-map','[v]','-map','2:a','-c:v','libx264','-threads','4','-preset','slow','-crf','18','-pix_fmt','yuv420p','-r','60','-frames:v','1200','-c:a','aac','-b:a','192k','-ar','48000','-t','20','-movflags','+faststart',str(args.output)],stdout=log,stderr=log,check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(args.output)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert video['nb_frames']=='1200' and video['r_frame_rate']=='60/1'
    assert abs(float(probe['format']['duration'])-20)<.002
    provenance['output_sha256']=sha(args.output);provenance['output_bytes']=args.output.stat().st_size
    (output_dir/'ending-provenance.json').write_text(json.dumps(provenance,indent=2))
    (output_dir/'ffprobe.json').write_text(json.dumps(probe,indent=2))
    print(json.dumps({'output':str(args.output),'duration':20,'fps':60,'frames':1200,'bytes':args.output.stat().st_size,'sha256':provenance['output_sha256']}),flush=True)

if __name__=='__main__':main()
