"""Produce the 1080-frame, 18-second master without realtime timing dependencies."""
import subprocess, time, json, hashlib, argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--work-dir',type=Path,default=Path(__file__).resolve().parent)
BASE=parser.parse_args().work_dir.resolve()
started=time.time()
with (BASE/'render.log').open('w') as rlog, (BASE/'encode.log').open('w') as elog:
    renderer=subprocess.Popen([str(BASE/'render_cpu'),str(BASE/'scene.bin'),'0','1080','1920','1080','2',str(BASE/'lcd.rgb'),'320','240'],stdout=subprocess.PIPE,stderr=rlog)
    encoder=subprocess.Popen(['ffmpeg','-hide_banner','-y','-f','image2pipe','-vcodec','ppm','-framerate','60','-i','pipe:0','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','12','-pix_fmt','yuv420p','-fps_mode','passthrough','-movflags','+faststart',str(BASE/'geometry-master.mp4')],stdin=renderer.stdout,stdout=elog,stderr=elog)
    renderer.stdout.close()
    er=encoder.wait();rr=renderer.wait()
    if er or rr:raise RuntimeError(f'renderer={rr},encoder={er}')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(BASE/'geometry-master.mp4')]))
receipt={'duration_wall_seconds':round(time.time()-started,2),'probe':probe,'master_sha256':hashlib.sha256((BASE/'geometry-master.mp4').read_bytes()).hexdigest(),'frame_log_lines':len((BASE/'render.log').read_text().splitlines()),'fps_semantics':'1080 independently projected poses at t = frame / 60; offline frame generation, not realtime UI performance'}
(BASE/'render-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'complete':True,'path':str(BASE/'geometry-master.mp4'),'wall_seconds':receipt['duration_wall_seconds'],'frames':receipt['frame_log_lines']}))
