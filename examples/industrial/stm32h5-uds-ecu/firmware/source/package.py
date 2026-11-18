#!/usr/bin/env python3
"""Create a deterministic, complete firmware source archive from pinned clean trees."""
from pathlib import Path
import argparse,gzip,hashlib,io,json,subprocess,tarfile

ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    c=json.loads((ROOT/'source/config.json').read_text())
    ap=argparse.ArgumentParser()
    for key in c['vendors']:ap.add_argument('--'+key.lower(),required=True,type=Path)
    args=ap.parse_args()
    roots={k:getattr(args,k.lower()).resolve() for k in c['vendors']}
    for pin in c['sourcePins']:
        d=roots[pin['root']]/pin.get('subPath','')
        got=subprocess.check_output(['git','-C',str(d),'rev-parse','HEAD'],text=True).strip()
        if got!=pin['revision']:raise RuntimeError('Revision mismatch: '+pin['name'])
        subprocess.run(['git','-C',str(d),'diff','--quiet','HEAD','--','.'],check=True)
        if pin.get('tree'):
            got=subprocess.check_output(['git','-C',str(d),'rev-parse','HEAD:'+pin['treePath']],text=True).strip()
            if got!=pin['tree']:raise RuntimeError('Vendored tree mismatch')
    files={}
    vendors=[]
    for key,spec in c['vendors'].items():
        base=roots[key]
        selected=set()
        for pattern in spec['patterns']:
            matches=[p for p in base.glob(pattern) if p.is_file()]
            if not matches:raise RuntimeError('Empty vendor selection: '+key+' '+pattern)
            selected.update(matches)
        for p in sorted(selected):
            if p.is_symlink():raise RuntimeError('Unexpected source symlink: '+str(p))
            rel=str(Path(spec['archivePath'])/p.relative_to(base));data=p.read_bytes()
            files[rel]=data;vendors.append({'path':rel,'bytes':len(data),'sha256':sha(data)})
    manifest={'schema':'labwired.vendor-source-export.v1','sourcePins':c['sourcePins'],'files':sorted(vendors,key=lambda x:x['path'])}
    (ROOT/'source/vendor-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for rel in c['applicationFiles']:
        p=ROOT/rel
        if not p.is_file() or p.is_symlink():raise RuntimeError('Missing application source: '+rel)
        files[rel]=p.read_bytes()
    entries=[]
    for entry in c['entries']:
        data=files[entry['path']]
        entries.append(dict(entry,bytes=len(data),sha256=sha(data)))
    destination=ROOT/'source'/c['archiveName']
    with destination.open('wb') as f,gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0,compresslevel=9) as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for rel,data in sorted(files.items()):
            info=tarfile.TarInfo(rel);info.size=len(data);info.mode=0o644;info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
            tar.addfile(info,io.BytesIO(data))
    data=destination.read_bytes()
    if len(data)>16*1024*1024:raise RuntimeError('Source archive exceeds existing 16 MiB artifact cap')
    bundle={'schema':'labwired.complete-firmware-source.v1','archive':c['archiveName'],'bytes':len(data),'sha256':sha(data),'entries':entries,'sourcePins':c['sourcePins'],'files':[{'path':p,'bytes':len(d),'sha256':sha(d)} for p,d in sorted(files.items())]}
    (ROOT/'source/source-bundle.json').write_text(json.dumps(bundle,indent=2)+'\n')
    print(json.dumps({k:v for k,v in bundle.items() if k not in ('files','sourcePins')},indent=2))
if __name__=='__main__':main()
