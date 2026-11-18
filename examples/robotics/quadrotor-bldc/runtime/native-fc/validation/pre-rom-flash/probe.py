from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).parent;r=json.loads((p/'receipt.json').read_text());env=os.environ.copy();env.pop('LABWIRED_RP2350_BOOTROM',None);start=time.time()
with(p/'runtime.log').open('w') as log:q=subprocess.run(r['argv'],cwd=p,env=env,stdout=log,stderr=subprocess.STDOUT)
r['exit']=q.returncode;r['seconds']=time.time()-start;(p/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
