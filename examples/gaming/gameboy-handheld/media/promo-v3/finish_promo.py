#!/usr/bin/env python3
"""Add restrained titles and the original synthesized score to the exact-pose master."""
import argparse, json, pathlib, subprocess

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',type=pathlib.Path,required=True)
    parser.add_argument('--audio',type=pathlib.Path,required=True)
    parser.add_argument('--captions',type=pathlib.Path,default=pathlib.Path(__file__).with_name('promo.ass'))
    parser.add_argument('--output',type=pathlib.Path,required=True)
    args=parser.parse_args()
    # The caller supplies ordinary local paths. No shell invocation or optical-flow filter is used.
    captions=str(args.captions.resolve()).replace('\\','\\\\').replace(':','\\:').replace("'","\\'")
    filters=(f"[0:v]subtitles=filename='{captions}'[v];"
             "[1:a]atrim=start=0:end=18,asetpts=PTS-STARTPTS,volume=-2dB,"
             "afade=t=in:st=0:d=0.08,afade=t=out:st=17.45:d=0.55[a]")
    subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(args.video),'-i',str(args.audio),
        '-filter_complex',filters,'-map','[v]','-map','[a]',
        '-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p',
        '-r','60','-frames:v','1080','-c:a','aac','-b:a','192k','-ar','48000',
        '-t','18','-movflags','+faststart',str(args.output)],check=True)
    probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(args.output)],capture_output=True,text=True,check=True)
    args.output.with_suffix('.ffprobe.json').write_text(probe.stdout)
    print(json.dumps({'output':str(args.output.resolve()),'duration':18,'fps':60,'frames':1080,'decorative_lines':False}))

if __name__=='__main__': main()
