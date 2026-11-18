"""Lossless geometry conversion for the recording-only CPU triangle renderer."""
import json, struct, hashlib, argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--work-dir',type=Path,default=Path(__file__).resolve().parent)
BASE=parser.parse_args().work_dir.resolve()
source=json.loads((BASE/'mesh.json').read_text())
records=[]
for part in source['features']:
    vertices=[]; indices=[]
    for face in part['faces']:
        off=len(vertices)
        v=face['vertices']; n=face['normals']
        vertices += [(*v[i:i+3],*n[i:i+3],0.,0.) for i in range(0,len(v),3)]
        indices += [x+off for x in face['indices']]
    records.append(dict(name=part['displayName'],color=part['material']['baseColor'],metal=part['material'].get('metalness',0),kind=0,vertices=vertices,indices=indices))
for part in json.loads((BASE.parent/'pcb/copper-mesh.json').read_text())['meshes']:
    v=part['positions'];n=part['normals']
    vertices=[(*v[i:i+3],*n[i:i+3],0.,0.) for i in range(0,len(v),3)]
    records.append(dict(name=part['name'],color=part['color'],metal=.65,kind=2 if part['net']==12 else 0,vertices=vertices,indices=part['indices']))
records.append(dict(name='LCD_FRAMEBUFFER',color='#829d58',metal=0,kind=1,
    vertices=[(-24.48,88.64,26.815,0,0,1,0,1),(24.48,88.64,26.815,0,0,1,1,1),(24.48,125.36,26.815,0,0,1,1,0),(-24.48,125.36,26.815,0,0,1,0,0)],indices=[0,1,2,0,2,3]))
# A photo material on the controller envelope is optional; no package shape is invented.
if (BASE/'controller.ppm').exists():
    records.append(dict(name='A1-PHOTO_MATERIAL',color='#20252b',metal=0,kind=3,
        vertices=[(-10.4,84.8,5.83,0,0,-1,1,1),(10.4,84.8,5.83,0,0,-1,0,1),(10.4,137.2,5.83,0,0,-1,0,0),(-10.4,137.2,5.83,0,0,-1,1,0)],indices=[0,2,1,0,3,2]))
with (BASE/'scene.bin').open('wb') as out:
    out.write(b'KCADCPU1');out.write(struct.pack('<I',len(records)))
    for r in records:
        name=r['name'].encode();out.write(struct.pack('<I',len(name)));out.write(name)
        color=[int(r['color'].lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
        out.write(struct.pack('<4f3I',*color,r['metal'],r['kind'],len(r['vertices']),len(r['indices'])))
        for v in r['vertices']:out.write(struct.pack('<8f',*v))
        out.write(struct.pack('<%dI'%len(r['indices']),*r['indices']))
(BASE/'render-provenance.json').write_text(json.dumps({
    'purpose':'Offline recording of immutable KernelCAD native triangle geometry; presentation-only rigid-body poses',
    'mesh_url':'https://mesh.kernelcad.com/mesh-artifacts/kQAFdaQs/v3.json?provenance=9ae8dcdbbc9bf46c519af88ff9c39a9d3bfd4957431f351ea22fba4e0669e196',
    'mesh_sha256':hashlib.sha256((BASE/'mesh.json').read_bytes()).hexdigest(),
    'feature_count':59,'revision':3,'model':'kQAFdaQs','source_provenance':source['provenance'],
    'fps':60,'duration_seconds':18,'frame_count':1080,
    'routing_source':'../pcb/routing.json',
    'render_method':'Per-frame exact geometry projection, triangle depth buffer, smooth normals, two directional lights, shadow map, four subpixel samples',
    'disclosures':['Offline CAD rendering, not a recording of realtime KernelCAD UI','Exploded offsets are presentation transforms, not a saved design change','Selected routing is a physical net highlight, not measured analog current','Controller package details use an optional sourced photo material; source geometry remains envelope-level'],
},indent=2))
print('Wrote',len(records),'objects',sum(len(r['indices'])//3 for r in records),'triangles')
if (BASE/'lcd-state.json').exists():
    state=json.loads((BASE/'lcd-state.json').read_text())
    filtered=[0.]*5
    with (BASE/'controls.bin').open('wb') as out:
        for frame in state:
            # Smooth three-frame mechanical indication driven only by recorded GPIO intent.
            mask=frame['joypad']
            for i,bit in enumerate([16,32,1,2,8]):filtered[i]+=.5*((1. if mask&bit else 0.)-filtered[i])
            out.write(struct.pack('<5f',*filtered))
