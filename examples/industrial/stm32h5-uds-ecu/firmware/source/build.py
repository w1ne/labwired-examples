#!/usr/bin/env python3
"""Build the editable application using verified offline vendor sources."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,time
from verify_export import verify_export

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def loadable_image(path):
    import struct
    data=Path(path).read_bytes()
    if data[:7]!=b'\x7fELF\x01\x01\x01':raise RuntimeError('Expected little-endian ELF32')
    h=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
    if h[1]!=40:raise RuntimeError('Expected ARM ELF')
    segments=[]
    for i in range(h[9]):
        p=struct.unpack_from('<IIIIIIII',data,h[4]+i*h[8])
        if p[0]!=1:continue
        segments.append({'virtualAddress':p[2],'physicalAddress':p[3],'fileBytes':p[4],'memoryBytes':p[5],'flags':p[6],'alignment':p[7],'sha256':hashlib.sha256(data[p[1]:p[1]+p[4]]).hexdigest()})
    return {'entry':h[3],'machine':h[1],'flags':h[6],'segments':segments}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--target',default='all');ap.add_argument('--verify-release',action='store_true')
    args=ap.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    c=json.loads((ROOT/'source/config.json').read_text())
    roots={key:ROOT/spec['archivePath'] for key,spec in c['vendors'].items()}
    if not verify_export(ROOT,roots):raise RuntimeError('Use the complete extracted source archive for this offline builder')
    version=subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0]
    toolchain=json.loads((ROOT/'source/toolchain.json').read_text())
    if version!=toolchain['compiler']:raise RuntimeError('Compiler version differs from the recorded build')
    for item in toolchain['files']:
        if item['kind']=='program':p=Path(shutil.which(item['query']))
        else:p=Path(subprocess.check_output(['arm-none-eabi-gcc',*c['cpuFlags'],item['query']],text=True).strip())
        if sha(p)!=item['sha256']:raise RuntimeError('Toolchain bytes differ: '+item['query'])
    targets=[t for t in c['targets'] if args.target in ('all',t['name'])]
    if not targets:raise RuntimeError('Unknown target '+args.target)
    before={rel:sha(ROOT/rel) for rel in c['applicationFiles']}
    record={'schema':'labwired.complete-source-rebuild.v1','compiler':version,'sourceBefore':before,'targets':[],'physicalHardwareTested':False}
    for target in targets:
        target_out=out/target['name'];target_out.mkdir(parents=True,exist_ok=True)
        variables={k:str(ROOT/v) for k,v in target['makeDependencies'].items()}
        variables[target['outputVariable']]=str(target_out/target['outputValue']) if target['outputValue'] else str(target_out)
        cmd=['make','-j2','all',*[k+'='+v for k,v in variables.items()]]
        start=time.monotonic();log=out/(target['name']+'-build.log')
        with log.open('wb') as f:r=subprocess.run(cmd,cwd=ROOT/target['directory'],stdout=f,stderr=subprocess.STDOUT)
        result={'target':target['name'],'command':cmd,'directory':str(ROOT/target['directory']),'exit':r.returncode,'seconds':time.monotonic()-start,'log':log.name}
        record['targets'].append(result);(out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
        if r.returncode:raise SystemExit(r.returncode)
        result['artifacts']={}
        for ext in ['elf','bin']:
            p=target_out/(target['artifactStem']+'.'+ext)
            result['artifacts'][ext]={'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p),'acceptedSha256':target['expected'][ext],'matchesAccepted':sha(p)==target['expected'][ext]}
        result['flashImageMatchesAccepted']=result['artifacts']['bin']['matchesAccepted']
        result['loadableImage']=loadable_image(target_out/(target['artifactStem']+'.elf'))
        result['loadableImageMatchesAccepted']=result['loadableImage']==target['expectedLoadableImage']
        if args.verify_release and not (result['flashImageMatchesAccepted'] and result['loadableImageMatchesAccepted']):
            (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');raise RuntimeError('Rebuilt flash bytes differ: '+target['name'])
    record['sourceAfter']={rel:sha(ROOT/rel) for rel in c['applicationFiles']};record['sourceUnchanged']=record['sourceBefore']==record['sourceAfter']
    if not record['sourceUnchanged']:raise RuntimeError('Application changed during build')
    record['scope']='Exact flash bytes and ELF PT_LOAD addresses, bytes, memory extents, flags and entry comparison against the accepted image. ELF debug paths can differ after relocation; each ELF digest and equality result is explicit. No physical execution is implied.'
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'targets':[{k:v for k,v in t.items() if k not in ('command','directory')} for t in record['targets']],'sourceUnchanged':record['sourceUnchanged']},indent=2))
if __name__=='__main__':main()
